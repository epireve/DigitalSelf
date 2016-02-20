import datetime
from django import forms
from django.forms.formsets import formset_factory
from django.contrib.admin import widgets
from django.forms.extras.widgets import SelectDateWidget
from django.forms.widgets import Select
from neemi.models import *
from mongoengine.django.auth import User
from widgets import SplitSelectDateTimeWidget

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


class FBPhotoCreateForm(forms.Form):

    backdatedDateTime = forms.DateTimeField(label="Photo taken on", widget=SplitSelectDateTimeWidget(years=range(2016,2000,-1)))
    backdatedDateTimeGranularity = forms.ChoiceField(label="Granularity", choices=((i,i) for i in ("day", "hour", "minute", "second")),initial="hour")
    createdDateTime = forms.DateTimeField(label="Photo uploaded on (optional)", widget=SplitSelectDateTimeWidget(years=range(2016,2000,-1)))
    caption = forms.CharField(label="Caption", initial="Default caption")
    uploadedBy = forms.CharField(label="Uploaded by", initial="Me", required=False)
    tags = forms.CharField(label="Tagged users (comma separated)", required=False)
    name = forms.CharField(label="Location name", required=False)
    street = forms.CharField(label="Street adress", required=False)
    zip = forms.CharField(label="Zip code", required=False)
    city = forms.CharField(label="City", required=False)
    state = forms.CharField(label="State", required= False)
    country = forms.CharField(label="Country", required=False)
    latitude = forms.FloatField(label="Latitude", required=False)
    longitude = forms.FloatField(label="Longitude", required=False)

    #from : Dict(string id, string name (full name) )
    #tags['data'] : List(Dict('created_time', 'x', 'y', 'id', 'name' (full name)') 'paging'

    def __init__(self, *args, **kwargs):
        self.user=kwargs.pop('user', None)
        super(FBPhotoCreateForm, self).__init__(*args, **kwargs)
        if self.user:
            currentuser = User.objects.get(username=self.user.username)
            self.fields['event'] = forms.ModelChoiceField(label="Event", queryset=FacebookData.objects(neemi_user=currentuser.id, data_type='EVENT'), required=False)

class FBEventCreateForm(forms.Form):

    owner = forms.CharField(label="Owner", initial="Me")
    rsvpStatus = forms.ChoiceField(label="RSVP status", choices=((i,i) for i in ("attending", "unsure", "declined", "noreply")))
    eventName = forms.CharField(label="Name of the event")
    description = forms.CharField(label="Description", required=False)
    startTime = forms.DateTimeField(label="Start time", widget=SplitSelectDateTimeWidget(years=range(2016,2000,-1)))
    endTime = forms.DateTimeField(label="End time", widget=SplitSelectDateTimeWidget(years=range(2016,2000,-1)))
    name = forms.CharField(label="Location name", required=False)
    street = forms.CharField(label="Street adress", required=False)
    zip = forms.CharField(label="Zip code", required=False)
    city = forms.CharField(label="City", required=False)
    state = forms.CharField(label="State", required= False)
    country = forms.CharField(label="Country", required=False)
    latitude = forms.FloatField(label="Latitude", required=False)
    longitude = forms.FloatField(label="Longitude", required=False)
#owner : Dict( string id, string name (full name)
#rsvp_status : string 'attending'... ?
#start_time string
#id

#place : Dict (string id, string name, dict location : ( string city, country, street, zip, float latitude, longitude) ... cf API)