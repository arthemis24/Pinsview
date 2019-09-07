from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import user_passes_test
from django.contrib import admin

from assets.views import Network
from ikwen.accesscontrol.views import SignIn
from django.contrib.auth.decorators import permission_required
from ikwen_kakocase.shopping.views import Home, FlatPageView

from ikwen_kakocase.trade.provider.views import ProviderDashboard
from ikwen_kakocase.trade.views import RetailerDashboard, LogicomDashboard
from ikwen_kakocase.kakocase.views import MerchantList
#from ikwen_pinsview.assets.views import AdminView


admin.autodiscover()

if getattr(settings, 'IS_RETAILER', False):
    Dashboard = RetailerDashboard
elif getattr(settings, 'IS_PROVIDER', False):
    Dashboard = ProviderDashboard
else:
    Dashboard = LogicomDashboard

if getattr(settings, 'IS_IKWEN', False):
    LandingPage = MerchantList
elif getattr(settings, 'IS_DELIVERY_COMPANY', False) or getattr(settings, 'IS_BANK', False):
    LandingPage = SignIn
else:
    LandingPage = Home

urlpatterns = patterns('',
    url(r'^laakam/', include(admin.site.urls)),

    url(r'^ikwen/dashboard/$', permission_required('trade.ik_view_dashboard')(Dashboard.as_view()), name='dashboard'),
    url(r'^ikwen/theming/', include('ikwen.theming.urls', namespace='theming')),
    url(r'^ikwen/cashout/', include('ikwen.cashout.urls', namespace='cashout')),
    url(r'^ikwen/', include('ikwen.core.urls', namespace='ikwen')),
    url(r'^page/(?P<url>[-\w]+)/$', FlatPageView.as_view(), name='flatpage'),

    url(r'^', include('ikwen_pinsview.assets.urls', namespace='locator')),
    # url(r'^', include('ikwen_pinsview.assets.urls', namespace='home')),
    url(r'^$', Network.as_view(), name='home'),


)
