import logging
logger = logging.getLogger(__name__)


from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import permalink

from django.template import Context, TemplateDoesNotExist
from django.template.loader import select_template

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.timezone import now
from datetime import datetime, timedelta

from bs4 import BeautifulSoup


from .utils import (
	make_activation_code, get_default_sites, ACTIONS, get_user_model
)
User = get_user_model()

NOT_SENT = 0
SENT = 1
ERROR_SENDING = 2
SENDING_STATUS_CHOICES = (
	(NOT_SENT, 'Not Sent'),
	(SENT, 'Sent'),
	(ERROR_SENDING, 'Error Sending'),
)

IMMEDIATE = 0
DAILY = 10
WEEKLY  = 25
MONTHLY = 50
YEARLY = 100
FREQUENCY_OPTIONS = (
	(IMMEDIATE, "Immediate"),
	(DAILY, "Daily"),
	(WEEKLY, "Weekly"),
	(MONTHLY, "Monthly"),
	(YEARLY, "Yearly")
)




class Newsletter(models.Model):
	site = models.ManyToManyField(Site, default=get_default_sites)

	title = models.CharField(
		max_length=200, verbose_name=_('newsletter title')
	)
	slug = models.SlugField(db_index=True, unique=True)

	email = models.EmailField(
		verbose_name=_('e-mail'), help_text=_('Sender e-mail')
	)
	sender = models.CharField(
		max_length=200, verbose_name=_('sender'), help_text=_('Sender name')
	)

	visible = models.BooleanField(
		default=True, verbose_name=_('visible'), db_index=True
	)

	track_links = models.BooleanField( default=True )

	send_html = models.BooleanField(
		default=True, verbose_name=_('send html'),
		help_text=_('Whether or not to send HTML versions of e-mails.')
	)

	objects = models.Manager()

	# Automatically filter the current site
	on_site = CurrentSiteManager()

	def get_templates(self, action):
		"""
		Return a subject, text, HTML tuple with e-mail templates for
		a particular action. Returns a tuple with subject, text and e-mail
		template.
		"""

		assert action in ACTIONS + ('message', ), 'Unknown action: %s' % action

		# Common substitutions for filenames
		tpl_subst = {
			'action': action,
			'newsletter': self.slug
		}

		# Common root path for all the templates
		tpl_root = 'newsletter/message/'

		
		text_template = select_template([
			tpl_root + '%(newsletter)s/%(action)s.txt' % tpl_subst,
			tpl_root + '%(action)s.txt' % tpl_subst,
		])

		if self.send_html:
			html_template = select_template([
				tpl_root + '%(newsletter)s/%(action)s.html' % tpl_subst,
				tpl_root + '%(action)s.html' % tpl_subst,
			])
		else:
			# HTML templates are not required
			html_template = None

		return (text_template, html_template)

	def __unicode__(self):
		return self.title

	class Meta:
		verbose_name = _('newsletter')
		verbose_name_plural = _('newsletters')

	def send_messages(self):
		subscriptions = Subscription.objects.get(newsletter=self,subscribed=True).exclude(unsubscribed=True)
		for subscription in subscriptions:
			subscription.send_subscription()

	@permalink
	def get_absolute_url(self):
		return (
			'newsletter_detail', (),
			{'newsletter_slug': self.slug}
		)

	@permalink
	def subscribe_url(self):
		return (
			'newsletter_subscribe_request', (),
			{'newsletter_slug': self.slug}
		)

	@permalink
	def update_url(self):
		return (
			'newsletter_update_request', (),
			{'newsletter_slug': self.slug}
		)

	@permalink
	def archive_url(self):
		return (
			'newsletter_archive', (),
			{'newsletter_slug': self.slug}
		)

	def get_sender(self):
		return u'%s <%s>' % (self.sender, self.email)

	def get_subscriptions(self):
		logger.debug(u'Looking up subscribers for %s', self)

		return Subscription.objects.filter(newsletter=self, subscribed=True)

	@classmethod
	def get_default_id(cls):
		try:
			objs = cls.objects.all()
			if objs.count() == 1:
				return objs[0].id
		except:
			pass
		return None

	@staticmethod
	def autocomplete_search_fields():
		return ("id__iexact", "title__icontains",)




class Subscription(models.Model):
	

	_admin_name = models.CharField(max_length=255, blank=True, null=True)

	user = models.ForeignKey(
		User, blank=True, null=True, verbose_name=_('user')
	)

	ip = models.IPAddressField(_("IP address"), blank=True, null=True)

	newsletter = models.ForeignKey('Newsletter', verbose_name=_('newsletter'))

	create_date = models.DateTimeField(editable=False, default=now)

	activation_code = models.CharField(
		verbose_name=_('activation code'), max_length=40,
		default=make_activation_code
	)

	subscribed = models.BooleanField(
		default=False, verbose_name=_('subscribed'), db_index=True
	)
	subscribe_date = models.DateTimeField(
		verbose_name=_("subscribe date"), null=True, blank=True
	)

	# This should be a pseudo-field, I reckon.
	unsubscribed = models.BooleanField(
		default=False, verbose_name=_('unsubscribed'), db_index=True
	)
	unsubscribe_date = models.DateTimeField(
		verbose_name=_("unsubscribe date"), null=True, blank=True
	)

	frequency = models.IntegerField(choices=FREQUENCY_OPTIONS, default=IMMEDIATE)
	last_sent_date = models.DateTimeField(null=True, blank=True)

	def __unicode__(self):
		return self._admin_name

	class Meta:

		ordering = ('_admin_name',)
		verbose_name = _('subscription')
		verbose_name_plural = _('subscriptions')
		unique_together = ('user', 'newsletter')

	def get_name(self):
		if self.user:
			return self.user.get_full_name()
		return None
		
	def get_email(self):
		if self.user:
			return self.user.email
		return None

	def update(self, action):
		"""
		Update subscription according to requested action:
		subscribe/unsubscribe/update/, then save the changes.
		"""

		assert action in ('subscribe', 'update', 'unsubscribe')

		# If a new subscription or update, make sure it is subscribed
		# Else, unsubscribe
		if action == 'subscribe' or action == 'update':
			self.subscribed = True
		else:
			self.unsubscribed = True

		logger.debug(
			_(u'Updated subscription %(subscription)s to %(action)s.'),
			{
				'subscription': self,
				'action': action
			}
		)

		# This triggers the subscribe() and/or unsubscribe() methods, taking
		# care of stuff like maintaining the (un)subscribe date.
		self.save()

	def _subscribe(self):
		"""
		Internal helper method for managing subscription state
		during subscription.
		"""
		logger.debug(u'Subscribing subscription %s.', self)

		self.subscribe_date = now()
		self.subscribed = True
		self.unsubscribed = False

	def _unsubscribe(self):
		"""
		Internal helper method for managing subscription state
		during unsubscription.
		"""
		logger.debug(u'Unsubscribing subscription %s.', self)

		self.subscribed = False
		self.unsubscribed = True
		self.unsubscribe_date = now()

	def save(self, *args, **kwargs):
		"""
		Perform some basic validation and state maintenance of Subscription.

			"""
		

		# This is a lame way to find out if we have changed but using Django
		# API internals is bad practice. This is necessary to discriminate
		# from a state where we have never been subscribed but is mostly for
		# backward compatibility. It might be very useful to make this just
		# one attribute 'subscribe' later. In this case unsubscribed can be
		# replaced by a method property.

		if self.pk:
			assert(Subscription.objects.filter(pk=self.pk).count() == 1)

			subscription = Subscription.objects.get(pk=self.pk)
			old_subscribed = subscription.subscribed
			old_unsubscribed = subscription.unsubscribed

			# If we are subscribed now and we used not to be so, subscribe.
			# If we user to be unsubscribed but are not so anymore, subscribe.
			if ((self.subscribed and not old_subscribed) or
			   (old_unsubscribed and not self.unsubscribed)):
				self._subscribe()

				assert not self.unsubscribed
				assert self.subscribed

			# If we are unsubcribed now and we used not to be so, unsubscribe.
			# If we used to be subscribed but are not subscribed anymore,
			# unsubscribe.
			elif ((self.unsubscribed and not old_unsubscribed) or
				  (old_subscribed and not self.subscribed)):
				self._unsubscribe()

				assert not self.subscribed
				assert self.unsubscribed
		else:
			if self.subscribed:
				self._subscribe()
			elif self.unsubscribed:
				self._unsubscribe()

		#Update admin name
		self._admin_name = (self.get_name()+" "+self.get_email()+" to "+self.newsletter.title).encode('ascii', 'ignore')

		super(Subscription, self).save(*args, **kwargs)

	def get_recipient(self):
		if self.user:
			return u'%s <%s>' % (self.get_name(), self.get_email())

		return None

	def get_unsubscribe_url(self, user):
		return reverse(
			'newsletter_unsubscribe_request',
			kwargs ={
				'newsletter_slug': self.newsletter.slug,
				'user_pk': user.pk
			}
		)

	def send_activation_email(self, action):
		assert action in ACTIONS, 'Unknown action: %s' % action

		(subject_template, text_template, html_template) = \
			self.get_templates(action)

		variable_dict = {
			'subscription': self,
			'site': Site.objects.get_current(),
			'newsletter': self.newsletter,
			'date': self.subscribe_date,
			'STATIC_URL': settings.STATIC_URL,
			'MEDIA_URL': settings.MEDIA_URL
		}

		unescaped_context = Context(variable_dict, autoescape=False)

		subject = subject_template.render(unescaped_context).strip()
		text = text_template.render(unescaped_context)

		message = EmailMultiAlternatives(
			subject, text,
			from_email=self.newsletter.get_sender(),
			to=[self.email]
		)

		if html_template:
			escaped_context = Context(variable_dict)

			message.attach_alternative(
				html_template.render(escaped_context), "text/html"
			)

		message.send()

		logger.debug(
			u'Activation email sent for action "%(action)s" to %(subscriber)s '
			u'with activation code "%(action_code)s".', {
				'action_code': self.activation_code,
				'action': action,
				'subscriber': self
			}
		)

	def get_templates(self, action):
		"""
		Return a subject, text, HTML tuple with e-mail templates for
		a particular action. Returns a tuple with subject, text and e-mail
		template.
		"""

		assert action in ACTIONS + ('newsletter', ), 'Unknown action: %s' % action

		# Common substitutions for filenames
		tpl_subst = {
			'action': action,
			'newsletter': self.newsletter.slug
		}

		# Common root path for all the templates
		tpl_root = 'newsletter/message/'

		#print "tpl_subst: "+str(tpl_subst)

		subject_template = select_template([
			tpl_root + '%(newsletter)s/%(action)s_subject.txt' % tpl_subst,
			tpl_root + '%(action)s_subject.txt' % tpl_subst,
		])

		text_template = select_template([
			tpl_root + '%(newsletter)s/%(action)s.txt' % tpl_subst,
			tpl_root + '%(action)s.txt' % tpl_subst,
		])

		if self.newsletter.send_html:
			html_template = select_template([
				tpl_root + '%(newsletter)s/%(action)s.html' % tpl_subst,
				tpl_root + '%(action)s.html' % tpl_subst,
			])
		else:
			# HTML templates are not required
			html_template = None

		return (subject_template, text_template, html_template)

	def send_subscription(self, messages=None):
		print "Send subscription to "+str(self.user)
		if self.subscribed == False:
			print "User has not yet subscribed"
			return

		if self.unsubscribed == True:
			print "User has unsubscribed"
			return

			
		#Send a social update if the timing is right.
		timing_is_right = True
		
		#Options 0-2 are not implemented on the front end.
		if self.last_sent_date:
			if self.unsubscribed == True:
				#User wants no emails
				timing_is_right = False
			elif self.frequency == IMMEDIATE:
				#user wants emails instantly, let's do it.
				timing_is_right = True
			elif self.frequency == DAILY:
				#user wants emails daily, only send email if it's been at least a day since last digest.
				time_since_digest = (now()-subscription.last_sent_date)
				timing_is_right =  time_since_digest >= timedelta(days=1)            
			elif self.frequency == WEEKLY:
				#user wants emails weekly, only send email if it's been at least a week since last digest.
				time_since_digest = (now()-subscription.last_sent_date)
				timing_is_right =  time_since_digest >= timedelta(weeks=1)            
			elif self.frequency == MONTHLY:
				#user wants emails weekly, only send email if it's been at least a week since last digest.
				time_since_digest = (now()-subscription.last_sent_date)
				timing_is_right =  time_since_digest >= timedelta(weeks=4)   
			elif self.frequency == YEARLY:
				#user wants emails weekly, only send email if it's been at least a week since last digest.
				time_since_digest = (now()-subscription.last_sent_date)
				timing_is_right =  time_since_digest >= timedelta(days=365)            
		else:
			timing_is_right = True
			

		if timing_is_right == False:
			print "Timing isn't right"
			return
		

		if messages:
			all_subscription_messages = Message.objects.filter(pk__in=messages)
		else:
			all_subscription_messages = Message.objects.filter(newsletter=self.newsletter, send_date__lte=now())
		
		message_receipts_to_send = []
		messages_to_send = []

		for message in all_subscription_messages:
			receipt, created = Receipt.objects.get_or_create(message=message, subscription=self)
			if receipt.sent_status != SENT:
				message_receipts_to_send.append(receipt)
				messages_to_send.append(message)

				message.sending = True
				message.sending_date = now()
				message.save()

		print "messages_to_send: "+str(messages_to_send)

		if len(messages_to_send) == 0:
			return


		#Update last
		self.last_sent_date = now()
		self.save()

		(subject_template, text_template, html_template) = \
			self.get_templates('newsletter')

		print "subject_template: "+str(subject_template)
		print "text_template: "+str(text_template)
		print "html_template: "+str(html_template)

		variable_dict = {
			'subscription': self,
			'site': Site.objects.get_current(),
			'receipts':message_receipts_to_send,
			'newsletter': self.newsletter,
			'date': now(),
			'UNSUBSCRIBE_URL': self.get_unsubscribe_url(self.user),
			'STATIC_URL': settings.STATIC_URL,
			'MEDIA_URL': settings.MEDIA_URL
		}

		unescaped_context = Context(variable_dict, autoescape=False)
		subject = subject_template.render(unescaped_context).strip()
		text = text_template.render(unescaped_context)

		print "SEND FROM "+str(self.newsletter.get_sender())+" TO: "+str(self.get_recipient())+" SUBJECT: "+str(subject)
		email_message = EmailMultiAlternatives(
			subject, text,
			from_email=self.newsletter.get_sender(),
			to=[self.get_recipient()]
		)

		if html_template:
			escaped_context = Context(variable_dict)
			rendered_html = html_template.render(escaped_context)

			#print "HTML MESSAGE: "+str(rendered_html)

			"""

			if self.newsletter.track_links:
				soup = BeautifulSoup(rendered_html)
				all_links = soup.find_all("a")            
				for link in all_links:
					if link.has_attr('href'):
						link_tracker, created = LinkTrack.objects.get_or_create(message=self, subscription=receipt.subscription, url=link['href'])
						link['href'] = link_tracker.get_tracker_url()

			rendered_html = soup.prettify()
			"""

			email_message.attach_alternative(
				rendered_html,
				"text/html"
			)

		try:
			logger.debug(
				ugettext(u'Submitting message to: %s.'),
				self
			)			
			
			email_message.send()

			for receipt in message_receipts_to_send:
				receipt.sent_status = SENT
				receipt.save()

				receipt.message.sending = False
				receipt.message.sent_date = now()
				receipt.message.save()

		except Exception, e:
			# TODO: Test coverage for this branch.
			logger.error(
				ugettext(u'Message %(subscription)s failed '
						 u'with error: %(error)s'),
				{'subscription': self,
				 'error': e}
			)

			print "ERRORS: error: %s"%(e)

			for receipt in message_receipts_to_send:
				receipt.sent_status = ERROR_SENDING
				receipt.save()

				receipt.message.sending = False
				receipt.message.save()

	

	@permalink
	def subscribe_activate_url(self):
		return ('newsletter_update_activate', (), {
			'newsletter_slug': self.newsletter.slug,
			'email': self.email,
			'action': 'subscribe',
			'activation_code': self.activation_code
		})

	@permalink
	def unsubscribe_activate_url(self):
		return ('newsletter_update_activate', (), {
			'newsletter_slug': self.newsletter.slug,
			'email': self.email,
			'action': 'unsubscribe',
			'activation_code': self.activation_code
		})

	@permalink
	def update_activate_url(self):
		return ('newsletter_update_activate', (), {
			'newsletter_slug': self.newsletter.slug,
			'email': self.email,
			'action': 'update',
			'activation_code': self.activation_code
		})




class Message(models.Model):
	""" Message """

	_admin_name = models.CharField(max_length=255, blank=True, null=True)
	title = models.CharField(max_length=200, verbose_name=_('title'))
	slug = models.SlugField(verbose_name=_('slug'))

	text = models.TextField(verbose_name=_('text'), blank=True, null=True)

	newsletter = models.ForeignKey(
		'Newsletter', verbose_name=_('newsletter'),
		default=Newsletter.get_default_id
	)

	date_create = models.DateTimeField(
		verbose_name=_('created'), auto_now_add=True, editable=False
	)
	date_modify = models.DateTimeField(
		verbose_name=_('modified'), auto_now=True, editable=False
	)

	send_date = models.DateTimeField(null=True)

	prepared = models.BooleanField(
		default=False, verbose_name=_('prepared'),
		db_index=True, editable=False
	)
	prepared_date = models.DateTimeField(null=True, blank=True)

	sending = models.BooleanField(
		default=False, verbose_name=_('sending'),
		db_index=True, editable=False
	)
	sending_date = models.DateTimeField(null=True, blank=True)


	sent = models.BooleanField(
		default=False, verbose_name=_('sent'),
		db_index=True, editable=False
	)
	sent_date = models.DateTimeField(null=True, blank=True)



	def __unicode__(self):
		try:
			return _(u"%(title)s in %(newsletter)s") % {
				'title': self.title,
				'newsletter': self.newsletter
			}
		except Newsletter.DoesNotExist:
			logger.warn(
				'Database inconsistency, related newsletter not found '
				'for message with id %d', self.id
			)

			return "%s" % self.title

	class Meta:
		verbose_name = _('message')
		verbose_name_plural = _('messages')
		unique_together = ('slug', 'newsletter')

	@classmethod
	def get_default_id(cls):
		try:
			objs = cls.objects.all().order_by('-date_create')
			if not objs.count() == 0:
				return objs[0].id
		except:
			pass

		return None

	@classmethod
	def submit_queue(cls):
		todo = cls.objects.filter(
			prepared=True, sent=False, sending=False,
			send_date__lte=now()
		)

		for message in todo:
			message.send()

	def prepare_to_send(self):

		if self.sent or self.prepared:
			return False

		self.prepared_date = now()
		self.prepared = True
		self.save()

		return True

	def get_templates(self, action):
		"""
		Return a subject, text, HTML tuple with e-mail templates for
		a particular action. Returns a tuple with subject, text and e-mail
		template.
		"""

		assert action in ACTIONS + ('message', ), 'Unknown action: %s' % action

		# Common substitutions for filenames
		tpl_subst = {
			'action': action,
			'newsletter': self.newsletter.slug,
			'message':self.slug
		}

		# Common root path for all the templates
		tpl_root = 'newsletter/message/'

		text_template = select_template([
			tpl_root + '%(newsletter)s/%(message)s/%(action)s.txt' % tpl_subst,
			tpl_root + '%(newsletter)s/%(action)s.txt' % tpl_subst,
			tpl_root + '%(action)s.txt' % tpl_subst,
		])

		if self.newsletter.send_html:
			html_template = select_template([
				tpl_root + '%(newsletter)s/%(message)s/%(action)s.html' % tpl_subst,
				tpl_root + '%(newsletter)s/%(action)s.html' % tpl_subst,
				tpl_root + '%(action)s.html' % tpl_subst,
			])
		else:
			# HTML templates are not required
			html_template = None

		return (text_template, html_template)


	def get_message_email(self, receipt):
		(text_template, html_template) = \
				self.get_templates('message')
		variable_dict = {
			'message': self,
			'receipt': receipt,
			'STATIC_URL': settings.STATIC_URL,
			'MEDIA_URL': settings.MEDIA_URL,
			'site': Site.objects.get_current()
		}
		escaped_context = Context(variable_dict)
		rendered_html = html_template.render(escaped_context)


		return rendered_html

	def get_archive_url(self, receipt):
		'^archive/<newsletter_slug:s>/<slug:s>/<receipt_slug:s>/$',

		return reverse(
			'newsletter_archive_detail_receipt', 
			kwargs={
				'newsletter_slug': self.newsletter.slug,
				'slug': self.slug,
				'receipt_slug':receipt.pk,
			}
		)

	

	def save(self, *args, **kwargs):
		#Update admin name
		self._admin_name = (self.title+" of "+self.newsletter.title).encode('ascii', 'ignore')

		super(Message, self).save(*args, **kwargs)



class LinkTrack(models.Model):

	message = models.ForeignKey('Message', null=True, blank=True)
	subscription = models.ForeignKey('Subscription')
	url = models.CharField(max_length=1000, db_index=True)
 
	create_date = models.DateTimeField(editable=False, default=now)
	
	viewed = models.BooleanField(default=False, db_index=True)
	view_count = models.IntegerField(default=0)
	first_viewed_date = models.DateTimeField(null=True, blank=True)
	last_viewed_date = models.DateTimeField(null=True, blank=True)

	def visit_link(self):
		self.view_count = self.view_count+1
		self.viewed = True
		if not self.first_viewed_date:
			self.first_viewed_date = now()
		self.last_viewed_date = now()
		self.save()

	def get_tracker_path(self):

		return reverse(
			'link_tracker', 
			kwargs={
				'link_tracker_id': self.pk
			}
		)

	def get_tracker_url(self):
		site = Site.objects.get_current()
		return "http://"+site.domain+self.get_tracker_path()

class Receipt(models.Model):

	_admin_name = models.CharField(max_length=255, blank=True, null=True)

	message = models.ForeignKey('Message', null=True,blank=True)
	subscription = models.ForeignKey('Subscription')
 
	create_date = models.DateTimeField(editable=False, default=now)
	sent_status = models.IntegerField(default=0, choices=SENDING_STATUS_CHOICES, db_index=True)

	email_viewed = models.BooleanField(default=False, db_index=True)
	email_view_count = models.IntegerField(default=0)
	email_first_viewed_date = models.DateTimeField(null=True, blank=True)
	email_last_viewed_date = models.DateTimeField(null=True, blank=True)
 
	archive_viewed = models.BooleanField(default=False, db_index=True)
	archive_view_count = models.IntegerField(default=0)
	archive_first_viewed_date = models.DateTimeField(null=True, blank=True)
	archive_last_viewed_date = models.DateTimeField(null=True, blank=True)

	def __unicode__(self):
		return self._admin_name

	class Meta:

		ordering = ('_admin_name',)

	def save(self, *args, **kwargs):
		#Update admin name
		self._admin_name = ("Message "+self.message._admin_name+" for Subscription "+self.subscription._admin_name).encode('ascii', 'ignore')

		super(Receipt, self).save(*args, **kwargs)

	def view_email(self):
		self.email_view_count = self.email_view_count+1
		self.email_viewed = True
		if not self.email_first_viewed_date:
			self.email_first_viewed_date = now()
		self.email_last_viewed_date = now()
		self.save()

	def view_archive(self):
		self.archive_view_count = self.archive_view_count+1
		self.archive_viewed = True
		if not self.archive_first_viewed_date:
			self.archive_first_viewed_date = now()
		self.archive_last_viewed_date = now()
		self.save()

	def get_email_tracker_url(self):
		return reverse('email_view_tracker', kwargs={'receipt_slug': self.pk})

	def get_archive_tracker_url(self):
		return reverse('archive_view_tracker', kwargs={'receipt_slug': self.pk})

	def get_full_email_tracking_url(self):
		site = Site.objects.get_current()
		return "http://"+site.domain+self.get_email_tracker_url()

	def get_full_archive_tracking_url(self):
		site = Site.objects.get_current()
		url = self.get_archive_tracker_url()
		return "http://"+site.domain+self.get_archive_tracker_url()

	
   
	
