from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def create_guest_user_for_profile(guest, default_password: str | None = None):
    """
    Create a loginable 'guest' user for this guest profile, if not exists.
    - Username: phone_number (your AUTH model already uses phone_number)
    - Role: 'guest'
    - Default password: provided or a generated one (could be OTP)
    """
    if guest.user_account:
        return guest.user_account

    with transaction.atomic():
        user = User.objects.create_user(
            phone_number=guest.phone_number,
            password=default_password or User.objects.make_random_password(),
            email=guest.email,
            role="guest",
            is_active=True,
        )
        guest.user_account = user
        guest.save(update_fields=["user_account"])
    return user


# from apps.guests.models import Guest

# def ensure_guest_profile(user):
#     """
#     Ensure Guest profile exists for a guest user.
#     Safe to call multiple times.
#     """
#     if hasattr(user, "guest_profile"):
#         return user.guest_profile

#     guest = Guest.objects.create(
#         user=user,
#         full_name=user.get_full_name() or "",
#         phone_number=user.phone_number,
#         email=getattr(user, "email", ""),
#     )
#     return guest

# apps/guests/services.py

from apps.guests.models import Guest

def ensure_guest_profile(user):
    """
    Guest role user login করলে তার জন্য Guest profile auto-create করবে
    """

    # শুধু guest user এর জন্য
    if getattr(user, "role", None) != "guest":
        return None

    # আগেই profile থাকলে সেটাই return
    guest = Guest.objects.filter(user_account=user).first()
    if guest:
        return guest

    # full_name safe ভাবে বানানো
    full_name = ""
    if hasattr(user, "first_name") or hasattr(user, "last_name"):
        full_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()

    # fallback: phone number
    if not full_name:
        full_name = user.phone_number

    guest = Guest.objects.create(
        user_account=user,              # ✅ CORRECT FIELD
        full_name=full_name,
        phone_number=user.phone_number, # Guest.phone_number unique
        email=getattr(user, "email", None),
        created_by=user,
    )

    return guest
