# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'SubscriptionGroup'
        db.delete_table(u'newsletter_subscriptiongroup')

        # Removing M2M table for field subscriptions on 'SubscriptionGroup'
        db.delete_table(db.shorten_name(u'newsletter_subscriptiongroup_subscriptions'))

        # Deleting model 'Submission'
        db.delete_table(u'newsletter_submission')

        # Removing M2M table for field subscription_groups on 'Submission'
        db.delete_table(db.shorten_name(u'newsletter_submission_subscription_groups'))

        # Removing M2M table for field subscriptions on 'Submission'
        db.delete_table(db.shorten_name(u'newsletter_submission_subscriptions'))

        # Deleting field 'Receipt.submission'
        db.delete_column(u'newsletter_receipt', 'submission_id')


    def backwards(self, orm):
        # Adding model 'SubscriptionGroup'
        db.create_table(u'newsletter_subscriptiongroup', (
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal(u'newsletter', ['SubscriptionGroup'])

        # Adding M2M table for field subscriptions on 'SubscriptionGroup'
        m2m_table_name = db.shorten_name(u'newsletter_subscriptiongroup_subscriptions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('subscriptiongroup', models.ForeignKey(orm[u'newsletter.subscriptiongroup'], null=False)),
            ('subscription', models.ForeignKey(orm[u'newsletter.subscription'], null=False))
        ))
        db.create_unique(m2m_table_name, ['subscriptiongroup_id', 'subscription_id'])

        # Adding model 'Submission'
        db.create_table(u'newsletter_submission', (
            ('prepared', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['newsletter.Message'])),
            ('newsletter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['newsletter.Newsletter'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sending', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('publish', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('publish_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 2, 9, 0, 0), null=True, blank=True, db_index=True)),
            ('sent', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal(u'newsletter', ['Submission'])

        # Adding M2M table for field subscription_groups on 'Submission'
        m2m_table_name = db.shorten_name(u'newsletter_submission_subscription_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('submission', models.ForeignKey(orm[u'newsletter.submission'], null=False)),
            ('subscriptiongroup', models.ForeignKey(orm[u'newsletter.subscriptiongroup'], null=False))
        ))
        db.create_unique(m2m_table_name, ['submission_id', 'subscriptiongroup_id'])

        # Adding M2M table for field subscriptions on 'Submission'
        m2m_table_name = db.shorten_name(u'newsletter_submission_subscriptions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('submission', models.ForeignKey(orm[u'newsletter.submission'], null=False)),
            ('subscription', models.ForeignKey(orm[u'newsletter.subscription'], null=False))
        ))
        db.create_unique(m2m_table_name, ['submission_id', 'subscription_id'])

        # Adding field 'Receipt.submission'
        db.add_column(u'newsletter_receipt', 'submission',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['newsletter.Submission']),
                      keep_default=False)


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'newsletter.article': {
            'Meta': {'ordering': "('sortorder',)", 'object_name': 'Article'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'articles'", 'to': u"orm['newsletter.Message']"}),
            'sortorder': ('django.db.models.fields.PositiveIntegerField', [], {'default': '20', 'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'newsletter.linktrack': {
            'Meta': {'object_name': 'LinkTrack'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'first_viewed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_viewed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['newsletter.Message']", 'null': 'True', 'blank': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['newsletter.Subscription']"}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'db_index': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'viewed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        },
        u'newsletter.message': {
            'Meta': {'unique_together': "(('slug', 'newsletter'),)", 'object_name': 'Message'},
            'date_create': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modify': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['newsletter.Newsletter']"}),
            'prepared': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'prepared_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'send_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'sending': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sending_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'sent_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'newsletter.newsletter': {
            'Meta': {'object_name': 'Newsletter'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'send_html': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'site': ('django.db.models.fields.related.ManyToManyField', [], {'default': '[1]', 'to': u"orm['sites.Site']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'track_links': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'})
        },
        u'newsletter.receipt': {
            'Meta': {'object_name': 'Receipt'},
            'archive_first_viewed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'archive_last_viewed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'archive_view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'archive_viewed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email_first_viewed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'email_last_viewed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'email_view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'email_viewed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['newsletter.Message']", 'null': 'True', 'blank': 'True'}),
            'sent_status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'subscription': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['newsletter.Subscription']"})
        },
        u'newsletter.subscription': {
            'Meta': {'ordering': "('user__last_name', 'user__first_name', 'name_field')", 'unique_together': "(('user', 'email_field', 'newsletter'),)", 'object_name': 'Subscription'},
            'activation_code': ('django.db.models.fields.CharField', [], {'default': "'f02a54a5b7bc154325e04c3cd926c11862a1a176'", 'max_length': '40'}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email_field': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'db_column': "'email'", 'blank': 'True'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'last_sent_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name_field': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'db_column': "'name'", 'blank': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['newsletter.Newsletter']"}),
            'subscribe_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subscribed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'unsubscribe_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'unsubscribed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['newsletter']