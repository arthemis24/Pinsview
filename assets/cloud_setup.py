# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from threading import Thread

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.utils.translation import gettext as _
from ikwen.billing.mtnmomo.views import MTN_MOMO
from ikwen.billing.orangemoney.views import ORANGE_MONEY
from ikwen_webnode.webnode.models import OperatorProfile
from permission_backend_nonrel.models import UserPermissionList, GroupPermissionList

from ikwen.accesscontrol.backends import UMBRELLA
from ikwen.accesscontrol.models import SUDO, Member
from ikwen.billing.models import Invoice, PaymentMean, InvoicingConfig
from ikwen.billing.utils import get_next_invoice_number
from ikwen.conf.settings import STATIC_ROOT, STATIC_URL, MEDIA_ROOT, MEDIA_URL
from ikwen.core.models import Service, SERVICE_DEPLOYED, OperatorWallet
from ikwen.core.tools import generate_django_secret_key, generate_random_key, reload_server
from ikwen.core.utils import add_database_to_settings, add_event, get_mail_content, \
    get_service_instance
from ikwen.flatpages.models import FlatPage
from ikwen.partnership.models import PartnerProfile
from ikwen.theming.models import Template, Theme

import logging
logger = logging.getLogger('ikwen')


if getattr(settings, 'LOCAL_DEV', False):
    CLOUD_HOME = '/home/roddy/PycharmProjects/CloudTest/'
else:
    CLOUD_HOME = '/home/ikwen/Cloud/'

CLOUD_FOLDER = CLOUD_HOME + 'PinsView/'


# from captcha.fields import ReCaptchaField


class DeploymentForm(forms.Form):
    """
    Deployment form of a platform
    """
    partner_id = forms.CharField(max_length=24, required=False)  # Service ID of the partner retail platform
    app_id = forms.CharField(max_length=24)
    customer_id = forms.CharField(max_length=24)
    project_name = forms.CharField(max_length=30)
    domain = forms.CharField(max_length=60, required=False)
    billing_cycle = forms.CharField(max_length=24)
    billing_plan_id = forms.CharField(max_length=24)
    setup_cost = forms.FloatField()
    monthly_cost = forms.FloatField()
    theme_id = forms.CharField()


def deploy(app, member, project_name, billing_plan, theme, monthly_cost,
           invoice_entries, billing_cycle, domain=None, partner_retailer=None):
    project_name_slug = slugify(project_name)  # Eg: slugify('Cool Shop') = 'cool-shop'
    ikwen_name = project_name_slug.replace('-', '')  # Eg: cool-shop --> 'coolshop'
    pname = ikwen_name
    i = 0
    while True:
        try:
            Service.objects.using(UMBRELLA).get(project_name_slug=pname)
            i += 1
            pname = "%s%d" % (ikwen_name, i)
        except Service.DoesNotExist:
            ikwen_name = pname
            break
    api_signature = generate_random_key(30)
    while True:
        try:
            Service.objects.using(UMBRELLA).get(api_signature=api_signature)
            api_signature = generate_random_key(30)
        except Service.DoesNotExist:
            break
    database = ikwen_name
    if domain:
        if domain.startswith('www.'):
            domain = domain.replace('www.', '')
        domain_type = Service.MAIN
        is_naked_domain = True
    else:
        domain = 'ikwen.com/' + ikwen_name
        domain_type = Service.SUB
        is_naked_domain = False
    if getattr(settings, 'IS_UMBRELLA', False):
        admin_url = domain + '/ikwen' + reverse('ikwen:staff_router')
    else:  # This is a deployment performed by a partner retailer
        admin_url = domain + reverse('ikwen:staff_router')
    is_pro_version = billing_plan.is_pro_version
    now = datetime.now()
    expiry = now + timedelta(days=15)

    # Create a copy of template application in the Cloud folder
    app_folder = CLOUD_HOME + '000Tpl/AppSkeleton'
    website_home_folder = CLOUD_FOLDER + ikwen_name
    media_root = MEDIA_ROOT + ikwen_name + '/'
    media_url = MEDIA_URL + ikwen_name + '/'
    default_images_folder = CLOUD_FOLDER + '000Tpl/images/000Default'
    if os.path.exists(default_images_folder):
        if os.path.exists(media_root):
            shutil.rmtree(media_root)
        shutil.copytree(default_images_folder, media_root)
        logger.debug("Media folder '%s' successfully created from '%s'" % (media_root, default_images_folder))
    elif not os.path.exists(media_root):
        os.makedirs(media_root)
        logger.debug("Media folder '%s' successfully created empty" % media_root)
    favicons_folder = media_root + 'favicons'
    if not os.path.exists(favicons_folder):
        os.makedirs(favicons_folder)
    if os.path.exists(website_home_folder):
        shutil.rmtree(website_home_folder)
    shutil.copytree(app_folder, website_home_folder)
    logger.debug("Service folder '%s' successfully created" % website_home_folder)

    service = Service(member=member, app=app, project_name=project_name, project_name_slug=ikwen_name, domain=domain,
                      database=database, url='https://' + domain, domain_type=domain_type, expiry=expiry,
                      admin_url='https://' + admin_url, billing_plan=billing_plan, billing_cycle=billing_cycle,
                      monthly_cost=monthly_cost, version=Service.TRIAL, retailer=partner_retailer,
                      api_signature=api_signature, home_folder=website_home_folder)
    service.save(using=UMBRELLA)
    logger.debug("Service %s successfully created" % pname)

    # Import template database and set it up
    db_folder = CLOUD_FOLDER + '000Tpl/DB/000Default'

    host = getattr(settings, 'DATABASES')['default'].get('HOST', '127.0.0.1')
    subprocess.call(['mongorestore', '--host', host, '-d', database, db_folder])
    logger.debug("Database %s successfully created on host %s from %s" % (database, host, db_folder))

    add_database_to_settings(database)
    # Re-create settings.py file as well as apache.conf file for the newly created project
    secret_key = generate_django_secret_key()
    allowed_hosts = '"%s", "www.%s"' % (domain, domain)
    settings_tpl = get_template('assets/cloud_setup/settings.html')
    settings_context = Context(
        {'secret_key': secret_key, 'ikwen_name': ikwen_name,  # 'business_setting': business_setting,
         'service': service, 'static_root': STATIC_ROOT, 'static_url': STATIC_URL,
         'media_root': media_root, 'media_url': media_url,
         'allowed_hosts': allowed_hosts, 'debug': getattr(settings, 'DEBUG', False)})
    settings_file = website_home_folder + '/conf/settings.py'
    fh = open(settings_file, 'w')
    fh.write(settings_tpl.render(settings_context))
    fh.close()
    logger.debug("Settings file '%s' successfully created" % settings_file)

    for group in Group.objects.using(database).all():
        try:
            gpl = GroupPermissionList.objects.get(group=group)
            group.delete()
            group.save(using=database)   # Recreate the group in the service DB with a new id.
            gpl.group = group    # And update GroupPermissionList object with the newly re-created group
            gpl.save(using=database)
        except GroupPermissionList.DoesNotExist:
            group.delete()
            group.save(using=database)  # Re-create the group in the service DB with anyway.
    new_sudo_group = Group.objects.using(database).get(name=SUDO)

    for s in member.get_services():
        db = s.database
        add_database_to_settings(db)
        collaborates_on_fk_list = member.collaborates_on_fk_list + [service.id]
        customer_on_fk_list = member.customer_on_fk_list + [service.id]
        if partner_retailer and partner_retailer.id not in customer_on_fk_list:
            customer_on_fk_list += [partner_retailer.id]
        group_fk_list = member.group_fk_list + [new_sudo_group.id]
        Member.objects.using(db).filter(pk=member.id).update(collaborates_on_fk_list=collaborates_on_fk_list,
                                                             customer_on_fk_list=customer_on_fk_list,
                                                             group_fk_list=group_fk_list)

    member.collaborates_on_fk_list = collaborates_on_fk_list
    member.customer_on_fk_list = customer_on_fk_list
    member.group_fk_list = group_fk_list

    member.is_iao = True
    member.save(using=UMBRELLA)

    member.is_bao = True
    member.is_staff = True
    member.is_superuser = True

    app.save(using=database)
    member.save(using=database)
    logger.debug("Member %s access rights successfully set for service %s" % (member.username, pname))

    # Copy payment means to local database
    for mean in PaymentMean.objects.using(UMBRELLA).all():
        if mean.slug == MTN_MOMO:
            mean.is_main = True
            mean.is_active = True
        elif mean.slug == ORANGE_MONEY:
            mean.is_main = False
            mean.is_active = True
        else:
            mean.is_main = False
            mean.is_active = False
        mean.save(using=database)
        logger.debug("PaymentMean %s created in database: %s" % (mean.slug, database))

    # Copy themes to local database
    for template in Template.objects.using(UMBRELLA).all():
        template.save(using=database)
    logger.debug("Template and theme successfully bound for service: %s" % pname)

    FlatPage.objects.using(database).create(url=FlatPage.AGREEMENT, title=FlatPage.AGREEMENT)
    FlatPage.objects.using(database).create(url=FlatPage.LEGAL_MENTIONS, title=FlatPage.LEGAL_MENTIONS)

    # Add member to SUDO Group
    obj_list, created = UserPermissionList.objects.using(database).get_or_create(user=member)
    obj_list.group_fk_list.append(new_sudo_group.id)
    obj_list.save(using=database)
    logger.debug("Member %s successfully added to sudo group for service: %s" % (member.username, pname))

    # Create wallets
    OperatorWallet.objects.using('wallets').create(nonrel_id=service.id, provider=MTN_MOMO)
    OperatorWallet.objects.using('wallets').create(nonrel_id=service.id, provider=ORANGE_MONEY)
    mail_signature = "%s<br>" \
                     "<a href='%s'>%s</a>" % (project_name, 'http://' + domain, domain)
    config = OperatorProfile(service=service, currency_code='XAF', currency_symbol='XAF', signature=mail_signature,
                             company_name=project_name, contact_email=member.email, contact_phone=member.phone)
    config.save(using=UMBRELLA)
    base_config = config.get_base_config()
    base_config.save(using=UMBRELLA)
    if partner_retailer:
        partner_retailer.save(using=database)
    service.save(using=database)

    # theme.save(using=database)  # Causes theme to be routed to the newly created database
    config.save(using=database)

    InvoicingConfig.objects.using(database).create()
    logger.debug("Configuration successfully added for service: %s" % pname)

    # Apache Server cloud_setup
    if getattr(settings, 'LOCAL_DEV', False):
        apache_tpl = get_template('assets/cloud_setup/apache.conf.local.html')
    else:
        apache_tpl = get_template('assets/cloud_setup/apache.conf.html')
    apache_context = Context({'is_naked_domain': is_naked_domain, 'domain': domain, 'ikwen_name': ikwen_name})
    fh = open(website_home_folder + '/apache.conf', 'w')
    fh.write(apache_tpl.render(apache_context))
    fh.close()

    vhost = '/etc/apache2/sites-enabled/' + domain + '.conf'
    subprocess.call(['sudo', 'ln', '-sf', website_home_folder + '/apache.conf', vhost])
    logger.debug("Apache Virtual Host '%s' successfully created" % vhost)

    # Send notification and Invoice to customer
    number = get_next_invoice_number()
    invoice_total = 0
    for entry in invoice_entries:
        invoice_total += entry.item.amount * entry.quantity
    invoice = Invoice(subscription=service, amount=invoice_total, number=number, due_date=expiry, last_reminder=now,
                      reminders_sent=1, is_one_off=True, entries=invoice_entries,
                      months_count=billing_plan.setup_months_count)
    invoice.save(using=UMBRELLA)
    vendor = get_service_instance()

    if member != vendor.member:
        add_event(vendor, SERVICE_DEPLOYED, member=member, object_id=invoice.id)
    if partner_retailer:
        partner_profile = PartnerProfile.objects.using(UMBRELLA).get(service=partner_retailer)
        try:
            Member.objects.get(pk=member.id)
        except Member.DoesNotExist:
            member.is_iao = False
            member.is_bao = False
            member.is_staff = False
            member.is_superuser = False
            member.save(using='default')
        service.save(using='default')
        config.save(using='default')
        sender = '%s <no-reply@%s>' % (partner_profile.company_name, partner_retailer.domain)
        sudo_group = Group.objects.get(name=SUDO)
        ikwen_sudo_gp = Group.objects.using(UMBRELLA).get(name=SUDO)
        add_event(vendor, SERVICE_DEPLOYED, group_id=ikwen_sudo_gp.id, object_id=invoice.id)
    else:
        sender = 'ikwen <no-reply@ikwen.com>'
        sudo_group = Group.objects.using(UMBRELLA).get(name=SUDO)
    add_event(vendor, SERVICE_DEPLOYED, group_id=sudo_group.id, object_id=invoice.id)
    invoice_url = 'http://www.ikwen.com' + reverse('billing:invoice_detail', args=(invoice.id,))
    subject = _("Your website %s was created" % project_name)
    html_content = get_mail_content(subject, '', template_name='core/mails/service_deployed.html',
                                    extra_context={'service_activated': service, 'invoice': invoice,
                                                   'member': member, 'invoice_url': invoice_url})
    msg = EmailMessage(subject, html_content, sender, [member.email])
    bcc = ['contact@ikwen.com']
    if vendor.config.contact_email:
        bcc.append(vendor.config.contact_email)
    msg.bcc = list(set(bcc))
    msg.content_subtype = "html"
    Thread(target=lambda m: m.send(), args=(msg,)).start()
    logger.debug("Notice email submitted to %s" % member.email)
    Thread(target=reload_server).start()
    logger.debug("Apache Scheduled to reload in 5s")
    return service
