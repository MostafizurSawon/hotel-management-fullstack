from django.contrib import admin
from .models import User

# Register your models here.
# admin.site.register(User)




from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import update_session_auth_hash


class CustomUserAdmin(BaseUserAdmin):
    # Use your own forms if you have custom User forms
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('phone_number', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('phone_number',)
    ordering = ('phone_number',)
    filter_horizontal = ()

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        (_('Personal info'), {'fields': ('role',)}),
        (_('Permissions'), {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'role', 'password1', 'password2'),
        }),
    )

    # Add the change password view URL to admin
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<id>/password/',
                self.admin_site.admin_view(self.user_change_password),
                name='auth_user_password_change',
            ),
        ]
        return custom_urls + urls

    def user_change_password(self, request, id, form_url=''):
        user = self.get_object(request, id)
        if not user:
            messages.error(request, "User does not exist.")
            return redirect('..')

        from django.contrib.auth.forms import AdminPasswordChangeForm
        if request.method == 'POST':
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Password changed successfully.')
                update_session_auth_hash(request, user)
                return redirect('..')
        else:
            form = AdminPasswordChangeForm(user)

        context = {
            'title': _('Change password: %s') % user.phone_number,
            'form': form,
            'user': user,
            'is_popup': False,
            'save_as': False,
            'has_view_permission': True,
            'opts': self.model._meta,
            'original': user,
        }
        from django.template.response import TemplateResponse
        return TemplateResponse(request, 'admin/auth/user/change_password.html', context)

admin.site.register(User, CustomUserAdmin)
