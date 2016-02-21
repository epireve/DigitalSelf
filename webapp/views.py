from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from forms import GetDataForm, KeywordSearchForm, REGISTER_CHOICES, DocumentSelectionForm, FBPhotoCreateForm, FBEventCreateForm
from neemi.data import get_user_data, get_all_user_data, getFacebookProfile
from neemi.search import simple_keyword_search
from neemi.stats import *
from neemi.models import *
from django.utils.dateparse import parse_datetime
import time, datetime, random, string
from mongoengine.base import BaseDict
from RDFGraphs.mygraph import MyGraph

def index(request, template='index.html'):

    response = render_to_response(
            template, locals(), context_instance=RequestContext(request)
        )
    return response

def register(request, template='register.html'):
    services = REGISTER_CHOICES
    response = render_to_response(
            template, locals(), context_instance=RequestContext(request)
        )
    return response

def search(request, template='search.html'):

    if request.method == 'POST':
        form = KeywordSearchForm(request.POST)
        if form.is_valid():
            print [form.data]
            print "GOOD DATA"
            print [form.cleaned_data]
            return simple_keyword_search(request=request,
                                         keyword=form.cleaned_data['keyword'],
                                         service=form.cleaned_data['service'])
        else:
            print "invalid form"
            dform = form
    else:
        dform = KeywordSearchForm()
        
    response = render_to_response(
    template, locals(), context_instance=RequestContext(request,{'form':dform})
        )
    return response

def contextualize(request, template='contextualize.html'):
    user = request.user
    if request.method == 'POST':
        form = DocumentSelectionForm(request.POST, user=user)
        if form.is_valid():
            currentuser = User.objects.get(username=request.user.username)
            doc = form.cleaned_data['document'] #FacebookData
            g = MyGraph()
            #if doc.data_type == "PHOTO":
            #    g.parse_photo(doc)
            if doc.data_type == "EVENT":
                g.parse_event(doc)
            otherphotos=FacebookData.objects(neemi_user=currentuser.id, idr__ne=doc.idr, data_type='PHOTO')
            otherevents=FacebookData.objects(neemi_user=currentuser.id, idr__ne=doc.idr, data_type='EVENT')
            for photo in otherphotos:
                if 'backdated_time' in photo.data:
                    time = parse_datetime(photo.data['backdated_time'])
                    if g.relevantDate(time):
                        p=MyGraph()
                        p.parse_photo(photo)
                        g.absorb_photograph(p)
            # for event in otherevents:
            #     if 'start_time' in event.data:
            #         time = parse_datetime(photo.data['backdated_time'])
            #         if g.relevantDate(time):
            #             e=MyGraph()
            #             e.parse_event(event)
            #             g.absorb_event(e)
            g.draw(name=doc.data['id'], lighten_types=True)
            dform = form
        else:
            print "invalid form"
            dform = DocumentSelectionForm()
    else:
        dform = DocumentSelectionForm(user=user)
    response = render_to_response(
        template, locals(), context_instance=RequestContext(request,{'form':dform})
        )
    return response

def add_fb_photo(request, template='add_fb_photo.html'):
    user = request.user
    if request.method == 'POST':
        form = FBPhotoCreateForm(request.POST, user=user)
        if form.is_valid():
            service_user = getFacebookProfile(request=request)
            currentuser = User.objects.get(username=request.user.username)
            data = form.cleaned_data
            if data['photoId']:
                photoId = data['photoId']
            else:
                photoId = ''.join(random.choice(string.digits) for _ in range(10))
            idr = 'photo:%s@facebook/photos#DUMMY%s' % (service_user.userid, photoId)
            backdated_time = data['backdatedDateTime'].strftime("%Y-%m-%dT%H:%M:%S+0000")
            granularity = data['backdatedDateTimeGranularity']
            if data['createdDateTime']:
                created_time=data['createdDateTime'].strftime("%Y-%m-%dT%H:%M:%S+0000")
            else:
                created_time=backdated_time
            caption = data['caption']
            try:
                fbprofile=FacebookData.objects.get(data_type='PROFILE', neemi_user=currentuser.id,idr = 'profile:%s@facebook'%(service_user.userid))
                me = fbprofile.data['name']
            except FacebookData.DoesNotExist:
                me = "me"
            if data['uploadedBy'] and data['uploadedBy'] != "Me":
                uploaded_by = data['uploadedBy']
            else:
                uploaded_by = me
            from_dict = dict([('id', "DUMMY"), ('name', uploaded_by)])
            tagsdata = []
            if data['tags']:
                for tag in data['tags'].split(','):
                    if tag=="Me":
                        tagdict = dict([('id', "DUMMY"),('name', me)])
                    else:
                        tagdict = dict([('id', "DUMMY") ,('name', tag)])
                    tagsdata.append(tagdict)
            tags=dict([('data', tagsdata)])
            event=None
            if data['event']:
                event = dict([('data', data['event']['data'])]) #doesn't work
            location_fields = ("name", "street", "zip", "city", "state", "country", "latitude", "longitude")
            location = dict()
            for field in location_fields:
                if data[field]:
                    location[field]=data[field]
            if location["name"]:
                place = dict([('id', "DUMMY"), ('name', location['name']), ('location', location)])
            else:
                place = dict([('id', "DUMMY"), ('location', location)])
            photodata = dict([('backdated_time', backdated_time), ('backdated_time_granularity', granularity), ('created_time', created_time), ('from', from_dict),('id', ("DUMMY" + photoId)),('tags', tags), ('name', caption)])
            if location:
                photodata['place']=place
            newphoto = FacebookData(idr=idr, data=photodata, neemi_user=currentuser, facebook_user=service_user, data_type='PHOTO', time=datetime.datetime.today()).save()

            # #TESTING
            # g = MyGraph()
            # g.parse_photo(newphoto)
            # print(g.serialize(format='n3'))
            # g.draw(name="truc", lighten_types=True)

            dform = form
        else:
            print "invalid form"
            dform = FBPhotoCreateForm()
    else:
        dform = FBPhotoCreateForm(user=user)
    response = render_to_response(template, locals(), context_instance=RequestContext(request,{'form':dform})
        )
    return response

def add_fb_event(request, template='add_fb_event.html'):
    if request.method == 'POST':
        form = FBEventCreateForm(request.POST)
        if form.is_valid():
            service_user = getFacebookProfile(request=request)
            currentuser = User.objects.get(username=request.user.username)
            data = form.cleaned_data
            if data['eventId']:
                eventId = data['eventId']
            else:
                eventId = ''.join(random.choice(string.digits) for _ in range(10))
            idr = 'event:%s@facebook/events#DUMMY%s' % (service_user.userid, eventId)
            try:
                fbprofile=FacebookData.objects.get(data_type='PROFILE', neemi_user=currentuser.id,idr = 'profile:%s@facebook'%(service_user.userid))
                me = fbprofile.data['name']
            except FacebookData.DoesNotExist:
                me = "me"
            if data['owner'] != "Me":
                ownername = data['owner']
            else:
                ownername = me
            owner = dict([('id', 'DUMMY'), ('name', ownername)])
            attendingdata = []
            if data['attending']:
                for guest in data['attending'].split(','):
                    if guest=="Me":
                        guestdict = dict([('id', "DUMMY"),('name', me)])
                    else:
                        guestdict = dict([('id', "DUMMY") ,('name', guest)])
                    attendingdata.append(guestdict)
            attending=dict([('data', attendingdata)])
            startTime = data['startTime'].strftime("%Y-%m-%dT%H:%M:%S+0000")
            endTime = data['endTime'].strftime("%Y-%m-%dT%H:%M:%S+0000")
            rsvpStatus = data['rsvpStatus']
            name = data['eventName']
            description = data['description']
            location_fields = ("name", "street", "zip", "city", "state", "country", "latitude", "longitude")
            location = dict()
            for field in location_fields:
                if data[field]:
                    location[field]=data[field]
            if location["name"]:
                place = dict([('id', "DUMMY"), ('name', location['name']), ('location', location)])
            else:
                place = dict([('id', "DUMMY"), ('location', location)])
            eventdata=dict([('attending', attending),('owner', owner), ('start_time', startTime), ('end_time', endTime), ('rsvp_status',rsvpStatus),('id', ("DUMMY" + eventId)), ('name', name), ('description', description)])
            if location:
                eventdata['place']=place
            newevent = FacebookData(idr=idr, data = eventdata, neemi_user = currentuser, facebook_user = service_user, data_type='EVENT', time=datetime.datetime.today()).save()

            # #TESTING
            # g = MyGraph()
            # g.parse_event(newevent)
            # print(g.serialize(format='n3'))
            # g.draw(name="truc", lighten_types=True)

            dform = form
        else:
            print "invalid form"
            dform = FBEventCreateForm()
    else:
        dform = FBEventCreateForm()
    response = render_to_response(template, locals(), context_instance=RequestContext(request,{'form':dform})
        )
    return response

def query_results(request, template='results.html'):
    response = render_to_response(
            template, locals(), context_instance=RequestContext(request)
        )
    return response

def get_data(request, template='data.html'):
    
    if request.method == 'POST':
        form = GetDataForm(request.POST)
        if form.is_valid():
            print [form.data]
            print "GOOD DATA"
            print [form.cleaned_data]
            if 'bt_search' in form.data:
                return get_all_user_data(request=request,
                                         service=form.cleaned_data['service'])
            elif 'bt_get_data_since' in form.data:
                return get_user_data(request=request,
                                     service=form.cleaned_data['service'],
                                     from_date="since_last",
                                     to_date=None,
                                     lastN=None)
            else:
                if form.cleaned_data['from_date'] != None:
                    from_date_epoch=int(time.mktime(form.cleaned_data['from_date'].timetuple()))//1*1000
                else:
                    from_date_epoch = None

                if form.cleaned_data['to_date'] != None:
                    to_date_epoch=int(time.mktime(form.cleaned_data['to_date'].timetuple()))//1*1000
                else:
                    to_date_epoch=None
        
                return get_user_data(request=request,
                                     service=form.cleaned_data['service'],
                                     from_date=from_date_epoch,
                                     to_date=to_date_epoch,
                                     lastN=form.cleaned_data['lastN'])
        else:
            print "invalid form"
            dform = form
    else:
        dform = GetDataForm()
    response = render_to_response(
            template, locals(), context_instance=RequestContext(request,{'form':dform})
        )
    return response


def delete(request, template='delete.html'):
    response = render_to_response(
            template, locals(), context_instance=RequestContext(request)
        )
    return response

def get_stats(request, template='stats.html'):
    if request.method == 'GET':
        stats = DBAnalysis(request)
        html_stats = stats.basic_stats()   

    response = render_to_response(
            template, locals(), context_instance=RequestContext(request)
        )

#    response = render_to_response(template, locals(), context_instance=RequestContext(request),#{"html_stats":html_stats})

    return response

def error(request, template='error.html'):
    message = request.GET.get('message')
    print "Message: ", message
    response = render_to_response(
            template, locals(), context_instance=RequestContext(request)
        )
    return response


