from functools import wraps
from typing import Iterable
from django.http import HttpRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator

from .roles import at_least, in_any, ROLE_SUPER_ADMIN

def _user_role(user) -> str | None:
    try:
        return getattr(user, "role", None)
    except Exception:
        return None

def _is_super(user) -> bool:
    return bool(getattr(user, "is_superuser", False))

def _deny(request: HttpRequest, msg: str = "You do not have permission to access this page."):
    # You can change this to raise PermissionDenied() if you prefer 403 over redirect.
    messages.error(request, msg)
    return redirect("core:no_access") if _has_url("core:no_access") else HttpResponseForbidden(msg)

def _has_url(name: str) -> bool:
    from django.urls import get_resolver
    try:
        get_resolver().resolve(f"/reverse-check/{name}/")  # forced miss
    except Exception:
        pass
    # quick/cheap check
    try:
        from django.urls import reverse
        reverse(name)
        return True
    except Exception:
        return False


# -----------------------------
# Decorators for function views
# -----------------------------
def require_any_role(*allowed_roles: str):
    """
    Allow if user's role is in allowed_roles OR user.is_superuser.
    Usage:
      @login_required
      @require_any_role("receptionist", "manager", "admin", "super_admin")
      def my_view(request): ...
    """
    allowed_set = set(allowed_roles)

    def deco(view_func):
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect("login")
            if _is_super(user) or in_any(_user_role(user), allowed_set):
                return view_func(request, *args, **kwargs)
            return _deny(request)
        return _wrapped
    return deco


def require_min_role(min_role: str):
    """
    Allow if user's role >= min_role by hierarchy OR user.is_superuser.
    Usage:
      @login_required
      @require_min_role("manager")
      def mgr_view(request): ...
    """
    def deco(view_func):
        @wraps(view_func)
        def _wrapped(request: HttpRequest, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect("login")
            if _is_super(user) or at_least(_user_role(user), min_role):
                return view_func(request, *args, **kwargs)
            return _deny(request)
        return _wrapped
    return deco


# -----------------------------
# Mixins for class-based views
# -----------------------------
class RequireAnyRoleMixin:
    """
    Example:
      class MyPage(RequireAnyRoleMixin, TemplateView):
          allowed_roles = ("receptionist", "manager", "admin", "super_admin")
          template_name = "..."
    """
    allowed_roles: Iterable[str] = ()

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect("login")
        if _is_super(user) or in_any(_user_role(user), self.allowed_roles):
            return super().dispatch(request, *args, **kwargs)
        return _deny(request)


class RequireMinRoleMixin:
    """
    Example:
      class MyAdminPage(RequireMinRoleMixin, TemplateView):
          min_role = "manager"
    """
    min_role: str = ROLE_SUPER_ADMIN  # secure default (nobody except super)

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect("login")
        if _is_super(user) or at_least(_user_role(user), self.min_role):
            return super().dispatch(request, *args, **kwargs)
        return _deny(request)
