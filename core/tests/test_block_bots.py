from core.bots import DISALLOWED_CRAWLERS
from core.middleware import is_blocked_user_agent
from django.test import TransactionTestCase

BLOCKED = [
    "Mozilla/5.0 (compatible; GPTBot/1.2; +https://openai.com/gptbot)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; spider-feedback@bytedance.com)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/600.2.5 (KHTML, like Gecko) Version/8.0.2 Safari/600.2.5 (Amazonbot/0.1; +https://developer.amazon.com/support/amazonbot)",
    "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
    "Mozilla/5.0 (compatible; YouBot (+http://www.you.com))",
    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
    "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
    "Mozilla/5.0 (compatible; DotBot/1.2; +https://opensiteexplorer.org/dotbot)",
    "Mozilla/5.0 (Linux; Android 7.0;) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)",
    "meta-webindexer/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/web-crawlers)",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0",
    "  Mozilla/5.0  ",
    "claudebot",  # case insensitive
]

ALLOWED = [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Mozilla/5.0+(compatible; UptimeRobot/2.0; http://www.uptimerobot.com/)",
    "Feedly/1.0 (+http://www.feedly.com/fetcher.html; 1 subscribers)",
    "curl/8.7.1",
    "",
]


class BlockBotsTestCase(TransactionTestCase):
    def test_list_has_no_empty_or_whitespace_entries(self):
        self.assertGreater(len(DISALLOWED_CRAWLERS), 10)
        for name in DISALLOWED_CRAWLERS:
            self.assertEqual(name, name.strip())
            self.assertGreater(len(name), 3)

    def test_every_listed_crawler_name_is_blocked_on_its_own(self):
        for name in DISALLOWED_CRAWLERS:
            self.assertTrue(
                is_blocked_user_agent(f"Mozilla/5.0 (compatible; {name}/1.0)"), name
            )

    def test_blocked_user_agents_get_a_tiny_403_everywhere(self):
        for ua in BLOCKED:
            for url in ["/", "/2024-01/", "/robots.txt", "/static/scss/core.css"]:
                response = self.client.get(url, HTTP_USER_AGENT=ua)
                self.assertEqual(response.status_code, 403, (ua, url))
                self.assertLess(len(response.content), 100, (ua, url))

    def test_allowed_user_agents_get_the_page(self):
        for ua in ALLOWED:
            self.assertFalse(is_blocked_user_agent(ua), ua)
            response = self.client.get("/", HTTP_USER_AGENT=ua)
            self.assertEqual(response.status_code, 200, ua)
            self.assertGreater(len(response.content), 1000, ua)

    def test_request_with_no_user_agent_header_at_all_is_allowed(self):
        # feeds and odd clients sometimes send nothing. don't break them.
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
