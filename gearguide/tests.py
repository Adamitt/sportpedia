from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, mock_open
from pathlib import Path
import json

from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from gearguide.models import Gear
from gearguide.forms import GearForm

User = get_user_model()


class GearGuideViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
            is_staff=True,
            is_superuser=True
        )
        self.sport = Sport.objects.create(
            name="Basketball",
            description="Test sport"
        )
        self.gear_user = Gear.objects.create(
            sport=self.sport,
            name="Test Shoes",
            description="User's test shoes",
            function="For playing",
            level="beginner",
            price_range="$50-100",
            owner=self.user,
            recommended_brands=["Nike", "Adidas"],
            materials=["Leather", "Rubber"],
            tags=["shoes", "basketball"]
        )
        self.gear_system = Gear.objects.create(
            sport=self.sport,
            name="System Ball",
            description="System basketball",
            function="For training",
            level="intermediate",
            price_range="$20-50",
            owner=None
        )

    def test_admin_only_function(self):
        from gearguide.views import admin_only
        
        self.assertTrue(admin_only(self.admin))
        self.assertFalse(admin_only(self.user))

    def test_gear_to_json_function(self):
        from gearguide.views import _gear_to_json
        
        result = _gear_to_json(self.gear_user)
        
        self.assertEqual(result["name"], "Test Shoes")
        self.assertEqual(result["sport_name"], "Basketball")
        self.assertEqual(result["level"], "beginner")
        self.assertEqual(result["owner"], "testuser")
        self.assertIsInstance(result["recommended_brands"], list)
        self.assertEqual(len(result["recommended_brands"]), 2)

    def test_show_all_gears_basic(self):
        response = self.client.get(reverse("gearguide:show_all_gears"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "gearguide/gearguide.html")
        self.assertIn("gears", response.context)
        self.assertEqual(len(response.context["gears"]), 2)

    def test_show_all_gears_filter_by_sport(self):
        response = self.client.get(
            reverse("gearguide:show_all_gears") + "?sport=basketball"
        )
        
        self.assertEqual(response.status_code, 200)
        gears = response.context["gears"]
        self.assertEqual(len(gears), 2)
        for gear in gears:
            self.assertEqual(gear.sport.name.lower(), "basketball")

    def test_show_all_gears_filter_by_level(self):
        response = self.client.get(
            reverse("gearguide:show_all_gears") + "?level=beginner"
        )
        
        self.assertEqual(response.status_code, 200)
        gears = response.context["gears"]
        self.assertEqual(len(gears), 1)
        self.assertEqual(gears[0].level, "beginner")

    def test_show_all_gears_filter_your_gears_anonymous(self):
        response = self.client.get(
            reverse("gearguide:show_all_gears") + "?view=your"
        )
        
        self.assertEqual(response.status_code, 200)
        gears = response.context["gears"]
        self.assertEqual(len(gears), 2)

    def test_show_all_gears_filter_your_gears_logged_in(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("gearguide:show_all_gears") + "?view=your"
        )
        
        self.assertEqual(response.status_code, 200)
        gears = response.context["gears"]
        self.assertEqual(len(gears), 1)
        self.assertEqual(gears[0].owner, self.user)


    def test_show_gear_detail_success(self):
        url = reverse("gearguide:card_details", args=[str(self.gear_user.id)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "gearguide/card_details.html")
        self.assertEqual(response.context["gear"].id, self.gear_user.id)

    def test_show_gear_detail_not_found(self):
        fake_id = "99999"
        url = reverse("gearguide:card_details", args=[fake_id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)

    @patch('gearguide.views.ActivityLog.objects.create')
    def test_show_gear_detail_logs_activity(self, mock_log):
        self.client.login(username="testuser", password="testpass123")
        url = reverse("gearguide:card_details", args=[str(self.gear_user.id)])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        mock_log.assert_called_once()

    def test_add_gear_login_required(self):
        response = self.client.get(reverse("gearguide:add_gear"))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_add_gear_get_form(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("gearguide:add_gear"))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("sports", response.context)
        self.assertIn("edit_mode", response.context)
        self.assertFalse(response.context["edit_mode"])

    def test_add_gear_post_success(self):
        self.client.login(username="testuser", password="testpass123")
        
        data = {
            "name": "New Gear",
            "description": "Test description",
            "sport": str(self.sport.id),
            "function": "Test function",
            "level": "beginner",
            "price_range": "$100-200",
            "recommended_brands": "Brand1, Brand2",
            "materials": "Material1, Material2",
            "tags": "tag1, tag2"
        }
        
        response = self.client.post(reverse("gearguide:add_gear"), data)
        
        self.assertEqual(response.status_code, 302)
        new_gear = Gear.objects.filter(name="New Gear").first()
        self.assertIsNotNone(new_gear)
        self.assertEqual(new_gear.owner, self.user)
        self.assertEqual(len(new_gear.recommended_brands), 2)
        self.assertEqual(len(new_gear.materials), 2)
        
        log = ActivityLog.objects.filter(
            user=self.user,
            action_type="CREATE"
        ).first()
        self.assertIsNotNone(log)

    def test_add_gear_with_sport_name(self):
        self.client.login(username="testuser", password="testpass123")
        
        data = {
            "name": "New Gear 2",
            "description": "Test",
            "sport": "Basketball",  
            "function": "Test",
            "level": "intermediate"
        }

        response = self.client.post(reverse("gearguide:add_gear"), data)
        self.assertEqual(response.status_code, 200)
        new_gear = Gear.objects.filter(name="New Gear 2").first()
        self.assertIsNone(new_gear)
        self.assertIn("sports", response.context)

    def test_edit_gear_login_required(self):
        response = self.client.post(
            reverse("gearguide:edit_gear", args=[self.gear_user.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_edit_gear_owner_can_edit(self):
        self.client.login(username="testuser", password="testpass123")
        
        data = {
            "name": "Updated Shoes",
            "description": "Updated description",
            "sport": str(self.sport.id),
            "function": "Updated function",
            "level": "intermediate",
            "price_range": "$150-200",
            "recommended_brands": "Nike",
            "materials": "Leather",
            "tags": "basketball"
        }
        
        response = self.client.post(
            reverse("gearguide:edit_gear", args=[self.gear_user.id]),
            data
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result["ok"])
        self.gear_user.refresh_from_db()
        self.assertEqual(self.gear_user.name, "Updated Shoes")
        self.assertEqual(self.gear_user.level, "intermediate")

    def test_edit_gear_admin_can_edit_any(self):
        self.client.login(username="admin", password="adminpass123")
        
        data = {
            "name": "Admin Updated",
            "description": "Updated by admin",
            "sport": str(self.sport.id),  
            "function": "Test",
            "level": "advanced",
            "price_range": "$200-300",
            "recommended_brands": "",
            "materials": "",
            "tags": ""
        }
        
        response = self.client.post(
            reverse("gearguide:edit_gear", args=[self.gear_user.id]),
            data
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result["ok"])

    def test_edit_gear_non_owner_forbidden(self):
        other_user = User.objects.create_user(
            username="other",
            password="pass123"
        )
        self.client.login(username="other", password="pass123")
        
        data = {
            "name": "Hacked",
            "description": "Test",
            "function": "Test",
            "level": "beginner",
            "price_range": "$100",
            "recommended_brands": "",
            "materials": "",
            "tags": ""
        }
        response = self.client.post(
            reverse("gearguide:edit_gear", args=[self.gear_user.id]),
            data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        if response.status_code == 200:
            result = json.loads(response.content)
            self.assertFalse(result["ok"])
        else:
            self.assertEqual(response.status_code, 403)

    def test_edit_gear_invalid_method(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("gearguide:edit_gear", args=[self.gear_user.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_gear_admin_only(self):
        self.client.login(username="testuser", password="testpass123")
        
        response = self.client.post(
            reverse("gearguide:delete_gear", args=[self.gear_user.id])
        )
        self.assertEqual(response.status_code, 403)
        result = json.loads(response.content)
        self.assertFalse(result["ok"])

    def test_delete_gear_admin_success(self):
        self.client.login(username="admin", password="adminpass123")
        
        gear_id = self.gear_user.id
        gear_name = self.gear_user.name
        response = self.client.post(
            reverse("gearguide:delete_gear", args=[gear_id])
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result["ok"])
        self.assertFalse(Gear.objects.filter(id=gear_id).exists())
        log = ActivityLog.objects.filter(
            user=self.admin,
            action_type="DELETE"
        ).first()
        self.assertIsNotNone(log)
        self.assertIn(gear_name, log.description)

    def test_delete_gear_not_found(self):
        
        self.client.login(username="admin", password="adminpass123")
        fake_id = 99999
        response = self.client.post(
            reverse("gearguide:delete_gear", args=[fake_id])
        )
        
        self.assertEqual(response.status_code, 404)

    def test_delete_gear_invalid_method(self):
        
        self.client.login(username="admin", password="adminpass123")
        response = self.client.get(
            reverse("gearguide:delete_gear", args=[self.gear_user.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_get_gear_json_success(self):
        
        response = self.client.get(
            reverse("gearguide:get_gear_json", args=[self.gear_user.id])
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result["ok"])
        self.assertIn("data", result)
        self.assertEqual(result["data"]["name"], "Test Shoes")
        self.assertEqual(result["data"]["sport_name"], "Basketball")
        self.assertIn("recommended_brands_text", result["data"])

    def test_get_gear_json_not_found(self):
        fake_id = 99999
        response = self.client.get(
            reverse("gearguide:get_gear_json", args=[fake_id])
        )
        self.assertIn(response.status_code, [404, 500])

    def test_get_gear_json_invalid_method(self):
        
        response = self.client.post(
            reverse("gearguide:get_gear_json", args=[self.gear_user.id])
        )
        self.assertEqual(response.status_code, 405)



    def test_gear_with_empty_arrays(self):
        
        gear = Gear.objects.create(
            sport=self.sport,
            name="Empty Arrays",
            description="Test",
            level="beginner",
            owner=self.user,
            recommended_brands=[],
            materials=[],
            tags=[]
        )
        from gearguide.views import _gear_to_json
        result = _gear_to_json(gear)
        self.assertEqual(result["recommended_brands"], [])
        self.assertEqual(result["materials"], [])
        self.assertEqual(result["tags"], [])

    def test_multiple_filters_combined(self):
        
        response = self.client.get(
            reverse("gearguide:show_all_gears") + 
            "?sport=basketball&level=beginner&view=all"
        )
        self.assertEqual(response.status_code, 200)
        gears = response.context["gears"]
        self.assertEqual(len(gears), 1)
        self.assertEqual(gears[0].name, "Test Shoes")

    def test_gear_without_owner(self):
        
        from gearguide.views import _gear_to_json
        result = _gear_to_json(self.gear_system)
        
        self.assertIsNone(result["owner"])
        self.assertEqual(result["name"], "System Ball")


class GearGuideIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="integrationuser",
            password="pass123"
        )
        self.admin = User.objects.create_user(
            username="integrationadmin",
            password="adminpass",
            is_staff=True
        )
        self.sport = Sport.objects.create(name="Soccer")

    def test_full_gear_lifecycle(self):
        self.client.login(username="integrationuser", password="pass123")

        create_data = {
            "name": "Lifecycle Gear",
            "description": "Test lifecycle",
            "sport": str(self.sport.id),
            "function": "Testing",
            "level": "beginner",
            "price_range": "$50"
        }
        response = self.client.post(reverse("gearguide:add_gear"), create_data)
        self.assertEqual(response.status_code, 302)
        gear = Gear.objects.get(name="Lifecycle Gear")
        response = self.client.get(
            reverse("gearguide:card_details", args=[str(gear.id)])
        )
        self.assertEqual(response.status_code, 200)
        edit_data = {
            "name": "Updated Lifecycle Gear",
            "description": "Updated",
            "sport": str(self.sport.id),
            "function": "Updated",
            "level": "intermediate",
            "price_range": "$100",
            "recommended_brands": "",
            "materials": "",
            "tags": ""
        }
        response = self.client.post(
            reverse("gearguide:edit_gear", args=[gear.id]),
            edit_data
        )
        self.assertEqual(response.status_code, 200)
        
        gear.refresh_from_db()
        self.assertEqual(gear.name, "Updated Lifecycle Gear")
        
        
        self.client.login(username="integrationadmin", password="adminpass")
        response = self.client.post(
            reverse("gearguide:delete_gear", args=[gear.id])
        )
        self.assertEqual(response.status_code, 200)
        
        
        self.assertFalse(Gear.objects.filter(id=gear.id).exists())

    def test_user_can_only_see_own_gears(self):
        
        Gear.objects.create(
            sport=self.sport,
            name="User Gear",
            description="User's gear",
            level="beginner",
            owner=self.user
        )
        Gear.objects.create(
            sport=self.sport,
            name="Admin Gear",
            description="Admin's gear",
            level="beginner",
            owner=self.admin
        )
        self.client.login(username="integrationuser", password="pass123")
        response = self.client.get(
            reverse("gearguide:show_all_gears") + "?view=your"
        )
        
        gears = response.context["gears"]
        self.assertEqual(len(gears), 1)
        self.assertEqual(gears[0].name, "User Gear")


class GearFormTestCase(TestCase):
    def setUp(self):
    
        self.sport = Sport.objects.create(
            name="Tennis",
            category="Individual",
            description="Test sport"
        )

    def test_form_initialization(self):
    
        form = GearForm()
        
    
        self.assertIn('sport', form.fields)
        
    
        choices = form.fields['sport'].widget.choices
        self.assertGreater(len(choices), 1) 
        
    
        self.assertEqual(choices[0], ('', '---------'))

    def test_form_fields_present(self):
    
        form = GearForm()
        
        expected_fields = [
            'name', 'function', 'description', 'level', 'price_range',
            'recommended_brands', 'materials', 'care_tips', 'ecommerce_link',
            'tags', 'image', 'sport'
        ]
        
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_form_clean_recommended_brands(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'recommended_brands': 'Nike, Adidas, Puma',
            'materials': '',
            'tags': ''
        })
        
        self.assertTrue(form.is_valid())
        cleaned_brands = form.cleaned_data['recommended_brands']
        self.assertEqual(cleaned_brands, ['Nike', 'Adidas', 'Puma'])

    def test_form_clean_materials(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'recommended_brands': '',
            'materials': 'Carbon, Steel, Aluminum',
            'tags': ''
        })
        
        self.assertTrue(form.is_valid())
        cleaned_materials = form.cleaned_data['materials']
        self.assertEqual(cleaned_materials, ['Carbon', 'Steel', 'Aluminum'])

    def test_form_clean_tags(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'recommended_brands': '',
            'materials': '',
            'tags': 'racket, tennis, gear'
        })
        
        self.assertTrue(form.is_valid())
        cleaned_tags = form.cleaned_data['tags']
        self.assertEqual(cleaned_tags, ['racket', 'tennis', 'gear'])

    def test_form_empty_arrays(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'recommended_brands': '',
            'materials': '',
            'tags': ''
        })
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['recommended_brands'], [])
        self.assertEqual(form.cleaned_data['materials'], [])
        self.assertEqual(form.cleaned_data['tags'], [])

    def test_form_with_whitespace(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'recommended_brands': ' Nike , Adidas , Puma ',
            'materials': ' Carbon , Steel ',
            'tags': ' tag1 , tag2 '
        })
        
        self.assertTrue(form.is_valid())
        
    
        self.assertEqual(form.cleaned_data['recommended_brands'], ['Nike', 'Adidas', 'Puma'])
        self.assertEqual(form.cleaned_data['materials'], ['Carbon', 'Steel'])
        self.assertEqual(form.cleaned_data['tags'], ['tag1', 'tag2'])

    def test_form_optional_fields(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Minimal Gear',
            'description': 'Test',
            'level': 'beginner'
        })
        self.assertTrue(form.is_valid())

    def test_form_with_ecommerce_link(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'ecommerce_link': 'https://tokopedia.com/product'
        })
        
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['ecommerce_link'],
            'https://tokopedia.com/product'
        )

    def test_form_with_image_url(self):
    
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'image': 'https://example.com/image.jpg'
        })
        
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data['image'],
            'https://example.com/image.jpg'
        )

    @patch('builtins.open', new_callable=mock_open, read_data='[{"id": 999, "name": "JSON Sport", "category": "Test"}]')
    @patch('pathlib.Path.exists', return_value=True)
    def test_form_loads_sports_from_json(self, mock_exists, mock_file):
    
        form = GearForm()
        
    
        choices = dict(form.fields['sport'].widget.choices)
        
    
        self.assertIn(str(self.sport.id), choices)

    @patch('pathlib.Path.exists', return_value=False)
    def test_form_handles_missing_json(self, mock_exists):
    
        form = GearForm()
        
    
        self.assertIn('sport', form.fields)
        choices = form.fields['sport'].widget.choices
        self.assertGreater(len(choices), 1)

    def test_form_invalid_ecommerce_url(self):
        
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'ecommerce_link': 'not-a-valid-url'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('ecommerce_link', form.errors)

    def test_form_invalid_image_url(self):
        
        form = GearForm(data={
            'sport': str(self.sport.id),
            'name': 'Test Gear',
            'description': 'Test',
            'level': 'beginner',
            'image': 'invalid-url'
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)