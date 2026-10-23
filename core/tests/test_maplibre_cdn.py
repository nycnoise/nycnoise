from django.test import TransactionTestCase


class MaplibreFromCdnTestCase(TransactionTestCase):
    def test_homepage_loads_maplibre_from_cdn_with_sri_and_not_from_static(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(
            'src="https://unpkg.com/maplibre-gl@5.2.0/dist/maplibre-gl.js"', body
        )
        self.assertIn(
            'href="https://unpkg.com/maplibre-gl@5.2.0/dist/maplibre-gl.css"', body
        )
        self.assertEqual(body.count('integrity="sha384-'), 2)
        self.assertEqual(body.count('crossorigin="anonymous"'), 2)
        self.assertNotIn("maplibre-gl.min", body)
        self.assertNotIn("core/lib/", body)
