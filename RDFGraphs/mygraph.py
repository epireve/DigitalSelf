import io
import os
import subprocess

import rdflib
from rdflib import RDF, RDFS
import rdflib.tools.rdf2dot


schema = rdflib.namespace.Namespace('http://schema.org/')
my = rdflib.namespace.Namespace('custom/')

tmp = 'tmp'



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


    def elaborate_my_types(self):
        if (None, None, my.Event) in self:
            self.add(my.Event, RDFS.subClassOf, schema.Event)
        if (None, None, my.Photograph) in self:
            self.add(my.Photograph, RDFS.subClassOf, schema.Photograph)


    def draw(self, name='default'):
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

