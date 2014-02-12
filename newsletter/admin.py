import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib import admin, messages
from django.contrib.sites.models import Site
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext, Context
from django.utils.formats import date_format
from django.utils.translation import ugettext, ungettext, ugettext_lazy as _
from django.utils.timezone import now
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.shortcuts import render_to_response

from sorl.thumbnail.admin import AdminImageMixin

from .admin_forms import *
from .admin_utils import *
from .models import *
from .settings import newsletter_settings

# Contsruct URL's for icons
ICON_URLS = {
    'yes': '%sadmin/img/icon-yes.gif' % settings.STATIC_URL,
    'wait': '%snewsletter/admin/img/waiting.gif' % settings.STATIC_URL,
    'submit': '%snewsletter/admin/img/submitting.gif' % settings.STATIC_URL,
    'no': '%sadmin/img/icon-no.gif' % settings.STATIC_URL
}


class NewsletterAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'admin_subscriptions', 'admin_messages'
    )
    prepopulated_fields = {'slug': ('title',)}

    """ List extensions """
    def admin_messages(self, obj):
        return '<a href="../message/?newsletter__id__exact=%s">%s</a>' % (
            obj.id, ugettext('Messages')
        )
    admin_messages.allow_tags = True
    admin_messages.short_description = ''

    def admin_subscriptions(self, obj):
        return \
            '<a href="../subscription/?newsletter__id__exact=%s">%s</a>' % \
            (obj.id, ugettext('Subscriptions'))
    admin_subscriptions.allow_tags = True
    admin_subscriptions.short_description = ''


class ArticleInline(AdminImageMixin, admin.StackedInline):
    model = Article
    extra = 2
    fieldsets = (
        (None, {
            'fields': ('title', 'sortorder', 'text')
        }),
        (_('Optional'), {
            'fields': ('url', 'image'),
            'classes': ('collapse',)
        }),
    )
    
    if newsletter_settings.RICHTEXT_WIDGET:
        formfield_overrides = {
            models.TextField: {'widget': newsletter_settings.RICHTEXT_WIDGET},
        }


class MessageAdmin(admin.ModelAdmin, ExtendibleModelAdminMixin):
    save_as = True
    list_display = (
        '_admin_name','admin_preview', 'date_create',
        'date_modify'
    )
    list_filter = ('newsletter', )
    date_hierarchy = 'date_create'
    prepopulated_fields = {'slug': ('title',)}

    inlines = [ArticleInline, ]

    """ List extensions """
    def admin_title(self, obj):
        return '<a href="%d/">%s</a>' % (obj.id, obj.title)
    admin_title.short_description = ugettext('message')
    admin_title.allow_tags = True

    def admin_preview(self, obj):
        return '<a href="%d/preview/">%s</a>' % (obj.id, ugettext('Preview'))
    admin_preview.short_description = ''
    admin_preview.allow_tags = True

    def admin_newsletter(self, obj):
        return '<a href="../newsletter/%s/">%s</a>' % (
            obj.newsletter.id, obj.newsletter
        )
    admin_newsletter.short_description = ugettext('newsletter')
    admin_newsletter.allow_tags = True

    """ Views """
    def preview(self, request, object_id):
        return render_to_response(
            "admin/newsletter/message/preview.html",
            {'message': self._getobj(request, object_id)},
            RequestContext(request, {}),
        )

    @xframe_options_sameorigin
    def preview_html(self, request, object_id):
        message = self._getobj(request, object_id)

        (subject_template, text_template, html_template) = \
            message.get_templates('message')

        if not html_template:
            raise Http404(_(
                'No HTML template associated with the newsletter this '
                'message belongs to.'
            ))

        c = Context({'message': message,
                     'site': Site.objects.get_current(),
                     'newsletter': message.newsletter,
                     'date': now(),
                     'STATIC_URL': settings.STATIC_URL,
                     'MEDIA_URL': settings.MEDIA_URL})

        return HttpResponse(html_template.render(c))

    @xframe_options_sameorigin
    def preview_text(self, request, object_id):
        message = self._getobj(request, object_id)

        (subject_template, text_template, html_template) = \
            message.get_templates('message')

        c = Context({
            'message': message,
            'site': Site.objects.get_current(),
            'newsletter': message.newsletter,
            'date': now(),
            'STATIC_URL': settings.STATIC_URL,
            'MEDIA_URL': settings.MEDIA_URL
        }, autoescape=False)

        return HttpResponse(text_template.render(c), mimetype='text/plain')

    def subscribers_json(self, request, object_id):
        message = self._getobj(request, object_id)

        json = serializers.serialize(
            "json", message.newsletter.get_subscriptions(), fields=()
        )
        return HttpResponse(json, mimetype='application/json')

    def admin_status(self, obj):
        if obj.prepared:
            if obj.sent:
                return u'<img src="%s" width="10" height="10" alt="%s"/>' % (
                    ICON_URLS['yes'], self.admin_status_text(obj))
            else:
                if obj.publish_date > now():
                    return \
                        u'<img src="%s" width="10" height="10" alt="%s"/>' % (
                            ICON_URLS['wait'], self.admin_status_text(obj))
                else:
                    return \
                        u'<img src="%s" width="12" height="12" alt="%s"/>' % (
                            ICON_URLS['wait'], self.admin_status_text(obj))
        else:
            return u'<img src="%s" width="10" height="10" alt="%s"/>' % (
                ICON_URLS['no'], self.admin_status_text(obj))

    admin_status.short_description = ''
    admin_status.allow_tags = True

    def admin_status_text(self, obj):
        if obj.prepared:
            if obj.sent:
                return ugettext("Sent.")
            else:
                if obj.publish_date > now():
                    return ugettext("Delayed submission.")
                else:
                    return ugettext("Submitting.")
        else:
            return ugettext("Not sent.")
    admin_status_text.short_description = ugettext('Status')

    """ Views """
    def prepare_to_send(self, request, object_id):
        message = self._getobj(request, object_id)

        prepared = message.prepare_to_send()

        if prepared == True:
            messages.info(request, ugettext("Your message is ready to send.")) 
            return HttpResponseRedirect('../../')
            
        else:
            messages.info(request, ugettext("Message already prepared."))
            return HttpResponseRedirect('../')

    def submit(self, request, object_id):
        message = self._getobj(request, object_id)

        message.send()

        messages.info(request, ugettext("Message sent."))
        return HttpResponseRedirect('../')



    """ URLs """
    def get_urls(self):
        urls = super(MessageAdmin, self).get_urls()

        
        my_urls = patterns(
            '',
            url(
                r'^(.+)/prepare/$',
                self._wrap(self.prepare_to_send),
                name=self._view_name('prepare_message')
            ), url(
                r'^(.+)/submit/$',
                self._wrap(self.submit),
                name=self._view_name('submit_message')
            ),
            url(r'^(.+)/preview/$',
                self._wrap(self.preview),
                name=self._view_name('preview')),
            url(r'^(.+)/preview/html/$',
                self._wrap(self.preview_html),
                name=self._view_name('preview_html')),
            url(r'^(.+)/preview/text/$',
                self._wrap(self.preview_text),
                name=self._view_name('preview_text')),
            url(r'^(.+)/subscribers/json/$',
                self._wrap(self.subscribers_json),
                name=self._view_name('subscribers_json')),
        )

        return my_urls + urls


class SubscriptionAdmin(admin.ModelAdmin, ExtendibleModelAdminMixin):
    form = SubscriptionAdminForm
    list_display = (
        '_admin_name', 'admin_subscribe_date',
        'admin_unsubscribe_date', 'admin_status_text', 'admin_status', 'frequency', 'last_sent_date'
    )
    list_display_links = ('_admin_name',)
    list_filter = (
        'newsletter', 'subscribed', 'unsubscribed', 'subscribe_date', 'frequency'
    )
    search_fields = (
        '_admin_name',
    )
    readonly_fields = (
        'ip', 'subscribe_date', 'unsubscribe_date', 'activation_code'
    )
    date_hierarchy = 'subscribe_date'
    actions = ['make_subscribed', 'make_unsubscribed', 're_save']

    """ List extensions """
    def admin_newsletter(self, obj):
        return '<a href="../newsletter/%s/">%s</a>' % (
            obj.newsletter.id, obj.newsletter
        )
    admin_newsletter.short_description = ugettext('newsletter')
    admin_newsletter.allow_tags = True

    def admin_status(self, obj):
        if obj.unsubscribed:
            return u'<img src="%s" width="10" height="10" alt="%s"/>' % (
                ICON_URLS['no'], self.admin_status_text(obj))

        if obj.subscribed:
            return u'<img src="%s" width="10" height="10" alt="%s"/>' % (
                ICON_URLS['yes'], self.admin_status_text(obj))
        else:
            return u'<img src="%s" width="10" height="10" alt="%s"/>' % (
                ICON_URLS['wait'], self.admin_status_text(obj))

    admin_status.short_description = ''
    admin_status.allow_tags = True

    def admin_status_text(self, obj):
        if obj.subscribed:
            return ugettext("Subscribed")
        elif obj.unsubscribed:
            return ugettext("Unsubscribed")
        else:
            return ugettext("Unactivated")
    admin_status_text.short_description = ugettext('Status')

    def admin_subscribe_date(self, obj):
        if obj.subscribe_date:
            return date_format(obj.subscribe_date)
        else:
            return ''
    admin_subscribe_date.short_description = _("subscribe date")

    def admin_unsubscribe_date(self, obj):
        if obj.unsubscribe_date:
            return date_format(obj.unsubscribe_date)
        else:
            return ''
    admin_unsubscribe_date.short_description = _("unsubscribe date")

    """ Actions """
    def make_subscribed(self, request, queryset):
        rows_updated = queryset.update(subscribed=True)
        self.message_user(
            request,
            ungettext(
                "%s user has been successfully subscribed.",
                "%s users have been successfully subscribed.",
                rows_updated
            ) % rows_updated
        )
    make_subscribed.short_description = _("Subscribe selected users")

    def make_unsubscribed(self, request, queryset):
        rows_updated = queryset.update(subscribed=False)
        self.message_user(
            request,
            ungettext(
                "%s user has been successfully unsubscribed.",
                "%s users have been successfully unsubscribed.",
                rows_updated
            ) % rows_updated
        )
    make_unsubscribed.short_description = _("Unsubscribe selected users")

    def re_save(self, request, queryset):
        for item in queryset:
            item.save()

    """ Views """
    def subscribers_import(self, request):
        if request.POST:
            form = ImportForm(request.POST, request.FILES)
            if form.is_valid():
                request.session['addresses'] = form.get_addresses()
                return HttpResponseRedirect('confirm/')
        else:
            form = ImportForm()

        return render_to_response(
            "admin/newsletter/subscription/importform.html",
            {'form': form},
            RequestContext(request, {}),
        )

    def subscribers_import_confirm(self, request):
        # If no addresses are in the session, start all over.
        if not 'addresses' in request.session:
            return HttpResponseRedirect('../')

        addresses = request.session['addresses']
        logger.debug('Confirming addresses: %s', addresses)
        if request.POST:
            form = ConfirmForm(request.POST)
            if form.is_valid():
                try:
                    for address in addresses.values():
                        address.save()
                finally:
                    del request.session['addresses']

                messages.success(
                    request,
                    _('%s subscriptions have been successfully added.') %
                    len(addresses)
                )

                return HttpResponseRedirect('../../')
        else:
            form = ConfirmForm()

        return render_to_response(
            "admin/newsletter/subscription/confirmimportform.html",
            {'form': form, 'subscribers': addresses},
            RequestContext(request, {}),
        )

    """ URLs """
    def get_urls(self):
        urls = super(SubscriptionAdmin, self).get_urls()

        my_urls = patterns(
            '',
            url(r'^import/$',
                self._wrap(self.subscribers_import),
                name=self._view_name('import')),
            url(r'^import/confirm/$',
                self._wrap(self.subscribers_import_confirm),
                name=self._view_name('import_confirm')),

            # Translated JS strings - these should be app-wide but are
            # only used in this part of the admin. For now, leave them here.
            url(r'^jsi18n/$',
                'django.views.i18n.javascript_catalog',
                {'packages': ('newsletter',)},
                name='newsletter_js18n')
        )

        return my_urls + urls

class ReceiptAdmin(admin.ModelAdmin, ExtendibleModelAdminMixin):
    list_display = (
        '_admin_name', 'create_date', 'sent_status',
        'email_viewed', 'email_view_count','email_first_viewed_date', 'email_last_viewed_date'
    )
    list_display_links = ('_admin_name', )
    list_filter = (
        'message', 'subscription', 'sent_status', 'email_viewed', 'archive_viewed'
    )
    search_fields = (
        '_admin_name',
    )
    readonly_fields = (
        'create_date', 'email_viewed', 'email_view_count','archive_viewed', 'archive_view_count', 'sent_status'
    )

    actions = ['re_save', ]

    def re_save(self, request, queryset):
        for item in queryset:
            item.save()


class LinkTrackAdmin(admin.ModelAdmin, ExtendibleModelAdminMixin):
    list_display = (
        'message', 'subscription', 'url', 'create_date',
        'viewed', 'view_count','first_viewed_date', 'last_viewed_date'
    )
    list_display_links = ('message', 'subscription')
    list_filter = (
        'message', 'subscription', 'viewed'
    )
    search_fields = (
        'message',
    )
    readonly_fields = (
        'create_date', 'viewed', 'view_count'
    )

    
admin.site.register(Receipt, ReceiptAdmin)
admin.site.register(LinkTrack, LinkTrackAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
