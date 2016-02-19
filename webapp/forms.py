import datetime
from django import forms
from django.forms.formsets import formset_factory
from django.contrib.admin import widgets
from django.forms.extras.widgets import SelectDateWidget
from django.forms.widgets import Select
from neemi.models import *
from mongoengine.django.auth import User

SERVICE_CHOICES=(('facebook','Facebook'),
                 ('foursquare','foursquare'),
                 ('twitter','Twitter'),
                 ('linkedin','LinkedIn'),
                 ('gmail','Gmail'), 
                 ('gcal','Google Calendar'),
                 ('googleplus', 'Google+'),
                 ('googlecontacts', 'Google Contacts'),
                 ('dropbox','Dropbox'),
                 ('firefoxHistory','Firefox History'),
                 ('firefoxSearchHistory','Firefox Search History'),
                 ('chromeHistory', 'Chrome History'),
                 ('chromeSearchHistory', 'Chrome Search History')
                )

REGISTER_CHOICES=(('facebook','Facebook'),
                 ('foursquare','foursquare'),
                 ('twitter','Twitter'),
                 ('linkedin','LinkedIn'),
                 ('gmail','Gmail'), 
                 ('gcal','Google Calendar'),
                 ('googleplus', 'Google+'),
                 ('googlecontacts', 'Google Contacts'),
                 ('dropbox','Dropbox'),
                )


class GetDataForm(forms.Form):
    service = forms.ChoiceField(label="Service",choices=SERVICE_CHOICES)
    #from_date = forms.DateField(label="From (optional)",widget=SelectDateWidget(years=range(2013,2005,-1)),required=False)
    #to_date = forms.DateField(label="To (optional)",widget=SelectDateWidget(years=range(2013,2005,-1)),required=False)
    #lastN = forms.IntegerField(label="Result limit (optional)", required=False)

class KeywordSearchForm(forms.Form):
    service = forms.ChoiceField(label="Service",choices=SERVICE_CHOICES)
    keyword = forms.CharField(label="Search",required=True)

class PhotoSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user=kwargs.pop('user', None)
        super(PhotoSelectionForm, self).__init__(*args, **kwargs)
        if self.user:
            currentuser = User.objects.get(username=self.user.username)
            self.fields['photo'] = forms.ModelChoiceField(label="Photo ID", queryset=FacebookData.objects(neemi_user=currentuser.id, data_type='PHOTO'))#, to_field_name='id')

