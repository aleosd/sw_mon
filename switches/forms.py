from django import forms
from datetimewidget.widgets import DateTimeWidget
from .models import Event


class DTForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = ['ev_type', 'ev_comment', 'ev_switch', 'ev_event']
        date_time_options = {
            'format': 'dd-mm-yyy',
            'autoclose': 'true',
            }
        widgets = {
            'ev_datetime': DateTimeWidget(attrs={'id':"ev_datetime",
                                                 'style':"width: 130px;"},
                                          options=date_time_options)
        }

