from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from sportlibrary.models import Sport
from gearguide.models import Gear
from profile_app.models import UserProfile, ActivityLog, SportProgress

# --- Read-Only Admin untuk Model yang Sudah Ada ---

class ReadOnlyAdminMixin:
    """Mixin untuk membuat model admin menjadi read-only."""
    
    def has_add_permission(self, request):
        return False # Menonaktifkan tombol "Add"
        
    def has_change_permission(self, request, obj=None):
        return False # Menonaktifkan tombol "Save" (edit)
        
    def has_delete_permission(self, request, obj=None):
        return False # Menonaktifkan tombol "Delete"
        
    def get_actions(self, request):
        # Menonaktifkan "delete selected"
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

@admin.register(Sport)
class SportReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Menampilkan Sport di admin site (read-only)."""
    list_display = ('name', 'category', 'difficulty')
    list_filter = ('category', 'difficulty')
    search_fields = ('name', 'description', 'history')

@admin.register(ActivityLog)
class ActivityLogReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Menampilkan ActivityLog di admin site (read-only)."""
    list_display = ('timestamp', 'user', 'action_type', 'description')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__username', 'description')
    
@admin.register(SportProgress)
class SportProgressReadOnlyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Menampilkan SportProgress di admin site (read-only)."""
    list_display = ('user', 'sport', 'time_spent', 'percent', 'completed', 'last_accessed')
    list_filter = ('completed', 'sport')
    search_fields = ('user__username', 'sport__name')

# --- Kustomisasi Tampilan User Admin ---

# Definisikan inline untuk UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

# Kustomisasi User admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'groups')
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Unregister User lama, register dengan yang baru
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)