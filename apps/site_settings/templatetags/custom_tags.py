from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, None)

@register.filter
def get_field(form, field_name):
    return form[field_name]



# from django import template

# register = template.Library()

# @register.filter(name='zip_lists')
# def zip_lists(a, b):
#     return zip(a, b)