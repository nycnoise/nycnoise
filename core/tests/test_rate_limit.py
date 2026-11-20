import base64
import pickle

from core.middleware import client_address, is_heavy_page
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import RequestFactory, TransactionTestCase

LIMIT = settings.RATE_LIMIT_PAGE_VIEWS


class RateLimitTestCase(TransactionTestCase):
    def setUp(self):
        cache.clear()

    def _get(self, path, ip, **extra):
        return self.client.get(path, HTTP_TRUE_CLIENT_IP=ip, **extra)

    def test_homepage_and_month_pages_count_against_the_limit(self):
        for i in range(LIMIT):
            response = self._get("/" if i % 2 else "/2024-01/", "203.0.113.5")
            self.assertEqual(response.status_code, 200, f"request {i}")
        # request number LIMIT + 1 is refused, with a tiny body
        response = self._get("/2024-02/", "203.0.113.5")
        self.assertEqual(response.status_code, 429)
        self.assertLess(len(response.content), 100)
        self.assertEqual(
            response.headers["Retry-After"], str(settings.RATE_LIMIT_WINDOW_SECONDS)
        )
        response = self._get("/", "203.0.113.5")
        self.assertEqual(response.status_code, 429)

    def test_other_addresses_are_not_affected(self):
        for _ in range(LIMIT + 5):
            self._get("/", "203.0.113.5")
        self.assertEqual(self._get("/", "203.0.113.5").status_code, 429)
        self.assertEqual(self._get("/", "203.0.113.6").status_code, 200)
        self.assertEqual(self._get("/2024-01/", "198.51.100.1").status_code, 200)

    def test_cheap_pages_are_never_counted_or_limited(self):
        for _ in range(LIMIT + 5):
            self._get("/", "203.0.113.5")
        self.assertEqual(self._get("/", "203.0.113.5").status_code, 429)
        # event pages, ics, robots, sitemap, static pages: still served
        for path in ["/robots.txt", "/sitemap.xml", "/submit-event"]:
            self.assertEqual(self._get(path, "203.0.113.5").status_code, 200, path)
        # and hammering cheap pages does not use up the heavy page budget
        cache.clear()
        for _ in range(LIMIT * 3):
            self._get("/robots.txt", "203.0.113.7")
        self.assertEqual(self._get("/", "203.0.113.7").status_code, 200)

    def test_head_requests_are_not_counted(self):
        # uptimerobot does a HEAD on / every few minutes
        for _ in range(LIMIT * 2):
            self.client.head("/", HTTP_TRUE_CLIENT_IP="203.0.113.8")
        self.assertEqual(self._get("/", "203.0.113.8").status_code, 200)

    def test_x_forwarded_for_is_ignored_and_true_client_ip_wins(self):
        rf = RequestFactory()
        request = rf.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1, 2.2.2.2")
        request.META["HTTP_TRUE_CLIENT_IP"] = "203.0.113.9"
        self.assertEqual(client_address(request), "203.0.113.9")
        # no edge header at all (local dev): the socket address, even when
        # a forged x-forwarded-for carries a public address
        request = rf.get("/", HTTP_X_FORWARDED_FOR="1.1.1.1", REMOTE_ADDR="10.0.0.2")
        self.assertEqual(client_address(request), "10.0.0.2")
        request = rf.get(
            "/", HTTP_X_FORWARDED_FOR="8.8.8.8, 9.9.9.9", REMOTE_ADDR="127.0.0.1"
        )
        self.assertEqual(client_address(request), "127.0.0.1")
        # the edge header wins over the socket address, and also over the
        # other spoofable headers ipware knows about
        request = rf.get(
            "/",
            HTTP_X_REAL_IP="8.8.8.8",
            HTTP_CF_CONNECTING_IP="8.8.4.4",
            REMOTE_ADDR="10.0.0.2",
        )
        request.META["HTTP_TRUE_CLIENT_IP"] = "203.0.113.9"
        self.assertEqual(client_address(request), "203.0.113.9")
        # ipv6 works too
        request = rf.get("/", REMOTE_ADDR="10.0.0.2")
        request.META["HTTP_TRUE_CLIENT_IP"] = "2001:db8::1"
        self.assertEqual(client_address(request), "2001:db8::1")

    def test_forged_forwarded_for_cannot_dodge_the_limit(self):
        # same true client, rotating forged x-forwarded-for values: one bucket
        for i in range(LIMIT + 1):
            response = self.client.get(
                "/",
                HTTP_TRUE_CLIENT_IP="203.0.113.77",
                HTTP_X_FORWARDED_FOR=f"10.1.{i}.1",
            )
        self.assertEqual(response.status_code, 429)

    def test_which_paths_are_heavy(self):
        rf = RequestFactory()
        for path in ["/", "/2024-01/", "/2026-12/"]:
            self.assertTrue(is_heavy_page(rf.get(path)), path)
        for path in [
            "/event/1",
            "/event/1/ics",
            "/2024-01",
            "/drone-party/",
            "/robots.txt",
            "/static/x.css",
        ]:
            self.assertFalse(is_heavy_page(rf.get(path)), path)
        # search is the index view with a full text query: counted too
        self.assertTrue(is_heavy_page(rf.get("/?s=noise")))
        self.assertFalse(is_heavy_page(rf.head("/")))

    def test_counter_really_lives_in_the_database(self):
        self._get("/2024-03/", "203.0.113.42")
        self._get("/2024-03/", "203.0.113.42")
        with connection.cursor() as cursor:
            cursor.execute(
                "select cache_key, value from django_cache_table "
                "where cache_key like %s",
                ["%ratelimit:203.0.113.42:%"],
            )
            rows = cursor.fetchall()
        self.assertEqual(len(rows), 1, rows)
        # the stored value is a pickle: decode it to check the count is 2
        self.assertEqual(pickle.loads(base64.b64decode(rows[0][1])), 2)
