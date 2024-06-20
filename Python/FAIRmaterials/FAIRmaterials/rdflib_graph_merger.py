from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, OWL, DCTERMS
import warnings

class RDFLibGraphMerger:
    """
    A class to merge RDFLib graphs (ontologies) and add ownership metadata.

    Methods:
        merge_ontologies(ontology_one, ontology_two): Merges two RDF graphs and removes specific triples.
        add_ontology_ownership(merged_graph, base_uri, ontology_title, ontology_version, ontology_authors=[]): Adds ownership metadata to the merged ontology graph.
    """

    @staticmethod
    def merge_ontologies(ontology_one, ontology_two):
        """
        Merges two RDF graphs (ontologies) and removes any triples with subjects containing "#Ontology".

        Args:
            ontology_one (rdflib.Graph): The first ontology to merge.
            ontology_two (rdflib.Graph): The second ontology to merge.

        Returns:
            rdflib.Graph: The merged ontology graph with specific triples removed.
        """
        # Merge the graphs
        merged_graph = ontology_one + ontology_two

        # Loop through RDF triples
        for subject, predicate, object_ in merged_graph:
            # Check if the subject contains "/Ontology"
            if "#Ontology" in str(subject):
                # Remove the triple from the graph
                merged_graph.remove((subject, predicate, object_))

        unique_subjects = {}
        # base_uri: xrdtool and xrdrecipe
        # argument: measurement
        for s, p, o in merged_graph:
            if '#' in s:
                base_uri, argument = s.split('#')
            else:
                base_uri, argument = s.rsplit('/', 1)

            if argument in unique_subjects and unique_subjects[argument] != base_uri:
                warnings.warn("There is already an existing RDF triple with the same Ontology label {}".format(s))
            else:
                unique_subjects[argument] = base_uri

        return merged_graph

    @staticmethod
    def add_ontology_ownership(merged_graph, base_uri, ontology_title, ontology_version, ontology_description):
        """
        Adds ownership metadata to the merged ontology graph.

        Args:
            merged_graph (rdflib.Graph): The merged ontology graph.
            base_uri (str): The base URI for the ontology.
            ontology_title (str): The title of the ontology.
            ontology_version (float): The version of the ontology.
            ontology_description (str): A description of the ontology.

        Returns:
            rdflib.Graph: The ontology graph with ownership metadata added.
        """
        if ontology_title is None:
            ontology_title = "merged_ontology"
        if base_uri is None:
            base_uri = "https://mergedontology#"
        if ontology_version is None:
            ontology_version = "1.0"
        if ontology_description is None:
            ontology_description = "This is the merged ontology of all the input sheets"

        ontology_namespace = Namespace(base_uri)
        merged_graph.bind(ontology_title, ontology_namespace)

        merged_graph.add((ontology_namespace.Ontology, RDF.type, OWL.Ontology))

        merged_graph.add((ontology_namespace.Ontology, DCTERMS.title, Literal(ontology_title)))

        merged_graph.add((ontology_namespace.Ontology, DCTERMS.hasVersion, Literal(ontology_version)))
        merged_graph.add((ontology_namespace.Ontology, OWL.versionInfo, Literal(ontology_version)))

        merged_graph.add((ontology_namespace.Ontology, DCTERMS.description, Literal(ontology_description)))

        # for author in ontology_authors:
        #     merged_graph.add((ontology_namespace.Ontology, DCTERMS.creator, Literal(author)))

        return merged_graph