import pytest
from rdflib import Graph, Literal
from rdflib.namespace import RDF, OWL, DCTERMS
from FAIRmaterials.rdflib_graph_merger import RDFLibGraphMerger

@pytest.fixture
def ontology_one():
    g = Graph()
    g.add((Literal("http://example.org/subject1"), RDF.type, Literal("http://example.org/Object")))
    g.add((Literal("http://example.org/subject1#Ontology"), RDF.type, Literal("http://example.org/Object")))
    return g

@pytest.fixture
def ontology_two():
    g = Graph()
    g.add((Literal("http://example.org/subject2"), RDF.type, Literal("http://example.org/Object")))
    g.add((Literal("http://example.org/subject2#Ontology"), RDF.type, Literal("http://example.org/Object")))
    return g

def test_merge_ontologies(ontology_one, ontology_two):
    merged_graph = RDFLibGraphMerger.merge_ontologies(ontology_one, ontology_two)
    
    # Ensure that the triples with "#Ontology" are removed
    for subject, predicate, object_ in merged_graph:
        assert "#Ontology" not in str(subject)

    # Ensure that all other triples are present
    assert (Literal("http://example.org/subject1"), RDF.type, Literal("http://example.org/Object")) in merged_graph
    assert (Literal("http://example.org/subject2"), RDF.type, Literal("http://example.org/Object")) in merged_graph

def test_add_ontology_ownership(ontology_one):
    base_uri = "http://example.org/"
    ontology_title = "TestOntology"
    ontology_version = "1.0"
    ontology_description = "This is an example description"
    
    merged_graph = RDFLibGraphMerger.add_ontology_ownership(ontology_one, base_uri, ontology_title, ontology_version, ontology_description)

    ontology_namespace = base_uri + "Ontology"
    
    # Check if the ontology metadata is added
    assert (ontology_namespace, RDF.type, OWL.Ontology) in merged_graph
    assert (ontology_namespace, DCTERMS.title, Literal(ontology_title)) in merged_graph
    assert (ontology_namespace, DCTERMS.hasVersion, Literal(ontology_version)) in merged_graph
    assert (ontology_namespace, OWL.versionInfo, Literal(ontology_version)) in merged_graph
    assert (ontology_namespace, DCTERMS.description, Literal(ontology_description)) in merged_graph