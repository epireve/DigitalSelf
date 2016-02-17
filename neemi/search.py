import time,datetime

from django.http import HttpResponseRedirect, HttpResponse

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User
from mongoengine.connection import get_db

from pymongo import MongoClient

from models import *

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
            print item.time
            #print item._data['time']
            #if item._data.has_field('message'):
            #    print item.message
        results = facebook_items
    else:
        results = None
    return HttpResponseRedirect(url)
        
