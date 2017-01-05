from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.TillClosureListView.as_view(),
        name='cashup_till_closure_list'),
    url(r'^closures/(?P<pk>[0-9]+)/$', views.TillClosureDetailView.as_view(),
        name='cashup_closure_detail'),
    url(r'^closures/$', views.TillClosureListView.as_view(),
        name='cashup_closure_list'),
    url(r'^closures/(?P<pk>[0-9]+)/edit/$', views.TillClosureUpdateView.as_view(),
        name='cashup_closure_update'),
    url(r'^closures/create/$', views.TillClosureCreateView.as_view(),
        name='cashup_closure_create'),
]
