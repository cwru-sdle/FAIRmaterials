import os
import tempfile
from pylode import VocPub
import graphviz

class RDFLibGraphSaver:
    """
    A class to save an input RDFLib graph under different formats and generate corresponding documentation for the ontology.

    Attributes:
        __rdflib_graph (rdflib.Graph): an RDFLib graph containing all information about the ontology.
        __graphviz_graph (graphviz.Digraph): an Graphviz graph containing all information about the ontology.
        __ontology_name (str): Name of the ontology.
    """

    def __init__(self, ontology_name, rdflib_graph, graphviz_graph):
        self.__ontology_name = ontology_name
        self.__rdflib_graph = rdflib_graph
        self.__graphviz_graph = graphviz_graph

    def save_rdflib_graph_owl(self):
        """
        Saves the RDFLib graph to an OWL file in TTL format.

        Returns:
            str: The file path of the saved OWL file.
        """
        # Define the folder name
        output_folder = f"{self.__ontology_name}_output"
        
        # Create the folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Define the file path within the folder
        file_path = os.path.join(output_folder, f"{self.__ontology_name}.ttl")
        
        # Write the RDFLib graph to the file in TTL format
        with open(file_path, "wb") as f:
            f.write(self.__rdflib_graph.serialize(format="ttl").encode('utf-8'))
            
        return file_path

    def save_rdflib_graph_jsonld(self):
        """
        Saves the RDFLib graph to a JSON-LD file.

        Returns:
            str: The file path of the saved JSON-LD file.
        """
        def rdf_namespaces_to_json_ld_context(graph):
            json_ld_context = {}
            for prefix, namespace in graph.namespaces():
                json_ld_context[prefix] = str(namespace)
            return json_ld_context

        json_ld_context = rdf_namespaces_to_json_ld_context(self.__rdflib_graph)

        # Define the folder name
        output_folder = f"{self.__ontology_name}_output"
        
        # Create the folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Define the file path within the folder
        file_path = os.path.join(output_folder, f"{self.__ontology_name}.json")
        
        # Write the RDFLib graph to the file in JSON-LD format
        with open(file_path, "wb") as f:
            f.write(self.__rdflib_graph.serialize(format="json-ld", context=json_ld_context).encode('utf-8'))
            
        return file_path
    
    def save_graphviz_graph(self):
        """
        Saves the Graphviz graph to a PNG file.

        Raises:
            graphviz.exceptions.GraphvizError: If the graph is empty and cannot be printed.
        """
        output_folder = f"{self.__ontology_name}_output"
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        if len(self.__graphviz_graph.body) == 0:
            raise graphviz.exceptions.GraphvizError("The graph is empty and cannot be printed")
        else:
            file_path = os.path.join(output_folder, f"{self.__ontology_name}Graph")
            self.__graphviz_graph.render(file_path, format="png", cleanup=True)


    def generate_pylode_html(self):
            """
            Generates an HTML file using PyLODE for the RDFLib graph containing all information about the ontology.

            Returns:
                str: The file path of the generated HTML file.
            """
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ttl') as temp_file:
                self.__rdflib_graph.serialize(destination=temp_file, format='turtle')
                temp_file_path = temp_file.name

            op = VocPub(ontology=temp_file_path)

            html = op.make_html()
            output_folder = f"{self.__ontology_name}_output"
            
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            file_path = os.path.join(output_folder, f"{self.__ontology_name}.html")

            with open(file_path, 'w') as file:
                pass  # 'pass' is used here to create an empty file

            op.make_html(destination=file_path)
            return file_path
