# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'IDevice'
        db.create_table('push_notifications_idevice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(related_name='idevices', to=orm['people.Person'])),
            ('development', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('token', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=64)),
            ('app_id', self.gf('django.db.models.fields.CharField')(default='', max_length=64)),
            ('invalidated', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('push_notifications', ['IDevice'])

    def backwards(self, orm):
        # Deleting model 'IDevice'
        db.delete_table('push_notifications_idevice')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'badges.badge': {
            'Meta': {'object_name': 'Badge'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['badges.BadgeCategory']"}),
            'certification': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['certifications.Certification']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'icon_large': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_donation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'precedence': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'badges.badgecategory': {
            'Meta': {'object_name': 'BadgeCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['partners.Partner']", 'null': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'badges.personbadge': {
            'Meta': {'unique_together': "(('person', 'badge'),)", 'object_name': 'PersonBadge'},
            'badge': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['badges.Badge']"}),
            'cached_description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '750'}),
            'cached_icon_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'cached_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'verification_status': ('django.db.models.fields.CharField', [], {'default': "'not_required'", 'max_length': '20'})
        },
        'certifications.certification': {
            'Meta': {'object_name': 'Certification'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['certifications.CertificationCategory']"}),
            'help_text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requires_verify': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'certifications.certificationcategory': {
            'Meta': {'object_name': 'CertificationCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'target': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'certifications.personcertification': {
            'Meta': {'unique_together': "(('person', 'certification'),)", 'object_name': 'PersonCertification'},
            'certification': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['certifications.Certification']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']"}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'partners.partner': {
            'Meta': {'ordering': "('sort_order', 'name')", 'object_name': 'Partner'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'default_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'default_image_set'", 'null': 'True', 'to': "orm['partners.PartnerLogo']"}),
            'donations_enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10', 'db_index': 'True'})
        },
        'partners.partnerlogo': {
            'Meta': {'object_name': 'PartnerLogo'},
            'big_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'big_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'large_uncropped': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'large_uncropped_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'original': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'image_set'", 'to': "orm['partners.Partner']"}),
            'small': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'small_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'small_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'small_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'staff_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '85', 'blank': 'True'}),
            'user_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wide_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'wide_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        'people.person': {
            'Meta': {'object_name': 'Person'},
            'accepted_tos_version': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'account_type': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'badges': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['badges.Badge']", 'through': "orm['badges.PersonBadge']", 'symmetrical': 'False'}),
            'birthdate': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'certifications': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['certifications.Certification']", 'through': "orm['certifications.PersonCertification']", 'symmetrical': 'False'}),
            'default_image': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'default_image_set'", 'null': 'True', 'to': "orm['people.PersonImage']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dog_history': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'friend_referral_discount': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'have_transportation': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'humane_society_parent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'humane_society_trained': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'phone_contact_opt_in': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'placeholder_creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'placeholder_creator'", 'null': 'True', 'to': "orm['auth.User']"}),
            'profile_quality': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ratings_average': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '3', 'decimal_places': '2', 'db_index': 'True'}),
            'ratings_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'referred_by_donor_program': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'referrer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['people.Person']", 'null': 'True', 'blank': 'True'}),
            'requested_dog_info': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'review_status': ('django.db.models.fields.CharField', [], {'default': "'not_reviewed'", 'max_length': '15'}),
            'search_preference': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10', 'blank': 'True'}),
            'search_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'search_score_boost': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sitter': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'sitter_set'", 'null': 'True', 'to': "orm['sitters.Sitter']"}),
            'testimonial_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'time_zone': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'will_administer_meds': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'people.personimage': {
            'Meta': {'object_name': 'PersonImage'},
            'big_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'big_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'large_uncropped': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'large_uncropped_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'medium_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'original': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'image_set'", 'to': "orm['people.Person']"}),
            'small': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'small_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'small_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'small_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'staff_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '85', 'blank': 'True'}),
            'user_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wide_thumb': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '200', 'blank': 'True'}),
            'wide_thumb_url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '200', 'blank': 'True'})
        },
        'push_notifications.idevice': {
            'Meta': {'object_name': 'IDevice'},
            'app_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '64'}),
            'development': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalidated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'idevices'", 'to': "orm['people.Person']"}),
            'token': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '64'})
        },
        'sitters.sitter': {
            'Meta': {'unique_together': "(('person',),)", 'object_name': 'Sitter'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'additional_tasks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'experience': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'featured_description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'featured_label': ('django.db.models.fields.CharField', [], {'max_length': '19', 'blank': 'True'}),
            'featured_original_price': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'friday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'giant_dogs': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'large_dogs': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '6', 'db_index': 'True'}),
            'max_latitude': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '6'}),
            'max_longitude': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '6'}),
            'medium_dogs': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'min_latitude': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '6'}),
            'min_longitude': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '6'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'monday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'neighborhood': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'next_craigslist_repost_reminder': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sitters'", 'to': "orm['people.Person']"}),
            'price': ('django.db.models.fields.IntegerField', [], {'default': '20'}),
            'promoted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'radius': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'ratings_average': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '3', 'decimal_places': '2', 'db_index': 'True'}),
            'ratings_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'review_status': ('django.db.models.fields.CharField', [], {'default': "'not_reviewed'", 'max_length': '15'}),
            'saturday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'search_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'searchable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'searchable_date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'small_dogs': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'sunday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'thursday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'time_with_dog': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'tuesday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user_hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'wednesday': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['push_notifications']