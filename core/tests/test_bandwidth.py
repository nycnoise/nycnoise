import uuid
from datetime import datetime

from core.models import Event, Venue
from dateutil import tz
from django.test import TransactionTestCase


class GzipAndEtagTestCase(TransactionTestCase):
    def setUp(self):
        venue = Venue.objects.create(name=f"venue {uuid.uuid4()}")
        Event.objects.create(
            venue=venue,
            title=f"event {uuid.uuid4()}",
            starttime=datetime.now().astimezone(tz.gettz("America/New_York")),
        )

    def test_homepage_is_gzipped_when_client_accepts_it(self):
        plain = self.client.get("/")
        self.assertEqual(plain.status_code, 200)
        self.assertNotIn("Content-Encoding", plain.headers)

        gzipped = self.client.get("/", HTTP_ACCEPT_ENCODING="gzip")
        self.assertEqual(gzipped.status_code, 200)
        self.assertEqual(gzipped.headers["Content-Encoding"], "gzip")
        self.assertLess(len(gzipped.content), len(plain.content) / 3)

    def test_homepage_has_etag_and_answers_304_on_match(self):
        first = self.client.get("/")
        self.assertEqual(first.status_code, 200)
        etag = first.headers["ETag"]
        self.assertTrue(etag)

        second = self.client.get("/", HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(second.status_code, 304)
        self.assertEqual(second.content, b"")

        # a non matching etag must still get the full page
        third = self.client.get("/", HTTP_IF_NONE_MATCH='"nope"')
        self.assertEqual(third.status_code, 200)
        self.assertGreater(len(third.content), 1000)

    def test_gzipped_response_etag_still_matches_on_second_request(self):
        first = self.client.get("/", HTTP_ACCEPT_ENCODING="gzip")
        etag = first.headers["ETag"]
        # gzip middleware turns the etag into a weak one
        self.assertTrue(etag.startswith("W/"))
        second = self.client.get(
            "/", HTTP_ACCEPT_ENCODING="gzip", HTTP_IF_NONE_MATCH=etag
        )
        self.assertEqual(second.status_code, 304)
