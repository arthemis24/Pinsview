# -*- coding: utf-8 -*-
from assets.models import OperatorProfile
from ikwen.core.utils import get_service_instance

__author__ = 'Roddy Mbogning'

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from ikwen_pinsview.assets.models import *


if getattr(settings, 'IS_IKWEN', False):
    _fieldsets = [
        (_('Company'), {'fields': ('company_name', 'short_description', 'slogan', 'latitude', 'longitude',
                                   'description', 'is_pro_version')}),
        # (_('Business'), {'fields': ('ikwen_share', 'payment_delay', )}),
        # (_('Platform'), {'fields': ('can_manage_delivery_options', 'allow_paypal_direct')}),
        (_('SMS'), {'fields': ('sms_api_script_url', 'sms_api_username', 'sms_api_password', )}),
        (_('Mailing'), {'fields': ('welcome_message', 'signature',)})
    ]
    # _readonly_fields = ('api_signature', )
else:
    service = get_service_instance()
    config = service.config
    _readonly_fields = ( 'is_pro_version',)
    _website_fields = {'fields': ()}
    _website_fields = {'fields': ('currency_code', 'currency_symbol')}

    _fieldsets = [
        (_('Company'), {'fields': ('company_name', 'short_description', 'slogan', 'description',)}),
        # (_('Website'), _website_fields),
        (_('Address & Contact'), {'fields': ('contact_email', 'contact_phone', 'address', 'country', 'city',
                                              'latitude', 'longitude',)}),
        (_('Social'), {'fields': ('facebook_link', 'twitter_link', 'google_plus_link', 'youtube_link', 'instagram_link',
                                  'tumblr_link', 'linkedin_link', )}),
        # (_('SMS'), {'fields': ('sms_sending_method', 'sms_api_script_url', 'sms_api_username', 'sms_api_password', )}),
        (_('Mailing'), {'fields': ('welcome_message', 'signature', )}),
    ]
    if config.is_pro_version:
        _fieldsets.extend([
            (_('External scripts'), {'fields': ('scripts', )}),
        ])


class OperatorProfileAdmin(admin.ModelAdmin):
    list_display = ('service', 'company_name')
    fieldsets = _fieldsets
    # readonly_fields = ('api_signature', )
    list_filter = ('company_name', 'contact_email', )
    save_on_top = True

    def delete_model(self, request, obj):
        self.message_user(request, "You are not allowed to delete Configuration of the platform")


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'zoom')
    fields = ('name', 'description', 'zoom')
    readonly_fields = ()


class DeviceAdmin(admin.ModelAdmin):
    list_display = ('category', 'name', 'phone', 'longitude', 'latitude', 'manager_name', 'description', 'techie')
    fields = ('category', 'city', 'name', 'phone', 'longitude', 'latitude', 'manager_name', 'description')
    readonly_fields = ()


class DeploymentInfoAdmin(admin.ModelAdmin):
    list_display = ('customer','company_name', 'activity', 'purpose', 'description')
    fields = ('company_name','activity', 'purpose', 'description')
    readonly_fields = ()


class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon',)


class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'longitude', 'latitude')


class TechieAdmin(admin.ModelAdmin):
    list_display = ('member', 'city')


class ZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')


class DeviceLogAdmin(admin.ModelAdmin):
    list_display = ('log_event_type', 'device', 'measure', 'techie')


class LogEventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'measure_label', 'is_active')


admin.site.register(DeploymentInfo, DeploymentInfoAdmin)
admin.site.register(Techie, TechieAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(DeviceCategory, DeviceCategoryAdmin)
admin.site.register(Zone, ZoneAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(DeviceLog, DeviceLogAdmin)
admin.site.register(LogEventType, LogEventTypeAdmin)
admin.site.register(OperatorProfile, OperatorProfileAdmin)
