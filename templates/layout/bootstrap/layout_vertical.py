# from django.conf import settings
# import json


# from web_project.template_helpers.theme import TemplateHelper

# menu_file_path =  settings.BASE_DIR / "templates" / "layout" / "partials" / "menu" / "vertical" / "json" / "vertical_menu.json"

# """
# This is an entry and Bootstrap class for the theme level.
# The init() function will be called in web_project/__init__.py
# """


# class TemplateBootstrapLayoutVertical:
#     def init(context):
#         context.update(
#             {
#                 "layout": "vertical",
#                 "content_navbar": True,
#                 "is_navbar": True,
#                 "is_menu": True,
#                 "is_footer": True,
#                 "navbar_detached": True,
#             }
#         )

#         # map_context according to updated context values
#         TemplateHelper.map_context(context)

#         TemplateBootstrapLayoutVertical.init_menu_data(context)

#         return context

#     def init_menu_data(context):
#         # Load the menu data from the JSON file
#         menu_data = json.load(menu_file_path.open()) if menu_file_path.exists() else []

#         # Updated context with menu_data
#         context.update({"menu_data": menu_data})


# from django.conf import settings
# import json
# from web_project.template_helpers.theme import TemplateHelper
# from pathlib import Path

# # Load menu JSON path dynamically by role
# def get_menu_file_path(role):
#     role = (role or "student").lower()  # Normalize role to lowercase
#     filename_map = {
#         "master_admin": "vertical_master_menu.json",
#         "admin": "vertical_menu.json",
#         "sub_admin": "vertical_sub_admin_menu.json",
#         "teacher": "vertical_teacher_menu.json",
#         "student": "vertical_student_menu.json",
#         # Add more roles and corresponding JSON file names here
#     }

#     filename = filename_map.get(role, "vertical_menu.json")  # Default menu
#     return Path(settings.BASE_DIR) / "templates" / "layout" / "partials" / "menu" / "vertical" / "json" / filename

# class TemplateBootstrapLayoutVertical:
#     @staticmethod
#     def init(context):
#         context.update({
#             "layout": "vertical",
#             "content_navbar": True,
#             "is_navbar": True,
#             "is_menu": True,
#             "is_footer": True,
#             "navbar_detached": True,
#         })

#         # Map context
#         TemplateHelper.map_context(context)

#         user = context.get("user")
#         if hasattr(user, "role"):
#             role = user.role
#         elif isinstance(user, dict) and "role" in user:
#             role = user["role"]
#         else:
#             role = "student"

#         role = role.lower()
#         print("--",user)
#         print("--",role)

#         TemplateBootstrapLayoutVertical.init_menu_data(context, role)
#         return context

#     @staticmethod
#     def init_menu_data(context, role):
#         menu_file_path = get_menu_file_path(role)

#         try:
#             with open(menu_file_path, 'r', encoding='utf-8') as file:
#                 context["menu_data"] = json.load(file)

#         except FileNotFoundError:
#             context["menu_data"] = []



from django.conf import settings
import json
from web_project.template_helpers.theme import TemplateHelper
from pathlib import Path
from django.contrib.auth.models import AnonymousUser

# Load menu JSON path dynamically by role
def get_menu_file_path(role):
    role = (role or "student").lower()  # Normalize role to lowercase
    filename_map = {
        "master_admin": "vertical_master_menu.json",
        "admin": "vertical_menu.json",
        "receptionist": "vertical_receptionist_menu.json",
        "teacher": "vertical_teacher_menu.json",
        "guest": "vertical_menu_guest.json",
    }
    filename = filename_map.get(role, "vertical_menu.json")  # Default menu
    return Path(settings.BASE_DIR) / "templates" / "layout" / "partials" / "menu" / "vertical" / "json" / filename

class TemplateBootstrapLayoutVertical:
    @staticmethod
    def init(context):
        context.update({
            "layout": "vertical",
            "content_navbar": True,
            "is_navbar": True,
            "is_menu": True,
            "is_footer": True,
            "navbar_detached": True,
        })

        # Map context
        TemplateHelper.map_context(context)

        user = context.get("user")
        if user and not isinstance(user, AnonymousUser) and hasattr(user, "role"):
            role = user.role.lower()
        elif isinstance(user, dict) and "role" in user:
            role = user["role"].lower()
        else:
            role = "guest"
            print(f"DEBUG: User is {user}, defaulting role to 'guest'")

        print(f"DEBUG: User: {user}, Role: {role}")

        TemplateBootstrapLayoutVertical.init_menu_data(context, role)
        return context

    @staticmethod
    def init_menu_data(context, role):
        menu_file_path = get_menu_file_path(role)
        try:
            with open(menu_file_path, 'r', encoding='utf-8') as file:
                context["menu_data"] = json.load(file)
        except FileNotFoundError:
            print(f"DEBUG: Menu file not found: {menu_file_path}")
            context["menu_data"] = []
