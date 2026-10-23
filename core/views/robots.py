from django.http import HttpResponse

from ..bots import DISALLOWED_CRAWLERS


def robots_txt(request):
    lines = []
    for name in DISALLOWED_CRAWLERS:
        lines += [f"User-agent: {name}", "Disallow: /", ""]
    # on purpose no "Disallow" lines for everyone else: listing private urls
    # here would just advertise them.
    lines += [
        "User-agent: *",
        "Allow: /",
        "",
        "Sitemap: https://nyc-noise.com/sitemap.xml",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
