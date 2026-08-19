from django import template

register = template.Library()


@register.filter
def star_display(rating):
    """Render a numeric rating (0-5) as filled/empty star characters."""
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        rating = 0
    full = int(round(rating))
    full = max(0, min(5, full))
    return '\u2605' * full + '\u2606' * (5 - full)


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return ''


@register.filter
def status_badge(status):
    return f'badge-{status}'
