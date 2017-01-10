from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  RedirectView)
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db.models import Sum

import rules
from rules.contrib.views import PermissionRequiredMixin

from .models import Business, Outlet, TillClosure
from .forms import OutletForm


# General views

class SimpleHomeRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        try:
            outlet = self.request.user.profile.outlets.get()
        except (Outlet.DoesNotExist, Outlet.MultipleObjectsReturned):
            return reverse('cashup_outlet_list')
        return outlet.get_absolute_url()


#--------- Business model views ---------#

class BusinessDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                                                                DetailView):
    permission_required = 'cashup.view_business'

    def get_object(self):
        return self.request.user.profile.business


class BusinessUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                                                UpdateView):
    permission_required = 'cashup.change_business'
    fields = ['name']

    def get_object(self):
        return self.request.user.profile.business


#--------- Outlet model views ---------#

class OutletListView(LoginRequiredMixin, ListView):
    # perms not required as only displays user's workplaces
    def get_queryset(self):
        return self.request.user.profile.outlets.all()


class OutletUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                                                UpdateView):
    model = Outlet
    permission_required = 'cashup.change_outlet'
    form_class = OutletForm
    success_url = '/'
    slug_url_kwarg = 'name'
    slug_field = 'name'

    def get_queryset(self):
        return self.request.user.profile.outlets.all()

    def get_success_url(self):
        return self.object.get_absolute_url()


class OutletCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Outlet
    permission_required = 'cashup.create_outlet'
    form_class = OutletForm
    success_url = "/"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(OutletCreateView, self).get_form_kwargs()
        kwargs['instance'] = self.model(
            business=self.request.user.profile.business)
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        self.object.personnel.add(self.request.user.profile)
        return HttpResponseRedirect(self.get_success_url())


#--------- TillClosure model views ---------#

class OutletTillClosureMixin(object):
    model = TillClosure



class OutletClosureListView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    template_name = 'cashup/tillclosure_list.html'
    context_object_name = 'outlet'
    permission_required = ['cashup.view_outlet', 'cashup.view_tillclosures_for_outlet']
    slug_url_kwarg = 'name'
    slug_field = 'name'

    def get_queryset(self):
        return self.request.user.profile.outlets.all()

    def get_context_data(self, *args, **kwargs):
        context = super(OutletClosureListView, self).get_context_data(
            *args, **kwargs)
        tillclosures = context['outlet'].tillclosures.all()
        context['object_list'] = tillclosures
        context['totals'] = tillclosures.aggregate(
            total_takings=Sum('total_takings'),
            till_difference=Sum('till_difference'))
        return context


class TillClosureDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                                                                DetailView):
    permission_required = 'cashup.view_tillclosure'
    model = TillClosure

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureDetailView, self).get_context_data(
            *args, **kwargs)
        context['outlet'] = context['object'].outlet
        return context


class TillClosureFormMixin(object):
    model = TillClosure
    fields = ['close_time', 'cash_takings', 'card_takings',
              'note_50GBP', 'note_20GBP', 'note_10GBP', 'note_5GBP',
              'coin_2GBP', 'coin_1GBP', 'coin_50p', 'coin_20p',
              'coin_10p', 'coin_5p', 'coin_2p', 'coin_1p', 'till_float',
              'notes']


class TillClosureUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                        TillClosureFormMixin, UpdateView):
    permission_required = 'cashup.change_tillclosure'

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureUpdateView, self).get_context_data(
            *args, **kwargs)
        context['outlet'] = context['object'].outlet
        return context


class TillClosureCreateView(LoginRequiredMixin, TillClosureFormMixin, CreateView):
    permission_required = 'cashup.create_tillclosure_for_outlet'

    def check_permissions(self):
        if not self.request.user.has_perm(
                self.permission_required, self.get_outlet()):
            raise PermissionDenied

    def dispatch(self, request, *args, **kwargs):
        self.check_permissions()
        return super(TillClosureCreateView, self).dispatch(
            request, *args, **kwargs)

    def get_outlet(self):
        if not hasattr(self, 'outlet') or self.outlet is None:
            outlet_name = self.kwargs.get('name')
            self.outlet = get_object_or_404(Outlet, name=outlet_name,
                business=self.request.user.profile.business)
        return self.outlet

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureCreateView, self).get_context_data(
            *args, **kwargs)
        context['outlet'] = self.get_outlet()
        return context

    def form_valid(self, form):
        outlet = self.get_outlet()
        form.instance.outlet = outlet
        form.instance.closed_by = self.request.user.profile
        return super(TillClosureCreateView, self).form_valid(form)

    def get_initial(self):
        return {
            'till_float': self.get_outlet().default_float
        }
