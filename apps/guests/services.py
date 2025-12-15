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
