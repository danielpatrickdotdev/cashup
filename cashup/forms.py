from django import forms

from .models import Outlet, StaffPosition, Personnel


class OutletForm(forms.ModelForm):
    def full_clean(self):
        super(OutletForm, self).full_clean()
        try:
            self.instance.validate_unique()
        except forms.ValidationError:
            self._update_errors("You already have an outlet with that name")

    class Meta:
        model = Outlet
        fields = ['name', 'default_float']

class StaffPositionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        if 'initial' in kwargs and 'personnel' in kwargs['initial']:
            self.personnel_name = Personnel.objects.get(
                pk=kwargs['initial']['personnel'])
        elif 'instance' in kwargs:
            self.personnel_name = kwargs['instance'].personnel.name
        super(StaffPositionForm, self).__init__(*args, **kwargs)

    def full_clean(self):
        super(StaffPositionForm, self).full_clean()
        if not self.is_bound:
            return
        p = self.cleaned_data.get('personnel', None)
        o = self.cleaned_data.get('outlet', None)
        if p and o and p.business != o.business:
            self._update_errors("Invalid staff choice for business")


    class Meta:
        model = StaffPosition
        fields = ['personnel', 'is_manager', 'is_staff']

StaffFormSet = forms.inlineformset_factory(Outlet, StaffPosition,
                                           form=StaffPositionForm)
