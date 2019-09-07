# Create your views here.
import json
import math
import time
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.auth.decorators import login_required, permission_required
# from ajaxuploader.backends.local import LocalUploadBackend
# from ajaxuploader.views.base import AjaxFileUploader
# import requests
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import modelform_factory
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.http import urlquote
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from ikwen.partnership.models import ApplicationRetailConfig

from ikwen.billing.models import CloudBillingPlan

from ikwen.accesscontrol.backends import UMBRELLA

from ikwen.core.models import Service, Application
from ikwen_pinsview.assets.admin import DeviceAdmin, DeploymentInfoAdmin
from ikwen_pinsview.assets.models import Device, DeviceCategory, City, Techie, LogEventType, DeviceLog, DeploymentInfo

from ikwen.accesscontrol.models import Member
from ikwen.core.utils import get_model_admin_instance, get_service_instance
from ikwen.theming.models import Theme

_BOT = 'Bot'


def is_registered_member(user):
    return user.is_authenticated()


class BaseView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(BaseView, self).get_context_data(**kwargs)
        context['categories'] = DeviceCategory.objects.all()
        return context


FIBER_BLOCK_SIZE = 50
DEVICE_BLOCK_SIZE = 50


class Prospect(TemplateView):
    template_name = 'assets/cr.html'

    def get_context_data(self, **kwargs):
        context = super(Prospect, self).get_context_data(**kwargs)
        category = None
        prospect_admin = get_model_admin_instance(Device, DeviceAdmin)
        ModelForm = modelform_factory(Device, fields=('category', 'city', 'name', 'phone', 'longitude', 'latitude', 'manager_name', 'description'))
        form = ModelForm(instance=category)
        prospect_form = helpers.AdminForm(form, list(prospect_admin.get_fieldsets(self.request)),
                                          prospect_admin.get_prepopulated_fields(self.request),
                                          prospect_admin.get_readonly_fields(self.request, obj=category))
        # context['category'] = category
        context['model_admin_form'] = prospect_form
        return context

    def post(self, request, *args, **kwargs):
        device_id = self.request.POST.get('device_id')
        category_id = self.request.POST.get('category')
        device = Device()
        if device_id:
            device = get_object_or_404(Device, pk=device_id)
        device_admin = get_model_admin_instance(Device, DeviceAdmin)
        ModelForm = device_admin.get_form(self.request)
        form = ModelForm(request.POST, instance=device)
        if form.is_valid():
            device.name = form.cleaned_data['name']
            device.description = form.cleaned_data['description']
            device.phone = form.cleaned_data['phone']
            device.latitude = form.cleaned_data['latitude']
            device.longitude = form.cleaned_data['longitude']
            device.manager_name = form.cleaned_data['manager_name']
            device.category = DeviceCategory.objects.get(pk=category_id)

            device.save()
            if device_id:
                next_url = reverse('locator:prospect', args=(device_id,))
                messages.success(request, _("Prospect %s successfully updated." % device.name))
            else:
                next_url = self.request.REQUEST.get('next')
                if not next_url:
                    next_url = reverse('locator:prospect')
                messages.success(request, _("Prospect %s successfully created." % device.name))
            return HttpResponseRedirect(next_url)
        else:
            context = self.get_context_data(**kwargs)
            context['errors'] = form.errors
            return render(request, self.template_name, context)


class Deploy(TemplateView):
    template_name = 'assets/deployment_request.html'

    def get_context_data(self, **kwargs):
        context = super(Deploy, self).get_context_data(**kwargs)
        deployment = None
        deployment_admin = get_model_admin_instance(DeploymentInfo, DeploymentInfoAdmin)
        ModelForm = modelform_factory(DeploymentInfo, fields=('company_name', 'activity', 'purpose', 'description'))
        form = ModelForm(instance=deployment)
        deployment_form = helpers.AdminForm(form, list(deployment_admin.get_fieldsets(self.request)),
                                          deployment_admin.get_prepopulated_fields(self.request))
        context['model_admin_form'] = deployment_form
        return context

    def post(self, request, *args, **kwargs):
        customer = request.user
        deploymentInfo = DeploymentInfo()
        deployment_admin = get_model_admin_instance(DeploymentInfo, DeploymentInfoAdmin)
        ModelForm = deployment_admin.get_form(self.request)
        form = ModelForm(request.POST, instance=deploymentInfo)
        if form.is_valid():
            deploymentInfo.company_name = form.cleaned_data['company_name']
            deploymentInfo.activity = form.cleaned_data['activity']
            deploymentInfo.purpose = form.cleaned_data['purpose']
            deploymentInfo.description = form.cleaned_data['description']
            deploymentInfo.customer = customer

            deploymentInfo.save()

            #  mail for user
            #  mail for ikwen/index.php?page=1
            next_url = reverse('locator:prospect')
            messages.success(request, _("Deployment for %s successfully created." % deploymentInfo.company_name))
            return HttpResponseRedirect(next_url)
        else:
            context = self.get_context_data(**kwargs)
            context['errors'] = form.errors
            return render(request, self.template_name, context)


class Network(BaseView):
    template_name = 'assets/pinsview.html'

    def get_context_data(self, **kwargs):

        context = super(Network, self).get_context_data(**kwargs)
        all_device_count = Device.objects.all().count()

        category = None
        prospect_admin = get_model_admin_instance(Device, DeviceAdmin)
        ModelForm = modelform_factory(Device, fields=('category', 'city', 'name', 'phone', 'longitude', 'latitude', 'manager_name', 'description'))
        form = ModelForm(instance=category)
        prospect_form = helpers.AdminForm(form, list(prospect_admin.get_fieldsets(self.request)),
                                          prospect_admin.get_prepopulated_fields(self.request),
                                          prospect_admin.get_readonly_fields(self.request, obj=category))

        context['model_admin_form'] = prospect_form

        if all_device_count > 0:
            context['last_device_id'] = (Device.objects.all().order_by('-id')[0]).id

        context['device_categories'] = DeviceCategory.objects.all().order_by('name')
        context['cities'] = City.objects.all()
        context['media_root'] = getattr(settings, 'MEDIA_URL')
        context['member'] = self.request.user
        device_queryset = Device.objects.all()

        context['devices'] = device_queryset[0:DEVICE_BLOCK_SIZE]
        count_devices = device_queryset.count()
        device_blocks = int(math.ceil(float(count_devices) / DEVICE_BLOCK_SIZE))
        context['device_blocks'] = device_blocks
        context['event_types'] = LogEventType.objects.all()
        return context


@login_required
def get_only_equipments(request, *args, **kwargs):
    equipments = Device.objects.filter(isActive=True)
    response = [equipment.to_dict() for equipment in equipments]
    return HttpResponse(json.dumps({'equipments': response}), 'content-type: text/json', **kwargs)


@login_required
def get_equipments_and_fibers(request, *args, **kwargs):
    devices = Device.objects.filter(isActive=True)
    equipments = [device.to_dict() for device in devices]
    return HttpResponse(json.dumps({'equipments': equipments}), 'content-type: text/json', **kwargs)


@login_required
@permission_required("device.add_device")
def save_device(request, *args, **kwargs):
    description = request.GET.get('description')
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    category_id = request.GET.get('category')
    techie = request.user
    description = description.replace('\n', ' ')
    category = DeviceCategory.objects.get(pk=category_id)
    device_count = Device.objects.all().count()
    name = category.name + "_" + str(device_count+15000)
    device = Device(name=name, category=category,  longitude=longitude, latitude=latitude, description=description,
                    techie=techie)
    device.save()
    return HttpResponse(
        json.dumps({'device': device.to_dict()}),
        content_type='application/json'
    )


@login_required
@permission_required("device.change_device")
def save_device_position(request, *args, **kwargs):
    name = request.POST.get('name', '')
    description = request.POST.get('description')
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    category_id = request.POST.get('category')
    techie = request.user
    member = Techie.objects.get(techie=techie)
    description = description.replace('\n', ' ')
    category = DeviceCategory.objects.get(pk=category_id)
    device_position = Device(category=category, name=name, longitude=longitude, latitude=latitude,
                             description=description, techie=member, status=Device.VALIDATE)
    device_position.save()
    if not name:
        device_count = Device.objects.all().count()
        name = category.name + "_" + str(device_count)
        device_position.name = name
        device_position.save()
    try:
        device_position.photo = request.FILES['photo']
    except:
        pass
    device_position.save()
    return HttpResponseRedirect(reverse('home')+ "?devicePlotted=yes")


def construct_filter_params_list(params_string):
    param_list = params_string.split(',')
    param_list.pop()
    return param_list


@login_required
def filter_network_data(request, *args, **kwargs):
    techie_id = request.GET.get('techieId')

    device_category_ids_params = construct_filter_params_list(request.GET.get('deviceCategory'))
    device_status_params = construct_filter_params_list(request.GET.get('deviceStatus'))

    equipments = Device.objects
    if techie_id:
        techie = Techie.objects.get(id=techie_id)
        equipments = equipments.filter(techie=techie)

    if len(device_category_ids_params) > 0:
        category_list = []
        for category_id in device_category_ids_params:
            category = DeviceCategory.objects.get(id=category_id)
            category_list.append(category)
        equipments = equipments.filter(category__in=category_list)
    else:
        equipments = equipments.none()
    if len(device_status_params) > 0:
        equipments = equipments.filter(status__in=device_status_params)
    # else:
    #     equipments = equipments.none()
    equipments = equipments.order_by('-id')
    devices = [equipment.to_dict() for equipment in equipments]

    return HttpResponse(
        json.dumps({
            'devices': devices
        }),
        content_type='application/json'
    )


@login_required
def search(request, *args, **kwargs):
    keyword = request.GET.get('query')
    techies = []
    equipment_qs = Device.objects
    equipments = equipment_qs.filter(Q(name__icontains=keyword) | Q(manager_name__icontains=keyword))
    equipment_count = equipments.count()

    corresponding_users = Member.objects.filter(username__icontains=keyword)
    techs = Techie.objects.filter(member__in=list(corresponding_users))
    devices = [device.to_dict() for device in equipments[:10]]
    for tech in techs:
        techicien = {
            'id': tech.id,
            'username': tech.member.username,
            'member': tech.member.to_dict(),
        }
        techies.append(techicien)
    response = {
        'devices': devices,
        'devices_count': equipment_count,
        'techies': techies
    }
    response = json.dumps(response)
    return HttpResponse(response)


@login_required
def load_equipments_by_city(request, *args, **kwargs):
    keyword = request.GET.get('query')
    techies = []
    equipments = Device.objects.filter(name__icontains=keyword)
    equipment_count = equipments.count()

    techs = Member.objects.filter(username__icontains=keyword)
    devices = [device.to_dict() for device in equipments[:10]]
    for tech in techs:
        techicien = {
            'id': tech.id,
            'username': tech.username,
        }
        techies.append(techicien)
    response = {
        'devices': devices,
        'devices_count': equipment_count,
        'techies': techies
    }
    response = json.dumps(response)
    return HttpResponse(response)


@login_required
def get_selected_device(request, *args, **kwargs):
    keyword = request.GET.get('deviceId')
    equipments = Device.objects.get(id=keyword)
    devices = equipments.to_dict()
    response = {
        'devices': devices
    }
    response = json.dumps(response)
    return HttpResponse(response)


@login_required
@permission_required('device.change_device')
def change_device_position(request, *args, **kwargs):
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    device_id = request.GET.get('deviceId')
    device = Device.objects.get(id=device_id)
    current_user = request.user
    techie = device.techie
    if current_user == techie.member or current_user.is_superuser:
        device.latitude = latitude
        device.longitude = longitude
        device.save()
        device = {
            'id': device.id,
            'lat': device.latitude,
            'lng': device.longitude,
            'icon': device.category.icon.url if device.category.icon.name else '',
            'zoom': device.category.zoom
        }
        return HttpResponse(
            json.dumps({'device': device}),
            content_type='application/json'
        )
    else:
        response = {
            'Error': "You don't have permission to update this device"
        }
    response = json.dumps(response)
    return HttpResponse(response)


def get_techie_installation(request, *args, **kwargs):
    techie_id = request.GET.get('techieId')
    techie = Techie.objects.get(pk=techie_id)


    equipments = Device.objects.filter(techie=techie)

    devices = [equipment.to_dict() for equipment in equipments]

    return HttpResponse(
        json.dumps({
            'devices': devices
        }),
        content_type='application/json'
    )


def get_recent_equipments(request, *args, **kwargs):

    string_date = request.GET.get('stringDate')
    equipments = Device.objects.all().order_by('-last_update')

    if request.GET.get('techieId'):
        techie_id = request.GET.get('techieId')
        techie = Techie.objects.get(id=techie_id)
        equipments.filter(techie=techie)
    if string_date:
        dates_list = retrieve_dates_from_interval(string_date)
        string_start_date = dates_list[0]
        string_end_date = dates_list[1]
        start_date = datetime.strptime(string_start_date, '%d-%m-%Y').date()
        end_date = datetime.strptime(string_end_date, '%d-%m-%Y').date()
        if start_date and end_date:
            equipments = equipments.filter(Q(last_update__gte=start_date) & Q(last_update__lt=end_date))
        elif start_date and not end_date:
            now = datetime.now()
            end_date = time.mktime(now.timetuple())
            equipments = equipments.filter(Q(last_update__gte=start_date) & Q(last_update__lt=end_date))
        elif end_date and not start_date:
            end_date_dtime = datetime.strptime(string_end_date, '%d-%m-%Y')
            end_date_dt = datetime(end_date_dtime.year, end_date_dtime.month, end_date_dtime.day, 0)
            start_date = int(time.mktime(end_date_dt.timetuple()))
            equipments = equipments.filter(Q(last_update__gte=start_date) & Q(last_update__lt=end_date))

    devices = [equipment.to_dict() for equipment in equipments]

    return HttpResponse(
        json.dumps({
            'devices': devices
        }),
        content_type='application/json'
    )


def grab_devices(request, *args, **kwargs):
    start = int(request.GET.get('start', 0))
    length = 50
    limit = start + length
    devices = []
    device_queryset = Device.objects.all().order_by('-id')[start:limit]
    for device in device_queryset:
        category = device.category
        equipment = {
            'id': device.id,
            'lat': float(device.latitude),
            'lng': float(device.longitude),
            'icon': category.icon.url if category.icon.name else '',
            'zoom': category.zoom
        }
        devices.append(equipment)

    return HttpResponse(
        json.dumps(devices),
        content_type='application/json'
    )


@login_required
def grab_device_info(request, *args, **kwargs):
    device_id = request.GET.get('deviceId')
    device = Device.objects.get(pk=device_id)
    equipment = {
        'id': device.id,
        'name': device.name,
        'techie': device.get_techie_name(),
        'manager': device.manager_name,
        'phone': device.phone,
        'description': device.description,
        'admin_url': device.get_admin_url(),
        'category': device.category.name,
        'created_on': device.created_on.strftime('%Y-%m-%d')
    }
    return HttpResponse(
        json.dumps({"device": equipment}),
        content_type='application/json'
    )


@login_required
def get_specific_device_data(request, *args, **kwargs):
    device_id = request.GET.get('deviceId')
    device_qs = Device.objects.get(id=device_id)
    devices = []
    category = device_qs.category
    device = {
        'id': device_qs.id,
        'desc': device_qs.description,
        'lat': float(device_qs.latitude),
        'lng': float(device_qs.longitude),
        'icon': category.icon.url if category.icon.name else '',
        'zoom': category.zoom
    }
    devices.append(device)

    return HttpResponse(
        json.dumps(devices),
        content_type='application/json'
    )


@login_required
def check_new_device(request, *args, **kwargs):
    techie = Techie.objects.get(member=request.user)
    last_device_id = request.GET.get('lastDeviceId')
    if len(last_device_id) > 0:
        start = last_device_id
        devices = []
        device_queryset = Device.objects.filter(id__gt=start).order_by('-id')
        for device in device_queryset:
            category = device.category
            device = {
                'id': device.id,
                'lat': float(device.latitude),
                'lng': float(device.longitude),
                'icon': category.icon.url if category.icon.name else '',
                'zoom': category.zoom
            }
            devices.append(device)

        return HttpResponse(
            json.dumps(devices),
            content_type='application/json'
        )
    return HttpResponse(
        json.dumps({'devices': ''}),
        content_type='application/json'
    )


@login_required
def check_data_integrity(request, *args, **kwargs):
    online_device_ids = []
    techie = Techie.objects.get(member=request.user)
    online_devices = Device.objects.all()
    if online_devices.count() > 0:
        last_device_id = online_devices.order_by('-id')[0]
        device_table_range = list(range(1,(last_device_id.id + 1)))
        for device in online_devices:
            online_device_ids.append(device.id)
        deleted_devices = [x for x in device_table_range if x not in online_device_ids]
    else:
        deleted_devices = []

    return HttpResponse(
        json.dumps({
            'deleted_devices': deleted_devices,
        }),
        content_type='application/json'
    )


@login_required
def get_asset_event_log(request, *args, **kwargs):
    asset_pk = request.GET.get('assetId')
    asset = Device.objects.get(pk=asset_pk)
    asset_logs = DeviceLog.objects.filter(device=asset)
    log_events = []
    for log in asset_logs:
        event = {
            'id': log.id,
            'type': log.log_event_type.name,
            'measure': log.measure,
            'details': log.details,
        }
        log_events.append(event)
    return HttpResponse(
                json.dumps({"event_list": log_events}),
                content_type='application/json'
            )


@login_required
@permission_required("device.add_device_log")
def save_event_log(request, *args, **kwargs):
    details = request.GET.get('details')
    log_event_type_id = request.GET.get('log_event_type_id')
    measure = request.GET.get('measure')
    asset_id = request.GET.get('asset_id')
    asset = Device.objects.get(pk=asset_id)
    log_event_type = LogEventType.objects.get(pk=log_event_type_id)
    techie = Techie.objects.get(member=request.user)
    event_log = DeviceLog(log_event_type=log_event_type, device=asset, measure=measure, details=details, techie=techie)
    event_log.save()
    event = {
        'id': event_log.id,
        'type': event_log.log_event_type.name,
        'measure': event_log.measure,
        'details': event_log.details,
    }
    return HttpResponse(
        json.dumps({'event_log': event}),)


@login_required
@permission_required("device.change_device")
def save_asset_position(request, *args, **kwargs):
    name = request.GET.get('name', '')
    manager_name = request.GET.get('manager_name')
    phone = request.GET.get('phone')
    city_id = request.GET.get('city')
    description = request.GET.get('description')
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    category_id = request.GET.get('category')
    member = request.user
    techie = Techie.objects.get(member=member)
    desc = description
    category = DeviceCategory.objects.get(pk=category_id)
    city = City.objects.get(pk=city_id)
    device_position = Device(category=category, name=name, longitude=longitude, latitude=latitude,city=city,
                             manager_name=manager_name,phone=phone, description=desc, techie=techie, status=Device.VALIDATE)
    device_position.save()
    if not name:
        device_count = Device.objects.all().count()
        name = category.name + "_" + str(device_count)
        device_position.name = name
        device_position.save()
    try:
        device_position.photo = request.FILES['photo']
    except:
        pass
    device_position.save()
    device = {
        'id': device_position.id,
        'lat': float(device_position.latitude),
        'lng': float(device_position.longitude),
        'icon': device_position.category.icon.url if device_position.category.icon.name else '',
        'zoom': device_position.category.zoom
    }
    return HttpResponse(json.dumps(device), content_type='application/json' )


@login_required
@permission_required("device.add_device_log")
def grab_event_log_detail(request, *args, **kwargs):
    log_pk = request.GET.get('logId')
    event_log = DeviceLog.objects.get(pk=log_pk)
    event = {
        'id': event_log.id,
        'type': event_log.log_event_type.name,
        'measure': event_log.measure,
        'details': event_log.details,
        'event_type_label': event_log.log_event_type.measure_label,
        'created_on': event_log.created_on,
    }
    return HttpResponse(json.dumps({"event": event}), content_type='application/json')


class DeployCloud(TemplateView):
    template_name = 'core/cloud_setup/deploy.html'

    def get_context_data(self, **kwargs):
        context = super(DeployCloud, self).get_context_data(**kwargs)
        context['billing_cycles'] = Service.BILLING_CYCLES_CHOICES
        app = Application.objects.using(UMBRELLA).get(slug='pinsview')
        context['app'] = app
        template_list = list(Template.objects.using(UMBRELLA).filter(app=app))
        context['theme_list'] = Theme.objects.using(UMBRELLA).filter(template__in=template_list)
        context['can_choose_themes'] = False
        if getattr(settings, 'IS_IKWEN', False):
            billing_plan_list = CloudBillingPlan.objects.using(UMBRELLA).filter(app=app, partner__isnull=True)
            if billing_plan_list.count() == 0:
                setup_months_count = 3
                context['ikwen_setup_cost'] = app.base_monthly_cost * setup_months_count
                context['ikwen_monthly_cost'] = app.base_monthly_cost
                context['setup_months_count'] = setup_months_count
        else:
            service = get_service_instance()
            billing_plan_list = CloudBillingPlan.objects.using(UMBRELLA).filter(app=app, partner=service)
            if billing_plan_list.count() == 0:
                retail_config = ApplicationRetailConfig.objects.using(UMBRELLA).get(app=app, partner=service)
                setup_months_count = 3
                context['ikwen_setup_cost'] = retail_config.ikwen_monthly_cost * setup_months_count
                context['ikwen_monthly_cost'] = retail_config.ikwen_monthly_cost
                context['setup_months_count'] = setup_months_count
        if billing_plan_list.count() > 0:
            context['billing_plan_list'] = billing_plan_list
            context['setup_months_count'] = billing_plan_list[0].setup_months_count
        return context

    def get(self, request, *args, **kwargs):
        member = request.user
        uri = request.META['REQUEST_URI']
        next_url = reverse('ikwen:sign_in') + '?next=' + urlquote(uri)
        if member.is_anonymous():
            return HttpResponseRedirect(next_url)
        if not getattr(settings, 'IS_IKWEN', False):
            if not member.has_perm('accesscontrol.sudo'):
                return HttpResponseForbidden("You are not allowed here. Please login as an administrator.")
        return super(DeployCloud, self).get(request, *args, **kwargs)

    # @method_decorator(csrf_protect)
    # @method_decorator(never_cache)
    # def post(self, request, *args, **kwargs):
    #     form = DeploymentForm(request.POST)
    #     if form.is_valid():
    #         app_id = form.cleaned_data.get('app_id')
    #         project_name = form.cleaned_data.get('project_name')
    #         billing_cycle = form.cleaned_data.get('billing_cycle')
    #         billing_plan_id = form.cleaned_data.get('billing_plan_id')
    #         domain = form.cleaned_data.get('domain')
    #         theme_id = form.cleaned_data.get('theme_id')
    #         partner_id = form.cleaned_data.get('partner_id')
    #         app = Application.objects.using(UMBRELLA).get(pk=app_id)
    #         theme = Theme.objects.using(UMBRELLA).get(pk=theme_id)
    #         billing_plan = CloudBillingPlan.objects.using(UMBRELLA).get(pk=billing_plan_id)
    #
    #         is_ikwen = getattr(settings, 'IS_IKWEN', False)
    #         if not is_ikwen or (is_ikwen and request.user.is_staff):
    #             customer_id = form.cleaned_data.get('customer_id')
    #             customer = Member.objects.using(UMBRELLA).get(pk=customer_id)
    #             setup_cost = form.cleaned_data.get('setup_cost')
    #             monthly_cost = form.cleaned_data.get('monthly_cost')
    #             if setup_cost < billing_plan.setup_cost:
    #                 return HttpResponseForbidden("Attempt to set a Setup cost lower than allowed.")
    #             if monthly_cost < billing_plan.monthly_cost:
    #                 return HttpResponseForbidden("Attempt to set a monthly cost lower than allowed.")
    #         else:
    #             # User self-deploying his website
    #             customer = Member.objects.using(UMBRELLA).get(pk=request.user.id)
    #             setup_cost = billing_plan.setup_cost
    #             monthly_cost = billing_plan.monthly_cost
    #
    #         partner = Service.objects.using(UMBRELLA).get(pk=partner_id) if partner_id else None
    #         invoice_entries = []
    #         domain_name = IkwenInvoiceItem(label='Domain name')
    #         domain_name_entry = InvoiceEntry(item=domain_name, short_description=domain)
    #         invoice_entries.append(domain_name_entry)
    #         website_setup = IkwenInvoiceItem(label='Website setup', price=billing_plan.setup_cost, amount=setup_cost)
    #         short_description = "Twelve months of service"
    #         website_setup_entry = InvoiceEntry(item=website_setup, short_description=short_description, total=setup_cost)
    #         invoice_entries.append(website_setup_entry)
    #         i = 0
    #         while True:
    #             try:
    #                 label = request.POST['item%d' % i]
    #                 amount = float(request.POST['amount%d' % i])
    #                 if not (label and amount):
    #                     break
    #                 item = IkwenInvoiceItem(label=label, amount=amount)
    #                 entry = InvoiceEntry(item=item, total=amount)
    #                 invoice_entries.append(entry)
    #                 i += 1
    #             except:
    #                 break
    #         if getattr(settings, 'DEBUG', False):
    #             service = deploy(app, customer, project_name, billing_plan, theme,
    #                              monthly_cost, invoice_entries, billing_cycle, domain, partner_retailer=partner)
    #         else:
    #             try:
    #                 service = deploy(app, customer, project_name, billing_plan, theme,
    #                                  monthly_cost, invoice_entries, billing_cycle, domain, partner_retailer=partner)
    #             except Exception as e:
    #                 context = self.get_context_data(**kwargs)
    #                 context['error'] = e.message
    #                 return render(request, 'core/cloud_setup/deploy.html', context)
    #         if is_ikwen:
    #             if request.user.is_staff:
    #                 next_url = reverse('partnership:change_service', args=(service.id, ))
    #             else:
    #                 next_url = reverse('ikwen:console')
    #         else:
    #             next_url = reverse('change_service', args=(service.id, ))
    #         return HttpResponseRedirect(next_url)
    #     else:
    #         context = self.get_context_data(**kwargs)
    #         context['form'] = form
    #         return render(request, 'core/cloud_setup/deploy.html', context)


def list_community(request, *args, **kwargs):
    q = request.GET['q'].lower()
    if len(q) < 2:
        return

    queryset = Member.objects.filter(is_active=True)
    word = slugify(q)[:4]
    if word:
        queryset = queryset.filter(Q(username__icontains=word) | Q(email__icontains=word) | Q(phone__icontains=word))

    community_user = []
    for s in queryset.order_by('username')[:6]:
        try:
            p = s.to_dict()
            community_user.append(p)
        except:
            pass

    response = {'object_list': community_user}
    callback = request.GET['callback']
    jsonp = callback + '(' + json.dumps(response) + ')'
    return HttpResponse(jsonp, content_type='application/json')