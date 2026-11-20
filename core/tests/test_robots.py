from datetime import datetime

from core.bots import DISALLOWED_CRAWLERS
from dateutil import tz
from django.test import TransactionTestCase

NYCTZ = tz.gettz("America/New_York")


class RobotsTxtTestCase(TransactionTestCase):
    def test_robots_txt_is_served_directly_without_redirect(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"].startswith("text/plain"))

    def test_robots_txt_disallows_every_listed_crawler_and_nobody_else(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertGreater(len(DISALLOWED_CRAWLERS), 10)
        for name in DISALLOWED_CRAWLERS:
            self.assertIn(f"User-agent: {name}\nDisallow: /\n", body)
        # exact line match: "Applebot-Extended" is fully disallowed,
        # "Applebot" only gets the archive years (tested separately)
        user_agent_lines = [l for l in body.splitlines() if l.startswith("User-agent")]
        for name in ["Googlebot", "bingbot", "facebookexternalhit"]:
            self.assertNotIn(f"User-agent: {name}", user_agent_lines)
        self.assertIn("User-agent: Applebot-Extended", user_agent_lines)
        self.assertNotIn("User-agent: Applebot\nDisallow: /\n", body)
        # everyone else may crawl everything, and we don't advertise
        # private urls like the admin by disallowing them
        self.assertIn("User-agent: *\nAllow: /\n", body)
        for private in ["admin", "internal-api", "venue-autocomplete"]:
            self.assertNotIn(private, body)
        self.assertIn("Sitemap: https://nyc-noise.com/sitemap.xml", body)

    def test_applebot_is_kept_off_past_years_only(self):
        body = self.client.get("/robots.txt").content.decode()
        groups = [g.splitlines() for g in body.split("\n\n")]
        applebot = [g for g in groups if g and g[0] == "User-agent: Applebot"]
        self.assertEqual(len(applebot), 1)
        disallows = applebot[0][1:]
        current_year = datetime.now().astimezone(NYCTZ).year
        expected = [f"Disallow: /{y}-" for y in range(2018, current_year)]
        self.assertEqual(disallows, expected)
        # sanity: the archive is hidden, this year and the homepage are not
        self.assertIn("Disallow: /2024-", disallows)
        self.assertIn(f"Disallow: /{current_year - 1}-", disallows)
        self.assertNotIn(f"Disallow: /{current_year}-", disallows)
        self.assertNotIn("Disallow: /", disallows)

    def test_blocked_crawlers_can_still_read_robots_txt(self):
        for ua in [
            "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
            "Mozilla/5.0 (compatible; MJ12bot/v2.0.7; http://mj12bot.com/)",
            "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)",
        ]:
            response = self.client.get("/robots.txt", HTTP_USER_AGENT=ua)
            self.assertEqual(response.status_code, 200, ua)
            self.assertTrue(response.headers["Content-Type"].startswith("text/plain"))
            self.assertIn("Disallow: /", response.content.decode())
            # and they are still blocked everywhere else
            self.assertEqual(self.client.get("/", HTTP_USER_AGENT=ua).status_code, 403)

    def test_trailing_slash_variant_is_still_a_404_not_a_static_page(self):
        response = self.client.get("/robots.txt/")
        self.assertEqual(response.status_code, 404)
