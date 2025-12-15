from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import User
from .utils import generate_otp, generate_password, send_sms_jbd
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.views.generic import TemplateView
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

from django.views import View

from .utils import role_required


import environ
env = environ.Env()
environ.Env.read_env()
TOKEN = env("JBD_SMS_TOKEN")

# jbd sms
SENDER_ID = "8809617615010"  # customize sender id here, max 11 chars

OTP_VALIDITY_MINUTES = 5
OTP_RESEND_COOLDOWN_SECONDS = 120  # Cooldown between sending OTPs

def can_send_otp(user):
    # Check cooldown on last OTP sent
    if not user.otp_created_at:
        return True
    elapsed = (timezone.now() - user.otp_created_at).total_seconds()
    return elapsed > OTP_RESEND_COOLDOWN_SECONDS

def send_otp_sms(user, otp, password):
    message = f"আপনার ওটিপি: {otp}, লগইন ফোন নম্বর: {user.phone_number}, পাসওয়ার্ড: {password} নবাবগঞ্জ সিটি কলেজ।"
    print("Sending otp...", TOKEN)
    return send_sms_jbd(user.phone_number, message, TOKEN, sender_id=SENDER_ID)




class GuestRegisterView(TemplateView):
    template_name = 'accounts/guest_register.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })
        return context

    def post(self, request, *args, **kwargs):
        phone = request.POST.get('phone_number')

        if request.user.is_authenticated:
            return redirect('index')

        # 1. If active user exists
        if User.objects.filter(phone_number=phone, is_active=True).exists():
            messages.error(request, "A user with this phone number already exists.")
            return redirect('guest_register')

        # 2. If inactive user exists, resend OTP (with cooldown)
        user_qs = User.objects.filter(phone_number=phone, is_active=False)
        if user_qs.exists():
            user = user_qs.first()
            if not self.can_send_otp(user):
                messages.error(request, "Please wait before requesting another OTP.")
                return redirect('guest_register')

            otp = generate_otp()
            password = generate_password()
            user.otp_code = otp
            user.otp_created_at = timezone.now()
            user.set_password(password)
            user.save(update_fields=['otp_code', 'otp_created_at', 'password'])

            status = send_otp_sms(user, otp, password)
            if status == "SENT":
                messages.success(request, "OTP resent successfully to your phone.")
                request.session['guest_phone'] = phone
                return redirect('guest_otp_verify')
            else:
                messages.error(request, "Failed to send OTP SMS. Please try again later.")
                return redirect('guest_register')

        # 3. Brand new user → send OTP first, then create user
        otp = generate_otp()
        password = generate_password()

        temp_user = User(
            phone_number=phone,
            role='student',
            is_active=False,
            otp_code=otp,
            otp_created_at=timezone.now(),
        )
        temp_user.set_password(password)

        status = send_otp_sms(temp_user, otp, password)

        if status == "SENT":
            user = User.objects.create(
                phone_number=phone,
                role='student',
                is_active=False,
                otp_code=otp,
                otp_created_at=timezone.now(),
            )
            user.set_password(password)
            user.save(update_fields=['password'])

            messages.success(request, "OTP sent successfully to your phone.")
            request.session['guest_phone'] = phone
            return redirect('guest_otp_verify')
        else:
            messages.error(request, "Failed to send OTP SMS. Please try again.")
            return redirect('guest_register')

    def can_send_otp(self, user):
        if not user.otp_created_at:
            return True
        elapsed = (timezone.now() - user.otp_created_at).total_seconds()
        return elapsed > 60  # OTP cooldown seconds




def normalize_phone_number(phone_number):
    # Strip spaces, hyphens, parentheses, or any other non-numeric characters
    phone_number = ''.join(c for c in phone_number if c.isdigit())

    # If phone number starts with 0, prepend the country code (880 for Bangladesh)
    if phone_number.startswith('0'):
        phone_number = '880' + phone_number[1:]  # Replace the leading 0 with country code

    # If the number already includes the country code, return it as it is
    elif not phone_number.startswith('880'):
        # If it's not starting with '880', we assume it's a wrong number or format.
        return None  # This handles invalid phone number formats

    return phone_number

# def guest_otp_verify(request):
#     if request.method == 'POST':
#         entered_otp = request.POST.get('otp')
#         phone = request.session.get('guest_phone')

#         if not phone:
#             return redirect('guest_login')

#         try:
#             user = User.objects.get(phone_number=phone)
#         except User.DoesNotExist:
#             return render(request, 'accounts/guest_otp_verify.html', {'error': 'User not found. Please login again.'})

#         if user.is_active:
#             messages.info(request, "Your account is already activated. Please login.")
#             return redirect('guest_login')

#         # Check OTP expiry
#         if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=OTP_VALIDITY_MINUTES):
#             user.otp_code = None
#             user.otp_created_at = None
#             user.save(update_fields=['otp_code', 'otp_created_at'])
#             return render(request, 'accounts/guest_otp_verify.html', {'error': 'OTP expired. Please request again.'})

#         if entered_otp == user.otp_code:
#             user.is_active = True
#             user.otp_code = None
#             user.otp_created_at = None
#             user.save(update_fields=['is_active', 'otp_code', 'otp_created_at'])

#             # Create blank PassportInfo and CV if not exist
#             PassportInfo.objects.get_or_create(user=user)
#             TravelAgencyCV.objects.get_or_create(user=user)

#             messages.success(request, "Your account is activated. You can now login.")
#             request.session.pop('guest_phone', None)
#             return redirect('guest_login')
#         else:
#             return render(request, 'accounts/guest_otp_verify.html', {'error': 'Invalid OTP'})

#     return render(request, 'accounts/guest_otp_verify.html')

class GuestOtpVerifyView(TemplateView):
    template_name = 'accounts/guest_otp_verify.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })
        return context

    def post(self, request, *args, **kwargs):
        phone = request.session.get('guest_phone')

        if not phone:
            messages.error(request, "Session expired. Please start over.")
            return redirect('guest_login')

        otp = request.POST.get('otp', '').strip()

        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            messages.error(request, "User not found. Please login again.")
            return redirect('guest_login')

        # Optional: agei expiry check kore nao
        if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=5):
            messages.error(request, "OTP expired. Please request a new one.")
            return redirect('guest_register')

        if otp == user.otp_code:
            user.is_active = True
            user.otp_code = None
            user.otp_created_at = None
            user.save(update_fields=['is_active', 'otp_code', 'otp_created_at'])

            login(request, user)
            request.session.pop('guest_phone', None)
            messages.success(request, "আপনার একাউন্টটি সফলভাবে একটিভেট হয়েছে l আপনার মোবাইলে প্রদত্ত এসএমএসটি ভালোভাবে সেভ করে রাখুন, পরবর্তীতে এটি কাজে লাগবে l")
            return redirect('guest_login')  # or dashboard as you like
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            # ✅ Same context as GET, so layout_path thakbe
            context = self.get_context_data()
            return self.render_to_response(context, status=400)


class LoginView(TemplateView):
    template_name = 'accounts/guest_login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('index')

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })
        return context

    def post(self, request, *args, **kwargs):
        phone = request.POST.get('phone_number')
        password = request.POST.get('password')
        normalized_phone = normalize_phone_number(phone)

        user = authenticate(request, phone_number=normalized_phone, password=password)

        if user is not None:
            if not user.is_active:
                messages.error(request, "আপনার অ্যাকাউন্ট এখনো অ্যাক্টিভ নয়। অনুগ্রহ করে OTP যাচাই করুন।")
                return redirect('guest_otp_verify')

            login(request, user)
            messages.success(request, f"{user.phone_number} এর জন্য সফলভাবে লগইন হয়েছে।")
            return redirect('index')

        messages.error(request, "ফোন নম্বর বা পাসওয়ার্ড সঠিক নয়।")
        return self.render_to_response(self.get_context_data())



class GuestForgotPasswordView(View):
    template_name = 'accounts/guest_forgot_password.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        phone = request.POST.get('phone_number')
        normalized_phone = normalize_phone_number(phone)

        if not normalized_phone:
            messages.error(request, "ফোন নম্বর সঠিক নয়। দয়া করে সঠিক নম্বর দিন (যেমন: 01XXXXXXXXX)।")
            return redirect('guest_forgot_password')

        try:
            user = User.objects.get(phone_number=normalized_phone, is_active=True, role='student')
        except User.DoesNotExist:
            messages.error(request, "এই ফোন নম্বর দিয়ে কোন ব্যবহারকারী পাওয়া যায়নি।")
            return redirect('guest_forgot_password')

        if not can_send_otp(user):
            messages.error(request, "অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন এবং পুনরায় চেষ্টা করুন।")
            return redirect('guest_forgot_password')

        otp = generate_otp()
        user.otp_code = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp_code', 'otp_created_at'])

        message = f"আপনার পাসওয়ার্ড রিসেট OTP: {otp}"
        status = send_sms_jbd(user.phone_number, message, TOKEN, sender_id=SENDER_ID)

        print("==>", normalized_phone)  # ✅ now logs in correct format

        if status == "SENT":
            messages.success(request, "OTP সফলভাবে পাঠানো হয়েছে।")
            request.session['reset_phone'] = normalized_phone  # ✅ FIXED
            return redirect('guest_reset_password')
        else:
            messages.error(request, "OTP পাঠাতে ব্যর্থ হয়েছে। দয়া করে আবার চেষ্টা করুন।")
            return redirect('guest_forgot_password')




class GuestResetPasswordView(View):
    template_name = 'accounts/guest_reset_password.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, kwargs)
        context.update({
            "layout_path": TemplateHelper.set_layout("layout_blank.html", context),
        })
        return context

    def get_user_from_session(self, request):
        phone = request.session.get('reset_phone')
        if not phone:
            return None
        try:
            return User.objects.get(phone_number=phone, is_active=True, role='student')
        except User.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        user = self.get_user_from_session(request)
        if not user:
            messages.error(request, "Session expired. Please start password reset again.")
            return redirect('guest_forgot_password')
        return render(request, self.template_name, self.get_context_data())

    def post(self, request, *args, **kwargs):
        user = self.get_user_from_session(request)
        if not user:
            messages.error(request, "User not found. Please start over.")
            return redirect('guest_forgot_password')

        entered_otp = request.POST.get('otp')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not entered_otp or not new_password or not confirm_password:
            messages.error(request, "অনুগ্রহ করে সব ঘর পূরণ করুন।")
            return redirect('guest_reset_password')

        if new_password != confirm_password:
            messages.error(request, "পাসওয়ার্ড মিলছে না।")
            return redirect('guest_reset_password')

        if user.otp_code != entered_otp:
            messages.error(request, "ভুল OTP দেওয়া হয়েছে।")
            return redirect('guest_reset_password')

        if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=OTP_VALIDITY_MINUTES):
            messages.error(request, "OTP মেয়াদোত্তীর্ণ হয়েছে। পুনরায় অনুরোধ করুন।")
            return redirect('guest_forgot_password')

        # Reset password
        user.set_password(new_password)
        user.otp_code = None
        user.otp_created_at = None
        user.save(update_fields=['password', 'otp_code', 'otp_created_at'])

        messages.success(request, "পাসওয়ার্ড সফলভাবে রিসেট হয়েছে। এখন লগইন করুন।")
        request.session.pop('reset_phone', None)
        return redirect('guest_login')



# class LogoutGetAllowedView(LogoutView):
#     def get(self, request, *args, **kwargs):
#         messages.success(request, "Logged Out Successfully.")
#         return self.post(request, *args, **kwargs)

# from django.contrib.auth.views import LogoutView
# from django.contrib import messages

# class CustomLogoutView(LogoutView):
#     def get(self, request, *args, **kwargs):
#         print("logged out!!")
#         messages.success(request, "Logged out successfully.")
#         return super().get(request, *args, **kwargs)


class CustomLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        print("logged out!!")
        messages.warning(request, "Logged out!")
        return super().post(request, *args, **kwargs)





# def guest_otp_verify(request):
#     if request.method == 'POST':
#         entered_otp = request.POST.get('otp')
#         phone = request.session.get('guest_phone')

#         if not phone:
#             return redirect('guest_login')

#         try:
#             user = User.objects.get(phone_number=phone)
#         except User.DoesNotExist:
#             context = {'error': 'User not found. Please login again.'}
#             return render(request, 'accounts/guest_otp_verify.html', context)

#         # Optional: Check if OTP expired (e.g., valid for 5 minutes)
#         if user.otp_created_at and timezone.now() > user.otp_created_at + timedelta(minutes=5):
#             user.otp_code = None
#             user.otp_created_at = None
#             user.save(update_fields=['otp_code', 'otp_created_at'])
#             context = {'error': 'OTP expired. Please request again.'}
#             return render(request, 'accounts/guest_otp_verify.html', context)

#         if entered_otp == user.otp_code:
#             # OTP matched: remove OTP fields
#             user.otp_code = None
#             user.otp_created_at = None
#             user.save(update_fields=['otp_code', 'otp_created_at'])

#             # Login user
#             login(request, user)
#             PassportInfo.objects.get_or_create(user=user)

#             # Clear phone from session
#             request.session.pop('guest_phone', None)

#             return redirect('guest_dashboard')
#         else:
#             context = {'error': 'Invalid OTP'}
#             return render(request, 'accounts/guest_otp_verify.html', context)



#     return render(request, 'accounts/guest_otp_verify.html')





# Guest change password from dashboard

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import redirect
from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

class GuestChangePasswordView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/guest_change_password_dashboard.html'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context["layout"] = "vertical"
        context["layout_path"] = TemplateHelper.set_layout("layout_vertical.html", context)
        return context

    def post(self, request, *args, **kwargs):
        password1 = request.POST.get('new_password1')
        password2 = request.POST.get('new_password2')

        if not password1 or not password2:
            messages.error(request, "দয়া করে সব ঘর পূরণ করুন।")
            return self.render_to_response(self.get_context_data())

        if password1 != password2:
            messages.error(request, "পাসওয়ার্ডগুলো মিলছে না।")
            return self.render_to_response(self.get_context_data())

        user = request.user
        user.set_password(password1)
        user.save()
        update_session_auth_hash(request, user)

        messages.success(request, "পাসওয়ার্ড সফলভাবে পরিবর্তন হয়েছে।")
        return redirect('index')










@login_required
def guest_cv_list_panel(request):
    guest_cvs = TravelAgencyCV.objects.select_related('user').all()
    return render(request, 'dashboard/guest_cv_list_panel.html', {'guest_cvs': guest_cvs})

@login_required
def guest_cv_list(request):
    guest_cvs = TravelAgencyCV.objects.select_related('user').all()
    return render(request, 'dashboard/guest_cv_list.html', {'guest_cvs': guest_cvs})
    # return render(request, 'hr/hr_guest_cvs_list.html', {'guest_cvs': guest_cvs})

@login_required
def guest_cv_detail_by_pk(request, pk):
    cv = get_object_or_404(TravelAgencyCV, pk=pk)
    return render(request, 'dashboard/guest_cv.html', {'cv': cv})



# @login_required
# def hr_guest_cvs_list(request):
#     guest_cvs = TravelAgencyCV.objects.select_related('user').all()
#     return render(request, 'dashboard/hr_guest_cvs_list.html', {'guest_cvs': guest_cvs})
#     # return render(request, 'hr/hr_guest_cvs_list.html', {'guest_cvs': guest_cvs})



@login_required
def guest_dashboard(request):
    if request.user.role != 'guest':
        return redirect('home')

    # return render(request, 'accounts/guest_dashboard.html')
    return render(request, 'dashboard/guest_d.html')


@login_required
def guest_change_password(request):
    if request.user.role != 'guest':
        return redirect('home')

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Your password has been updated successfully.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'accounts/guest_change_password.html', {'form': form})


@login_required
def view_guest_cv(request):

    return render(request, 'accounts/guest_cv.html')


@login_required
def view_guest_cv_by_pk(request, pk):
    cv = get_object_or_404(TravelAgencyCV, pk=pk)
    return render(request, 'dashboard/guest_cv.html', {'cv': cv})




@login_required
def admin_dashboard(request):
    if request.user.role == 'admin':
        # return render(request, 'accounts/admin_dashboard.html')
        return render(request, 'dashboard/admin_d.html')
    return redirect('home')

@login_required
def admin_index(request):
    if request.user.role != 'admin':
        return redirect('home')
    return render(request, 'dashboard/admin_index.html')




@login_required
def hr_dashboard(request):
    if request.user.role != 'hr':
        return redirect('home')


    # HR dashboard logic here
    return render(request, 'accounts/hr_dashboard.html')




@login_required
def hr_view_guests_passport(request):
    # Ensure only HR users can access
    if request.user.role != 'hr':
        return redirect('home')  # or permission denied page

    # Get all PassportInfo for users with role 'guest'
    guest_passports = PassportInfo.objects.filter(user__role='student')

    context = {
        'guest_passports': guest_passports,
    }
    return render(request, 'hr/hr_guest_passports.html', context)


@login_required
def hr_guest_cvs_list(request):
    if request.user.role != 'hr':
        return redirect('home')  # or permission denied page
    guest_cvs = TravelAgencyCV.objects.select_related('user').all()
    return render(request, 'hr/hr_guest_cvs_list.html', {'guest_cvs': guest_cvs})




@login_required
def guest_cv_detail(request, pk):

    cv = TravelAgencyCV.objects.get(pk=pk)
    return render(request, 'hr/guest_cv_detail.html', {'cv': cv})



# from clients.forms import TravelAgencyCVForm

# @login_required
# def guest_cv_detail(request, pk):
#     if request.user.role != 'hr':
#         return redirect('home')

#     cv = get_object_or_404(TravelAgencyCV, pk=pk)

#     # Optional: confirm this cv belongs to a guest
#     if cv.user.role != 'guest':
#         return redirect('home')

#     if request.method == 'POST':
#         form = TravelAgencyCVForm(request.POST, request.FILES, instance=cv)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'CV updated successfully.')
#             return redirect('guest_cv_detail', pk=cv.pk)  # Or wherever you want to redirect
#         else:
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         form = TravelAgencyCVForm(instance=cv)

#     return render(request, 'hr/guest_cv_edit.html', {'form': form, 'cv': cv})







# Template paid

# from django.views.generic import TemplateView
# from web_project import TemplateLayout


# # """
# # This file is a view controller for multiple pages as a module.
# # Here you can override the page view layout.
# # Refer to test/urls.py file for more pages.
# # """


# class accountsView(TemplateView):
#     # Predefined function
#     def get_context_data(self, **kwargs):
#         # A function to init the global layout. It is defined in web_project/__init__.py file
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))

#         return context


# from web_project import TemplateLayout
# from web_project.template_helpers.theme import TemplateHelper

# class accountsView(TemplateView):
#     def get_context_data(self, **kwargs):
#         context = TemplateLayout.init(self, super().get_context_data(**kwargs))
#         context.update({
#             "layout_path": TemplateHelper.set_layout("layout_blank.html", context),  # ✅ This line is MANDATORY
#         })
#         return context