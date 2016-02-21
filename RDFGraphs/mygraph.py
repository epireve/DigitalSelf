import io
import os
import subprocess

import rdflib
from rdflib import RDF, RDFS, BNode, Literal
import rdflib.tools.rdf2dot
from unidecode import unidecode
from django.utils.dateparse import parse_datetime

schema = rdflib.namespace.Namespace('http://schema.org/')
#my = rdflib.namespace.Namespace('custom/')
my = rdflib.namespace.Namespace('http://example.org/')

tmp = os.path.join(os.path.dirname(__file__), 'tmp')


unique_types = {
    schema.Person: schema.name,
    my.Photograph: my.idr,
}

common_types = [ schema.Text, schema.Date ]


class MyGraph(rdflib.Graph):
    def __init__(self, *args, **kwargs):
        rdflib.Graph.__init__(self, *args, **kwargs)
        self.bind("schema", schema)
        self.bind("my", my)
        self.mainnode = None

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
        if len(set(fblocation.keys()) & set(address_components)):
            if 'name' in fblocation:
                address=self.bnode(label=fblocation['name'])
            else:
                address=self.bnode(label="Location")
            self.add((address, RDF.type, schema.PostalAddress))
            self.add((place, schema.address, address))
            if 'street' in fblocation:
                streetAddress = Literal(fblocation['street'])
                self.add((streetAddress, RDF.type, schema.Text))
                self.add((address, schema.streetAddress, streetAddress))
            if 'zip' in fblocation:
                zip = Literal(fblocation['zip'])
                self.add((zip, RDF.type, schema.Text))
                self.add((address, schema.postalCode, zip))
            if 'city' in fblocation:
                city = Literal(fblocation['city'])
                self.add((city, RDF.type, schema.Text))
                self.add((address, schema.addressLocality, city))
            if 'state' in fblocation:
                state = Literal(fblocation['state'])
                self.add((state, RDF.type, schema.Text))
                self.add((address, schema.addressRegion, state))
            if 'country' in fblocation:
                country = Literal(fblocation['country'])
                self.add((country, RDF.type, schema.Text))
                self.add((address, schema.addressCountry, country))
        if 'latitude' in fblocation and 'longitude' in fblocation:
            geo = self.bnode(label="g")
            self.add((geo, RDF.type, schema.GeoCoordinates))
            self.add((place, schema.geo, geo))
            lat = Literal(fblocation['latitude'])
            lon = Literal(fblocation['longitude'])
            self.add((lat, RDF.type, schema.Number))
            self.add((lon, RDF.type, schema.Number))
            self.add((geo, schema.latitude, lat))
            self.add((geo, schema.longitude, lon))


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
                bn = self.bnode(label=unidecode(tag['name']))
                self.add((bn, RDF.type, schema.Person))
                name=Literal(unidecode(tag['name']))
                self.add((name, RDF.type, schema.Text))
                self.add((bn, schema.name, name))
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
            if FBLocation['name'] is not None:
                placeLabel = FBLocation['name']
            else:
                placeLabel = "Photo location"
            place = self.bnode(label=placeLabel)
            self.add((place, RDF.type, schema.Place))
            self.add((main, schema.contentLocation, place))
            self.enrich_place_with_fb_data(place, FBLocation)
        if 'from' in data:
            name = Literal(unidecode(data['from']['name']))
            self.add((name, RDF.type, schema.Text))
            uploader = self.bnode(label=unidecode(data['from']['name']))
            self.add((main, schema.publisher, uploader))
            self.add((uploader, schema.name, name))
            self.add((uploader, RDF.type, schema.Person))
        #if 'event' in data:
            #parse event ?
            #event node with id ?
        if 'name' in data:
            description = Literal(unidecode(data['name']))
            self.add((description, RDF.type, schema.Text))
            self.add((main, schema.description, description))

    # def parse_photo(self, photo):
    #     main = g.bnode(label=?)
    #     g.add(main, RDF.type, my.Photograph)
    #     if ... is not None:
    #         date = Literal(...) #backdated_time
    #         g.add(date, RDF.type, schema.Date)
    #         g.add(main, schema.dateCreated, date)
    #     schema.about(schema.Person): people present and maybe more
    #     schema.datePublished(schema.Date): created_time
    #     schema.dateModified(schema.Date): updated_time
    #     schema.contentLocation(schema.Place): place
    #     schema.publisher(schema.Person): from
    #     schema.recordedAt(my.Event) with its label?
    #     schema.description(schema.Text): name(caption)
    #     my.?(?): backdated_time_granularity
    #     my.dateCreatedGranularity(my.Granularity)

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
            name = Literal(unidecode(data['owner']['name']))
            self.add((name, RDF.type, schema.Text))
            owner = self.bnode(label=unidecode(data['owner']['name']))
            self.add((owner, schema.name, name))
            self.add((owner, RDF.type, schema.Person))
            self.add((main, schema.organizer, owner))
        if 'attending' in data:
            for guest in data['attending']['data']:
                bn = self.bnode(label=unidecode(guest['name']))
                self.add((bn, RDF.type, schema.Person))
                name=Literal(unidecode(guest['name']))
                self.add((name, RDF.type, schema.Text))
                self.add((bn, schema.name, name))
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
            if FBLocation['name'] is not None:
                placeLabel = FBLocation['name']
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





    def create_or_find_absorbed_node(self, g, n):
        if not isinstance(n, BNode):
            return n
        type = g.value(subject=n, predicate=RDF.type)
        if type in unique_types:
            id_prop = unique_types[type]
            id = g.value(subject=n, predicate=id_prop)
            #if (None, id_prop, id) in self:
            #    return self.value(predicate=id_prop, object=id)
            for subj in self.subjects(id_prop, id):
                if (subj, RDF.type, type) in self:
                    return subj
        return self.bnode()

    def absorb_node(self, g, subj):
        type = g.value(subject=subj, predicate=RDF.type)
        if type is schema.Place:
            pass #TODO
        nsubj = self.create_or_find_absorbed_node(g, subj)
        for (pred, obj) in g.predicate_objects(subj):
            nobj = self.absorb_node(g, obj)
            self.add((nsubj, pred, nobj))
            if ((pred == schema.publisher or pred == schema.about)
                    and (obj, RDF.type, schema.Person) in g
                    and (self.mainnode, RDF.type, my.Event) in self):
                self.add((self.mainnode, schema.attendee, nobj))
        return nsubj



    def relevantDate(self, datetime):
        #TODO
        return True

    def recordedIn(self, gph):
        #TODO
        return True


    # update graph representing an event using graph gph representing a photograph
    def absorb_photograph(self, gph):
        event = self.mainnode
        photo = gph.mainnode
        assert (event, RDF.type, my.Event) in self
        assert (photo, RDF.type, my.Photograph) in gph
        if not self.recordedIn(gph):
            return
        nphoto = self.absorb_node(gph, photo)
        self.add((event, schema.recordedIn, nphoto))
        self.add((nphoto, schema.recordedAt, event))



# We suppose that the publisher was at the event


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
        path_dot = os.path.join(tmp, name+'_dot')
        with io.open(path_dot, mode='w', newline='') as f:
            rdflib.tools.rdf2dot.rdf2dot(self, f)
        path_png = os.path.join(tmp, name+'.png')
        subprocess.call(["dot", "-Tpng", path_dot, "-o", path_png])


if __name__ == '__main__':
    # g = MyGraph()
    #g.parse(tmp+'/project_statement_example.n3', format='n3')
    #print(g.serialize(format='n3'))
    #g.draw('project_statement_example')
    pass
