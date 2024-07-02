import argparse
from rdflib import Graph as rdfGraph
import graphviz
from FAIRmaterials.fair_sheet_parser import FairSheetParser
from FAIRmaterials.rdflib_graph_saver import RDFLibGraphSaver
from FAIRmaterials.rdflib_graph_merger import RDFLibGraphMerger
import os

def main():
    """
    Main function to parse command-line arguments and execute the FairSheetParser and RDFLibGraphSaver methods.

    This function sets up and parses command-line arguments, creates an instance of the 
    FairSheetParser class, calls various methods on the parser instance to process 
    the ontology information specified in the CSV sheets, creates an instance of RDFLibGraphSaver to save RDFLib graphs in different formats and generate 
    documentation.

    Command-line Arguments:
        --folder_path (str): Folder where the FAIRSheetInput CSV files are located.
        --include_graph_valuetype (bool): Whether to include valuetype and units in the Graphviz PNG.
        --include_pylode_docs (bool): Whether to output HTML documentation for the created ontology.
        --add_external_onto_info (bool): Whether to import description and label info from external ontology terms (Optional).
        --merge_title (str): string containing title for the merged RDF dataset (Optional).
        --merge_author (str): string containing authors for the merged RDF dataset (Optional).
        --merge_URL (str): string containing URL for the merged RDF dataset.
        --merge_description (str): String containing description for the merged RDF dataset.
    
    Raises:
        argparse.ArgumentError: If there is an error in parsing command-line arguments.

    Example:
        To run the script with the required arguments:
        
        .. code-block:: console

            $ python main.py --folder_path /path/to/csv --include_graph_valuetype --include_pylode_docs

    """
    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument('--folder_path', help='Folder where the FAIRSheetInput csv files are located', required=True)
    parser.add_argument('--include_graph_valuetype', help="User decides whether or not the creation of the graphviz graph includes or doesnt include data type properties (Optional)", action="store_true")
    parser.add_argument('--include_pylode_docs', help="User decides whether or not the package also outputs html documentation for the created ontology (Optional)", action="store_true")
    parser.add_argument('--add_external_onto_info', help="Whether to import description and label info from external ontology terms (Optional)", action="store_true")
    parser.add_argument('--merge_title', help="string containing title for the merged RDF dataset (Optional)")
    parser.add_argument('--merge_base_uri', help="string containing URL for the merged RDF dataset (Optional)")
    parser.add_argument('--merge_description', help="string containing description for the merged RDF dataset (Optional)")
    parser.add_argument('--merge_version', help="string containing version for the merged RDF dataset (Optional)")
    # Parse arguments
    args = parser.parse_args()

    # Group files by prefix
    files = [f for f in os.listdir(args.folder_path) if os.path.isfile(os.path.join(args.folder_path, f))]
    grouped_files = []
    for file in files:
        prefix = file.split("-")[0]
        grouped_files.append(prefix)

    ontologies = []
    
    for prefix in set(grouped_files):
        rdflib_graph = rdfGraph()
        graphviz_graph = graphviz.Digraph(strict=False)

        specific_folder = args.folder_path + "/" + prefix
        # Create FairSheetParser instance
        fair_sheet_parser = FairSheetParser(specific_folder, args.include_graph_valuetype, rdflib_graph, graphviz_graph, args.add_external_onto_info)

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
        
        ontologies.append(rdflib_graph)
        
    if len(ontologies) > 1:
        merger = RDFLibGraphMerger()
        first_graph = ontologies[0]
        remaining_graphs = ontologies[1:]
        for graph in remaining_graphs:
            merged_graph = merger.merge_ontologies(first_graph, graph)

        merged_graph = merger.add_ontology_ownership(merged_graph, args.merge_base_uri, args.merge_title, args.merge_version, args.merge_description)
        merged_rdflib_graph_saver = RDFLibGraphSaver("merged_ontology", merged_graph, None)
        # Save RDFLib graph to OWL file
        merged_rdflib_graph_saver.save_rdflib_graph_owl()

        # Save RDFLib graph to JSON-LD file
        merged_rdflib_graph_saver.save_rdflib_graph_jsonld()

        # Generate PyLode documentation
        if args.include_pylode_docs:
            merged_rdflib_graph_saver.generate_pylode_html()

# Execute main function if the script is run directly
if __name__ == "__main__":
    main()