from rdflib import Graph
def merge_ontologies(ontology1_path, ontology2_path, ontology3_path, ontology4_path):
    # Load the ontologies into separate graphs
    graph1 = Graph()
    graph1.parse(ontology1_path, format='ttl')
    
    graph2 = Graph()
    graph2.parse(ontology2_path, format='ttl')

    graph3 = Graph()
    graph3.parse(ontology3_path, format='ttl')

    graph4 = Graph()
    graph4.parse(ontology4_path, format='ttl')

    # Merge the graphs
    merged_graph = graph1 + graph2 + graph3 + graph4

    return merged_graph

def main():
    # Paths to the ontologies
    ontology1_path = "/mnt/vstor/CSE_MSE_RXF131/cradle-members/sdle/ach159/git/fairmaterials/packages/python_v3_package/AsterGDEMFiles/AsterGDEMOntology-v0.2.owl"
    ontology2_path = "/mnt/vstor/CSE_MSE_RXF131/cradle-members/sdle/ach159/git/fairmaterials/packages/python_v3_package/ICPOESFiles/ICPOESOntology-v0.2.owl"
    ontology3_path = "/mnt/vstor/CSE_MSE_RXF131/cradle-members/sdle/ach159/git/fairmaterials/packages/python_v3_package/PVCellFiles/PVCellOntology-v0.2.owl"
    ontology4_path = "/mnt/vstor/CSE_MSE_RXF131/cradle-members/sdle/ach159/git/fairmaterials/packages/python_v3_package/PVModuleFiles/PVModuleOntology-v0.2.owl"
    # Merge the ontologies
    merged_graph = merge_ontologies(ontology1_path, ontology2_path, ontology3_path, ontology4_path)

    # Save the merged ontology
    merged_graph.serialize(destination="mds-ontov0.2.owl", format='ttl')

if __name__ == "__main__":
    main()