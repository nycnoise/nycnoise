import re

from django.http import HttpResponseForbidden

from .bots import DISALLOWED_CRAWLERS

# user agents that get a 403 before any view runs. the crawler names come
# from core/bots.py (same list as robots.txt). the extras below are things
# that showed up in the access logs and don't identify themselves as crawlers.
_EXTRA_BLOCKED_SUBSTRINGS = [
    "HeadlessChrome",
]

# some scrapers send exactly this and nothing else as their user agent.
# matched on the whole string, so real browsers (which start with "Mozilla/5.0 (")
# are not affected.
_BLOCKED_EXACT_USER_AGENTS = {
    "Mozilla/5.0",
}

BLOCKED_USER_AGENT_RE = re.compile(
    "|".join(
        re.escape(name) for name in DISALLOWED_CRAWLERS + _EXTRA_BLOCKED_SUBSTRINGS
    ),
    re.IGNORECASE,
)


def is_blocked_user_agent(user_agent):
    user_agent = user_agent.strip()
    if user_agent in _BLOCKED_EXACT_USER_AGENTS:
        return True
    return BLOCKED_USER_AGENT_RE.search(user_agent) is not None


class BlockBotsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_blocked_user_agent(request.META.get("HTTP_USER_AGENT", "")):
            return HttpResponseForbidden("forbidden", content_type="text/plain")
        return self.get_response(request)
