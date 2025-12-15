
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, UpdateView
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from web_project import TemplateLayout, TemplateHelper
from apps.room.models import Room

from .models import Payment
from .forms import PaymentEditForm

def _preserve_qs(request):
    qs = request.GET.urlencode()
    return qs



@method_decorator(login_required, name="dispatch")
class PaymentListPage(RequireAnyRoleMixin, ListView):
    model = Payment
    template_name = "payments/payment_list.html"
    context_object_name = "payments"
    paginate_by = 25
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_queryset(self):
        qs = (Payment.objects
              .select_related("booking", "booking__guest", "booking__room", "booking__room__category")
              .order_by("-received_at", "-id"))

        q         = self.request.GET.get("q", "").strip()
        method    = self.request.GET.get("method", "")
        date_from = self.request.GET.get("from", "")
        date_to   = self.request.GET.get("to", "")
        room_id   = self.request.GET.get("room", "")   # 👈 read room

        if q:
            qs = qs.filter(
                Q(booking__guest__full_name__icontains=q) |
                Q(booking__guest__phone_number__icontains=q) |
                Q(booking__guest__email__icontains=q) |
                Q(booking__room__room_number__icontains=q) |
                Q(txn_ref__icontains=q) |
                Q(note__icontains=q)
            )
        if method:
            qs = qs.filter(method=method)
        if room_id:
            qs = qs.filter(booking__room_id=room_id)  # 👈 filter by room
        if date_from:
            qs = qs.filter(received_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(received_at__date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        rooms = Room.objects.select_related("category").order_by("room_number")  # 👈 provide rooms

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "Payments History",
            "preserved_qs": _preserve_qs(self.request),
            "rooms": rooms,                                     # 👈 pass to template
            "filter_values": {
                "q": self.request.GET.get("q", ""),
                "room": self.request.GET.get("room", ""),       # 👈 keep selected
                "method": self.request.GET.get("method", ""),
                "from": self.request.GET.get("from", ""),
                "to": self.request.GET.get("to", ""),
            },
        })
        return ctx


@method_decorator(login_required, name="dispatch")
class PaymentEditPage(RequireAnyRoleMixin, UpdateView):
    model = Payment
    form_class = PaymentEditForm
    template_name = "payments/payment_edit.html"
    allowed_roles = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

    def get_success_url(self):
        qs = self.request.GET.urlencode()
        base = reverse("payment_list")
        return f"{base}?{qs}" if qs else base

    def get_context_data(self, **kwargs):
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
        p = self.object
        guest = getattr(p.booking.guest, "full_name", "Guest")
        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": f"Edit Payment #{p.id} — {guest}",
            "preserved_qs": self.request.GET.urlencode(),
        })
        return ctx

    def form_valid(self, form):
        obj = form.save(commit=False)
        # model.clean() will validate over/under-pay; save then sync booking caches via signal
        obj.save()
        messages.success(self.request, "✅ Payment updated.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "❌ Please fix the errors below.")
        return super().form_invalid(form)


@require_POST
@login_required
def payment_delete(request, pk: int):
    p = get_object_or_404(Payment, pk=pk)
    booking = p.booking
    p.delete()  # signals keep caches in sync if you hooked them; else manual: booking.sync_payment_caches()
    messages.success(request, "🗑️ Payment deleted.")
    # back to list, preserve existing filters if any (Referer বা qs)
    qs = request.GET.urlencode()
    url = reverse("payment_list")
    return redirect(f"{url}?{qs}" if qs else url)

from types import SimpleNamespace

# @login_required
# def payment_invoice(request, pk: int):
#     payment = get_object_or_404(
#         Payment.objects.select_related("booking__guest", "booking__room"),
#         pk=pk
#     )

#     # 👇 Wrap the request so TemplateLayout.init sees .request
#     # wrapper = SimpleNamespace(request=request)
#     ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))
#     ctx.update({
#         "layout_path": TemplateHelper.set_layout("layout_blank.html", ctx),
#         "payment": payment,
#     })

#     # ctx = TemplateLayout.init(wrapper, {
#     #     "page_title": f"Invoice — #{payment.id}",
#     #     "payment": payment,
#     # })
#     return render(request, "payments/payment_invoice.html", ctx)

# apps/bookings/views_payments.py

from types import SimpleNamespace
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from web_project import TemplateLayout, TemplateHelper

from .models import Payment

@login_required
def payment_invoice(request, pk: int):
    payment = get_object_or_404(
        Payment.objects.select_related("booking", "booking__guest", "booking__room"),
        pk=pk,
    )

    # TemplateLayout.init expects an object that has `.request`
    wrapper = SimpleNamespace(request=request)

    # Base context via your theme/layout helper
    ctx = TemplateLayout.init(wrapper, {})
    ctx.update({
        "layout_path": TemplateHelper.set_layout("layout_blank.html", ctx),
        "page_title": f"Invoice — #{payment.id}",
        "payment": payment,
    })

    return render(request, "payments/payment_invoice.html", ctx)



# from django.utils import timezone
# from django.db.models import Sum

# from web_project import TemplateLayout, TemplateHelper
# from .models import Payment

# def _money(n: int) -> int:
#     # amounts are stored as integer BDT in your project
#     return int(n or 0)

# @login_required
# def payment_invoice(request, pk: int):
#     payment = get_object_or_404(Payment.objects.select_related(
#         "booking", "booking__guest", "booking__room"
#     ), pk=pk)

#     booking = payment.booking
#     payments = booking.payments.order_by("received_at", "id")

#     # Totals (server-side, robust)
#     charges = payments.filter(kind=Payment.Kind.CHARGE).aggregate(s=Sum("amount"))["s"] or 0
#     refunds = payments.filter(kind=Payment.Kind.REFUND).aggregate(s=Sum("amount"))["s"] or 0
#     paid = _money(charges - refunds)

#     ctx = {
#         "payment": payment,
#         "booking": booking,
#         "payments": payments,
#         "paid_total": paid,
#         "due_total": _money(booking.net_amount - paid),
#         "now": timezone.now(),
#     }
#     ctx = TemplateLayout.init(request, ctx)
#     ctx["layout_path"] = TemplateHelper.set_layout("layout_blank.html", ctx)  # প্রিন্ট ফ্রেন্ডলি

#     return render(request, "payments/payment_invoice.html", ctx)

# @login_required
# def payment_invoice_partial(request, pk: int):
#     """
#     Modal-এ লোড করার জন্য শুধুই ইনভয়েস HTML fragment রিটার্ন করবে।
#     """
#     payment = get_object_or_404(Payment.objects.select_related(
#         "booking", "booking__guest", "booking__room"
#     ), pk=pk)
#     booking = payment.booking
#     payments = booking.payments.order_by("received_at", "id")

#     charges = payments.filter(kind=Payment.Kind.CHARGE).aggregate(s=Sum("amount"))["s"] or 0
#     refunds = payments.filter(kind=Payment.Kind.REFUND).aggregate(s=Sum("amount"))["s"] or 0
#     paid = _money(charges - refunds)

#     html = render(
#         request,
#         "payments/_invoice_partial.html",
#         {
#             "payment": payment,
#             "booking": booking,
#             "payments": payments,
#             "paid_total": paid,
#             "due_total": _money(booking.net_amount - paid),
#             "now": timezone.now(),
#         },
#     ).content.decode("utf-8")

#     return JsonResponse({"ok": True, "html": html})
