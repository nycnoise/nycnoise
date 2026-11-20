import uuid
from datetime import datetime

from core.models import Event, Venue
from dateutil import tz
from django.test import TransactionTestCase

NYCTZ = tz.gettz("America/New_York")


class SitemapMonthRangeTestCase(TransactionTestCase):
    def test_sitemap_only_lists_months_that_actually_render(self):
        venue = Venue.objects.create(name=f"venue {uuid.uuid4()}")
        now = datetime.now().astimezone(NYCTZ)
        for starttime in [
            now,
            datetime(2017, 6, 1, 20, 0, tzinfo=NYCTZ),  # before the site existed
            datetime(3000, 3, 15, 20, 0, tzinfo=NYCTZ),  # typo'd far future
            datetime(2019, 2, 3, 20, 0, tzinfo=NYCTZ),  # fine
        ]:
            Event.objects.create(
                venue=venue, title=f"event {uuid.uuid4()}", starttime=starttime
            )

        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(f"/{now.year}-{now.month:02d}/", body)
        self.assertIn("/2019-02/", body)
        self.assertNotIn("/2017-06/", body)
        self.assertNotIn("/3000-03/", body)

        # and every month url the sitemap lists is a 200, not a 404
        import re

        months = sorted(set(re.findall(r"/(\d{4}-\d{2})/", body)))
        self.assertEqual(months, ["2019-02", f"{now.year}-{now.month:02d}"])
        for m in months:
            self.assertEqual(self.client.get(f"/{m}/").status_code, 200, m)
