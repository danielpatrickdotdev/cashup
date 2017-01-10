from django import forms

from .models import Outlet


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

