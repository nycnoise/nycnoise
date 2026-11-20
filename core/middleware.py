import re
import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseForbidden
from python_ipware import IpWare

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
        # blocked crawlers must still be able to read robots.txt: search
        # engines treat a 4xx robots.txt as "no rules, crawl everything",
        # so the polite ones would never learn that they're unwelcome.
        if request.path != "/robots.txt" and is_blocked_user_agent(
            request.META.get("HTTP_USER_AGENT", "")
        ):
            return HttpResponseForbidden("forbidden", content_type="text/plain")
        return self.get_response(request)


# the pages worth rate limiting: the homepage and the month archives. they are
# 50 to 100 kb each (gzipped) and are what scrapers re-fetch over and over.
# event pages, ics, gcal, static files etc are tiny and not counted.
_HEAVY_PATH_RE = re.compile(r"^/(\d{4}-\d{2}/)?$")


# on render, requests arrive through render's cloudflare edge, which sets
# True-Client-IP to the real visitor address. X-Forwarded-For is NOT in the
# precedence list on purpose: render appends to it instead of replacing it,
# so a client can forge the first value. locally there is no edge header and
# REMOTE_ADDR is the client itself.
# https://github.com/un33k/python-ipware
_ipware = IpWare(precedence=("HTTP_TRUE_CLIENT_IP", "REMOTE_ADDR"))


def client_address(request):
    ip, _trusted_route = _ipware.get_client_ip(request.META)
    return str(ip) if ip is not None else "unknown"


def is_heavy_page(request):
    return request.method == "GET" and _HEAVY_PATH_RE.match(request.path) is not None


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_heavy_page(request):
            window = settings.RATE_LIMIT_WINDOW_SECONDS
            # fixed window: the key changes every `window` seconds
            bucket = int(time.time()) // window
            key = f"ratelimit:{client_address(request)}:{bucket}"
            # add() only sets the key if it does not exist yet, so the first
            # request of a window creates it with its expiry
            cache.add(key, 0, timeout=window)
            try:
                count = cache.incr(key)
            except ValueError:
                # the key expired between add() and incr(), start over
                cache.add(key, 1, timeout=window)
                count = 1
            if count > settings.RATE_LIMIT_PAGE_VIEWS:
                response = HttpResponse(
                    "too many requests", status=429, content_type="text/plain"
                )
                response["Retry-After"] = str(window)
                return response
        return self.get_response(request)
