from rdflib import Graph as rdfGraph, Namespace, Literal, URIRef, OWL, XSD 
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS
import csv
from collections import defaultdict
import re
import glob
from pathlib import Path

class FairSheetParser:
    """
    A class to parse FAIR ontology sheets and create a corresponding RDFLib graph.

    Attributes:
        __ontology_info_path (str): Path to the ontology information CSV file that the user fills out.
        __obj_property_path (str): Path to the object property CSV file that the user fills out.
        __data_property_path (str): Path to the data property CSV file that the user fills out.
        __namespace_path (str): Path to the namespace CSV file that the user fills out.
        __entity_path (str): Path to the entity CSV file that the user fills out.
        __datatype_conversions (dict): Dictionary for datatype conversions of strings to XSD objects.
        __rdflib_graph (rdflib.Graph): an RDFLib graph that will contain all information about the ontology.
        __graphviz_graph (graphviz.Digraph): an Graphviz graph that will used to visualize all information about the ontology.
        __ontology_base_uri (Namespace): Base URI of the ontology.
        __ontology_name (str): Name of the ontology.
        __ontology_version (str): Version of the ontology.
        __include_graph_valuetype (bool): Flag that determines whether or not to include valuetype and unit edges in Graphviz graph.
        __individual_relationship (dict): Dictionary to store existing relationships between individuals of entities.
        __namespace_uris (dict): Dictionary of namespace prefixes and their corresponding base URIs.
        __ontology_info (dict): Dictionary to store ontology OWL URIs and the ontology's correspnding Base URI.
        __entity_uris (dict): Dictionary of entity URIs.
        __obj_property_uris (dict): Dictionary of object property URIs.
        __data_property_uris (dict): Dictionary of data property URIs.
    """

    def __init__(self, folder_path, include_graph_valuetype, rdflib_graph, graphviz_graph, add_external_onto_info):
        """
        Initializes the FairSheetParser object with the provided ontology sheet folder and populates the RDFLib graph and Graphviz PNG using the information provided in these sheets.

        Args:
            folder_path (str): The folder containing ontology CSV files.
            include_graph_valuetype (bool): Flag to include valuetype and unit edges in the Graphviz png.
            rdflib_graph (rdflib.Graph): An empty rdflib graph
            graphviz_graph (graphviz.Digraph): An empty graphviz graph
        """
        ontology_info_path = next(iter(glob.glob(folder_path + "- OntologyInfo.csv")))
        obj_property_path = next(iter(glob.glob(folder_path + "- RelationshipDefinitions.csv")))
        data_property_path = next(iter(glob.glob(folder_path + "- ValueTypeDefinitions.csv")))
        namespace_path = next(iter(glob.glob(folder_path + "- NameSpace.csv")))
        entity_path = next(iter(glob.glob(folder_path + "- VariableDefinitions.csv")))
        self.__ontology_info_path = ontology_info_path
        self.__obj_property_path = obj_property_path
        self.__data_property_path = data_property_path
        self.__namespace_path = namespace_path
        self.__entity_path = entity_path
        self.__datatype_conversions = {
            "xsd:integer": XSD.integer,
            "xsd:string": XSD.string,
            "xsd:date": XSD.date,
            "xsd:dateTime": XSD.dateTime,
            "xsd:float": XSD.float,
            "xsd:boolean": XSD.boolean
        }

        self.__rdflib_graph = rdflib_graph
        self.__graphviz_graph = graphviz_graph

        with open(self.__ontology_info_path, 'r') as onto_info_file:
            csv_reader = csv.reader(onto_info_file)
            ontology_metadata = list(csv_reader)

            self.__ontology_base_uri = Namespace(ontology_metadata[1][1])
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, RDF.type, OWL.Ontology))

            self.__ontology_name = ontology_metadata[0][1]
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, RDFS.label, Literal(self.__ontology_name)))
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, DCTERMS.title, Literal(self.__ontology_name)))

            self.__ontology_version = ontology_metadata[2][1]
            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, OWL.versionInfo, Literal(self.__ontology_version)))

            authorsList = [author.strip() for author in ontology_metadata[3][1].split(",")]
            if authorsList[0] != "":
                for author in authorsList:
                    self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, DCTERMS.creator, Literal(author)))

            self.__rdflib_graph.add((self.__ontology_base_uri.Ontology, DCTERMS.description, Literal(ontology_metadata[4][1])))

        self.__include_graph_valuetype = include_graph_valuetype
        self.__individual_relationship = {}

        self.__namespace_uris, self.__ontology_info = self.parse_namespace()
        self.__entity_uris = self.parse_entities()
        self.parse_object_properties()
        self.parse_data_properties()

        # Add external ontology information
        if add_external_onto_info:
            self.add_external_ontology_info()

    def parse_namespace(self):
        """
        Parses the namespace CSV file and updates the RDFLib graph with namespace bindings.

        Returns:
            tuple: A tuple containing:
                - dict: A dictionary of namespace prefixes and their corresponding base URIs.
                - dict: A dictionary of the ontology OWL file URI and its corresponding base URI.
        """
        namespace_dict = {}
        ontology_info_dict = {}

        with open(self.__namespace_path, newline='') as namespace_file:
            csv_reader = csv.DictReader(namespace_file)
            next(csv_reader)

            for row in csv_reader:
                prefix_name = row["Prefix Name"].lower()
                namespace_dict[prefix_name] = Namespace(row["Ontology URL"])
                ontology_info_dict[row["Ontology Info"]] = row["Ontology URL"]
                self.__rdflib_graph.bind(prefix_name, namespace_dict[prefix_name])

            namespace_dict[self.__ontology_name] = self.__ontology_base_uri
            self.__rdflib_graph.bind(self.__ontology_name, self.__ontology_base_uri)

        return namespace_dict, ontology_info_dict

    def parse_entities(self):
        """
        Parses the entity CSV file and updates the RDFLib and Graphviz graphs with the terms, definitions, and other information specified in the CSV file.

        Returns:
            dict: A dictionary containing processed entities and their URIs.
        """
        entitiesCreated = {}
        entities_to_process = defaultdict(list)

        pattern = r'[^\w\s]'

        with open(self.__entity_path, newline='') as entity_file:
            csv_reader = csv.DictReader(entity_file)
            next(csv_reader)

            for row in csv_reader:
                entity = row['fullName']

                if row["Belongs to Ontology"] == "":
                    ontology_namespace = self.__ontology_base_uri
                    entity_uri = ontology_namespace[Literal(entity)]
                else:
                    ontology_namespace = self.__namespace_uris[row["Belongs to Ontology"].lower()]
                    entity_uri = ontology_namespace[Literal(entity.split(":")[1])]

                entities_to_process[entity] = {
                    'name': row["Variable Name"],
                    'parent': row["Parent Variable"],
                    'definition': row["Definition of Variable"],
                    'alt_names': row["Alternative Name(s)"].strip().split(","),
                    'fullName': entity,
                    'unit': row["Unit"]
                }

                entitiesCreated[entity] = entity_uri

                if row["Belongs to Ontology"] == "":
                    self.__graphviz_graph.node(re.sub(pattern, '', entity_uri), label=("mds:" + entity), style='filled', color="lightblue")
                else:
                    self.__graphviz_graph.node(re.sub(pattern, '', entity_uri), label=entity, style='filled', color="lightblue")

            def dfs(entity, entities_to_process):
                entity_uri = entitiesCreated[(entity["fullName"])]
                entity_graphviz_id = re.sub(pattern, '', entity_uri)
                entity_subclassOf_box_id = "superclassOf" + entity_graphviz_id
                entity_unit_id = entity_graphviz_id + "unit"

                self.__rdflib_graph.add((entity_uri, RDF.type, OWL.Class))
                self.__rdflib_graph.add((entity_uri, RDFS.label, Literal(entity['name'])))

                if entity['unit'] != "":
                    namespace_unit, unit_unit = entity['unit'].split(':')
                    unit_uri = self.__namespace_uris[(namespace_unit).lower()][unit_unit]
                    self.__rdflib_graph.add((entity_uri, URIRef("https://w3id.org/pmd/co/unit"), unit_uri))

                if entity['alt_names'][0] != "":
                    for altName in entity['alt_names']:
                        self.__rdflib_graph.add((entity_uri, SKOS.altLabel, Literal(altName)))
                else:
                    self.__rdflib_graph.add((entity_uri, SKOS.altLabel, Literal("")))

                if entity['definition'] != "":
                    self.__rdflib_graph.add((entity_uri, SKOS.definition, Literal(entity['definition'])))

                if entity['parent'] != "" and (entities_to_process.__contains__(entity['parent'])):
                    parent_uri = entitiesCreated[(entity['parent'])]
                    parent_graphviz_id = re.sub(pattern, '', parent_uri)
                    self.__rdflib_graph.add((entity_uri, RDFS.subClassOf, parent_uri))
                    self.__graphviz_graph.node(entity_subclassOf_box_id, label="subclass of", color="darkblue", shape="box")
                    self.__graphviz_graph.edge(parent_graphviz_id, entity_subclassOf_box_id, style="dashed, bold", dir="back")
                    self.__graphviz_graph.edge(entity_subclassOf_box_id, entity_graphviz_id, style="dashed, bold", dir="none")

                    if self.__include_graph_valuetype and entity["unit"] != "":
                        self.__graphviz_graph.node(entity_unit_id, label="unit", color="darkblue", style="filled", shape="box", fontcolor="white")
                        self.__graphviz_graph.node(entity['fullName'] + "unit", label=entity["unit"], color="yellow", style="filled", fontcolor="black")
                        self.__graphviz_graph.edge(entity_graphviz_id, entity_unit_id, style="bold", dir="none")
                        self.__graphviz_graph.edge(entity_unit_id, entity['fullName'] + "unit", style="bold", dir="forward")

                elif entity['parent'] != "":
                    parent_uri = entitiesCreated[entity["parent"]]
                    parent_graphviz_id = re.sub(pattern, '', parent_uri)
                    self.__rdflib_graph.add((entity_uri, RDFS.subClassOf, parent_uri))
                    self.__graphviz_graph.node(entity_subclassOf_box_id, label="subclass of", color="darkblue", shape="box")
                    self.__graphviz_graph.edge(parent_graphviz_id, entity_subclassOf_box_id, style="dashed, bold", dir="back")
                    self.__graphviz_graph.edge(entity_subclassOf_box_id, entity_graphviz_id, style="dashed, bold", dir="none")

                    if self.__include_graph_valuetype and entity["unit"] != "":
                        self.__graphviz_graph.node(entity_unit_id, label="unit", color="darkblue", style="filled", shape="box", fontcolor="white")
                        self.__graphviz_graph.node(entity['fullName'] + "unit", label=entity["unit"], color="yellow", style="filled", fontcolor="black")
                        self.__graphviz_graph.edge(entity_graphviz_id, entity_unit_id, style="bold", dir="none")
                        self.__graphviz_graph.edge(entity_unit_id, entity['fullName'] + "unit", style="bold", dir="forward")

                entities_to_process.pop(entity['fullName'])
                return entity['fullName']

            for entity in list(entities_to_process.keys()):
                dfs(entities_to_process[entity], entities_to_process)

        return entitiesCreated

    # def parse_values_csv(self):
    #     """
    #     Method to parse the values CSV file.

    #     Returns:
    #         dict: Dictionary mapping ontology names to their base URIs.
    #     """

    #     values_dict = {}
    #     with open(self.__values_path, newline='') as values_file:
    #         csv_reader = csv.DictReader(values_file)
    #         count = 1
    #         existing_objects = {}
    #         column_vars = []
    #         column_obj_indices = []
    #         column_obj_start_index = 0
    #         column_obj_end_index = 0
    #         current_obj = None

    #         # Iterate over each column in the CSV file
    #         for column in csv_reader.fieldnames:
    #             # Extract domain and relationship from column header using regex patterns
    #             domain_pattern = r'\((.*?)\-\>'
    #             relationship_pattern = r'^([^()]*)'
    #             domain = re.search(domain_pattern, column).group(1)
    #             relationship = re.search(relationship_pattern, column).group(1)
    #             column_vars.append({'domain': domain, 'relationship': relationship})
    #             if current_obj is None:
    #                 current_obj = domain
    #                 column_obj_start_index = 0
    #             elif current_obj != domain:
    #                 column_obj_indices.append((column_obj_start_index, column_obj_end_index-1))
    #                 column_obj_start_index = column_obj_end_index
    #             column_obj_end_index += 1
    #         column_obj_indices.append((column_obj_start_index, column_obj_end_index-1))

    #         # Iterate over each row in the CSV file
    #         for row in csv_reader:
    #             curr_objects = {}
    #             row_keys = list(row.keys())
    #             row_values = list(row.values())

    #             # Iterate over each group of columns representing an object
    #             for i, j in column_obj_indices:
    #                 # Generate a unique hash for the object based on column variables and row data
    #                 object_hash = hash(str(column_vars[i:j+1]) + str(row_keys[i:j+1] + row_values[i:j+1]))
    #                 domain = column_vars[i]['domain']

    #                 # Check if the object already exists, if not, create a new RDF instance
    #                 if object_hash not in existing_objects:
    #                     entity_uri = self.__entity_uris[domain]
    #                     instance_key = URIRef(entity_uri + str(count))
    #                     self.__rdflib_graph.add((instance_key, RDF.type, URIRef(entity_uri)))
    #                     existing_objects[object_hash] = instance_key
    #                 else:
    #                     instance_key = existing_objects[object_hash]

    #                 # Add RDF triples for each property of the object
    #                 for index in range(i,j+1):
    #                     relationship_val = self.__data_property_uris[column_vars[index]['relationship']]
    #                     self.__rdflib_graph.add((URIRef(instance_key), URIRef(relationship_val), Literal(row_values[index])))
    #                 curr_objects[domain] = instance_key

    #             # Add RDF triples for relationships specified in __individual_relationship
    #             for domain in self.__individual_relationship.keys():
    #                 for relationshipRange, relationship in self.__individual_relationship[domain]:
    #                     if domain not in curr_objects.keys():
    #                         entity_uri = self.__entity_uris[domain]
    #                         instance_key = URIRef(entity_uri + str(count))
    #                         self.__rdflib_graph.add((instance_key, RDF.type, URIRef(entity_uri)))
    #                         curr_objects[domain] = instance_key
    #                     if relationshipRange not in curr_objects.keys():
    #                         entity_uri = self.__entity_uris[relationshipRange]
    #                         instance_key = URIRef(entity_uri + str(count))
    #                         self.__rdflib_graph.add((instance_key, RDF.type, URIRef(entity_uri)))
    #                         curr_objects[relationshipRange] = instance_key
    #                     self.__rdflib_graph.add((URIRef(curr_objects[domain]), relationship, URIRef(curr_objects[relationshipRange])))
                    
    #             count+=1

    #         # Add ontology name and base URI to the values dictionary
    #         values_dict[self.__ontology_name] = self.__ontology_base_uri

    #     return values_dict

    def parse_object_properties(self):
        """
        Parses the relationship CSV file and updates the RDFLib and Graphviz graphs with the terms, definitions, and other information about relationships specified in the CSV file.

        Returns:
            dict: A dictionary containing processed object properties and their corresponding URIs.
        """
        pattern = r'[^\w\s]'
        with open(self.__obj_property_path, newline='') as obj_property_file:
            csv_reader = csv.DictReader(obj_property_file)
            next(csv_reader)

            obj_property_list = {}

            for row in csv_reader:
                # Skip rows where Domain or Range are empty
                if not row["Domain"] or not row["Range"]:
                    continue
                obj_property_uri = self.__namespace_uris[self.__ontology_name][Literal(row["Relationship Name"])]
                graphviz_obj_prop_uri = re.sub(pattern, '', obj_property_uri + row["Domain"] + row["Range"])

                if row["Belongs to Ontology"] == "" and (obj_property_uri not in obj_property_list.values()):
                    self.__rdflib_graph.add((obj_property_uri, RDF.type, OWL.ObjectProperty))
                    self.__graphviz_graph.node(graphviz_obj_prop_uri, label=row["Relationship Name"], color="darkblue", style="filled", fontcolor="white", shape="box")
                    self.__rdflib_graph.add((obj_property_uri, RDFS.label, Literal(row["Relationship Name"])))
                    
                    if row["Definition"] != "":
                        self.__rdflib_graph.add((obj_property_uri, SKOS.definition, Literal(row["Definition"])))
                    
                    if row["Alternative Name(s)"] != "":
                        alternativeNamesList = row["Alternative Name(s)"].strip().split(",")
                        if alternativeNamesList[0] != "":
                            for altName in alternativeNamesList:
                                self.__rdflib_graph.add((obj_property_uri, SKOS.altLabel, Literal(altName)))

                    obj_property_list[row["fullName"]] = obj_property_uri
                    self.__rdflib_graph.add((obj_property_uri, RDF.type, OWL.ObjectProperty))

                elif row["Belongs to Ontology"] != "" and (obj_property_uri not in obj_property_list.values()):
                    obj_property_uri = self.__namespace_uris[row["Belongs to Ontology"].lower()][Literal(row["Relationship Name"])]
                    graphviz_obj_prop_uri = re.sub(pattern, '', obj_property_uri + row["Domain"] + row["Range"])
                    self.__rdflib_graph.add((obj_property_uri, RDF.type, OWL.ObjectProperty))
                    self.__graphviz_graph.node(graphviz_obj_prop_uri, label=row["Relationship Name"], color="darkblue", style="filled", fontcolor="white", shape="box")
                    obj_property_list[row["fullName"]] = obj_property_uri
                elif row["Belongs to Ontology"] != "":
                    obj_property_uri = self.__namespace_uris[row["Belongs to Ontology"]][Literal(row["Relationship Name"])]
                    graphviz_obj_prop_uri = re.sub(pattern, '', obj_property_uri + row["Domain"] + row["Range"])

                self.__rdflib_graph.add((obj_property_uri, RDFS.domain, self.__entity_uris[row["Domain"]]))
                self.__rdflib_graph.add((obj_property_uri, RDFS.range, self.__entity_uris[row["Range"]]))

                if row["Domain"] not in self.__individual_relationship:
                    self.__individual_relationship[row["Domain"]] = []
                self.__individual_relationship[row["Domain"]] += [(row["Range"], obj_property_uri)]

                graphviz_domain = re.sub(pattern, '', self.__entity_uris[row["Domain"]])
                graphviz_range = re.sub(pattern, '', self.__entity_uris[row["Range"]])
                self.__graphviz_graph.edge(graphviz_domain, graphviz_obj_prop_uri, style="bold", dir="none")
                self.__graphviz_graph.edge(graphviz_obj_prop_uri, graphviz_range, style="bold", dir="forward")
            
        return obj_property_list

    def add_external_ontology_info(self):
        """
        Adds external ontology information to all terms in the RDFLib graph that belonged to other ontologies in the FAIR sheets.
        """
        for ontology_file, base_uri in self.__ontology_info.items():
            try:
                graph = rdfGraph().parse(ontology_file, format='ttl')
            except Exception as e:
                warnings.warn(f"Failed to parse ontology file {ontology_file}: {e}")
                continue  # Skip to the next ontology file
            graph = rdfGraph().parse(ontology_file, format='ttl')
            if "http:" in base_uri:
                http_uri = base_uri
                https_uri = base_uri.replace("http", "https")
            else:
                http_uri = base_uri.replace("https", "http")
                https_uri = base_uri

            referenced_terms = set()
            for subj, pred, obj in self.__rdflib_graph:
                if subj.startswith(http_uri):
                    referenced_terms.add(str(subj)[len(http_uri):])
                if subj.startswith(https_uri):
                    referenced_terms.add(str(subj)[len(https_uri):])
            
            for term in referenced_terms:
                term = URIRef(base_uri + term)
                for s, p, o in graph.triples((term, SKOS.definition, None)):
                    self.__rdflib_graph.add((s, p, o))
                for s, p, o in graph.triples((term, DCTERMS.description, None)):
                    self.__rdflib_graph.add((s, p, o))
                for s, p, o in graph.triples((term, SKOS.altLabel, None)):
                    self.__rdflib_graph.add((s, p, o))
                # for s, p, o in graph.triples((term, RDFS.label, None)):
                #     self.__rdflib_graph.add((s, p, o))

    def parse_data_properties(self):
        """
        Parses data properties from a CSV file and updates the RDFLib and Graphviz graphs.

        This method reads data properties from a specified CSV file and processes each row to 
        generate URIs for data properties, create RDF triples, and update a Graphviz graph. 
        The method handles different namespaces based on the ontology specified in the CSV rows.

        Returns:
            dict: A dictionary containing processed data properties and their URIs.
        
        Raises:
            FileNotFoundError: If the data property CSV file cannot be found.
            csv.Error: If there is an error reading the CSV file.
        """
        pattern = r'[^\w\s]'
        with open(self.__data_property_path, newline='') as data_property_file:
            csv_reader = csv.DictReader(data_property_file)
            next(csv_reader)

            data_property_list = {}

            for row in csv_reader:

                # Skip rows where Domain or Range are empty
                if not row["Domain"] or not row["Range"]:
                    continue

                # Generate URI for the data property
                data_property_uri = self.__namespace_uris[self.__ontology_name][Literal(row["ValueType Name"])]
                graphviz_data_prop_uri = re.sub(pattern, '', data_property_uri + row["Domain"] + row["Range"])

                # If conditions met, adds triples representing the data property with its type, label, definition, and alternative names
                if row["Belongs to Ontology"] == "" and (data_property_uri not in data_property_list.values()):
                    self.__rdflib_graph.add((data_property_uri, RDF.type, OWL.DatatypeProperty))
                    self.__rdflib_graph.add((data_property_uri, RDFS.label, Literal(row["ValueType Name"])))
                    if self.__include_graph_valuetype:
                        self.__graphviz_graph.node(graphviz_data_prop_uri, label=row["ValueType Name"], color="darkblue", style="filled", fontcolor="white", shape="box")
                    
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
                    if self.__include_graph_valuetype:
                        graphviz_data_prop_uri = re.sub(pattern, '', data_property_uri + row["Domain"] + row["Range"])
                        self.__graphviz_graph.node(graphviz_data_prop_uri, label=row["ValueType Name"], color="darkblue", style="filled", fontcolor="white", shape="box")
                
                # Adds triples representing the domain and range of the object property 
                self.__rdflib_graph.add((data_property_uri, RDFS.domain, self.__entity_uris[row["Domain"]]))
                self.__rdflib_graph.add((data_property_uri, RDFS.range, self.__datatype_conversions[row["Range"]]))
                if self.__include_graph_valuetype:
                    graphviz_domain = re.sub(pattern, '', self.__entity_uris[row["Domain"]])
                    graphviz_range = re.sub(pattern, '', (graphviz_data_prop_uri + row["Range"]))
                    self.__graphviz_graph.node(graphviz_range, label=row["Range"], color="yellow", style="filled", fontcolor="black")
                    self.__graphviz_graph.edge(graphviz_domain, graphviz_data_prop_uri, style="bold", dir="none")
                    self.__graphviz_graph.edge(graphviz_data_prop_uri, graphviz_range, style="bold", dir="forward")
            
        return data_property_list
    
    def get_rdf_graph(self):
        """
        Gets the current RDFLib Graph

        Returns:
            rdflib.Graph: The current rdflib graph
        """
        return self.__rdflib_graph

    def get_graphviz_graph(self):
        """
        Gets the current Graphviz Graph

        Returns:
            graphviz.Digraph: The current Graphviz graph
        """
        return self.__graphviz_graph
    
    def get_ontology_name(self):
        """
        Gets the user-specified name of the ontology

        Returns:
            str: The user-specified name of the ontology
        """
        return self.__ontology_name

    def get_ontology_base_uri(self):
        """
        Gets the base URI of the Ontology

        Returns:
            str: The user-specified base URI of the ontology
        """
        return self.__ontology_base_uri
    
    def get_namespace_uris(self):
        """
        Gets the namespace URIs of the Ontology

        Returns:
            str: The user-specified namespace URIs of the ontology
        """
        return self.__namespace_uris