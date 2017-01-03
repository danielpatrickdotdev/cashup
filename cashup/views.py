from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Till, TillClosure


class TillUserMixin(LoginRequiredMixin):
    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

class TillListView(TillUserMixin, ListView):
    model = Till

    def get(self, *args, **kwargs):
        qs = self.get_queryset()
        if len(self.get_queryset()) == 1:
            till = qs.get()
            return HttpResponseRedirect(reverse('cashup_till_detail', args=[till.pk]))
        return super(TillListView, self).get(*args, **kwargs)


class TillDetailView(TillUserMixin, DetailView):
    model = Till


class TillClosureUserMixin(LoginRequiredMixin):
    def get_queryset(self):
        return self.model.objects.filter(till__user=self.request.user)


class TillClosureListView(TillClosureUserMixin, ListView):
    model = TillClosure

    def get_context_data(self, *args, **kwargs):
        context = super(TillClosureListView, self).get_context_data(*args, **kwargs)
        if hasattr(self, 'till'):
           context['till'] = self.till
        return context

    def get_queryset(self):
        qs = super(TillClosureListView, self).get_queryset()
        pk = self.kwargs.pop('pk', None)
        if pk:
            self.till = get_object_or_404(Till, pk=pk)
            if self.till.user != self.request.user:
                raise Http404('TillClosure does not exist')
            qs.filter(till=self.till)
        return qs


class TillClosureDetailView(TillClosureUserMixin, DetailView):
    model = TillClosure


class TillClosureFormMixin(TillClosureUserMixin):
    model = TillClosure
    fields = ['till', 'close_time', 'cash_takings', 'card_takings',
              'note_50GBP', 'note_20GBP', 'note_10GBP', 'note_5GBP',
              'coin_2GBP', 'coin_1GBP', 'coin_50p', 'coin_20p',
              'coin_10p', 'coin_5p', 'coin_2p', 'coin_1p', 'till_float',
              'notes']

class TillClosureUpdateView(TillClosureFormMixin, UpdateView):
    pass

class TillClosureCreateView(TillClosureFormMixin, CreateView):
    pass
