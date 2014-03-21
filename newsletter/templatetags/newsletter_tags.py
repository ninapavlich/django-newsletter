from django.template import Library

from ..models import *

register = Library()

@register.assignment_tag
def get_message_email(receipt):
	return receipt.message.get_message_email(receipt)

@register.assignment_tag
def get_message_archive_url(receipt):
	return receipt.message.get_archive_url(receipt)