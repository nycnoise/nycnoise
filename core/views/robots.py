from django.http import HttpResponse

from ..bots import DISALLOWED_CRAWLERS
from ..utils_datemath import FIRST_MONTH_START, get_current_new_york_datetime


def archive_years_to_hide_from_applebot():
    # applebot (siri / spotlight search) is welcome on the homepage and on the
    # current year, but it re-crawls old month pages several times an hour and
    # those are the heaviest pages on the site. every past year gets a
    # "Disallow: /YYYY-" prefix, computed so this never needs updating.
    current_year = get_current_new_york_datetime().year
    return list(range(FIRST_MONTH_START.year, current_year))


def robots_txt(request):
    lines = []
    for name in DISALLOWED_CRAWLERS:
        lines += [f"User-agent: {name}", "Disallow: /", ""]
    lines += ["User-agent: Applebot"]
    for year in archive_years_to_hide_from_applebot():
        lines.append(f"Disallow: /{year}-")
    lines.append("")
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
