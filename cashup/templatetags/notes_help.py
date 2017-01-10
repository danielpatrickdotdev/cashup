from django import template

from cashup.models import NotesHelpText


register = template.Library()


@register.simple_tag
def random_help_text():
    return NotesHelpText.objects.order_by('?').first()
