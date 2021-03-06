import logging

logger = logging.getLogger(__name__)

from django_extensions.management.jobs import HourlyJob

from django.utils.translation import ugettext as _
from newsletter.models import Message


class Job(HourlyJob):
    help = "Submit pending messages."

    def execute(self):
        logger.info(_('Submitting queued newsletter mailings'))
        Message.submit_queue()
