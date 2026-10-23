# crawlers we don't want. this one list feeds both robots.txt (which the
# polite ones honor) and the user agent blocklist middleware (for the ones
# that don't). names are matched case-insensitively as substrings of the
# user agent string.
#
# NOT in this list on purpose, since they feed search and link previews:
# Googlebot, bingbot, Applebot, facebookexternalhit, DuckDuckBot

AI_CRAWLERS = [
    "GPTBot",
    "ChatGPT-User",
    "OAI-SearchBot",
    "ClaudeBot",
    "Claude-Web",
    "anthropic-ai",
    "PerplexityBot",
    "Perplexity-User",
    "YouBot",
    "CCBot",
    "Bytespider",
    "Amazonbot",
    "Applebot-Extended",
    "Google-Extended",
    "meta-externalagent",
    "meta-webindexer",
    "ImagesiftBot",
    "Diffbot",
    "omgili",
    "cohere-ai",
    "AI2Bot",
    "ElevenlabsCrawler",
    "LinkupBot",
    "SofyaBot",
    "AionBot",
    "PetalBot",
    "Timpibot",
    "Webzio-Extended",
]

SEO_CRAWLERS = [
    "AhrefsBot",
    "SemrushBot",
    "DotBot",
    "MJ12bot",
    "BLEXBot",
    "DataForSeoBot",
]

DISALLOWED_CRAWLERS = AI_CRAWLERS + SEO_CRAWLERS
