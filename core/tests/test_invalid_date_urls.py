from django.test import TransactionTestCase


class IncorrectDateUrlsTestCase(TransactionTestCase):
    def test_incorrect_date_urls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # this should work
        response = self.client.get("/2022-01/")
        self.assertEqual(response.status_code, 200)

        # this should work too
        response = self.client.get("/2032-01/")
        self.assertEqual(response.status_code, 200)

        # this should not work
        response = self.client.get("/2022-15/")
        self.assertEqual(response.status_code, 404)
