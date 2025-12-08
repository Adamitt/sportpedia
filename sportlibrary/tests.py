from django.test import TestCase
from sportlibrary.models import Sport
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.template.response import TemplateResponse
from django.http import HttpRequest
from unittest.mock import mock_open, patch
from sportlibrary import views
from django.test import SimpleTestCase
from django.urls import reverse, resolve
from sportlibrary import views
import uuid
import json

class SportModelTest(TestCase):
    def test_create_sport_successfully(self):
        """Test bahwa Sport bisa dibuat dengan semua field terisi dengan benar"""
        sport = Sport.objects.create(
            name="Football",
            category="Team",
            difficulty="Medium",
            description="A popular team sport played worldwide.",
            history="Originated in England in the 19th century.",
            rules=["No hands", "Score by kicking the ball into goal"],
            techniques=["Dribbling", "Passing"],
            benefits=["Teamwork", "Cardio"],
            popular_countries=["Brazil", "England"],
            tags=["outdoor", "ball"]
        )

        # Pastikan semua field sesuai
        self.assertEqual(sport.name, "Football")
        self.assertEqual(sport.category, "Team")
        self.assertEqual(sport.difficulty, "Medium")
        self.assertIn("No hands", sport.rules)
        self.assertIn("Brazil", sport.popular_countries)
        self.assertEqual(sport.tags, ["outdoor", "ball"])

    def test_str_method_returns_name(self):
        """Test bahwa __str__() mengembalikan nama olahraga"""
        sport = Sport.objects.create(
            name="Basketball",
            category="Team",
            difficulty="Medium",
            description="Basketball description",
            history="Basketball history"
        )
        self.assertEqual(str(sport), "Basketball")

    def test_default_json_fields_are_empty_lists(self):
        """Test bahwa JSONField default bernilai list kosong"""
        sport = Sport.objects.create(
            name="Tennis",
            category="Solo",
            difficulty="Hard",
            description="A racket sport played individually.",
            history="Originated in France."
        )
        self.assertEqual(sport.rules, [])
        self.assertEqual(sport.techniques, [])
        self.assertEqual(sport.benefits, [])
        self.assertEqual(sport.popular_countries, [])
        self.assertEqual(sport.tags, [])

    def test_uuid_is_auto_generated(self):
        """Test bahwa ID sport otomatis berupa UUID"""
        sport = Sport.objects.create(
            name="Swimming",
            category="Water",
            difficulty="Medium",
            description="A water-based sport.",
            history="Known since ancient times."
        )
        self.assertIsInstance(sport.id, uuid.UUID)

class SportLibraryViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mock_data = [
            {
                "id": "1",
                "name": "Football",
                "category": "Team",
                "difficulty": "Medium",
                "description": "A team sport",
                "history": "Old game"
            },
            {
                "id": "2",
                "name": "Tennis",
                "category": "Solo",
                "difficulty": "Hard",
                "description": "A racket sport",
                "history": "Originated in France"
            }
        ]

    # ---- show_sports() ----
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {"id": "1", "name": "Football"},
        {"id": "2", "name": "Tennis"}
    ]))
    def test_show_sports_view_renders_correctly(self, mock_file):
        """Test show_sports menampilkan template dan context dengan benar"""
        request = self.factory.get("/sportlibrary/")
        response = views.show_sports(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, TemplateResponse)
        self.assertTemplateUsed(response, "sportlibrary/sportlibrary.html")
        self.assertIn("sports", response.context_data)
        self.assertEqual(len(response.context_data["sports"]), 2)
        self.assertEqual(response.context_data["sports"][0]["name"], "Football")

    # ---- sport_detail() ----
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {"id": "1", "name": "Football"},
        {"id": "2", "name": "Tennis"}
    ]))
    def test_sport_detail_view_found(self, mock_file):
        """Test sport_detail dengan ID valid"""
        request = self.factory.get("/sportlibrary/1/")
        response = views.sport_detail(request, sport_id="1")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sportlibrary/detail.html")
        self.assertIn("sport", response.context_data)
        self.assertEqual(response.context_data["sport"]["name"], "Football")

    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {"id": "1", "name": "Football"}
    ]))
    def test_sport_detail_view_not_found(self, mock_file):
        """Test sport_detail dengan ID tidak ditemukan (404)"""
        request = self.factory.get("/sportlibrary/999/")
        response = views.sport_detail(request, sport_id="999")

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    # ---- saved_sports() ----
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {"id": "1", "name": "Football"}
    ]))
    def test_saved_sports_view_returns_json_context(self, mock_file):
        """Test saved_sports mengembalikan JSON di context"""
        request = self.factory.get("/bookmarklist/")
        response = views.saved_sports(request)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bookmarklist.html")
        self.assertIn("all_sports_json", response.context_data)

        # Pastikan JSON valid dan berisi data yang benar
        data = json.loads(response.context_data["all_sports_json"])
        self.assertEqual(data[0]["name"], "Football")

class SportLibraryURLTest(SimpleTestCase):
    def test_show_sports_url_resolves(self):
        """URL '' mengarah ke view show_sports"""
        url = reverse('sportlibrary:show_sports')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.show_sports)

    def test_saved_sports_url_resolves(self):
        """URL 'saved/' mengarah ke view saved_sports"""
        url = reverse('sportlibrary:saved_sports')
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.saved_sports)

    def test_sport_detail_url_resolves(self):
        """URL '<int:sport_id>/' mengarah ke view sport_detail"""
        url = reverse('sportlibrary:sport_detail', args=[1])
        resolver = resolve(url)
        self.assertEqual(resolver.func, views.sport_detail)
        self.assertEqual(resolver.kwargs['sport_id'], 1)