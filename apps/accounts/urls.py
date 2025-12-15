from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import GuestRegisterView, LoginView, GuestOtpVerifyView, CustomLogoutView, GuestForgotPasswordView, GuestResetPasswordView, GuestChangePasswordView
from django.contrib.auth.decorators import login_required
from .views_smslog import SmsLogListPage, SmsLogExportCSVView


urlpatterns = [
    # path('register/', GuestRegisterView.as_view(), name='guest_register'),
    path('login/', LoginView.as_view(), name='guest_login'),

    path('logout/', CustomLogoutView.as_view(), name='logoutt'),

    path('otp-verify/', GuestOtpVerifyView.as_view(), name='guest_otp_verify'),

    path('dashboard/', views.guest_dashboard, name='guest_dashboard'),
    path('change-password/', views.guest_change_password, name='guest_change_password'),


    # role based dashboard
    # path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),


    path('forgot-password/', GuestForgotPasswordView.as_view(), name='guest_forgot_password'),
    path('reset-password/', GuestResetPasswordView.as_view(), name='guest_reset_password'),

    # Dashboard password change view
    path('dashboard/change-password/', GuestChangePasswordView.as_view(), name='guest_change_password_dashboard'),

    # sms
    path("sms-logs/", SmsLogListPage.as_view(), name="sms_log_list"),
    path("sms-logs/export/", SmsLogExportCSVView.as_view(), name="sms_log_export"),


    # Django built-in password reset views
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]
