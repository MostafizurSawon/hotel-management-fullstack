from django import template

register = template.Library()

@register.filter
def add_class(value, arg):
    """
    Adds a CSS class to a form field.
    Usage: {{ form.field|add_class:"my-class" }}
    """
    return value.as_widget(attrs={'class': arg})


@register.filter
def star_range(value):
    try:
        return range(int(value))
    except:
        return range(0)



# passport



@register.filter
def dynamic_attr(obj, field_name):
    return getattr(obj, field_name, None)
