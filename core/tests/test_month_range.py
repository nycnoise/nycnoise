import uuid
from datetime import datetime

from core.models import Event, Venue
from dateutil import relativedelta, tz
from django.test import TransactionTestCase

NYCTZ = tz.gettz("America/New_York")


def month_url(dt):
    return f"/{dt.year}-{dt.month:02d}/"


def month_link(dt):
    return f'href="{month_url(dt)}"'


class ArchiveMonthRangeTestCase(TransactionTestCase):
    def setUp(self):
        now = datetime.now().astimezone(NYCTZ)
        self.this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.next_month = self.this_month + relativedelta.relativedelta(months=1)
        self.last_valid = self.this_month + relativedelta.relativedelta(months=24)
        self.first_invalid = self.last_valid + relativedelta.relativedelta(months=1)

    def test_months_up_to_two_years_ahead_render_even_with_no_events(self):
        self.assertEqual(self.client.get(month_url(self.this_month)).status_code, 200)
        self.assertEqual(self.client.get(month_url(self.next_month)).status_code, 200)
        self.assertEqual(self.client.get(month_url(self.last_valid)).status_code, 200)

    def test_months_past_two_years_ahead_are_404(self):
        self.assertEqual(
            self.client.get(month_url(self.first_invalid)).status_code, 404
        )
        self.assertEqual(self.client.get("/2195-07/").status_code, 404)
        self.assertEqual(self.client.get("/2152-12/").status_code, 404)

    def test_a_typoed_far_future_event_does_not_reopen_the_range(self):
        venue = Venue.objects.create(name=f"venue {uuid.uuid4()}")
        Event.objects.create(
            venue=venue,
            title=f"event {uuid.uuid4()}",
            starttime=datetime(3000, 3, 15, 20, 0, tzinfo=NYCTZ),
        )
        self.assertEqual(self.client.get("/3000-03/").status_code, 404)

    def test_last_valid_month_has_no_next_link_and_the_one_before_does(self):
        response = self.client.get(month_url(self.last_valid))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, month_link(self.first_invalid))
        previous = self.last_valid - relativedelta.relativedelta(months=1)
        self.assertContains(response, month_link(previous))

        response = self.client.get(month_url(previous))
        self.assertContains(response, month_link(self.last_valid))

    def test_homepage_links_to_previous_and_next_month(self):
        response = self.client.get("/")
        previous = self.this_month - relativedelta.relativedelta(months=1)
        self.assertContains(response, month_link(previous))
        self.assertContains(response, month_link(self.next_month))

    def test_past_empty_months_still_render_back_to_2018(self):
        self.assertEqual(self.client.get("/2020-04/").status_code, 200)
        self.assertEqual(self.client.get("/2018-01/").status_code, 200)
        self.assertEqual(self.client.get("/2017-12/").status_code, 404)

    def test_no_previous_month_link_before_2018(self):
        response = self.client.get("/2018-01/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="/2017-12/"')
        self.assertContains(response, 'href="/2018-02/"')
        response = self.client.get("/2018-02/")
        self.assertContains(response, 'href="/2018-01/"')
