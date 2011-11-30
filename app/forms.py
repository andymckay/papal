from datetime import datetime, timedelta
from django import forms
from app.models import PapalStats

class PapalForm(forms.Form):

    server = forms.ChoiceField(choices=[])
    level = forms.MultipleChoiceField(choices=[], required=False)
    start = forms.DateField(initial=datetime.today() - timedelta(days=7))
    end = forms.DateField(initial=datetime.today())

    def __init__(self, *args, **kw):
        super(PapalForm, self).__init__(*args, **kw)
        choices = [(p, p) for p in  PapalStats.objects.values_list('server', flat=True).distinct()]
        levels = sorted([(p, p) for p in  PapalStats.objects.values_list('level', flat=True).distinct()])
        levels.insert(0, ['', ''])
        self.fields['server'].choices = choices
        self.fields['level'].choices = levels

        for key, field in self.fields.items():
            # WTF twitter bootstrap?
            if key == 'level':
                continue
            field.widget.attrs = {'style':'height: 28px !important'}

    def clean_level(self):
        data = self.cleaned_data['level']
        if data and data == [u'']:
            return []
        return data

    def as_bootstrap(self):
        return self._html_output(u"""
        <div class="clearfix">
            %(label)s
            <div class="input">
             %(field)s%(help_text)s
            </div>
        </div>
        """, u'%s', '', u' %s', True)


class PapalDataForm(forms.ModelForm):

    class Meta:
        model = PapalStats
        fields = ('server', 'flag', 'date')
