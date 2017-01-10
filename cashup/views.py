from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, RedirectView
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.db.models import Sum

import rules
from rules.contrib.views import PermissionRequiredMixin

from .models import Business, Outlet, TillClosure
from .forms import OutletForm


#--------- Mixins ---------#

class BusinessContextMixin(object):
    def get_context_data(self, *args, **kwargs):
        context = super(BusinessContextMixin, self).get_context_data(*args, **kwargs)
        business = getattr(self.request.user, 'business', None)
        if business is None: 
            business = self.workplaces.first().business
        context['business'] = business
        return context


class UserBusinessMixin(object):
    def get_user_business(self):
        if not hasattr(self, 'business') or self.business is None:
            self.business = getattr(self.request.user, 'business', None)
            if self.business is None:
                raise PermissionDenied
        return self.business


class OutletQuerysetMixin(object):
    def get_queryset(self):
        return self.request.user.workplaces.all()


# General views

class SimpleHomeRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        try:
            outlet = self.request.user.workplaces.get()
        except (Outlet.DoesNotExist, Outlet.MultipleObjectsReturned):
            return reverse('cashup_outlet_list')
        return outlet.get_absolute_url()


#--------- Business model views ---------#

class BusinessDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                                            UserBusinessMixin, DetailView):
    permission_required = 'cashup.view_business'

    def get_object(self):
        return self.get_user_business()


class BusinessUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                            UserBusinessMixin, UpdateView):
    permission_required = 'cashup.change_business'
    fields = ['name']

    def get_object(self):
        return self.get_user_business()


#--------- Outlet model views ---------#

class OutletListView(LoginRequiredMixin, OutletQuerysetMixin,
                                            BusinessContextMixin, ListView):
    # perms not required as only displays user's workplaces
    pass


class OutletUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                            BusinessContextMixin, UpdateView):
    model = Outlet
    permission_required = 'cashup.change_outlet'
    form_class = OutletForm
    success_url = '/'
    slug_url_kwarg = 'outlet_name'
    slug_field = 'name'

    def get_queryset(self):
        return self.request.user.workplaces.all()

    def get_success_url(self):
        print("NAME:",self.object.name)
        return self.object.get_absolute_url()


class OutletCreateView(LoginRequiredMixin, UserBusinessMixin, CreateView):
    model = Outlet
    form_class = OutletForm
    success_url = "/"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        business = self.get_user_business() # confirms user is authorised
        kwargs = super(OutletCreateView, self).get_form_kwargs()
        kwargs['instance'] = self.model(business=business)
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        self.object.staff.add(self.request.user)
        return HttpResponseRedirect(self.get_success_url())


#--------- TillClosure model views ---------#

class OutletTillClosureMixin(object):
    model = TillClosure

    def get_staff_outlets(self):
        return self.request.user.workplaces.all()

    def get_queryset(self):
        return self.get_outlet().tillclosures.all()

    def get_outlet(self):
        if not hasattr(self, 'outlet') or self.outlet is None:
            outlet_name = self.kwargs.get('outlet_name')
            self.outlet = get_object_or_404(
                self.get_staff_outlets(), name=outlet_name)
        return self.outlet

    def get_context_data(self, *args, **kwargs):
        context = super(OutletTillClosureMixin, self).get_context_data(*args, **kwargs)
        context['outlet'] = self.get_outlet()
        return context


class OutletClosureListView(LoginRequiredMixin, OutletQuerysetMixin, DetailView):
    template_name = 'cashup/tillclosure_list.html'
    context_object_name = 'outlet'
    permission_required = 'cashup.view_outlet'
    slug_url_kwarg = 'outlet_name'
    slug_field = 'name'

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
                                            OutletTillClosureMixin, DetailView):
    permission_required = 'cashup.view_tillclosure_new'


class TillClosureFormMixin(OutletTillClosureMixin):
    fields = ['close_time', 'cash_takings', 'card_takings',
              'note_50GBP', 'note_20GBP', 'note_10GBP', 'note_5GBP',
              'coin_2GBP', 'coin_1GBP', 'coin_50p', 'coin_20p',
              'coin_10p', 'coin_5p', 'coin_2p', 'coin_1p', 'till_float',
              'notes']


class TillClosureUpdateView(LoginRequiredMixin, PermissionRequiredMixin,
                                            TillClosureFormMixin, UpdateView):
    permission_required = 'cashup.change_tillclosure'


class TillClosureCreateView(LoginRequiredMixin, TillClosureFormMixin, CreateView):
    permission_required = 'cashup.create_tillclosure_for_outlet'

    def check_permissions(self):
        if not self.request.user.has_perm(
                self.permission_required, self.get_outlet()):
            raise PermissionDenied

    def get(self, request, *args, **kwargs):
        self.check_permissions()
        return super(TillClosureCreateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.check_permissions()
        return super(TillClosureCreateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        outlet = self.get_outlet()
        form.instance.outlet = outlet
        form.instance.closed_by = self.request.user
        return super(TillClosureCreateView, self).form_valid(form)

    def get_initial(self):
        return {
            'till_float': self.get_outlet().default_float
        }
