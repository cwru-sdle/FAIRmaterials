import os
import tempfile
import pytest
import rdflib
import graphviz
from FAIRmaterials.rdflib_graph_saver import RDFLibGraphSaver
from graphviz import backend as gv_backend

@pytest.fixture
def rdflib_graph():
    graph = rdflib.Graph()
    graph.add((rdflib.URIRef("http://example.org/subject"),
               rdflib.URIRef("http://example.org/predicate"),
               rdflib.URIRef("http://example.org/object")))
    graph.add((rdflib.URIRef("http://example.org/ontology"),
               rdflib.RDF.type,
               rdflib.OWL.Ontology))
    graph.add((rdflib.URIRef("http://example.org/ontology"),
               rdflib.URIRef("http://purl.org/dc/terms/title"),
               rdflib.Literal("Example Ontology")))
    return graph

@pytest.fixture
def empty_rdflib_graph():
    return rdflib.Graph()

@pytest.fixture
def graphviz_graph():
    graph = graphviz.Digraph()
    graph.node('A')
    graph.node('B')
    graph.edge('A', 'B')
    return graph

@pytest.fixture
def empty_graphviz_graph():
    return graphviz.Digraph()

@pytest.fixture
def saver(rdflib_graph, graphviz_graph):
    return RDFLibGraphSaver("test_ontology", rdflib_graph, graphviz_graph)

@pytest.fixture
def empty_saver(empty_rdflib_graph, empty_graphviz_graph):
    return RDFLibGraphSaver("empty_ontology", empty_rdflib_graph, empty_graphviz_graph)

def test_save_rdflib_graph_owl_valid(saver):
    file_path = saver.save_rdflib_graph_owl()
    assert os.path.exists(file_path)
    assert file_path.endswith(".ttl")
    with open(file_path, "r") as f:
        content = f.read()
        assert "ns1:subject" in content

def test_save_rdflib_graph_owl_empty(empty_saver):
    with pytest.raises(ValueError):
        empty_saver.save_rdflib_graph_owl()

def test_save_rdflib_graph_jsonld_valid(saver):
    file_path = saver.save_rdflib_graph_jsonld()
    assert os.path.exists(file_path)
    assert file_path.endswith(".json")
    with open(file_path, "r") as f:
        content = f.read()
        assert "@context" in content

def test_save_rdflib_graph_jsonld_empty(empty_saver):
    with pytest.raises(ValueError):
        empty_saver.save_rdflib_graph_jsonld()

def test_save_graphviz_graph_valid(saver):
    output_folder = f"{saver._RDFLibGraphSaver__ontology_name}_output"
    file_path = os.path.join(output_folder, "test_ontologyGraph.png")
    saver.save_graphviz_graph()
    assert os.path.exists(file_path)

def test_save_graphviz_graph_valid_empty(empty_saver):
    with pytest.raises(gv_backend.ExecutableNotFound):
        empty_saver.save_graphviz_graph()

def test_generate_pylode_html_valid(saver):
    file_path = saver.generate_pylode_html()
    assert os.path.exists(file_path)
    assert file_path.endswith(".html")
    with open(file_path, "r") as f:
        content = f.read()
        assert "<html>" in content

def test_generate_pylode_html_empty(empty_saver):
    with pytest.raises(ValueError):
        empty_saver.generate_pylode_html()
