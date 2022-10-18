from django.test import TestCase, Client


class ViewsTests(TestCase):
    def test_index(self):
        client = Client()
        response = client.get("/herald/")
        self.assertContains(response, "MyNotification")

    def test_preview_text(self):
        client = Client()
        response = client.get("/herald/0/text/")
        self.assertContains(response, "Hello World")
        self.assertEqual(response["content-type"], "text/plain; charset=utf-8")

    def test_preview_html(self):
        client = Client()
        response = client.get("/herald/0/html/")
        self.assertContains(response, "<html><body>Hello World</body></html>")
        self.assertEqual(response["content-type"], "text/html; charset=utf-8")
