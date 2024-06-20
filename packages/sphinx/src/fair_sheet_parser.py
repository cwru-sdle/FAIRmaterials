from rdflib import Graph as rdfGraph, Namespace, Literal, URIRef, OWL, XSD 
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS
from rdflib.extras.infixowl import Class, Ontology, Property, min, only, some
import subprocess
from rdflib.tools.rdf2dot import rdf2dot
import json
import io
import csv
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import networkx as nx
import matplotlib.pyplot as plt
import pydotplus
import pydot
import numpy as np
import graphviz
from IPython.display import display, Image
import argparse
from collections import defaultdict
import re
from owlready2 import get_ontology

class FairSheetParser:
    """
    FairSheetParser class for parsing FAIRSheet input data and generating RDF graphs.
    Attributes:
        __obj_property_path (str): Path to the CSV file containing object property definitions.
        __data_property_path (str): Path to the CSV file containing data property definitions.
        __namespace_path (str): Path to the CSV file containing namespace definitions.
        __entity_path (str): Path to the CSV file containing entity definitions.
        __values_path (str): Path to the CSV file containing values definitions.
        __datatype_conversions (dict): Mapping of XSD datatype strings to rdflib XSD objects.
        __ontology_name (str): Name of the ontology.
        __ontology_base_uri (Namespace): Base URI of the ontology.
        __include_valuetype_graphviz_edges (bool): Flag to include data type properties in the graphviz graph.
        __individual_relationship (dict): Dictionary storing individual relationships.
        __rdflib_graph (rdfGraph): RDFLib Graph object.
        __graphviz_graph (graphviz.Digraph): Graphviz Digraph object.
        __namespace_uris (dict): Dictionary mapping prefix names to ontology URLs.
        __entity_uris (dict): Dictionary mapping entity names to their URIs.
        __obj_property_uris (dict): Dictionary mapping object property names to their URIs.
        __data_property_uris (dict): Dictionary mapping data property names to their URIs.
        __values_uris (dict): Dictionary mapping ontology names to their base URIs.
    """

    def __init__(self, ontology_sheet_folder, include_valuetype_graphviz_edges):
        """
        Constructor method that initializes the FairSheetParser object.

        Args:
            ontology_name (str): Name of the ontology.
            ontology_base_uri (str): Base URI of the ontology.
            ontology_sheet_folder (str): Folder where the FAIRSheetInput CSV files are located.
            include_valuetype_graphviz_edges (bool): Flag to include data type properties in the graphviz graph.
        """

        # Set paths to CSV files and other attributes
        import glob
        ontology_info_path = next(iter(glob.glob(ontology_sheet_folder + "/*OntologyInfo.csv")))
        obj_property_path = next(iter(glob.glob(ontology_sheet_folder + "/*RelationshipDefinitions.csv")))
        data_property_path = next(iter(glob.glob(ontology_sheet_folder + "/*ValueTypeDefinitions.csv")))
        namespace_path = next(iter(glob.glob(ontology_sheet_folder + "/*NameSpace.csv")))
        entity_path = next(iter(glob.glob(ontology_sheet_folder + "/*VariableDefinitions.csv")))
        values_path = next(iter(glob.glob(ontology_sheet_folder + "/*Values.csv")))
        self.__ontology_info_path = ontology_info_path
        self.__obj_property_path = obj_property_path
        self.__data_property_path = data_property_path
        self.__namespace_path = namespace_path
        self.__entity_path = entity_path
        self.__values_path = values_path
        self.__datatype_conversions = {
            "xsd:integer": XSD.integer,
            "xsd:string": XSD.string,
            "xsd:date": XSD.date,
            "xsd:dateTime": XSD.dateTime,
            "xsd:float": XSD.float
        }

        # Initialize RDFLib Graph and Graphviz Digraph
        self.__rdflib_graph = rdfGraph()
        self.__graphviz_graph = graphviz.Digraph(strict=False)

        # Set ontology name, base URI, and other attributes
        with open(self.__ontology_info_path, 'r') as onto_info_file:
            csv_reader = csv.reader(onto_info_file)
            ontology_metadata = list(csv_reader)
            print(ontology_metadata[1][1])
            print(ontology_metadata[0][1])
            print(ontology_metadata[2][1])
            print(ontology_metadata[3][1])
            #Setting base URI of Ontology
            self.__ontology_base_uri = Namespace(ontology_metadata[1][1])
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, RDF.type, OWL.Ontology))
            #Setting Ontology Name in metadata
            self.__ontology_name = ontology_metadata[0][1]
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, RDFS.label, Literal(self.__ontology_name)))
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, DCTERMS.title, Literal(self.__ontology_name)))
            #Setting Version of ontology in ontoloy metadata
            self.__ontology_version = ontology_metadata[2][1]
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, DCTERMS.hasVersion, Literal(self.__ontology_version)))
            #Add authors to the ontology metadata
            authorsList = [author.strip() for author in ontology_metadata[3][1].split(",")]
            if authorsList[0] != "":
                for author in authorsList:
                    self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, DCTERMS.creator, Literal(author)))
            #Add Ontology description to ontology metadata
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, DCTERMS.description, Literal(ontology_metadata[4][1])))
        self.__include_valuetype_graphviz_edges = include_valuetype_graphviz_edges
        self.__individual_relationship = {}

        # Parse CSV files and populate dictionaries
        self.__namespace_uris = self.parse_namespace_csv()
        self.__entity_uris = self.parse_entity_csv()
        self.__obj_property_uris = self.parse_obj_prop_csv()
        self.__data_property_uris = self.parse_data_prop_csv()
        self.__values_uris = self.parse_values_csv()

    def parse_namespace_csv(self):
        """
        Method to parse the namespace CSV file and bind namespaces to the RDFLib graph.

        Returns:
            dict: Dictionary mapping prefix names to ontology URLs.
        """

        # Initialize an empty dictionary for namespace bindings
        namespace_dict = {}

        # Open the namespace CSV file and read its contents
        with open(self.__namespace_path, newline='') as namespace_file:
            csv_reader = csv.DictReader(namespace_file)
            next(csv_reader)
            # Iterate over each row in the CSV file
            for row in csv_reader:
                # Convert namespace prefix to lowercase
                prefix_name = row["Prefix Name"].lower()
                # Create a namespace binding and add it to the RDFLib graph
                namespace_dict[prefix_name] = Namespace(row["Ontology URL"])
                self.__rdflib_graph.bind(prefix_name, namespace_dict[prefix_name])
            # Bind the ontology name and base URI to the RDFLib graph    
            namespace_dict[self.__ontology_name] = self.__ontology_base_uri
            self.__rdflib_graph.bind(self.__ontology_name, self.__ontology_base_uri)
        return namespace_dict

    def parse_entity_csv(self):
        """
        Method to parse the entity CSV file and create RDF triples for entities.

        Returns:
            dict: Dictionary mapping entity names to their URIs.
        """

        # Initialize dictionary to store entity names and their URIs
        entitiesCreated = {}

        # Initialize dctionary to store entity data to process
        entities_to_process = defaultdict(list)
        
        pattern = r'[^\w\s]'

        # Open the entity CSV file for reading
        with open(self.__entity_path, newline='') as entity_file:
            csv_reader = csv.DictReader(entity_file)
            next(csv_reader)

            # Iterate over each row in the CSV file
            for row in csv_reader:
                # Extract entity details from the row
                entity = row['fullName']
                ontology_name = None

                # If no ontology is specified, use the ontology base URI                 
                if row["Belongs to Ontology"] == "":
                    ontology_namespace = self.__ontology_base_uri
                    entity_uri = ontology_namespace[Literal(entity)]
                # If an ontology is specified, use its namespace
                else:
                    ontology_namespace = self.__namespace_uris[row["Belongs to Ontology"].lower()]
                    entity_uri = ontology_namespace[Literal(entity.split(":")[1])]
                
                # Store entity data for processing
                entities_to_process[entity] = {
                        'name': row["Variable Name"],
                        'parent': row["Parent Variable"],
                        'definition': row["Definition of Variable"],
                        'alt_names': row["Alternative Name(s)"].strip().split(","),
                        'fullName': entity,
                        'unit': row["Unit"]
                    }

                # Store the entity name and its URI in the dictionary
                entitiesCreated[entity] = entity_uri
                
                # On a graphviz graph, creates a node for the parent entity (classes)
                self.__graphviz_graph.node(re.sub(pattern, '', entity_uri), label=row["Variable Name"], style = 'filled', color="lightblue")
        
            def dfs(entity, entities_to_process):
                """
                Depth-first search (DFS) function to process entities and their relationships.

                Args:
                    entity (dict): Dictionary representing the entity to process.
                    entities_to_process (dict): Dictionary containing entities to process.

                Returns:
                    str: Full name of the processed entity.
                """

                # Retrieve the URI of the entity from the entitiesCreated dictionary
                entity_uri = entitiesCreated[(entity["fullName"])]

                # Generate a unique identifier for the entity in the graphviz graph
                entity_graphviz_id = re.sub(pattern, '', entity_uri)

                # Create an identifier for the node representing the superclassOf relationship in the graphviz graph
                entity_subclassOf_box_id = "superclassOf" + entity_graphviz_id

                # Add RDF triples representing the entity as a class in the RDFLib graph
                self.__rdflib_graph.add((entity_uri, RDF.type, RDFS.Class))
                self.__rdflib_graph.add((entity_uri, RDFS.label, Literal(entity['name'])))

                # Add RDF triple representing the unit of the entity if it exists
                if entity['unit'] != "":
                    namespace_unit, unit_unit = entity['unit'].split(':')
                    unit_uri = self.__namespace_uris[(namespace_unit).lower()][unit_unit]
                    self.__rdflib_graph.add((entity_uri, URIRef("https://w3id.org/pmd/co/unit"), unit_uri))

                # Add RDF triples representing alternative names of the entity
                if entity['alt_names'][0] != "":
                    for altName in entity['alt_names']:
                        self.__rdflib_graph.add((entity_uri, SKOS.altLabel, Literal(altName)))

                # Add RDF triple representing the definition of the entity
                if entity['definition'] != "":
                    self.__rdflib_graph.add((entity_uri, SKOS.definition, Literal(entity['definition'])))
                        
                # Check if the entity has a parent and it exists in the entities to process
                if entity['parent'] != "" and (entities_to_process.__contains__(entity['parent'])):
                    dfs(entity['parent'], entities_to_process)
                    parent_uri = entitiesCreated[(entity['parent'])]
                    parent_graphviz_id = re.sub(pattern, '', parent_uri)
                    self.__rdflib_graph.add((entity_uri, RDFS.subClassOf, parent_uri))
                    # On a graphviz graph, creates a node for the child entity (subclasses)and edges representing the relationship
                    self.__graphviz_graph.node(entity_subclassOf_box_id, label="subclass of", color="darkblue", shape="box")
                    self.__graphviz_graph.edge(parent_graphviz_id, entity_subclassOf_box_id, style="dashed", dir="back")
                    self.__graphviz_graph.edge(entity_subclassOf_box_id, entity_graphviz_id, style="dashed", dir="none")

                # If the entity has a parent but it does not exist in the entities to process
                elif entity['parent'] != "":
                    parent_uri = entitiesCreated[entity["parent"]]
                    parent_graphviz_id = re.sub(pattern, '', parent_uri)
                    self.__rdflib_graph.add((entity_uri, RDFS.subClassOf, parent_uri))
                    # On a graphviz graph, creates a node for the child entity (subclasses)and edges representing the relationship
                    self.__graphviz_graph.node(entity_subclassOf_box_id, label="subclass of", color="darkblue", shape="box")
                    self.__graphviz_graph.edge(parent_graphviz_id, entity_subclassOf_box_id, style="dashed", dir="back")
                    self.__graphviz_graph.edge(entity_subclassOf_box_id, entity_graphviz_id, style="dashed", dir="none")
                
                # Remove the processed entity from the entities to process dictionary
                entities_to_process.pop(entity['fullName'])
                
                # Return the full name of the processed entity
                return entity['fullName']
                
                # if entity['unit'] != "": 
                #     pmd_value_uri = self.__namespace_uris["PMDCo"][Literal("value")]
                #     unit_class, unit_instance = entity['unit'].split(':')
                #     self.__rdflib_graph.add((pmd_value_uri, RDF.type, OWL.ObjectProperty))
                #     self.__rdflib_graph.add((entity['unit'], RDF.type, entity['unit']))
                #     self.__rdflib_graph.add((entity['unit'], RDF.type, entity['unit']))
                #     self.__rdflib_graph.add((entity['unit'], RDFS.domain, self.__entity_uris[row["Domain"]]))
                #     self.__rdflib_graph.add((entity['unit'], RDFS.range, self.__entity_uris[row["Range"]]))
            
            # Iterate over entities to process and call dfs for each entity
            for entity in list(entities_to_process.keys()):
                dfs(entities_to_process[entity], entities_to_process)

        # Return the dictionary containing processed entities and their URIs
        return entitiesCreated

    def parse_values_csv(self):
        """
        Method to parse the values CSV file.

        Returns:
            dict: Dictionary mapping ontology names to their base URIs.
        """

        values_dict = {}
        with open(self.__values_path, newline='') as values_file:
            csv_reader = csv.DictReader(values_file)
            count = 1
            existing_objects = {}
            column_vars = []
            column_obj_indices = []
            column_obj_start_index = 0
            column_obj_end_index = 0
            current_obj = None

            # Iterate over each column in the CSV file
            for column in csv_reader.fieldnames:
                # Extract domain and relationship from column header using regex patterns
                domain_pattern = r'\((.*?)\-\>'
                relationship_pattern = r'^([^()]*)'
                domain = re.search(domain_pattern, column).group(1)
                relationship = re.search(relationship_pattern, column).group(1)
                column_vars.append({'domain': domain, 'relationship': relationship})
                if current_obj is None:
                    current_obj = domain
                    column_obj_start_index = 0
                elif current_obj != domain:
                    column_obj_indices.append((column_obj_start_index, column_obj_end_index-1))
                    column_obj_start_index = column_obj_end_index
                column_obj_end_index += 1
            column_obj_indices.append((column_obj_start_index, column_obj_end_index-1))

            # Iterate over each row in the CSV file
            for row in csv_reader:
                curr_objects = {}
                row_keys = list(row.keys())
                row_values = list(row.values())

                # Iterate over each group of columns representing an object
                for i, j in column_obj_indices:
                    # Generate a unique hash for the object based on column variables and row data
                    object_hash = hash(str(column_vars[i:j+1]) + str(row_keys[i:j+1] + row_values[i:j+1]))
                    domain = column_vars[i]['domain']

                    # Check if the object already exists, if not, create a new RDF instance
                    if object_hash not in existing_objects:
                        entity_uri = self.__entity_uris[domain]
                        instance_key = URIRef(entity_uri + str(count))
                        self.__rdflib_graph.add((instance_key, RDF.type, URIRef(entity_uri)))
                        existing_objects[object_hash] = instance_key
                    else:
                        instance_key = existing_objects[object_hash]

                    # Add RDF triples for each property of the object
                    for index in range(i,j+1):
                        relationship_val = self.__data_property_uris[column_vars[index]['relationship']]
                        self.__rdflib_graph.add((URIRef(instance_key), URIRef(relationship_val), Literal(row_values[index])))
                    curr_objects[domain] = instance_key

                # Add RDF triples for relationships specified in __individual_relationship
                for domain in self.__individual_relationship.keys():
                    for relationshipRange, relationship in self.__individual_relationship[domain]:
                        if domain not in curr_objects.keys():
                            entity_uri = self.__entity_uris[domain]
                            instance_key = URIRef(entity_uri + str(count))
                            self.__rdflib_graph.add((instance_key, RDF.type, URIRef(entity_uri)))
                            curr_objects[domain] = instance_key
                        if relationshipRange not in curr_objects.keys():
                            entity_uri = self.__entity_uris[relationshipRange]
                            instance_key = URIRef(entity_uri + str(count))
                            self.__rdflib_graph.add((instance_key, RDF.type, URIRef(entity_uri)))
                            curr_objects[relationshipRange] = instance_key
                        self.__rdflib_graph.add((URIRef(curr_objects[domain]), relationship, URIRef(curr_objects[relationshipRange])))
                    
                count+=1

            # Add ontology name and base URI to the values dictionary
            values_dict[self.__ontology_name] = self.__ontology_base_uri

        return values_dict
    
    def save_rdflib_graph_owl(self):
        """
        Method to save the RDFLib graph to a file in TTL (Turtle) format.
        """

        with open((self.__ontology_name + ".owl"), "wb") as f:
            f.write(self.__rdflib_graph.serialize(format="ttl").encode('utf-8'))

    def save_rdflib_graph_jsonld(self):
        """
        Method to save the RDFLib graph to a file in JSON-LD format.
        """

        with open((self.__ontology_name + ".json"), "wb") as f:
            f.write(self.__rdflib_graph.serialize(format="json-ld").encode('utf-8'))

    def parse_obj_prop_csv(self):
        """
        Method to parse the object property CSV file.

        Returns:
            dict: Dictionary mapping object property names to their URIs.
        """

        pattern = r'[^\w\s]'
        with open(self.__obj_property_path, newline='') as obj_property_file:
            csv_reader = csv.DictReader(obj_property_file)
            next(csv_reader)

            obj_property_list = {}

            # Generate URI for the object property
            for row in csv_reader:
                obj_property_uri = self.__namespace_uris[self.__ontology_name][Literal(row["Relationship Name"])]
                graphviz_obj_prop_uri = re.sub(pattern, '', obj_property_uri + row["Domain"] + row["Range"])

                # Check if the object property belongs to a specific ontology
                if row["Belongs to Ontology"] == "" and (obj_property_uri not in obj_property_list.values()):
                    # Add RDF triples representing the object property
                    self.__rdflib_graph.add((obj_property_uri, RDF.type, OWL.ObjectProperty))
                    self.__graphviz_graph.node(graphviz_obj_prop_uri, label = row["Relationship Name"], color="darkblue", style = "filled", fontcolor="white", shape="box")
                    self.__rdflib_graph.add((obj_property_uri, RDFS.label, Literal(row["Relationship Name"])))
                    
                    if row["Definition"] != "":
                        self.__rdflib_graph.add((obj_property_uri, SKOS.definition, Literal(row["Definition"])))
                    
                    if row["Alternative Name(s)"] != "":
                        alternativeNamesList = row["Alternative Name(s)"].strip().split(",")
                        if alternativeNamesList[0] != "":
                            for altName in alternativeNamesList:
                                self.__rdflib_graph.add((obj_property_uri, SKOS.altLabel, Literal(altName)))

                    obj_property_list[row["fullName"]]=obj_property_uri
                    self.__rdflib_graph.add((obj_property_uri, RDF.type, OWL.ObjectProperty))

                # If the object property belongs to a specific ontology, use its namespace URI
                elif row["Belongs to Ontology"] != "" and (obj_property_uri not in obj_property_list.values()):
                    obj_property_uri = self.__namespace_uris[row["Belongs to Ontology"].lower()][Literal(row["Relationship Name"])]
                    graphviz_obj_prop_uri = re.sub(pattern, '', obj_property_uri + row["Domain"] + row["Range"])
                    self.__rdflib_graph.add((obj_property_uri, RDF.type, OWL.ObjectProperty))
                    self.__graphviz_graph.node(graphviz_obj_prop_uri, label = row["Relationship Name"], color="darkblue", style = "filled", fontcolor="white", shape="box")
                    obj_property_list[row["fullName"]]=obj_property_uri
                elif row["Belongs to Ontology"] != "":
                    obj_property_uri = self.__namespace_uris[row["Belongs to Ontology"]][Literal(row["Relationship Name"])]
                    graphviz_obj_prop_uri = re.sub(pattern, '', obj_property_uri + row["Domain"] + row["Range"])

                # Adds triples representing the domain and range of the object property 
                self.__rdflib_graph.add((obj_property_uri, RDFS.domain, self.__entity_uris[row["Domain"]]))
                self.__rdflib_graph.add((obj_property_uri, RDFS.range, self.__entity_uris[row["Range"]]))

                # Store individual relationships for further processing
                if row["Domain"] not in self.__individual_relationship:
                    self.__individual_relationship[row["Domain"]] = []
                self.__individual_relationship[row["Domain"]] += [(row["Range"], obj_property_uri)]

                # On a graphviz graph, creates a node for the object property and edges connecting it representing relationships between entities
                graphviz_domain = re.sub(pattern, '', self.__entity_uris[row["Domain"]])
                graphviz_range = re.sub(pattern, '', self.__entity_uris[row["Range"]])
                self.__graphviz_graph.edge(graphviz_domain, graphviz_obj_prop_uri, style="bold", dir="none")
                self.__graphviz_graph.edge(graphviz_obj_prop_uri,graphviz_range, style="bold", dir="forward")
            
        return obj_property_list

    def save_graphviz_graph(self):
        """
        Method to save the Graphviz graph visualization.
        """

        if len(self.__graphviz_graph.body) == 0:
            # Raise an exception if the graph is empty
            raise graphviz.exceptions.GraphvizError("The graph is empty and cannot be printed")
        else:
            print("Hi")
            # Render the graph to a PNG file with the ontology name and clean up intermediate files
            # self.__graphviz_graph.render(self.__ontology_name + "Graph", format="png", cleanup=True)


    def parse_data_prop_csv(self):
        """
        Method to parse the data property CSV file.

        Returns:
            dict: Dictionary mapping data property names to their URIs.
        """

        pattern = r'[^\w\s]'
        with open(self.__data_property_path, newline='') as data_property_file:
            csv_reader = csv.DictReader(data_property_file)
            next(csv_reader)

            data_property_list = {}

            for row in csv_reader:
                # Generate URI for the data property
                data_property_uri = self.__namespace_uris[self.__ontology_name][Literal(row["ValueType Name"])]
                graphviz_data_prop_uri = re.sub(pattern, '', data_property_uri + row["Domain"] + row["Range"])

                # If conditions met, adds triples representing the data property with its type, label, definition, and alternative names
                if row["Belongs to Ontology"] == "" and (data_property_uri not in data_property_list.values()):
                    self.__rdflib_graph.add((data_property_uri, RDF.type, OWL.DatatypeProperty))
                    self.__rdflib_graph.add((data_property_uri, RDFS.label, Literal(row["ValueType Name"])))
                    if self.__include_valuetype_graphviz_edges:
                        self.__graphviz_graph.node(graphviz_data_prop_uri, label = row["ValueType Name"], color="darkblue", style = "filled", fontcolor="white", shape="box")
                    
                    if row["Definition of Property"] != "":
                        self.__rdflib_graph.add((data_property_uri, SKOS.definition, row["Definition"]))
                    
                    if row["Alternative Name(s)"] != "":
                        alternativeNamesList = row["Alternative Name(s)"].strip().split(",")
                        for altName in alternativeNamesList:
                            self.__rdflib_graph.add((data_property_uri, SKOS.altLabel, Literal(altName)))

                    data_property_list[row["fullName"].split("(")[0]] = data_property_uri
                    self.__rdflib_graph.add((data_property_uri, RDF.type, OWL.DatatypeProperty))

                # Else, it uses a different namespace URI based on the ontology specified in the row.    
                elif row["Belongs to Ontology"] != "" and (data_property_uri not in data_property_list.values()):
                    data_property_uri = Namespace(self.__namespace_uris[row["Belongs to Ontology"].lower()])[Literal(row["ValueType Name"])]
                    self.__rdflib_graph.add((data_property_uri, RDF.type, OWL.DatatypeProperty))
                    data_property_list[row["fullName"].split("(")[0]] = data_property_uri
                    if self.__include_valuetype_graphviz_edges:
                        graphviz_data_prop_uri = re.sub(pattern, '', data_property_uri + row["Domain"] + row["Range"])
                        self.__graphviz_graph.node(graphviz_data_prop_uri, label = row["ValueType Name"], color="darkblue", style = "filled", fontcolor="white", shape="box")
                
                # Adds triples representing the domain and range of the object property 
                self.__rdflib_graph.add((data_property_uri, RDFS.domain, self.__entity_uris[row["Domain"]]))
                self.__rdflib_graph.add((data_property_uri, RDFS.range, self.__datatype_conversions[row["Range"]]))
                if self.__include_valuetype_graphviz_edges:
                    graphviz_domain = re.sub(pattern, '', self.__entity_uris[row["Domain"]])
                    graphviz_range = re.sub(pattern, '', (graphviz_data_prop_uri + row["Range"]))
                    self.__graphviz_graph.node(graphviz_range, label = row["Range"], color="yellow", style = "filled", fontcolor="black")
                    self.__graphviz_graph.edge(graphviz_domain, graphviz_data_prop_uri, style="bold", dir="none")
                    self.__graphviz_graph.edge(graphviz_data_prop_uri,graphviz_range, style="bold", dir="forward")
            
        return data_property_list

def main():
    """
    Main function for executing the FairSheetParser. Command-line arguments are required to run "main"
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Example script with command-line arguments.')

    # Add arguments
    # parser.add_argument('--ontology_name', help='Name of the ontology', required=True)
    # parser.add_argument('--ontology_base_uri', help='Base URI of the ontology (the ontology URI, minus the name of the ontology)', required=True)
    parser.add_argument('--ontology_sheet_folder', help='Folder where the FAIRSheetInput csv files are located', required=True)
    parser.add_argument('--include_valuetype_graphviz_edges', help="User decides whether or not the creation of the graphviz graph includes or doesnt include data type properties", action="store_true")

    # Parse arguments
    args = parser.parse_args()

    # Create FairSheetParser instance
    fair_sheet_parser = FairSheetParser(args.ontology_sheet_folder, args.include_valuetype_graphviz_edges)

    # Save RDFLib graph to OWL file
    fair_sheet_parser.save_rdflib_graph_owl()

    # Save RDFLib graph to OWL file
    fair_sheet_parser.save_rdflib_graph_jsonld()
    
    # Save Graphviz graph visualization
    fair_sheet_parser.save_graphviz_graph()


    # g = rdfGraph()
    # g.parse(""./pmd_core.ttl"", format='ttl')
    # print(len(g))
    # g.serialize(destination="pmd.nt", format="nt")
    # graph = rdfGraph()
    # graph.parse("https://materialdigital.github.io/core-ontology/ontology.ttl", format="turtle")

    # # Serialize the graph to NTriples format
    # output_file = "output.rdf"
    # graph.serialize(destination=output_file, format="xml")
    # pmd_core_ontology = get_ontology(output_file).load()
    # print(list(pmd_core_ontology.classes()))
    # print("test")

# Execute main function if the script is run directly
if __name__ == "__main__":
    main()