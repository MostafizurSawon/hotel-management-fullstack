
from django.views.generic import ListView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from web_project import TemplateLayout, TemplateHelper

from apps.core.guards import RequireAnyRoleMixin
from apps.core.roles import ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..core.models import SmsLog
import csv

ALLOWED_ROLES = (ROLE_RECEPTIONIST, ROLE_MANAGER, ROLE_ADMIN, ROLE_SUPER_ADMIN)

from django.utils.dateparse import parse_date

def _filter_sms_queryset(request):
    """
    Shared filter for list + CSV.
    Query params:
      q       : search text
      status  : SENT / FAIL / OK
      from    : created_at >= date
      to      : created_at <= date
    """
    qs = SmsLog.objects.order_by("-created_at")
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()
    from_date = parse_date(request.GET.get("from") or "")
    to_date   = parse_date(request.GET.get("to") or "")

    if q:
        qs = qs.filter(
            Q(to__icontains=q) |
            Q(body__icontains=q) |
            Q(result__icontains=q) |
            Q(context__icontains=q)
        )
    if status:
        qs = qs.filter(result__istartswith=status)
    if from_date:
        qs = qs.filter(created_at__date__gte=from_date)
    if to_date:
        qs = qs.filter(created_at__date__lte=to_date)

    return qs

@method_decorator(login_required, name="dispatch")
class SmsLogListPage(RequireAnyRoleMixin, ListView):
    model = SmsLog
    template_name = "core/sms_log_list.html"
    context_object_name = "logs"
    paginate_by = 50
    allowed_roles = ALLOWED_ROLES

    def get_queryset(self):
        return _filter_sms_queryset(self.request)

    def get_context_data(self, **kwargs):
        # initialize base ctx via TemplateLayout (so layout bits exist)
        ctx = TemplateLayout.init(self, super().get_context_data(**kwargs))

        params = self.request.GET.copy()
        params.pop("page", None)

        ctx.update({
            "layout_path": TemplateHelper.set_layout("layout_vertical.html", ctx),
            "page_title": "SMS Logs",
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "preserved_qs": params.urlencode(),
            "from_date": self.request.GET.get("from", ""),
            "to_date": self.request.GET.get("to", ""),
        })
        return ctx


# @method_decorator(login_required, name="dispatch")
# class SmsLogListPage(RequireAnyRoleMixin, ListView):
#     model = SmsLog
#     template_name = "core/sms_log_list.html"
#     context_object_name = "logs"
#     paginate_by = 50
#     allowed_roles = ALLOWED_ROLES

#     def get_queryset(self):
#         return _filter_sms_queryset(self.request)

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         # Keep it Vuexy-friendly: page title, preserve filters, etc.
#         params = self.request.GET.copy()
#         params.pop("page", None)
#         ctx.update({
#             "page_title": "SMS Logs",
#             "q": self.request.GET.get("q", ""),
#             "status": self.request.GET.get("status", ""),
#             "preserved_qs": params.urlencode(),
#         })
#         return ctx


@method_decorator(login_required, name="dispatch")
class SmsLogExportCSVView(RequireAnyRoleMixin, View):
    """
    Export filtered logs as CSV (no pagination).
    Avoid MRO issue by NOT inheriting SmsLogListPage.
    """
    allowed_roles = ALLOWED_ROLES

    def get(self, request, *args, **kwargs):
        qs = _filter_sms_queryset(request)

        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="sms_logs.csv"'
        resp.write("\ufeff")  # Excel-friendly BOM

        w = csv.writer(resp)
        w.writerow(["ID", "To", "Context", "Result", "Body", "Provider", "Booking ID", "Created At"])
        for r in qs:
            w.writerow([
                r.id,
                r.to or "",
                r.context or "",
                r.result or "",
                (r.body or "").replace("\r", " ").replace("\n", " "),
                getattr(r, "provider", "") or "",
                getattr(r, "booking_id", "") or "",
                r.created_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(r, "created_at", None) else "",
            ])
        return resp
