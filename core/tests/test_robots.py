from core.bots import DISALLOWED_CRAWLERS
from django.test import TransactionTestCase


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
        # exact line match: "Applebot-Extended" is disallowed but "Applebot" is not
        user_agent_lines = [l for l in body.splitlines() if l.startswith("User-agent")]
        for name in ["Googlebot", "bingbot", "Applebot", "facebookexternalhit"]:
            self.assertNotIn(f"User-agent: {name}", user_agent_lines)
        self.assertIn("User-agent: Applebot-Extended", user_agent_lines)
        # everyone else may crawl everything, and we don't advertise
        # private urls like the admin by disallowing them
        self.assertIn("User-agent: *\nAllow: /\n", body)
        for private in ["admin", "internal-api", "venue-autocomplete"]:
            self.assertNotIn(private, body)
        self.assertIn("Sitemap: https://nyc-noise.com/sitemap.xml", body)

    def test_trailing_slash_variant_is_still_a_404_not_a_static_page(self):
        response = self.client.get("/robots.txt/")
        self.assertEqual(response.status_code, 404)
