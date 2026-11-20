from datetime import datetime

from dateutil import relativedelta, tz

# DO NOT USE PYTZ <> DO NOT USE PYTZ <> DO NOT USE PYTZ
# https://blog.ganssle.io/articles/2018/03/pytz-fastest-footgun.html
NYCTZ = tz.gettz("America/New_York")


def get_current_new_york_datetime():
    return datetime.now().astimezone(NYCTZ)


def first_day_of_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_previous_current_next_month_start(dt):
    current_month_start = first_day_of_month(dt)

    return (
        current_month_start - relativedelta.relativedelta(months=1),
        current_month_start,
        current_month_start + relativedelta.relativedelta(months=1),
    )


def beginning_of_day(dt):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


# the range of month archive urls (/YYYY-MM/) that render and that the sitemap
# lists. anything outside of it is a 404, otherwise crawlers follow "next month"
# links forever (we saw bots fetching /2195-07/), and every empty month page
# is ~50 kb. the range is on purpose NOT based on the first/last event in the
# database, since a typo'd event in the year 3000 would reopen the trap.
FIRST_MONTH_START = datetime(2018, 1, 1, 0, 0, 0, 0, tzinfo=NYCTZ)
MONTHS_INTO_THE_FUTURE = 24


def last_valid_month_start():
    return first_day_of_month(
        get_current_new_york_datetime()
    ) + relativedelta.relativedelta(months=MONTHS_INTO_THE_FUTURE)


def is_valid_archive_month(month_start):
    return FIRST_MONTH_START <= month_start <= last_valid_month_start()
