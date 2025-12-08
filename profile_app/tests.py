from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from .models import UserProfile, ActivityLog
import datetime

class ProfileModelTests(TestCase):

    def setUp(self):
        # Buat user untuk pengujian model
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com', 
            password='testpass123'
        )

    def test_user_profile_creation(self):
        """
        Tes bahwa UserProfile dibuat secara otomatis (seperti di view) atau manual, 
        dan __str__ method-nya benar.
        """
        # View menggunakan get_or_create, kita simulasikan pembuatan manual
        profile = UserProfile.objects.create(
            user=self.user,
            olahraga_favorit="Sepak Bola",
            preferensi="Suka nonton"
        )
        self.assertEqual(str(profile), 'testuser')
        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(self.user.profile, profile) # Cek related_name

    def test_activity_log_creation_and_ordering(self):
        """
        Tes bahwa ActivityLog dibuat dengan benar, __str__ method-nya benar,
        dan diurutkan dengan benar (terbaru dulu).
        """
        log1 = ActivityLog.objects.create(
            user=self.user,
            action_type='MODULE_ACCESS',
            description="Mengakses modul A"
        )
        # Kita buat log kedua sedikit setelahnya untuk memastikan urutan
        log2 = ActivityLog.objects.create(
            user=self.user,
            action_type='VIDEO_VIEW',
            description="Menonton video B"
        )

        # Cek __str__ method (format timestamp mungkin sedikit berbeda, jadi kita cek awalnya)
        self.assertTrue(str(log2).startswith('testuser - Viewed Video at'))

        # Cek ordering (Meta: ordering = ['-timestamp'])
        logs = ActivityLog.objects.filter(user=self.user)
        self.assertEqual(logs.first(), log2) # Log terbaru (log2) harus di awal
        self.assertEqual(logs.last(), log1)


class ProfileViewsTests(TestCase):

    def setUp(self):
        """
        Siapkan user, password, profile, dan client yang sudah login
        untuk semua tes view.
        """
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            username='viewuser', 
            email='view@example.com', 
            password=self.password
        )
        # Buat profile awal untuk user
        self.profile = UserProfile.objects.create(
            user=self.user,
            olahraga_favorit="Basket",
            preferensi="Suka main pagi",
            foto_profil="http://example.com/foto.png"
        )
        
        # Buat beberapa log aktivitas
        ActivityLog.objects.create(user=self.user, action_type='MODULE_ACCESS', description="Log 1")
        ActivityLog.objects.create(user=self.user, action_type='VIDEO_VIEW', description="Log 2")

        # Inisialisasi client dan login
        self.client = Client()
        self.client.login(username='viewuser', password=self.password)

        # Siapkan URL
        self.profile_url = reverse('profile_app:profile_page')
        self.settings_url = reverse('profile_app:pengaturan_akun')
        self.login_url = f"{settings.LOGIN_URL}?next={self.profile_url}"
        self.settings_login_url = f"{settings.LOGIN_URL}?next={self.settings_url}"


    def test_profile_page_get(self):
        """
        Tes GET request ke halaman profile_page.
        Memastikan status 200, template benar, dan konteks (user, profile, aktivitas) ada.
        """
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_app/profile.html')
        self.assertEqual(response.context['user'], self.user)
        self.assertEqual(response.context['profile'], self.profile)
        self.assertEqual(len(response.context['aktivitas']), 2)
        self.assertEqual(response.context['aktivitas'][0].description, "Log 2") # Cek urutan

    def test_profile_page_get_or_create(self):
        """
        Tes bahwa profile page membuat profile jika belum ada.
        """
        new_user = User.objects.create_user(username='newuser', password='pw')
        self.client.login(username='newuser', password='pw')
        
        # Pastikan profile belum ada
        self.assertFalse(UserProfile.objects.filter(user=new_user).exists())
        
        # Akses halaman
        response = self.client.get(self.profile_url)
        
        # Cek profile sudah dibuat
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user=new_user).exists())

    def test_profile_page_redirects_if_not_logged_in(self):
        """Tes bahwa halaman profile me-redirect ke login jika belum login."""
        self.client.logout()
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)

    def test_pengaturan_akun_get(self):
        """Tes GET request ke halaman pengaturan_akun."""
        response = self.client.get(self.settings_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile_app/pengaturan_akun.html')
        self.assertEqual(response.context['user'], self.user)
        self.assertEqual(response.context['profile'], self.profile)

    def test_pengaturan_akun_redirects_if_not_logged_in(self):
        """Tes bahwa halaman pengaturan me-redirect ke login jika belum login."""
        self.client.logout()
        response = self.client.get(self.settings_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.settings_login_url)

    def test_pengaturan_akun_post_update_all(self):
        """Tes POST request untuk update semua data (User dan UserProfile)."""
        form_data = {
            'email': 'new_email@example.com',
            'password': 'newpassword456',
            'olahraga_favorit': 'Renang',
            'preferensi': 'Suka malam hari',
            'foto_profil': 'http://example.com/new.png'
        }
        
        response = self.client.post(self.settings_url, data=form_data)
        
        # Cek redirect ke halaman profile
        self.assertRedirects(response, self.profile_url)
        
        # Ambil data terbaru dari database
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        # Cek data user (email, password)
        self.assertEqual(self.user.email, 'new_email@example.com')
        self.assertTrue(self.user.check_password('newpassword456'))
        
        # Cek data profile
        self.assertEqual(self.profile.olahraga_favorit, 'Renang')
        self.assertEqual(self.profile.preferensi, 'Suka malam hari')
        self.assertEqual(self.profile.foto_profil, 'http://example.com/new.png')

        # Cek apakah user masih login setelah ganti password
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'], self.user)

    def test_pengaturan_akun_post_duplicate_email_error(self):
        """
        Tes bahwa update gagal dengan pesan error jika email sudah dipakai user lain.
        """
        # Buat user lain dengan email yang spesifik
        other_user = User.objects.create_user(
            username='otheruser', 
            email='existing@example.com', 
            password='pw'
        )
        
        form_data = {
            'email': 'existing@example.com', # Coba pakai email 'other_user'
            'olahraga_favorit': 'Gagal Update',
        }
        
        response = self.client.post(self.settings_url, data=form_data)
        
        # Harusnya redirect kembali ke halaman pengaturan, BUKAN profile page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.settings_url)
        
        # Cek apakah ada pesan error
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), '❌ Email sudah digunakan.')
        
        # Pastikan data TIDAK berubah
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.olahraga_favorit, 'Gagal Update')
        self.assertEqual(self.profile.olahraga_favorit, 'Basket') # Masih data lama