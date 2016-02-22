import io
import os
import subprocess

import rdflib
from rdflib import RDF, RDFS, BNode, Literal
import rdflib.tools.rdf2dot
from unidecode import unidecode
from geopy.geocoders.googlev3 import GoogleV3
from django.conf import settings
from webapp.settings import GEOCODING_ID, MEDIA_ROOT
import string
from django.utils.dateparse import parse_datetime
from datetime import timedelta

schema = rdflib.namespace.Namespace('http://schema.org/')
#my = rdflib.namespace.Namespace('custom/')
my = rdflib.namespace.Namespace('http://example.org/')

#save_folder = os.path.join(os.path.dirname(__file__), 'tmp')
save_folder = MEDIA_ROOT

unique_types = {
    schema.Person: schema.name,
    my.Photograph: my.idr,
}

common_types = [ schema.Text, schema.Date, schema.Number, my.Granularity ]


def readDateLiteral(lit):
    date = lit.toPython()
    if isinstance(date, unicode):
        date = parse_datetime(date)
    return date

class MyGraph(rdflib.Graph):
    def __init__(self, *args, **kwargs):
        rdflib.Graph.__init__(self, *args, **kwargs)
        self.bind("schema", schema)
        self.bind("my", my)
        self.mainnode = None
        self.geocoder = None

    def bnode(self, label=None):
        bn = BNode()
        if label is not None:
            self.add((bn, RDFS.label, Literal(label)))
        return bn

    def bnode_find(self, type, id, label=None):
        assert type in unique_types
        id_prop = unique_types[type]
        if (None, id_prop, id) in self:
            return self.value(predicate=id_prop, object=id)
        return self.bnode(label=label)


    def enrich_place_with_fb_data(self, place, fblocation):
        address_components = ["street", "zip", "city", "state", "country"]
        if 'name' in fblocation:
            placeName=unidecode(fblocation['name'])
        else:
            placeName="Location"
        if len(set(fblocation.keys()) & set(address_components)):
            address=self.bnode(label=Literal(placeName))
            self.add((address, RDF.type, schema.PostalAddress))
            self.add((place, schema.address, address))
            if 'street' in fblocation:
                streetAddress = Literal(unidecode(fblocation['street']))
                self.add((streetAddress, RDF.type, schema.Text))
                self.add((address, schema.streetAddress, streetAddress))
            if 'zip' in fblocation:
                zip = Literal(unidecode(fblocation['zip']))
                self.add((zip, RDF.type, schema.Text))
                self.add((address, schema.postalCode, zip))
            if 'city' in fblocation:
                city = Literal(unidecode(fblocation['city']))
                self.add((city, RDF.type, schema.Text))
                self.add((address, schema.addressLocality, city))
            if 'state' in fblocation:
                state = Literal(unidecode(fblocation['state']))
                self.add((state, RDF.type, schema.Text))
                self.add((address, schema.addressRegion, state))
            if 'country' in fblocation:
                country = Literal(unidecode(fblocation['country']))
                self.add((country, RDF.type, schema.Text))
                self.add((address, schema.addressCountry, country))
        geo = self.bnode(label="g")
        self.add((geo, RDF.type, schema.GeoCoordinates))
        if 'latitude' in fblocation and 'longitude' in fblocation:
            lat = Literal(fblocation['latitude'])
            lon = Literal(fblocation['longitude'])
            self.add((lat, RDF.type, schema.Number))
            self.add((lon, RDF.type, schema.Number))
            self.add((geo, schema.latitude, lat))
            self.add((geo, schema.longitude, lon))
            self.add((place, schema.geo, geo))
            if 'street' not in fblocation:
                #reverse geocode
                if self.geocoder is None:
                    self.geocoder=GoogleV3(api_key=GEOCODING_ID)
                geoloc=self.geocoder.reverse((lat, lon),exactly_one=True)
                address = Literal(unidecode(geoloc.address))
                fullAddress = self.bnode(label=Literal("Full address"))
                self.add((fullAddress, RDF.type, schema.Text))
                self.add((place, schema.address, fullAddress))
        elif 'street' in fblocation:
            if self.geocoder is None:
                self.geocoder=GoogleV3(api_key=GEOCODING_ID)
            query = ''.join((fblocation[i] for i in address_components if i in fblocation))
            geoloc = self.geocoder.geocode(query)
            lat = Literal(geoloc.latitude)
            lon = Literal(geoloc.longitude)
            self.add((lat, RDF.type, schema.Number))
            self.add((lon, RDF.type, schema.Number))
            self.add((geo, schema.latitude, lat))
            self.add((geo, schema.longitude, lon))
            self.add((place, schema.geo, geo))


    def add_person(self, strname):
        name = Literal(strname)
        self.add((name, RDF.type, schema.Text))
        bn = self.bnode_find(schema.Person, name, label=strname)
        self.add((bn, RDF.type, schema.Person))
        self.add((bn, schema.name, name))
        return bn

    def parse_photo(self, photo):
        """
        :param photo: a FacebookData instance with data_type "PHOTO"
        :type photo: :class:`neemi.models.FacebookData`
        """

        data = photo.data
        main = self.bnode(label=unidecode(photo.__unicode__()))
        if self.mainnode is not None:
            raise Exception("Graph already parsed something")
        self.mainnode = main
        self.add((main, RDF.type, my.Photograph))
        idr = Literal(photo.idr)
        self.add((idr, RDF.type, schema.Text))
        self.add((main, my.idr, idr))
        if 'backdated_time' in data:
            date = Literal(data['backdated_time'])
            self.add((date, RDF.type, schema.Date))
            self.add((main, schema.dateCreated, date))
        if 'backdated_time_granularity' in data:
            granularity = Literal(data['backdated_time_granularity'])
            self.add((granularity, RDF.type, my.Granularity))
            self.add((main, my.dateCreatedGranularity, granularity))
        if 'tags' in data:
            for tag in data['tags']['data']:
                bn = self.add_person(unidecode(tag['name']))
                self.add((main, schema.about, bn))
        if 'created_time' in data:
            createdTime = Literal(data['created_time'])
            self.add((createdTime, RDF.type, schema.Date))
            self.add((main, schema.datePublished, createdTime))
        if 'updated_time' in data:
            updatedTime = Literal(data['updated_time'])
            self.add((updatedTime, RDF.type, schema.Date))
            self.add((main, schema.dateModified, updatedTime))
        if 'place' in data:
            FBLocation = data['place']['location']
            if 'name' in FBLocation:
                placeLabel = unidecode(FBLocation['name'])
            else:
                placeLabel = "Photo location"
            place = self.bnode(label=placeLabel)
            self.add((place, RDF.type, schema.Place))
            self.enrich_place_with_fb_data(place, FBLocation)
            self.add((main, schema.contentLocation, place))
        if 'from' in data:
            uploader = self.add_person(unidecode(data['from']['name']))
            self.add((main, schema.publisher, uploader))
        #if 'event' in data:
            #parse event ?
            #event node with id ?
        if 'name' in data:
            description = Literal(unidecode(data['name']))
            self.add((description, RDF.type, schema.Text))
            self.add((main, schema.description, description))

    #     schema.dateCreated(schema.Date): backdated_time
    #     schema.about(schema.Person): people present and maybe more
    #     schema.datePublished(schema.Date): created_time
    #     schema.dateModified(schema.Date): updated_time
    #     schema.contentLocation(schema.Place): place
    #     schema.publisher(schema.Person): from
    #     schema.recordedAt(my.Event) with its label?
    #     schema.description(schema.Text): name(caption)
    #     my.dateCreatedGranularity(my.Granularity): backdated_time_granularity

    def parse_event(self, event):
        """
        :param event: FacebookData document that has data_type 'EVENT'
        :type event: :class:`neemi.models.FacebookData`
        """
        data = event.data
        main = self.bnode(label=unidecode(event.__unicode__()))
        if self.mainnode is not None:
            raise Exception("Graph already parsed something")
        self.mainnode = main
        self.add((main, RDF.type, my.Event))
        idr = Literal(event.idr)
        self.add((idr, RDF.type, schema.Text))
        self.add((main, my.idr, idr))
        if 'owner' in data:
            owner = self.add_person(unidecode(data['owner']['name']))
            self.add((main, schema.organizer, owner))
        if 'attending' in data:
            for guest in data['attending']['data']:
                bn = self.add_person(unidecode(guest['name']))
                self.add((main, schema.attendee, bn))
        if 'start_time' in data:
            startTime = Literal(data['start_time'])
            self.add((startTime, RDF.type, schema.Date))
            self.add((main, schema.startDate, startTime))
        if 'end_time' in data:
            endTime = Literal(data['end_time'])
            self.add((endTime, RDF.type, schema.Date))
            self.add((main, schema.endDate, endTime))
        if 'place' in data:
            FBLocation = data['place']['location']
            if 'name' in FBLocation:
                placeLabel = unidecode(FBLocation['name'])
            else:
                placeLabel = "Event location"
            place = self.bnode(label=placeLabel)
            self.add((place, RDF.type, schema.Place))
            self.add((main, schema.location, place))
            self.enrich_place_with_fb_data(place, FBLocation)
        #photos ?
        if 'name' in data:
            name = Literal(unidecode(data['name']))
            self.add((name, RDF.type, schema.Text))
            self.add((main, schema.name, name))
        if 'description' in data:
            description = Literal(unidecode(data['description']))
            self.add((description, RDF.type, schema.Text))
            self.add((main, schema.description, description))

    # schema.attendee(schema.Person)
    # schema.endDate(schema.Date)
    # schema.location(schema.Place)
    # schema.organizer(schema.Person)
    # schema.recordedIn(schema.CreativeWork>my.Photograph)
    # schema.startDate(schema.Date)
    # schema.description(schema.Text)
    # schema.name(schema.Text)
    # my.startBefore(schema.Date)
    # my.endAfter(schema.Date)




    # def place_already_present(self, place, g):
    #     geo = g.value(place, schema.geo)
    #     if geo is not None:
    #         lo = g.value(geo, schema.longitude)
    #         la = g.value(geo, schema.latitude)
    #         for selfplace in self.objects(self.mainnode, schema.location):
    #             spgeo = self.value(selfplace, schema.geo)
    #             if spgeo is not None:
    #                 splo = self.value(spgeo, schema.longitude)
    #                 spla = self.value(spgeo, schema.latitude)
    #                 if lo == splo and la == spla:
    #                     return True
    #     return False
    #
    # def not_to_be_absorbed(self, n, g, ignored):
    #     if not(isinstance(n, BNode) or isinstance(n, Literal)):
    #         return
    #     if n in ignored:
    #         return
    #     ignored.add(n)
    #     for o in g.objects(n, None):
    #         self.not_to_be_absorbed(o, g, ignored)
    #
    # def places_not_to_be_absorbed(self, g):
    #     """
    #
    #     :type g: MyGraph
    #     """
    #     ignored = set()
    #     if g.isEventGraph():
    #         objects = g.objects(g.mainnode, schema.location)
    #     else:
    #         assert g.isPhotographGraph()
    #         objects = g.objects(g.mainnode, schema.contentLocation)
    #     for place in objects:
    #         if self.place_already_present(place, g):
    #             self.not_to_be_absorbed(place, g, ignored)
    #     return ignored

    def updateStartBefore(self, date):
        datelit = Literal(date)
        currentlit = self.value(self.mainnode, my.startBefore)
        if currentlit is not None:
            current = readDateLiteral(currentlit)
            if current <= date:
                return
            self.remove((self.mainnode, my.startBefore, None)) #NEW
        self.add((self.mainnode, my.startBefore, datelit))
        self.add((datelit, RDF.type, schema.Date))

    def updateEndAfter(self, date):
        datelit = Literal(date)
        currentlit = self.value(self.mainnode, my.endAfter)
        if currentlit is not None:
            print('currentlit',currentlit)
            print(currentlit.toPython())
            current = readDateLiteral(currentlit)
            if current >= date:
                return
            self.remove((self.mainnode, my.endAfter, None))  # NEW
        self.add((self.mainnode, my.endAfter, datelit))
        self.add((datelit, RDF.type, schema.Date))

    def handleDate(self, g, s, ns, p, o, no):
        date = readDateLiteral(o)
        if p == schema.dateCreated and g.isPhotographGraph:
            gran = str(g.value(g.mainnode, my.dateCreatedGranularity))
            if gran == "minute" or gran == "second":
                dmin = date
                dmax = date
            elif gran == "hour":
                dmin = date - timedelta(hours=1)
                dmax = date + timedelta(hours=1)
            elif gran == "day":
                dmin = date - timedelta(days=1)
                dmax = date + timedelta(days=1)
            else:
                raise Exception('Granularity value is '+gran)
            self.updateStartBefore(dmax)
            self.updateEndAfter(dmin)
        if g.isEventGraph():
            if p == my.startBefore:
                self.updateStartBefore(date)
            if p == my.endAfter:
                self.updateEndAfter(date)
            if p == schema.startDate or p == schema.endDate:
                self.add((ns, p, no))





    def find_or_create(self, n, map, g):
        if not isinstance(n, BNode):
            return n
        if n in map:
            return map[n]
        type = g.value(subject=n, predicate=RDF.type)
        if type in unique_types:
            id_prop = unique_types[type]
            id = g.value(subject=n, predicate=id_prop)
            for subj in self.subjects(id_prop, id):
                if (subj, RDF.type, type) in self:
                    map[n] = subj
                    return subj
        bn = self.bnode()
        map[n] = bn
        return bn

    def absorb_triples(self, g, map):
        #ignored = self.places_not_to_be_absorbed(g)
        for (s, p, o) in g:
            #if not (s in ignored):
            ns = self.find_or_create(s, map, g)
            no = self.find_or_create(o, map, g)
            if ((p == schema.publisher or p == schema.about)
                        and s == g.mainnode
                        and g.isPhotographGraph()
                        and self.isEventGraph()
                        and (o, RDF.type, schema.Person) in g):
                self.add((self.mainnode, schema.attendee, no))
            if (p == schema.contentLocation
                        and s == g.mainnode):
                self.add((self.mainnode, schema.location, no))
            if (o, RDF.type, schema.Date) in g and s == g.mainnode:
                self.handleDate(g, s, ns, p, o, no)
            else:
                self.add((ns, p, no))
        return map







    def relevantDate(self, datetime):
        assert self.isEventGraph()
        delta = timedelta(hours=12)
        sdlit = self.value(self.mainnode, schema.startDate)
        edlit = self.value(self.mainnode, schema.endDate)
        if sdlit is not None and edlit is not None:
            sd = readDateLiteral(sdlit)
            ed = readDateLiteral(edlit)
            if sd-delta <= datetime and datetime <= ed+delta:
                return True
        sblit = self.value(self.mainnode, my.startBefore)
        ealit = self.value(self.mainnode, my.endAfter)
        if sblit is not None and ealit is not None:
            sb = readDateLiteral(sblit)
            ea = readDateLiteral(ealit)
            if min(sb,ea) - delta <= datetime and datetime <= max(sb,ea) + delta:
                return True
        if sdlit is None and edlit is None and sblit is None and ealit is None:
            return True
        return False



    def recordedIn(self, gph):
        assert gph.isPhotographGraph()
        dlit = gph.value(gph.mainnode, schema.dateCreated)
        d = readDateLiteral(dlit)
        return self.relevantDate(d)

    def sameEvent(self, ge):
        assert ge.isEventGraph()
        for pred in [ schema.startDate, schema.endDate, my.startBefore, my.endAfter ]:
            lit = ge.value(ge.mainnode, pred)
            if lit is not None:
                d = readDateLiteral(lit)
                if self.relevantDate(d):
                    return True
        return False

    def isPhotographGraph(self):
        return (self.mainnode is not None) and (self.mainnode, RDF.type, my.Photograph) in self

    def isEventGraph(self):
        return (self.mainnode is not None) and (self.mainnode, RDF.type, my.Event) in self


    # update graph representing an event using graph gph representing a photograph
    def absorb_photograph(self, gph):
        assert self.isEventGraph()
        assert gph.isPhotographGraph()
        if not self.recordedIn(gph):
            return
        map = self.absorb_triples(gph, {})
        nphoto = map[gph.mainnode]
        event = self.mainnode
        self.add((event, schema.recordedIn, nphoto))
        self.add((nphoto, schema.recordedAt, event))

    def absorb_event(self, ge):
        assert self.isEventGraph()
        assert ge.isEventGraph()
        if not self.sameEvent(ge):
            return
        map = { ge.mainnode: self.mainnode }
        self.absorb_triples(ge, map)

    def eventFromPhotograph(self):
        assert self.isPhotographGraph()
        g = MyGraph()
        phlabel = self.value(subject=self.mainnode, predicate=RDFS.label)
        main = g.bnode('Event associated to '+phlabel)
        g.add((main, RDF.type, my.Event))
        g.mainnode = main
        g.absorb_photograph(self)
        return g

    def elaborate_my_types(self):
        if (None, None, my.Event) in self:
            self.add((my.Event, RDFS.subClassOf, schema.Event))
        if (None, None, my.Photograph) in self:
            self.add((my.Photograph, RDFS.subClassOf, schema.Photograph))


    def draw(self, name='default', lighten_types=False):
        if lighten_types:
            g = MyGraph()
            g += self
            for t in common_types:
                g.remove((None, RDF.type, t))
            g.draw(name=name)
            return
        path_dot = os.path.join(save_folder, name+'_dot')
        with io.open(path_dot, mode='w', newline='') as f:
            rdflib.tools.rdf2dot.rdf2dot(self, f)
        path_png = os.path.join(save_folder, name+'.png')
        subprocess.call(["dot", "-Tpng", path_dot, "-o", path_png])

    def save(self, name="default"):
        path = os.path.join(save_folder, name+'.n3')
        self.serialize(path, 'n3')


if __name__ == '__main__':
    g = MyGraph()
    g.parse(save_folder+'/project_statement_example.n3', format='n3')
    #print(g.serialize(format='n3'))
    #g.draw('project_statement_example')
    pass
