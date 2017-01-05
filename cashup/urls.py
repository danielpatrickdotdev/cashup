from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.TillClosureListView.as_view(),
        name='cashup_closures_list'),
    url(r'^(?P<pk>[0-9]+)/$', views.TillClosureDetailView.as_view(),
        name='cashup_closure_detail'),
    url(r'^(?P<pk>[0-9]+)/edit/$', views.TillClosureUpdateView.as_view(),
        name='cashup_closure_update'),
    url(r'^create/$', views.TillClosureCreateView.as_view(),
        name='cashup_closure_create'),
]
