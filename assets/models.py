from collections import defaultdict

from django.core.urlresolvers import reverse
from django.db import models
from datetime import datetime
import datetime

from ikwen.core.models import Model, AbstractConfig
from django.forms import ModelForm, Textarea
from django.utils import translation, timezone
# Create your models here.
from ikwen.accesscontrol.models import Member
from ikwen.core.utils import to_dict


class City(models.Model):
    name = models.CharField(max_length=50)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Cities'


class Zone(models.Model):
    name = models.CharField(max_length=50)
    city = models.ForeignKey(City)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __unicode__(self):
        return self.name


class LogEventType(models.Model):
    name = models.CharField(max_length=240)
    measure_label = models.CharField(max_length=240, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Log types'

    def to_dict(self):
        var = to_dict(self)
        return var


class DeviceCategory(models.Model):
    name = models.CharField(max_length=240, blank=True)
    icon = models.ImageField(blank=True, upload_to="icons")
    description = models.TextField(blank=True)
    zoom = models.IntegerField(default=20)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Device categories'

    def to_dict(self):
        var = to_dict(self)
        return var


class Techie(Model):
    member = models.ForeignKey(Member)
    city = models.ForeignKey(City, null=True, blank=True)

    def __unicode__(self):
        if self.member.first_name and self.member.last_name:
            return "%s %s" % (self.member.first_name, self.member.last_name)
        elif self.member.first_name and not self.member.last_name:
            return "%s" % self.member.first_name
        elif not self.member.first_name and self.member.last_name:
            return "%s" % self.member.last_name
        elif not self.member.first_name and not self.member.last_name:
            return "%s" % self.member.username


class Device(Model):
    PENDING = "Pending"
    VALIDATE = "Validate"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (VALIDATE, "Validate"),
    )
    category = models.ForeignKey(DeviceCategory)
    name = models.CharField(max_length=240)
    longitude = models.CharField(max_length=240, default="0.0")
    latitude = models.CharField(max_length=240, default="0.0")
    manager_name = models.CharField(max_length=240, blank=True)
    phone = models.CharField(max_length=240, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING, editable=False)
    zone = models.ForeignKey(Zone, blank=True, null=True, editable=False)
    techie = models.ForeignKey(Techie, null=True, blank=True)
    photo = models.ImageField(Techie, null=True, blank=True)
    city = models.ForeignKey(City, null=True, blank=True)
    isActive = models.BooleanField(default=True, editable=False)

    def __unicode__(self):
        return self.name

    def get_techie_name(self):
        if self.techie.member.first_name and self.techie.member.last_name:
            return "%s %s" % (self.techie.member.first_name, self.techie.member.last_name)
        elif self.techie.member.first_name and not self.techie.member.last_name:
            return "%s" % self.techie.member.first_name
        elif not self.techie.member.first_name and self.techie.member.last_name:
            return "%s" % self.techie.member.last_name
        elif not self.techie.member.first_name and not self.techie.member.last_name:
            return "%s" % self.techie.member.username

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name),
                       args=[self.id])

    def to_dict(self):
        var = to_dict(self)
        var['category'] = self.category.to_dict()
        var['display_techie_name'] = self.get_techie_name()
        del (var['created_on'])
        del (var['updated_on'])
        return var

    def get_description(self):
        return self.description.replace("\n", ' ').replace("\r", '')


class DeviceLog(Model):
    log_event_type = models.ForeignKey(LogEventType)
    device = models.ForeignKey(Device)
    measure = models.IntegerField(default=20)
    details = models.TextField(blank=True)
    techie = models.ForeignKey(Techie, null=True, blank=True)

    def __unicode__(self):
        return self.log_event_type.name

    def to_dict(self):
        var = to_dict(self)
        return var


class AddDeviceForm(ModelForm):
    class Meta:
        model = Device
        widgets = {
            'description': Textarea(attrs={'cols': 80, 'rows': 50}),
        }
        fields = ['name', 'category', 'longitude', 'latitude']


class OperatorProfile(AbstractConfig):
    BANKING = "Banking"
    SHOPPING = "Shopping"
    ADS = "Ads"
    STATUS_CHOICES = (
        (BANKING, "Banking"),
        (SHOPPING, "Shopping"),
        (ADS, "Ads"),
    )
    business_type = models.IntegerField(max_length=15, choices=STATUS_CHOICES, default=SHOPPING)

    class Meta:
        verbose_name = "Operator"
        verbose_name_plural = "Operators"

    def to_dict(self):
        var = to_dict(self)
        del (var['balance'])
        del (var['company_name_slug'])
        del (var['address'])
        del (var['short_description'])
        del (var['description'])
        del (var['slogan'])
        del (var['cash_out_min'])
        del (var['logo'])
        del (var['cover_image'])
        del (var['signature'])
        del (var['welcome_message'])
        del (var['facebook_link'])
        del (var['twitter_link'])
        del (var['google_plus_link'])
        del (var['youtube_link'])
        del (var['instagram_link'])
        del (var['tumblr_link'])
        del (var['linkedin_link'])
        del (var['scripts'])
        del (var['allow_paypal_direct'])
        del (var['sms_sending_method'])
        del (var['sms_api_script_url'])
        del (var['sms_api_username'])
        del (var['sms_api_password'])
        del (var['is_pro_version'])
        return var


class DeploymentInfo(Model):
    MARKETING = "Marketing"
    CASH_COLLECT = "Cash collect"
    AGENT_TRACKING = "Agent tracking"
    PURPOSE_CHOICES = (
        (MARKETING, "Banking"),
        (CASH_COLLECT, "Cash collect"),
        (AGENT_TRACKING, "Agent tracking"),
    )
    PENDING = "Pending"
    PROCCEDED = "Proceded"
    COMPLETE = "Complete"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (PROCCEDED, "Cash collect"),
        (COMPLETE, "Complete"),
    )
    customer = models.ForeignKey(Member)
    company_name = models.CharField(max_length=240)
    activity = models.CharField(max_length=240)
    purpose = models.CharField(max_length=100, choices=PURPOSE_CHOICES, default=MARKETING)
    status = models.CharField(max_length=100, choices=PURPOSE_CHOICES, default=PENDING)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return self.customer.get_short_name()

    def to_dict(self):
        var = to_dict(self)
        return var
