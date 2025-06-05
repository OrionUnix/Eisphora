from django import template

register = template.Library()

@register.filter
def lookup(obj, key):
    if not key:  # Ajoute une vérification pour éviter les clés vides
        return None
    return obj.get(key)  # Utilise .get() au lieu de [] pour éviter KeyError