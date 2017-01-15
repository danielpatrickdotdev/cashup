from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  RedirectView)
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse, reverse_lazy
from django.db.models import Sum, F
from django.forms import inlineformset_factory

import rules
from rules.contrib.views import PermissionRequiredMixin

from .models import Business, Outlet, TillClosure, Personnel, StaffPosition
from .forms import OutletForm, StaffFormSet, StaffPositionForm


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
    success_url = reverse_lazy('cashup_business_detail')

    def get_object(self):
        return self.request.user.profile.business


#--------- Personnel model views ---------#

class PersonnelDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                                                                DetailView):
    permission_required = 'cashup.view_personnel'
    slug_url_kwarg = 'username'
    slug_field = 'user__username'

    def get_queryset(self):
        return Personnel.objects.filter(
            business=self.request.user.profile.business)

class PersonnelUpdateView(LoginRequiredMixin,
                          PermissionRequiredMixin, UpdateView):
    fields = ['is_manager']
    permission_required = 'cashup.change_personnel'
    slug_url_kwarg = 'username'
    slug_field = 'user__username'

    def get_queryset(self):
        return Personnel.objects.filter(
            business=self.request.user.profile.business)


class PersonnelListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'cashup.view_personnel_list'

    def get_queryset(self):
        return Personnel.objects.filter(
            business=self.request.user.profile.business)


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
    staff_form_class = StaffFormSet

    def post(self, request, *args, **kwargs):
        redirect = super(OutletUpdateView, self).post(request, *args, **kwargs)
        potential_staff = self.object.business.personnel.exclude(
            positions__outlet=self.object)
        initial = [
            {'personnel': person.pk} for person in potential_staff]
        Form = inlineformset_factory(Outlet,
                                     StaffPosition,
                                     form=StaffPositionForm,
                                     extra=len(potential_staff))
        qs = StaffPosition.objects.filter(
            outlet=self.object).exclude(personnel__is_owner=True)
        staff_form = Form(request.POST, instance=self.object, queryset=qs,initial=initial)
        if staff_form.is_valid():
            staff_form.save()
        else:
            self.invalid_staff_form = staff_form
            return self.render_to_response(self.get_context_data())
        return redirect

    def create_formset(self):
        potential_staff = self.object.business.personnel.exclude(
            positions__outlet=self.object)
        initial = [
            {'personnel': person.pk} for person in potential_staff]
        Form = inlineformset_factory(Outlet,
                                     StaffPosition,
                                     form=StaffPositionForm,
                                     extra=len(potential_staff))
        qs = StaffPosition.objects.filter(
            outlet=self.object).exclude(personnel__is_owner=True)
        return Form(instance=self.object, queryset=qs, initial=initial)

    def get_queryset(self):
        return self.request.user.profile.outlets.all()

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, *args, **kwargs):
        context = super(OutletUpdateView, self).get_context_data(
            *args, **kwargs)
        if hasattr(self, 'invalid_staff_form'):
            context['staff_forms'] = self.invalid_staff_form
        else:
            context['staff_forms'] = self.create_formset()
        return context


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



class TillClosureListViewBase(LoginRequiredMixin, PermissionRequiredMixin,
                                                SingleObjectMixin, ListView):
    order_dict = {'date': 'close_time',
                  '-date': '-close_time',
                  'takings': 'total_takings',
                  '-takings': '-total_takings',
                  'difference': 'till_difference',
                  '-difference': '-till_difference'}

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(TillClosureListViewBase, self).get(request, *args, **kwargs)

    def has_audit_perms(self):
        return self.request.user.has_perm(self.audit_perms, self.object)

    def get_queryset(self):
        """
        must be overridden to ensure self.queryset is instantiated before
        calling this method via super()
        """
        show_deleted = self.request.GET.get('showdeleted', 0) == '1'
        order_by = self.request.GET.get('order-by', None)
        if not show_deleted or not self.has_audit_perms():
            self.queryset = self.queryset.filter(version_superseded_time=None)
        if order_by in self.order_dict:
            self.order_by = order_by
            self.queryset = self.queryset.order_by(self.order_dict[order_by])
        return self.queryset

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureListViewBase, self).get_context_data(
            *args, **kwargs)
        if hasattr(self, 'order_by'):
            context['order_by'] = self.order_by
        context['totals'] = self.queryset.aggregate(
            total_takings=Sum('total_takings'),
            till_difference=Sum('till_difference'))
        return context


class OutletTillClosureListView(TillClosureListViewBase):
    template_name = 'cashup/outlet_tillclosure_list.html'
    context_object_name = 'outlet'
    permission_required = ['cashup.view_outlet', 'cashup.view_tillclosures_for_outlet']
    audit_perms = 'cashup.view_outlet_tillclosure_audit_trail'
    slug_url_kwarg = 'name'
    slug_field = 'name'

    def get_object(self, *args, **kwargs):
        return super(OutletTillClosureListView, self).get_object(
            queryset=self.request.user.profile.outlets.all(), *args, **kwargs)

    def get_queryset(self):
        self.queryset = TillClosure.audit_trail.filter(
            pk=F('identity'), outlet=self.object)
        return super(OutletTillClosureListView, self).get_queryset()


class PersonnelTillClosureListView(TillClosureListViewBase):
    template_name = 'cashup/personnel_tillclosure_list.html'
    context_object_name = 'personnel'
    permission_required = ['cashup.view_personnel_tillclosure_list']
    audit_perms = 'cashup.view_personnel_tillclosure_audit_trail'
    slug_url_kwarg = 'username'
    slug_field = 'user__username'

    def get_object(self, *args, **kwargs):
        return super(PersonnelTillClosureListView, self).get_object(
            queryset=Personnel.objects.all(), *args, **kwargs)

    def get_queryset(self):
        self.queryset = TillClosure.audit_trail.filter(
            pk=F('identity'), closed_by=self.object)
        return super(PersonnelTillClosureListView, self).get_queryset()


class TillClosureAuditTrailListView(LoginRequiredMixin, PermissionRequiredMixin,
                                                                DetailView):
    template_name = 'cashup/tillclosure_audit_trail_list.html'
    permission_required = 'cashup.view_tillclosure_audit_trail'
    model = TillClosure

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureAuditTrailListView, self).get_context_data(
            *args, **kwargs)
        tillclosure = context['object']
        context['outlet'] = tillclosure.outlet
        pk = tillclosure.pk
        audit_trail = TillClosure.audit_trail.filter(identity=pk)
        context['object_list'] = audit_trail
        return context


class TillClosureDetailView(LoginRequiredMixin, PermissionRequiredMixin,
                                                                DetailView):
    permission_required = 'cashup.view_tillclosure'
    queryset = TillClosure.audit_trail.filter(pk=F('identity'))

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureDetailView, self).get_context_data(
            *args, **kwargs)
        context['outlet'] = context['object'].outlet
        return context


class TillClosureAuditTrailDetailView(LoginRequiredMixin,
                                        PermissionRequiredMixin, DetailView):
    permission_required = 'cashup.view_tillclosure_audit_trail'
    template_name = 'cashup/tillclosure_audit_trail_detail.html'
    context_object_name = 'object'

    def get_object(self):
        pk = self.kwargs.get('pk')
        version = self.kwargs.get('version')
        return get_object_or_404(TillClosure.audit_trail, identity=pk,
            version_number=version)

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureAuditTrailDetailView, self).get_context_data(
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

    def form_valid(self, form):
        form.instance.updated_by = self.request.user.profile
        return super(TillClosureUpdateView, self).form_valid(form)


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
        form.instance.updated_by = self.request.user.profile
        return super(TillClosureCreateView, self).form_valid(form)

    def get_initial(self):
        return {
            'till_float': self.get_outlet().default_float
        }
