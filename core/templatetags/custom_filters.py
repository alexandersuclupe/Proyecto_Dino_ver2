from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Accede a un valor de un diccionario de forma segura"""
    return dictionary.get(key, None)
