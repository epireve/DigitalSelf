import time,datetime

from django.http import HttpResponseRedirect, HttpResponse

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User
from mongoengine.connection import get_db

from pymongo import MongoClient
from RDFGraphs.mygraph import MyGraph
from models import *
from django.utils.dateparse import parse_datetime
import datetime
from geopy.geocoders.googlev3 import *

def simple_keyword_search(request,keyword,service=None):
    url = '/search/'
    currentuser = User.objects.get(username=request.user.username)
    if service == 'facebook':
        mongo_db = get_db()
        print [mongo_db]
        #facebook_items = FacebookData.objects(data__message.contains(keyword))
        #facebook_items = FacebookData.objects(data_type='FEED')
        #facebook_items = mongo_db.command('text', 'facebook_data', search=keyword)
        #facebook_items = FacebookData.objects.command('text',
        facebook_items = FacebookData.objects(neemi_user=currentuser.id)
        for item in facebook_items:
            # print item
            print '----'
            if item.data_type=='PHOTO':
                print "Found a photo"
                if 'event' in item.data:
                    print "Photo has an associated event %s" % item.data['event']
                print item.data['created_time']
                if 'backdated_time' in item.data:
                    print "Backdated time :%s" %item.data['backdated_time']
                    #TESTING
                    p = MyGraph()
                    p.parse_photo(item)
                    #print(p.serialize(format='n3'))
                    p.draw(name="search_photo")
                    ep = p.eventFromPhotograph()
                    ep.draw('eventFromPhoto', True)
                related = related_to_fb_photo(request, item)
                print "Found %s related items" % len(related)
            elif item.data_type=='EVENT':
                e = MyGraph()
                e.parse_event(item)
                e.draw(name='search_event')
                print "Found an event"
            elif item.data_type=='FRIEND':
                print "Found friends"
            elif item.data_type=='ALBUM':
                print "Found an album"
            else:
                print item.data_type
            #print item._data['time']
            #if item._data.has_field('message'):
            #    print item.message
        #e.absorb_photograph(p)
        #e.draw('merge')
        e.absorb_event(ep)
        e.draw('absorb_event', True)
        results = facebook_items
    elif service=='gcal':
        gcal_items = GcalData.objects(neemi_user=currentuser.id)
        for item in gcal_items:
            print '----'
    else:
        results = None
    return HttpResponseRedirect(url)

def related_to_fb_photo(request, photo):
    related = set()
    related.add(photo)
    createdtime = parse_datetime(photo.data['created_time'])
    currentuser = User.objects.get(username=request.user.username)
    fbphotos = FacebookData.objects(neemi_user=currentuser.id, data_type='PHOTO')
    albumid = ""
    if photo.data['id'] == "DUMMY":
        print "Contextualizing mock photo"
    if 'album' in photo.data:
        print "Photo has an album"
        albumid = photo.data['album']['id']
        try:
            album = FacebookData.objects(data__id = albumid).get()
            related.add(album)
        except DoesNotExist:
            print "Album does not exist in database"
    for item in fbphotos:
        created_delta = parse_datetime(item.data['created_time']) - createdtime
        if abs(created_delta).days == 0 :
            related.add(item)
            print "Found related photo by created time"
        elif 'event' in item.data and 'event' in photo.data and photo.data['event']==item.data['event']:
            related.add(item).add(photo.data['event'])
            print "Found related photo by event, and related event"
        elif 'album' in item.data and item.data['album']['id']==albumid:
            related.add(item)
            print "Found related photo in the same album"
    return related
