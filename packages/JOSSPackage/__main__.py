import argparse
from rdflib import Graph as rdfGraph
import graphviz
from SDLEFairPackage.fair_sheet_parser import FairSheetParser
from SDLEFairPackage.rdflib_graph_saver import RDFLibGraphSaver

def __main__():
    """
    Main function to parse command-line arguments and execute the FairSheetParser and RDFLibGraphSaver methods.

    This function sets up and parses command-line arguments, creates an instance of the 
    FairSheetParser class, calls various methods on the parser instance to process 
    the ontology information specified in the CSV sheets, creates an instance of RDFLibGraphSaver to save RDFLib graphs in different formats and generate 
    documentation.

    Command-line Arguments:
        --ontology_sheet_folder (str): Folder where the FAIRSheetInput CSV files are located.
        --include_valuetype_graphviz_edges (bool): Whether to include valuetype and units in the Graphviz PNG.
        --include_pylode_docs (bool): Whether to output HTML documentation for the created ontology.
    
    Raises:
        argparse.ArgumentError: If there is an error in parsing command-line arguments.

    Example:
        To run the script with the required arguments:
        
        .. code-block:: console

            $ python main.py --ontology_sheet_folder /path/to/csv --include_valuetype_graphviz_edges --include_pylode_docs

    """
    parser = argparse.ArgumentParser()
    # Add arguments
    parser.add_argument('--ontology_sheet_folder', help='Folder where the FAIRSheetInput csv files are located', required=True)
    parser.add_argument('--include_valuetype_graphviz_edges', help="User decides whether or not the creation of the graphviz graph includes or doesnt include data type properties", action="store_true")
    parser.add_argument('--include_pylode_docs', help="User decides whether or not the package also outputs html documentation for the created ontology", action="store_true")
    
    # Parse arguments
    args = parser.parse_args()

    rdflib_graph = rdfGraph()
    graphviz_graph = graphviz.Digraph(strict=False)

    # Create FairSheetParser instance
    fair_sheet_parser = FairSheetParser(args.ontology_sheet_folder, args.include_valuetype_graphviz_edges, rdflib_graph, graphviz_graph)

    rdflib_graph = fair_sheet_parser.get_rdf_graph()
    graphviz_graph = fair_sheet_parser.get_graphviz_graph()
    ontology_name = fair_sheet_parser.get_ontology_name()

    rdflib_graph_saver = RDFLibGraphSaver(ontology_name, rdflib_graph, graphviz_graph)
    # Save RDFLib graph to OWL file
    rdflib_graph_saver.save_rdflib_graph_owl()

    # Save RDFLib graph to JSON-LD file
    rdflib_graph_saver.save_rdflib_graph_jsonld()
    
    # Save Graphviz graph visualization
    rdflib_graph_saver.save_graphviz_graph()

    # Generate PyLode documentation
    if args.include_pylode_docs:
        rdflib_graph_saver.generate_pylode_html()

# Execute main function if the script is run directly
if __name__ == "__main__":
    __main__()