import io
import os
import subprocess

import rdflib
from rdflib import RDF, RDFS
import rdflib.tools.rdf2dot


schema = rdflib.namespace.Namespace('http://schema.org/')
my = rdflib.namespace.Namespace('custom/')

tmp = os.path.join(os.path.dirname(__file__), 'tmp')

common_types = [ schema.Text, schema.Date ]


class MyGraph(rdflib.Graph):
    def __init__(self, *args, **kwargs):
        rdflib.Graph.__init__(self, *args, **kwargs)
        self.bind("schema", schema)
        self.bind("my", my)

    def bnode(self, label=None):
        bn = rdflib.BNode()
        if label is not None:
            g.add(bn, RDFS.label, label)
        return bn

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



    # schema.attendee(schema.Person)
    # schema.endDate(schema.Date)
    # schema.location(schema.Place)
    # schema.organizer(schema.Person)
    # schema.recordedIn(schema.CreativeWork>my.Photograph)
    # schema.startDate(schema.Date)
    # schema.description(schema.Text)
    # schema.name(schema.Text)
    # schema.duration(schema.Duration)?
    # my.startBefore(schema.Date)
    # my.endAfter(schema.Date)



    def add_person(self, name):
        namelit = rdflib.Literal(name)
        if (None, schema.name, namelit) in self:
            return self.value(predicate=schema.name, object=namelit)
        bn = self.bnode(label=name)
        self.add((bn, RDF.type, schema.Person))
        self.add((bn, schema.name, namelit))
        return bn

    # update graph representing an event using graph gph representing a photograph
    def absorb_photograph(self, gph):
        event = self.mainnode
        photo = gph.mainode
        assert (event, RDF.type, my.Event) in self
        assert (photo, RDF.type, my.Photograph) in gph
        self.add((photo, RDF.type, my.Photograph))
        self.add((event, schema.recordedIn, photo))
        # Persons
        for person in gph.objects(photo, schema.publisher):
            if (person, RDF.type, schema.Person) in gph:
                pnode = self.add_person(gph.value(subject=person, predicate=schema.name))
                self.add((event, schema.attendee, pnode))
        for person in gph.objects(photo, schema.about):
            if (person, RDF.type, schema.Person) in gph:
                pnode = self.add_person(gph.value(subject=person, predicate=schema.name))
                self.add((event, schema.attendee, pnode))
        # TODO


# We suppose that the publisher was at the event


    def elaborate_my_types(self):
        if (None, None, my.Event) in self:
            self.add(my.Event, RDFS.subClassOf, schema.Event)
        if (None, None, my.Photograph) in self:
            self.add(my.Photograph, RDFS.subClassOf, schema.Photograph)


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
    g = MyGraph()
    g.parse(tmp+'/project_statement_example.n3', format='n3')
    #print(g.serialize(format='n3'))
    g.draw('project_statement_example')

