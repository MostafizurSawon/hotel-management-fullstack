from .roles import ROLE_INDEX

# def role_flags(request):
#     user = getattr(request, "user", None)
#     role = getattr(user, "role", None) if user and user.is_authenticated else None
#     return {
#         "current_role": role,
#         "role_index": ROLE_INDEX.get(role, -1),
#     }


def role_flags(request):
    user = getattr(request, "user", None)
    role = getattr(user, "role", None) if user and user.is_authenticated else None

    can_manage_guests = role in {"receptionist", "manager", "admin", "super_admin"}

    return {
        "current_role": role,
        "role_index": ROLE_INDEX.get(role, -1),
        "can_manage_guests": can_manage_guests,
    }
