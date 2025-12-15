# apps/bookings/signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.core.cache import cache

from .models import Payment, Booking
from apps.core.sms import send_sms_jbd, normalize_bd_mobile
from apps.core.site_meta import get_hotel_meta  # helper to read site_settings

# ==================== SMS feature toggles ====================
# Later, you can flip these or move to Django settings:
#   - To re-enable CHECKED_OUT SMS: set STATUS["CHECKED_OUT"] = True
SMS_FLAGS = {
    "CREATED": True,   # new booking (RESERVED) SMS
    "STATUS": {
        "CHECKED_IN":  True,
        "CHECKED_OUT": False,   # 🚫 disabled as requested
        "CANCELLED":   True,
    }
}
# Or read from settings with defaults:
# SMS_FLAGS = getattr(settings, "SMS_FLAGS", SMS_FLAGS)

# -------------------- 1) PAYMENT SIGNAL --------------------
@receiver([post_save, post_delete], sender=Payment)
def recalc_booking_totals(sender, instance: Payment, **kwargs):
    """
    Whenever a Payment is created/updated/deleted,
    keep the parent Booking caches in sync.
    """
    booking = instance.booking
    booking.sync_payment_caches(save=True)  # ✅ no SMS here

# -------------------- 2) BOOKING STATUS → SMS --------------------
def _compose_status_sms(booking: Booking, new_status: str) -> str:
    hotel, phone = get_hotel_meta()
    tmpl_map = getattr(settings, "SMS_TEMPLATES", {}) or {}

    code = booking.pk
    room = getattr(getattr(booking, "room", None), "room_number", "Room")
    ci = booking.check_in.strftime("%d %b %Y")
    co = booking.check_out.strftime("%d %b %Y")

    ctx = {
        "hotel": hotel,
        "phone": phone or "",
        "code": code,
        "room": room,
        "check_in": ci,
        "check_out": co,
    }

    key = None
    if new_status == Booking.Status.CHECKED_IN:
        key = "CHECKED_IN"
    elif new_status == Booking.Status.CHECKED_OUT:
        key = "CHECKED_OUT"
    elif new_status == Booking.Status.CANCELLED:
        key = "CANCELLED"

    if key and key in tmpl_map:
        try:
            return tmpl_map[key].format(**ctx)
        except Exception:
            pass

    if new_status == Booking.Status.CHECKED_IN:
        return f"{hotel}: Checked-in.\nCode: {code} | Room: {room}\nIn: {ci}  Out: {co}"
    if new_status == Booking.Status.CHECKED_OUT:
        return f"{hotel}: Checked-out. Thanks for staying!\nCode: {code}"
    if new_status == Booking.Status.CANCELLED:
        return f"{hotel}: Booking {code} cancelled."
    return f"{hotel}: Booking {code} status updated: {new_status}."

@receiver(pre_save, sender=Booking)
def _capture_old_status(sender, instance: Booking, **kwargs):
    """
    Cache previous status so post_save can detect changes.
    """
    if not instance.pk:
        instance._old_status = None
        return
    try:
        old = sender.objects.get(pk=instance.pk)
        instance._old_status = getattr(old, "status", None)
    except sender.DoesNotExist:
        instance._old_status = None

@receiver(post_save, sender=Booking)
def _send_status_sms_when_changed(sender, instance: Booking, created, **kwargs):
    """
    Send SMS when booking status actually changes to:
    CHECKED_IN / CHECKED_OUT / CANCELLED
    De-duped for 5 minutes to avoid duplicates.
    """
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = getattr(instance, "status", None)
    if not new_status or old_status == new_status:
        return

    # Only these trigger SMS (and only if enabled in flags)
    target_statuses = {
        Booking.Status.CHECKED_IN,
        # Booking.Status.CHECKED_OUT,
        Booking.Status.CANCELLED,
    }
    if new_status not in target_statuses:
        return

    # 🔒 Respect feature flag (CHECKED_OUT disabled now)
    flag = SMS_FLAGS["STATUS"].get(new_status, False)
    if not flag:
        return  # 🚫 skip sending for this status

    # De-dup key (5 min)
    cache_key = f"sms:booking_status:{instance.pk}:{new_status}"
    if cache.get(cache_key):
        return
    cache.set(cache_key, True, timeout=300)

    # Guest phone
    guest = getattr(instance, "guest", None)
    mobile = getattr(guest, "phone_number", None) if guest else None
    m01 = normalize_bd_mobile(mobile)
    if not m01:
        return

    # Compose & send
    msg = _compose_status_sms(instance, new_status)
    send_sms_jbd(m01, msg)

# ===================== 3) BOOKING CREATED (RESERVED) → SMS =====================
def _compose_created_sms(booking: Booking) -> str:
    hotel, phone = get_hotel_meta()
    tmpl_map = getattr(settings, "SMS_TEMPLATES", {}) or {}

    code = booking.pk
    room = getattr(getattr(booking, "room", None), "room_number", "Room")
    ci = booking.check_in.strftime("%d %b %Y")
    co = booking.check_out.strftime("%d %b %Y")

    ctx = {
        "hotel": hotel,
        "phone": phone or "",
        "code": code,
        "room": room,
        "check_in": ci,
        "check_out": co,
    }

    if "RESERVED" in tmpl_map:
        try:
            return tmpl_map["RESERVED"].format(**ctx)
        except Exception:
            pass

    return f"{hotel}: Booking confirmed.\nCode: {code} | Room: {room}\nIn: {ci}  Out: {co}"

@receiver(post_save, sender=Booking)
def _send_created_sms(sender, instance: Booking, created, **kwargs):
    """
    Send SMS once when a booking is first created (RESERVED).
    De-duped for 5 minutes to avoid accidental double sends.
    """
    if not created or not SMS_FLAGS.get("CREATED", True):
        return

    try:
        if hasattr(Booking, "Status") and getattr(instance, "status", None) is not None:
            if instance.status != Booking.Status.RESERVED:
                return
    except Exception:
        pass

    cache_key = f"sms:booking_created:{instance.pk}"
    if cache.get(cache_key):
        return
    cache.set(cache_key, True, timeout=300)

    guest = getattr(instance, "guest", None)
    mobile = getattr(guest, "phone_number", None) if guest else None
    m01 = normalize_bd_mobile(mobile)
    if not m01:
        return

    msg = _compose_created_sms(instance)
    send_sms_jbd(m01, msg)
