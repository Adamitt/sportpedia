# landingpage/tests/test_views.py
import json
import os
import tempfile
from datetime import timedelta

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from landingpage.models import Testimonial
from gearguide.models import Gear
from sportlibrary.models import Sport
from metrics.models import ViewCounter

# --- Import helper yang mau kita tes langsung ---
from landingpage.views import _normalize_terms, _norm_cat


class _TempBaseDirMixin:
    """
    Mixin untuk membuat BASE_DIR sementara yang berisi:
    - database/sports.json
    - database/gears.json
    Supaya view `search`/`home` yang baca file ini tidak error.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls._basedir = cls._tmpdir.name
        os.makedirs(os.path.join(cls._basedir, "database"), exist_ok=True)

        # Minimal sports.json
        with open(os.path.join(cls._basedir, "database", "sports.json"), "w", encoding="utf-8") as f:
            json.dump([
                {"id": 1, "name": "Bulu Tangkis", "description": "desc", "history": "hist"},
                {"id": 2, "name": "Yoga", "description": "desc2", "history": "hist2"},
            ], f)

        # Minimal gears.json (boleh kosong; search sekarang tidak memakainya)
        with open(os.path.join(cls._basedir, "database", "gears.json"), "w", encoding="utf-8") as f:
            json.dump([], f)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._tmpdir.cleanup()


class UnitHelperTests(TestCase):
    def test_normalize_terms(self):
        self.assertEqual(_normalize_terms("  Tennis, Yoga!!  "), ["tennis", "yoga"])
        self.assertEqual(_normalize_terms("a b c"), [])  # < 2 chars di-ignore
        self.assertEqual(_normalize_terms("Pickle-ball"), ["pickle-ball"])

    def test_norm_cat(self):
        self.assertEqual(_norm_cat("gearguide"), "Gear")
        self.assertEqual(_norm_cat("Gear Guide"), "Gear")
        self.assertEqual(_norm_cat("library"), "Library")
        self.assertEqual(_norm_cat("Something Else"), "Something Else")


@override_settings(ROOT_URLCONF="sportpedia.urls")  # pastikan url project dipakai
class SearchViewTests(_TempBaseDirMixin, TestCase):
    def setUp(self):
        self.client = Client()
        # Buat beberapa Sport & Gear di DB
        self.s1 = Sport.objects.create(
            id=2, name="Yoga", category="Indoor",
            difficulty="easy", description="Relaxing sport", history="Ancient"
        )
        self.s2 = Sport.objects.create(
            id=3, name="Tennis", category="Outdoor",
            difficulty="medium", description="Racket sport", history="Modern"
        )
        self.g1 = Gear.objects.create(
            sport=self.s1, name="Yoga Block",
            description="Foam block", function="Support",
            level="beginner", price_range="$", image=""
        )
        self.g2 = Gear.objects.create(
            sport=self.s2, name="Tennis Racket",
            description="Racket description", function="Hit ball",
            level="intermediate", price_range="$$", image=""
        )

    def test_search_returns_matching_both_lists(self):
        url = reverse("landingpage:search")
        resp = self.client.get(url, {"q": "tennis"})
        self.assertEqual(resp.status_code, 200)
        # Context tersedia
        gear_results = resp.context["gear_results"]
        sport_results = resp.context["sport_results"]
        # Harus match tennis racket (gear) & Tennis (sport)
        self.assertTrue(any("Tennis Racket" == g["name"] for g in gear_results))
        self.assertTrue(any(s.name == "Tennis" for s in sport_results))

    def test_search_empty_query_returns_empty_lists(self):
        url = reverse("landingpage:search")
        resp = self.client.get(url, {"q": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["gear_results"], [])
        self.assertEqual(list(resp.context["sport_results"]), [])


@override_settings(ROOT_URLCONF="sportpedia.urls")
class HomeWhatsHotTests(_TempBaseDirMixin, TestCase):
    def setUp(self):
        self.client = Client()
        now = timezone.now()

        # HANYA kategori ini yang diambil oleh view: "Library", "Gear", "Gear Guide"
        # Buat 4 data supaya bisa terpotong top-3
        self.v1 = ViewCounter.objects.create(
            key="sport:2", title="Yoga", url="/sportlibrary/2/",
            category="Library", image="", views=5, last_seen=now - timedelta(minutes=5)
        )
        self.v2 = ViewCounter.objects.create(
            key="gear:abc", title="Tennis Racket", url="/gearguide/details/abc/",
            category="Gear", image="", views=7, last_seen=now - timedelta(minutes=10)
        )
        self.v3 = ViewCounter.objects.create(
            key="sport:3", title="Tennis", url="/sportlibrary/3/",
            category="Library", image="", views=7, last_seen=now - timedelta(minutes=20)
        )
        self.v4 = ViewCounter.objects.create(
            key="guide:tips", title="Guide Tips", url="/gearguide/",
            category="Gear Guide", image="", views=3, last_seen=now - timedelta(minutes=1)
        )
        # Ada kategori lain → harus ke-filter keluar
        ViewCounter.objects.create(
            key="forum:1", title="Forum", url="/forum/",
            category="Forum", image="", views=100, last_seen=now
        )

    def test_home_shows_top3_by_views_then_last_seen(self):
        resp = self.client.get(reverse("landingpage:home"))
        self.assertEqual(resp.status_code, 200)
        hot_items = resp.context["hot_items"]
        self.assertEqual(len(hot_items), 3)

        # Urutan: v2 (views 7, newer last_seen?), v3 (views 7, older), v1 (5)
        self.assertEqual(hot_items[0]["title"], "Tennis Racket")  # Gear
        self.assertEqual(hot_items[0]["category"], "Gear")

        self.assertEqual(hot_items[1]["title"], "Tennis")         # Library
        self.assertEqual(hot_items[1]["category"], "Library")

        self.assertEqual(hot_items[2]["title"], "Yoga")           # Library
        self.assertEqual(hot_items[2]["category"], "Library")

        # Pastikan "Forum" tidak muncul
        self.assertFalse(any(it["title"] == "Forum" for it in hot_items))

    def test_api_popular_categories_returns_top_items(self):
        url = reverse("landingpage:api_popular_categories")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["items"]
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["title"], "Tennis Racket")
        self.assertEqual(items[1]["title"], "Tennis")
        self.assertEqual(items[1]["category"], "Library")
        self.assertEqual(items[1].get("excerpt"), "")
        self.assertEqual(items[2]["title"], "Yoga")
        self.assertEqual(items[2].get("excerpt"), "desc")

    def test_api_popular_categories_limit_query(self):
        url = reverse("landingpage:api_popular_categories")
        resp = self.client.get(url, {"limit": "2"})
        self.assertEqual(resp.status_code, 200)
        items = resp.json()["items"]
        self.assertEqual(len(items), 2)

@override_settings(ROOT_URLCONF="sportpedia.urls")
class TestimonialsApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        # bikin user normal & admin
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username="u1", password="pass")
        self.admin = User.objects.create_superuser(username="admin", password="pass", email="a@a.a")

        # seed
        self.t1 = Testimonial.objects.create(
            user=self.user, title="T1", text="Hello 1", category="library", image_url=""
        )
        self.t2 = Testimonial.objects.create(
            user=None, title="T2", text="Hello 2", category="community", image_url=""
        )

    def test_list_all_and_filter(self):
        url = reverse("landingpage:api_testimonials_list")
        r = self.client.get(url, {"category": "all", "limit": 60})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertGreaterEqual(len(data["items"]), 2)

        r2 = self.client.get(url, {"category": "community"})
        self.assertEqual(r2.status_code, 200)
        data2 = r2.json()
        self.assertTrue(all(item["category"] == "community" for item in data2["items"]))

    def test_create_requires_valid_category_and_sets_owner(self):
        self.client.login(username="u1", password="pass")
        url = reverse("landingpage:api_testimonials_create")
        r = self.client.post(url, {
            "text": "Bagus banget!",
            "title": "",
            "category": "library",
            "image_url": "https://img.test/x.jpg"
        })
        self.assertEqual(r.status_code, 200)
        payload = r.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["item"]["user"], "u1")  # owner terisi

    def test_create_accepts_json_payload(self):
        self.client.login(username="u1", password="pass")
        url = reverse("landingpage:api_testimonials_create")
        payload = {
            "text": "JSON payload!",
            "title": "JSON title",
            "category": "library",
            "image_url": "https://img.json/test.jpg",
        }
        r = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["item"]["text"], "JSON payload!")
        self.assertEqual(data["item"]["title"], "JSON title")

    def test_update_owner_or_admin_only(self):
        # user lain tidak boleh
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other = User.objects.create_user(username="other", password="pass")
        self.client.login(username="other", password="pass")
        url = reverse("landingpage:api_testimonials_update", kwargs={"pk": self.t1.pk})
        r = self.client.post(url, {"text": "try hack", "category": "library"})
        self.assertEqual(r.status_code, 403)

        # owner boleh
        self.client.login(username="u1", password="pass")
        r2 = self.client.post(url, {"text": "updated by owner", "category": "library"})
        self.assertEqual(r2.status_code, 200)
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.text, "updated by owner")

        # admin boleh
        self.client.login(username="admin", password="pass")
        r3 = self.client.post(url, {"text": "admin update", "category": "library"})
        self.assertEqual(r3.status_code, 200)
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.text, "admin update")

    def test_update_accepts_json_payload(self):
        self.client.login(username="u1", password="pass")
        url = reverse("landingpage:api_testimonials_update", kwargs={"pk": self.t1.pk})
        payload = {"text": "JSON update", "category": "library"}
        r = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.t1.refresh_from_db()
        self.assertEqual(self.t1.text, "JSON update")

    def test_delete_owner_or_admin_only(self):
        # anon → 403
        url = reverse("landingpage:api_testimonials_delete", kwargs={"pk": self.t1.pk})
        r = self.client.post(url)
        self.assertEqual(r.status_code, 403)

        # owner bisa hapus
        self.client.login(username="u1", password="pass")
        r2 = self.client.post(url)
        self.assertEqual(r2.status_code, 200)
        self.assertFalse(Testimonial.objects.filter(pk=self.t1.pk).exists())

        # admin bisa hapus yang anonymous
        url2 = reverse("landingpage:api_testimonials_delete", kwargs={"pk": self.t2.pk})
        self.client.login(username="admin", password="pass")
        r3 = self.client.post(url2)
        self.assertEqual(r3.status_code, 200)
        self.assertFalse(Testimonial.objects.filter(pk=self.t2.pk).exists())
