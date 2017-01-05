from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Till, TillClosure


class TillDetailView(LoginRequiredMixin, DetailView):
    def get_object(self):
        return self.request.user.till


class TillClosureUserMixin(LoginRequiredMixin):
    model = TillClosure

    def get_queryset(self):
        return self.model.objects.filter(till__user=self.request.user)


class TillClosureListView(TillClosureUserMixin, ListView):
    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureListView, self).get_context_data(*args, **kwargs)
        context['till'] = getattr(self.request.user, 'till', None)
        return context


class TillClosureDetailView(TillClosureUserMixin, DetailView):
    pass


class TillClosureFormMixin(TillClosureUserMixin):
    fields = ['closed_by', 'close_time', 'cash_takings', 'card_takings',
              'note_50GBP', 'note_20GBP', 'note_10GBP', 'note_5GBP',
              'coin_2GBP', 'coin_1GBP', 'coin_50p', 'coin_20p',
              'coin_10p', 'coin_5p', 'coin_2p', 'coin_1p', 'till_float',
              'notes']


class TillClosureUpdateView(TillClosureFormMixin, UpdateView):
    pass


class TillClosureCreateView(TillClosureFormMixin, CreateView):
    def form_valid(self, form):
        form.instance.till = self.request.user.till
        return super(TillClosureFormMixin, self).form_valid(form)

    def get_initial(self):
        return {
            'till_float': self.request.user.till.default_float,
        }
