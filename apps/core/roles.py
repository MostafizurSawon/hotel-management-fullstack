# Reusable role constants + helpers

ROLE_GUEST         = "guest"
ROLE_RECEPTIONIST  = "receptionist"
ROLE_HOUSEKEEPING  = "housekeeping"
ROLE_MANAGER       = "manager"
ROLE_ACCOUNTANT    = "accountant"
ROLE_ADMIN         = "admin"
ROLE_SUPER_ADMIN   = "super_admin"

# Strict hierarchy (lower index = lower privilege)
ROLE_ORDER = [
    ROLE_GUEST,
    ROLE_HOUSEKEEPING,
    ROLE_RECEPTIONIST,
    ROLE_ACCOUNTANT,
    ROLE_MANAGER,
    ROLE_ADMIN,
    ROLE_SUPER_ADMIN,
]

ROLE_INDEX = {r: i for i, r in enumerate(ROLE_ORDER)}

# Small helpers
def role_index(role: str | None) -> int:
    if not role:
        return -1
    return ROLE_INDEX.get(role, -1)

def at_least(user_role: str | None, min_role: str) -> bool:
    return role_index(user_role) >= role_index(min_role)

def in_any(user_role: str | None, allowed: list[str] | tuple[str, ...]) -> bool:
    return user_role in set(allowed)
