from django import template
register = template.Library()

@register.filter(name='key')
def key(value, arg):
    return value[arg]