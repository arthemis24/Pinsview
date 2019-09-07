from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import user_passes_test
from django.contrib import admin

from ikwen_pinsview.assets.views import save_device_position, filter_network_data, grab_event_log_detail, \
    is_registered_member, search, get_techie_installation, get_selected_device, save_asset_position, \
    get_recent_equipments, Network, change_device_position, grab_devices, save_device, grab_device_info, \
    check_new_device, check_data_integrity, get_specific_device_data, Prospect, get_asset_event_log, save_event_log,\
    DeployCloud, Deploy, list_community


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^pinsview/deployCloud/$', DeployCloud.as_view(), name='deploy_cloud'),
    url(r'^$', Network.as_view(), name='network'),
    url(r'^$', Network.as_view(), name='home'),
    # url(r'^$', user_passes_test(is_registered_member)(Network.as_view()), name='network'),
    url(r'^prospect/$', user_passes_test(is_registered_member)(Prospect.as_view()), name='prospect'),
    url(r'^deploy/$', user_passes_test(is_registered_member)(Deploy.as_view()), name='deploy'),

    url(r'^save_device$', save_device, name='save_device'),
    url(r'^save_device_position$', save_device_position, name='save_device_position'),
    url(r'^save_asset_position$', save_asset_position, name='save_asset_position'),
    url(r'^filter_network_data$', filter_network_data, name='filter_network_data'),
    url(r'^full_search$', search, name='search'),
    url(r'^get_selected_device$', get_selected_device, name='get_selected_device'),
    url(r'^change_device_position$', change_device_position, name='change_device_position'),
    url(r'^get_techie_installation$', get_techie_installation, name='get_techie_installation'),
    url(r'^get_recent_equipments$', get_recent_equipments, name='get_recent_equipments'),
    url(r'^grab_devices$', grab_devices, name='grab_devices'),
    url(r'^grab_device_info$', grab_device_info, name='grab_device_info'),
    url(r'^check_new_device$', check_new_device, name='check_new_device'),
    url(r'^check_device_data_integrity$', check_data_integrity, name='check_data_integrity'),
    url(r'^get_specific_device_data$', get_specific_device_data, name='get_specific_device_data'),
    url(r'^get_asset_event_log$', get_asset_event_log, name='get_asset_event_log'),
    url(r'^save_event_log$', save_event_log, name='save_event_log'),
    url(r'^grab_event_log_detail$', grab_event_log_detail, name='grab_event_log_detail'),
    url(r'^list_community$', list_community, name='list_community'),
)
