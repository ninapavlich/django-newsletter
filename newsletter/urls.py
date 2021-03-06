from django.conf.urls import patterns

from  surlex.dj import surl

from .views import (
    NewsletterListView, NewsletterDetailView,
    MessageArchiveIndexView, MessageArchiveDetailView,
    SubscribeRequestView, UnsubscribeRequestView, UpdateRequestView,
    ActionTemplateView, UpdateSubscriptionViev,
)

urlpatterns = patterns(
    '',

    surl(r'^receipt/email/<receipt_slug:s>.png', 'newsletter.views.receipt_email',name='email_view_tracker' ),
    surl(r'^receipt/archive/<receipt_slug:s>.png', 'newsletter.views.receipt_archive',name='archive_view_tracker' ),
    surl(r'^linktrack/<link_tracker_id:s>', 'newsletter.views.link_tracker', name='link_tracker' ),
    
    # Archive views
    surl(
        '^archive/<newsletter_slug:s>/<slug:s>/<receipt_slug:s>/$',
        MessageArchiveDetailView.as_view(), name='newsletter_archive_detail_receipt'
    ),
    surl(
        '^archive/<newsletter_slug:s>/<slug:s>/$',
        MessageArchiveDetailView.as_view(), name='newsletter_archive_detail'
    ),
    surl(
        '^archive/<newsletter_slug:s>/$',
        MessageArchiveIndexView.as_view(), name='newsletter_archive'
    ),

    # Newsletter list and detail view
    surl('^$', NewsletterListView.as_view(), name='newsletter_list'),
    surl(
        '^<newsletter_slug:s>/$',
        NewsletterDetailView.as_view(), name='newsletter_detail'
    ),



    # Action request views
    surl(
        '^<newsletter_slug:s>/subscribe/$',
        SubscribeRequestView.as_view(),
        name='newsletter_subscribe_request'
    ),
    surl(
        '^<newsletter_slug:s>/subscribe/confirm/$',
        SubscribeRequestView.as_view(confirm=True),
        name='newsletter_subscribe_confirm'
    ),
    surl(
        '^<newsletter_slug:s>/update/$',
        UpdateRequestView.as_view(),
        name='newsletter_update_request'
    ),
    surl(
        '^<newsletter_slug:s>/unsubscribe/<user_pk:s>/$',
        UnsubscribeRequestView.as_view(),
        name='newsletter_unsubscribe_request'
    ),
    surl(
        '^<newsletter_slug:s>/unsubscribe/confirm/$',
        UnsubscribeRequestView.as_view(confirm=True),
        name='newsletter_unsubscribe_confirm'
    ),

    # Activation email sent view
    surl(
        '^<newsletter_slug:s>/<action=subscribe|update|unsubscribe>/'
        'email-sent/$',
        ActionTemplateView.as_view(
            template_name='newsletter/subscription_%(action)s_email_sent.html'
        ),
        name='newsletter_activation_email_sent'),

    # Action confirmation views
    surl(
        '^<newsletter_slug:s>/subscription/<email=[-_a-zA-Z0-9@\.\+~]+>/'
        '<action=subscribe|update|unsubscribe>/activate/<activation_code:s>/$',
        UpdateSubscriptionViev.as_view(), name='newsletter_update_activate'
    ),
    surl(
        '^<newsletter_slug:s>/subscription/<email=[-_a-zA-Z0-9@\.\+~]+>/'
        '<action=subscribe|update|unsubscribe>/activate/$',
        UpdateSubscriptionViev.as_view(), name='newsletter_update'
    ),

    # Action activation completed view
    surl(
        '^<newsletter_slug:s>/<action=subscribe|update|unsubscribe>/'
        'activation-completed/$',
        ActionTemplateView.as_view(
            template_name='newsletter/subscription_%(action)s_activated.html'
        ),
        name='newsletter_action_activated'),

    
    
)
