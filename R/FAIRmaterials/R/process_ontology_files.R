#' @title Process Ontology CSV Files
#'
#' @description This function reads, processes, and combines ontology CSV files from a specified folder.
#' These CSV files must be formatted with template from:
#'
#' \url{https://docs.google.com/spreadsheets/d/1k7gFRc1Yslc-m65aWfFCxqk5UtrKZl9c3GyEFQvLSFU/edit?usp=drive_link}
#'
#' It can handle subdirectories by producing separate unmerged outputs for each subdirectory.
#' The function generates an ontology tree plot, saves it as SVG, and serializes the RDF object
#' to Turtle and JSON-LD formats in the specified folder. Additionally, it allows for the merging
#' of multiple ontologies, with options to customize the merged RDF dataset's metadata.
#'
#' @details This function processes ontology CSV files in a specified folder and its subdirectories.
#' For each subdirectory, it creates separate unmerged outputs named with the folder name prefix.
#' The merged output is generated in the main folder path.
#'
#' If you have a single ontology, place all CSV files in the specified folder and run the function with default parameters.
#' The function will generate outputs for this single ontology, including an ontology tree plot and serialized RDF formats.
#'
#' For multiple ontologies across different subdirectories, the function will process each subdirectory separately. Each
#' subdirectories ontology will have its own set of outputs. Additionally the function will merge the ontologies from all
#' subdirectories. This merged output can have customized metadata such as title, authors, version, URL, and description.
#' If no metadata is specified the merging process concatenates titles, authors, and descriptions from all included ontologies.
#' Note that specifying a base uri is required for merging ontologies.
#'
#'
#' @param folder_path Path to the folder containing ontology CSV files.
#' @param add_external_onto_info Logical indicating whether to update information in RDF.
#' @param include_graph_valuetype Logical indicating whether to include value types in the graph.
#' @param merge_base_uri String containing base URI for the merged ontology.
#'  Defaults to NULL but is required for merging ontologies.
#'  Leave as default when only processing one ontology.
#' @param merge_title String containing title for the merged ontology..
#'  Defaults to NULL will concatenate titles of all merged ontologies.
#'  Leave as default when only processing one ontology.
#' @param merge_author One String containing authors for the merged ontology.
#'  Defaults to NULL will concatenate all unique Author names of merged ontologies.
#'  Leave as default when only processing one ontology.
#' @param merge_version String containing version for the merged ontology..
#'  Defaults to NULL will leave version blank.
#'  Leave as default when only processing one ontology.
#' @param merge_description String containing description for the merged ontology.
#'  Defaults to NULL will concatenate descriptions of all merged ontologies with relative titles as prefixes.
#'  Leave as default when only processing one ontology.
#' @returns NULL
#'
#' @export
#'
#' @importFrom dplyr bind_rows
#' @importFrom tidyr replace_na
#' @importFrom DiagrammeR create_graph render_graph add_node add_edge add_global_graph_attrs
#' @importFrom rdflib rdf rdf_add rdf_serialize
#' @importFrom grDevices svg dev.off
#'
#' @examples
#' # Create temporary directory
#' temp_dir <- tempdir()
#' XRay_test_folder <- file.path(temp_dir, "XRay")
#' dir.create(XRay_test_folder, recursive = TRUE)
#'
#' # Copy CSV files from the package's extdata to the temporary directory
#' extdata_path <- system.file("extdata", "XRay", package = "FAIRmaterials")
#' file.copy(from = list.files(extdata_path, full.names = TRUE),
#'   to = XRay_test_folder, recursive = TRUE)
#'
#' # Process the CSV files in temp the XRay folder
#' process_ontology_files(XRay_test_folder, add_external_onto_info = FALSE)
#'
#' # Clean up
#' unlink(temp_dir, recursive = TRUE)
process_ontology_files <- function(folder_path, add_external_onto_info = FALSE, include_graph_valuetype = TRUE, merge_base_uri = NULL, merge_title = NULL, merge_author = NULL, merge_version = NULL, merge_description = NULL) {

  all_files <- list.files(folder_path, full.names = TRUE, recursive = TRUE, pattern = "\\.csv$")
  if (length(all_files) > 5 & is.null(merge_base_uri)) { stop("Merging ontologies requires a merge_base_uri") }
  main_dir <- normalizePath(folder_path)

  subdirs <- unique(dirname(all_files))
  for (subdir in subdirs) {
    subdir <- normalizePath(subdir)
    if (subdir == main_dir) {next}
    sub_files <- list.files(subdir, full.names = TRUE, pattern = "\\.csv$")
    subdir_name <- basename(subdir)
    process_files(sub_files, subdir, paste0(subdir_name, "_"), include_valuetype = include_graph_valuetype, update_missing = add_external_onto_info, mergeTitle = NULL, mergeAuthor = NULL, mergeVersion = NULL, mergeURL = NULL, mergedescription = NULL)
  }

  process_files(all_files, main_dir, include_valuetype = include_graph_valuetype, update_missing = add_external_onto_info, mergeTitle = merge_title, mergeAuthor = merge_author, mergeVersion = merge_version, mergeURL = merge_base_uri, mergedescription = merge_description)

  message("Process completed successfully. Outputs saved in the specified folder.")
}


