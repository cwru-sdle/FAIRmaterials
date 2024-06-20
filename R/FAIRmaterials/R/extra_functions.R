#' generate rdf object
#'
#' @param NameSpace  Data frame for Name Spaces
#' @param ValueTypeDefinitions Data frame for Value Type Definitions.
#' @param RelationshipDefinitions Data frame for Relationship Definitions.
#' @param VariableDefinitions Data frame for Variable Definitions.
#' @param OntologyInfo Data frame for Ontology Info.
#' @param update_missing Whether to update missing information.
#' @return An "rdf" object from the 'rdflib' package
#'
#' @importFrom dplyr bind_rows filter
#' @importFrom rdflib rdf rdf_add
#' @importFrom stats setNames complete.cases
#' @noRd
generate_rdf_obj <- function(NameSpace, ValueTypeDefinitions, RelationshipDefinitions, VariableDefinitions, OntologyInfo, update_missing = FALSE) {

  VariableDefinitions$`AlternativeName(s)` <- base::gsub('"', '', as.character(VariableDefinitions$`AlternativeName(s)`))
  ValueTypeDefinitions$ValueTypeName <- base::gsub(" ", "", as.character(ValueTypeDefinitions$ValueTypeName))

  edges_from_relationship_rdf <- data.frame(
    from = RelationshipDefinitions$Domain,
    to = RelationshipDefinitions$Range,
    rel = RelationshipDefinitions$RelationshipName
  )
  edges_from_var_rdf <- data.frame(
    from = VariableDefinitions$VariableName,
    to = VariableDefinitions$ParentVariable,
    rel = "rdfs:subClassOf"
  )
  edges_from_var_rdf <- tidyr::replace_na(edges_from_var_rdf, list(from = "NA"))
  edges_from_value_rdf <- data.frame(
    from = ValueTypeDefinitions$Domain,
    to = ValueTypeDefinitions$Range,
    rel = ValueTypeDefinitions$ValueTypeName
  )
  edges_rdf <- dplyr::bind_rows(edges_from_relationship_rdf, edges_from_value_rdf, edges_from_var_rdf)
  for (x in 1:base::length(edges_rdf)) {
    edges_rdf[[x]] <- base::gsub(";.*$", "", edges_rdf[[x]])
    edges_rdf[[x]] <- base::gsub(" ", "", edges_rdf[[x]])
  }

  vertices_rdf <- dplyr::bind_rows(
    data.frame(name = edges_from_relationship_rdf$rel, type = "Relationship"),
    data.frame(name = edges_from_relationship_rdf$from, type = "Entity"),
    data.frame(name = edges_from_relationship_rdf$to, type = "Entity"),
    data.frame(name = edges_from_value_rdf$rel, type = "Relationship"),
    data.frame(name = edges_from_value_rdf$from, type = "Entity"),
    data.frame(name = edges_from_value_rdf$to, type = "Value"),
    data.frame(name = edges_from_var_rdf$rel, type = "Relationship"),
    data.frame(name = edges_from_var_rdf$to, type = "Entity"),
    data.frame(name = edges_from_var_rdf$from, type = "Entity")
  )
  vertices_rdf <- base::unique(vertices_rdf)
  vertices_rdf$name <- base::gsub(";.*$", "", vertices_rdf$name)
  vertices_rdf$name <- base::gsub(" ", "", vertices_rdf$name)

  namespace1 <- vector()

  for (x in 1:nrow(NameSpace)) {
    namespace1[NameSpace$PrefixName[x]] <- NameSpace$OntologyURL[x]
  }

  namespace1 <- c(namespace1,
                  sd = "http://www.w3.org/2001/XMLSchema#",
                  owl = "http://www.w3.org/2002/07/owl#",
                  rdfs = "http://www.w3.org/2000/01/rdf-schema#",
                  rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  xsd = "http://www.w3.org/2001/XMLSchema#",
                  skos = "http://www.w3.org/2004/02/skos/core#",
                  pmd = "https://w3id.org/pmd/co/",
                  PMDCo = "https://w3id.org/pmd/co#",
                  QUDT = "https://qudt.org/vocab/unit/",
                  dcterms = "http://purl.org/dc/terms/"

  )
  namespace1[as.character(OntologyInfo[5,2])] <- as.character(OntologyInfo[1,2])

  # Ensure there are no duplicates by keeping the last occurrence
  namespace1 <- namespace1[!duplicated(names(namespace1), fromLast = TRUE)]

  rdf_obj <- rdflib::rdf()

  get_full_uri <- function(term) {
    parts <- base::unlist(base::strsplit(term, ":", fixed = TRUE))
    prefix <- parts[1]
    name <- parts[2]

    if (prefix %in% base::names(namespace1)) {
      return(base::paste0(namespace1[prefix], name))
    } else {
      return(base::paste0(OntologyInfo[1,2], term))
    }
  }

  extract_term <- function(full_uri) {
    parts <- base::unlist(base::strsplit(full_uri, "[#/]", fixed = FALSE))
    return(parts[length(parts)])
  }

  for (x in 1:base::length(vertices_rdf$name)) {
    if (is.na(vertices_rdf$name[x])) {next}
    if (vertices_rdf$type[x] == "Entity") {
      subject_uri <- get_full_uri(vertices_rdf$name[x])

      rdflib::rdf_add(
        rdf_obj,
        subject = subject_uri,
        predicate = get_full_uri("rdf:type"),
        object = get_full_uri("rdfs:Class")
      )

      rdflib::rdf_add(
        rdf_obj,
        subject = subject_uri,
        predicate = get_full_uri("rdf:label"),
        object = base::gsub(".*:\\s?", "", vertices_rdf$name[x])
      )

      if (vertices_rdf$name[x] %in% VariableDefinitions$fullName) {
        rNum <- base::which(vertices_rdf$name[x] == VariableDefinitions$fullName)

        rdflib::rdf_add(
          rdf_obj,
          subject = subject_uri,
          predicate = get_full_uri("rdfs:comment"),
          object = base::ifelse(!is.na(VariableDefinitions$DefinitionofVariable[rNum]),
                                VariableDefinitions$DefinitionofVariable[rNum], "_")
        )

        rdflib::rdf_add(
          rdf_obj,
          subject = subject_uri,
          predicate = get_full_uri("skos:altLabel"),
          object = base::ifelse(!is.na(VariableDefinitions$`AlternativeName(s)`[rNum]),
                                VariableDefinitions$`AlternativeName(s)`[rNum], "_")
        )

        rdflib::rdf_add(
          rdf_obj,
          subject = subject_uri,
          predicate = get_full_uri("PMDCo:unit"),
          object = base::ifelse(!is.na(VariableDefinitions$Unit[rNum]),
                                get_full_uri(VariableDefinitions$Unit[rNum]), "_")
        )

        if (!is.na(VariableDefinitions$ParentVariable[rNum])) {
          rdflib::rdf_add(
            rdf_obj,
            subject = subject_uri,
            predicate = get_full_uri("rdfs:subClassOf"),
            object = get_full_uri(VariableDefinitions$ParentVariable[rNum])
          )
        }
      }
    }
  }

  for (i in 1:base::nrow(edges_rdf)) {
    if (is.na(edges_rdf$rel[i])) {next}
    if (edges_rdf$rel[i] == ("rdfs:subClassOf")) {next}
    if (edges_rdf$rel[i] %in% ValueTypeDefinitions$ValueTypeName) {next}
    subject_uri <- get_full_uri(edges_rdf$from[i])
    object_uri <- get_full_uri(edges_rdf$to[i])
    predicate_uri <- get_full_uri(edges_rdf$rel[i])

    rdflib::rdf_add(
      rdf_obj,
      subject = predicate_uri,
      predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
      object = "http://www.w3.org/2002/07/owl#ObjectProperty"
    )
    rdflib::rdf_add(
      rdf_obj,
      subject = predicate_uri,
      predicate = "http://www.w3.org/2000/01/rdf-schema#domain",
      object = get_full_uri(edges_rdf$from[i])
    )
    rdflib::rdf_add(
      rdf_obj,
      subject = predicate_uri,
      predicate = "http://www.w3.org/2000/01/rdf-schema#range",
      object = get_full_uri(edges_rdf$to[i])
    )
  }

  for (x in 1:base::length(ValueTypeDefinitions$ValueTypeName)) {
    if (is.na(ValueTypeDefinitions$ValueTypeName[x])) {next}
    subject_uri <- get_full_uri(ValueTypeDefinitions$ValueTypeName[x])
    rdflib::rdf_add(
      rdf_obj,
      subject = subject_uri,
      predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
      object = "http://www.w3.org/2002/07/owl#DatatypeProperty"
    )
    rdflib::rdf_add(
      rdf_obj,
      subject = subject_uri,
      predicate = "http://www.w3.org/2000/01/rdf-schema#domain",
      object = get_full_uri(ValueTypeDefinitions$Domain[x])
    )
    rdflib::rdf_add(
      rdf_obj,
      subject = subject_uri,
      predicate = "http://www.w3.org/2000/01/rdf-schema#range",
      object = get_full_uri(ValueTypeDefinitions$Range[x])
    )
  }

  if (update_missing) {
    rdf_obj <- update_missing_info(rdf_obj, namespace1)
  }
  return(rdf_obj)
}


#' Serialize RDF Object
#'
#' Serializes an RDF object to a specified file format and path.
#'
#' @param rdf_obj RDF object to serialize.
#' @param namespace List of namespaces (optional). Must be formatted as c(prefix = uri, ...)
#' @param output_path Path to save the serialized RDF file.
#' @param file_type File format for serialization ("rdfxml", "nquads", "ntriples", "turtle", "jsonld").
#' @importFrom rdflib rdf_serialize
#' @noRd
serialize_rdf_obj <- function(rdf_obj, namespace, output_path, file_type, base) {

  # Validate file_type
  valid_types <- c("rdfxml", "nquads", "ntriples", "turtle", "jsonld")
  if (!file_type %in% valid_types) {
    stop("Invalid file_type. Must be one of: ", paste(valid_types, collapse = ", "))
  }

  # Serialize the RDF object
  rdflib::rdf_serialize(rdf_obj, output_path, format = file_type, namespace = namespace, base = "")
}


#' Merge Two rdf Objects
#'
#' Merges two rdf objects by converting them to triples, combining the data frames,
#' and adding all triples to a new RDF object.
#'
#' @param rdf_obj1 First rdf object.
#' @param rdf_obj2 Second rdf object.
#' @return Merged RDF object.
#' @importFrom rdflib rdf rdf_query rdf_add
#' @importFrom dplyr bind_rows
#' @noRd
merge_rdf_obj <- function(rdf_obj1, rdf_obj2) {
  # Extract triples from both RDF objects
  triples1 <- rdflib::rdf_query(rdf_obj1, "SELECT ?s ?p ?o WHERE { ?s ?p ?o }")
  triples2 <- rdflib::rdf_query(rdf_obj2, "SELECT ?s ?p ?o WHERE { ?s ?p ?o }")

  # Combine triples into a single data frame
  combined_triples <- dplyr::bind_rows(triples1, triples2)

  # Create a new RDF object
  merged_rdf <- rdflib::rdf()

  # Add all triples to the new RDF object
  for (i in 1:nrow(combined_triples)) {
    rdflib::rdf_add(
      merged_rdf,
      subject = as.character(combined_triples$s[i]),
      predicate = as.character(combined_triples$p[i]),
      object = as.character(combined_triples$o[i])
    )
  }

  return(merged_rdf)
}

#' Get Full URI
#'
#' Retrieves the full URI from a given term using the provided namespaces.
#'
#' @param term A term with a prefix and name separated by a colon.
#' @param namespace1 List of namespaces.
#' @return Full URI.
#' @noRd
get_full_uri <- function(term, namespace1) {
  parts <- base::unlist(base::strsplit(term, ":", fixed = TRUE))
  prefix <- parts[1]
  name <- parts[2]

  if (prefix %in% base::names(namespace1)) {
    return(base::paste0(namespace1[prefix], name))
  } else {
    return(base::paste0("http://example.org/", term))
  }
}

#' Extract Term from URI
#'
#' Extracts the term from a full URI.
#'
#' @param full_uri A full URI.
#' @return Extracted term.
#' @noRd
extract_term <- function(full_uri) {
  parts <- base::unlist(base::strsplit(full_uri, "[#/]", fixed = FALSE))
  return(utils::tail(parts, 1))
}

#' Clean Data Frames
#'
#' Removes the first row and original columns from data frames.
#'
#' @param NameSpace Data frame for NameSpace.
#' @param VariableDefinitions Data frame for VariableDefinitions.
#' @param ValueTypeDefinitions Data frame for ValueTypeDefinitions.
#' @param RelationshipDefinitions Data frame for RelationshipDefinitions.
#' @param OntologyInfo Data frame for OntologyInfo
#' @return List of cleaned data frames.
#' @importFrom dplyr filter
#' @importFrom tidyr replace_na
#' @noRd
clean_data_frames <- function(NameSpace, VariableDefinitions, ValueTypeDefinitions, RelationshipDefinitions, OntologyInfo) {

  NameSpace <- NameSpace[-1,]
  VariableDefinitions <- VariableDefinitions[-1,]
  ValueTypeDefinitions <- ValueTypeDefinitions[-1,]
  RelationshipDefinitions <- RelationshipDefinitions[-1,]
  tempRow <- as.data.frame(t(colnames(OntologyInfo)))
  colnames(tempRow) <- colnames(OntologyInfo)
  OntologyInfo <- as.data.frame(rbind(OntologyInfo, tempRow, stringsAsFactors = FALSE))
  colnames(OntologyInfo) <- ""

  colnames(NameSpace) <- base::gsub(" ", "", base::colnames(NameSpace))
  colnames(RelationshipDefinitions) <- base::gsub(" ", "", base::colnames(RelationshipDefinitions))
  colnames(ValueTypeDefinitions) <- base::gsub(" ", "", base::colnames(ValueTypeDefinitions))
  colnames(VariableDefinitions) <- base::gsub(" ", "", base::colnames(VariableDefinitions))
  colnames(OntologyInfo) <- base::gsub(" ", "", base::colnames(OntologyInfo))

  ValueTypeDefinitions$ValueTypeName <- base::ifelse(
    !is.na(ValueTypeDefinitions$BelongstoOntology),
    base::paste0(ValueTypeDefinitions$BelongstoOntology, ": ", ValueTypeDefinitions$ValueTypeName),
    ValueTypeDefinitions$ValueTypeName
  )
  RelationshipDefinitions$RelationshipName <- base::ifelse(
    !is.na(RelationshipDefinitions$fullName),
    RelationshipDefinitions$fullName,
    RelationshipDefinitions$RelationshipName
  )
  VariableDefinitions$VariableName <- base::ifelse(
    !is.na(VariableDefinitions$fullName),
    VariableDefinitions$fullName,
    VariableDefinitions$VariableName
  )

  list(NameSpace = NameSpace, VariableDefinitions = VariableDefinitions, ValueTypeDefinitions = ValueTypeDefinitions,
       RelationshipDefinitions = RelationshipDefinitions, OntologyInfo = OntologyInfo)
}

#' Plot Ontology Tree
#'
#' Generates an ontology tree visualization from the provided value type, relationship, and variable definitions.
#'
#' @param ValueTypeDefinitions Data frame for Value Type Definitions.
#' @param RelationshipDefinitions Data frame for Relationship Definitions.
#' @param VariableDefinitions Data frame for Variable Definitions.
#' @param include_valuetype Logical indicating whether to include value types in the plot.
#'
#' @return A DiagrammeR graph object representing the ontology tree visualization.
#'
#' @importFrom dplyr bind_rows filter
#' @importFrom DiagrammeR create_graph add_node add_edge render_graph add_global_graph_attrs
#' @importFrom DiagrammeRsvg export_svg
#' @importFrom stringr str_replace_all
#' @importFrom utils head
#' @noRd
plot_ontology_tree2 <- function(ValueTypeDefinitions, RelationshipDefinitions, VariableDefinitions, include_valuetype = TRUE) {

  ValueTypeDefinitions$ValueTypeName <- paste(ValueTypeDefinitions$ValueTypeName, seq_len(nrow(ValueTypeDefinitions)) + 2, sep = ";")
  ValueTypeDefinitions$Range <- paste(ValueTypeDefinitions$Range, seq_len(nrow(ValueTypeDefinitions)), sep = ";")
  ValueTypeDefinitions$RelNodeID <- ValueTypeDefinitions$ValueTypeName

  RelationshipDefinitions$RelationshipName <- paste(RelationshipDefinitions$RelationshipName, seq_len(nrow(RelationshipDefinitions)), sep = ";")
  col_number <- which(names(RelationshipDefinitions) == "PropertyName")

  RelationshipDefinitions$PropertyName <- apply(RelationshipDefinitions, 1, function(x, col_num) {
    paste(x[col_num], paste(1, which(x == x[col_num]), col_num, sep = ":"), sep = ";")
  }, col_num = col_number)

  VariableDefinitionsEdges <- dplyr::filter(VariableDefinitions, !is.na(VariableDefinitions$ParentVariable))
  VariableDefinitionsEdges$RelNodeID <- paste("rdfs:SubclassOf", seq_len(nrow(VariableDefinitionsEdges)), sep = ";")

  VariableDefinitionsEdges2 <- dplyr::filter(VariableDefinitions, !is.na(VariableDefinitions$Unit))
  VariableDefinitionsEdges2$RelNodeID <- paste("pmd:unit", seq_len(nrow(VariableDefinitionsEdges2)), sep = ";")
  VariableDefinitionsEdges2$Unit <- paste(VariableDefinitionsEdges2$Unit, seq_len(nrow(VariableDefinitionsEdges2)), sep = ";")

  RelationshipDefinitionsEdges <- dplyr::filter(RelationshipDefinitions, !is.na(RelationshipDefinitions$Range))
  RelationshipDefinitionsEdges$RelationshipName <- paste(RelationshipDefinitionsEdges$RelationshipName, seq_len(nrow(RelationshipDefinitionsEdges)), sep = ";")
  RelationshipDefinitionsValues <- dplyr::filter(ValueTypeDefinitions, !is.na(ValueTypeDefinitions$Range))
  RelationshipDefinitionsValues$DataPropertyRange <- paste(RelationshipDefinitionsValues$Range, seq_len(nrow(RelationshipDefinitionsValues)), sep = ";")

  edges_from_relationship <- data.frame(
    from = RelationshipDefinitionsEdges$Domain,
    to = RelationshipDefinitionsEdges$RelationshipName,
    rel = RelationshipDefinitionsEdges$RelationshipName
  )
  edges_to_relationship <- data.frame(
    from = RelationshipDefinitionsEdges$RelationshipName,
    to = RelationshipDefinitionsEdges$Range,
    rel = RelationshipDefinitionsEdges$RelationshipName
  )
  edges_from_value <- data.frame(
    from = ValueTypeDefinitions$Domain,
    to = ValueTypeDefinitions$ValueTypeName,
    rel = ValueTypeDefinitions$ValueTypeName
  )
  edges_to_value <- data.frame(
    from = ValueTypeDefinitions$ValueTypeName,
    to = ValueTypeDefinitions$Range,
    rel = ValueTypeDefinitions$ValueTypeName
  )
  edges_to_var <- data.frame(
    from = VariableDefinitionsEdges$ParentVariable,
    to = VariableDefinitionsEdges$RelNodeID,
    rel = VariableDefinitionsEdges$RelNodeID
  )
  edges_from_var <- data.frame(
    from = VariableDefinitionsEdges$RelNodeID,
    to = VariableDefinitionsEdges$VariableName,
    rel = VariableDefinitionsEdges$RelNodeID
  )
  edges_to_unit <- data.frame(
    from = VariableDefinitionsEdges2$VariableName,
    to = VariableDefinitionsEdges2$RelNodeID,
    rel = VariableDefinitionsEdges2$RelNodeID
  )
  edges_from_unit <- data.frame(
    from = VariableDefinitionsEdges2$RelNodeID,
    to = VariableDefinitionsEdges2$Unit,
    rel = VariableDefinitionsEdges2$RelNodeID
  )

  if (!include_valuetype) {
    edges <- dplyr::bind_rows(edges_from_relationship, edges_to_relationship, edges_to_var, edges_from_var)
    edges$style = ifelse(grepl("SubclassOf", edges$to) | grepl("SubclassOf", edges$from), "dotted", "bold")
  } else{
    edges <- dplyr::bind_rows(edges_from_relationship, edges_to_relationship, edges_from_value, edges_to_value, edges_to_var, edges_from_var, edges_to_unit, edges_from_unit)
    edges$style = ifelse(grepl("SubclassOf", edges$to) | grepl("SubclassOf", edges$from), "dotted", "bold")
  }
  if (!include_valuetype) {
    vertices <- dplyr::bind_rows(
      data.frame(name = edges_from_relationship$rel, type = "Relationship"),
      data.frame(name = edges_from_relationship$from, type = "Entity"),
      data.frame(name = edges_to_relationship$to, type = "Entity"),
      data.frame(name = edges_from_var$rel, type = "Relationship"),
      data.frame(name = edges_from_var$to, type = "Entity"),
      data.frame(name = edges_to_var$from, type = "Entity"))
  } else {
    vertices <- dplyr::bind_rows(
      data.frame(name = edges_from_relationship$rel, type = "Relationship"),
      data.frame(name = edges_from_relationship$from, type = "Entity"),
      data.frame(name = edges_to_relationship$to, type = "Entity"),
      data.frame(name = edges_from_value$rel, type = "Relationship"),
      data.frame(name = edges_from_value$from, type = "Entity"),
      data.frame(name = edges_to_value$to, type = "Value"),
      data.frame(name = edges_from_var$rel, type = "Relationship"),
      data.frame(name = edges_from_var$to, type = "Entity"),
      data.frame(name = edges_to_var$from, type = "Entity"),
      data.frame(name = edges_to_unit$rel, type = "Relationship"),
      data.frame(name = edges_from_unit$to, type = "Value"),
      data.frame(name = edges_to_unit$from, type = "Entity"))
  }

  vertices <- unique(vertices)

  vertices$fillcolor <- ifelse(grepl("SubclassOf", vertices$name), "white",
                               ifelse(vertices$type == "Entity", "royalblue1",
                                      ifelse(vertices$type == "Value", "yellow", "lightblue")))
  vertices$color <- ifelse(grepl("SubclassOf", vertices$name), "blue", "black")
  vertices$shape <- ifelse(vertices$type == "Entity", "rectangle",
                           ifelse(vertices$type == "Value", "ellipse", "rectangle"))
  vertices$size <- ifelse(vertices$type == "Entity", 1,
                          ifelse(vertices$type == "Value", .6, .8))
  vertices$fontcolor <- ifelse(vertices$type == "Entity", "white", "black")

  vertices$name <- gsub(" ", "", vertices$name)
  edges$rel <- gsub(" ", "", edges$rel)
  edges$from <- gsub(" ", "", edges$from)
  edges$to <- gsub(" ", "", edges$to)

  vertices <- vertices[!is.na(vertices$name) & !grepl("NA;", vertices$name), ]
  edges <- edges[stats::complete.cases(edges[, c("rel", "from", "to")]) & !grepl("NA;", edges$rel) & !grepl("NA;", edges$from) & !grepl("NA;", edges$to), ]

  g <- DiagrammeR::create_graph() %>%
    DiagrammeR::add_global_graph_attrs(
      attr = "overlap",
      value = "false",
      attr_type = "graph")

  for (i in 1:nrow(vertices)) {
    g <- DiagrammeR::add_node(g, label = vertices$name[i], type = vertices$type[i], node_aes = DiagrammeR::node_aes(color = vertices$color[i], fillcolor = vertices$fillcolor[i], shape = vertices$shape[i], fontcolor = vertices$fontcolor[i],
                                                                                                                    fontsize = 5, width = vertices$size[i], height = vertices$size[i]/2))
  }

  for (i in 1:nrow(edges)) {
    g <- DiagrammeR::add_edge(g, from = edges$from[i], to = edges$to[i], rel = edges$rel[i], edge_aes = DiagrammeR::edge_aes(style = edges$style[i], color = "black", penwidth = 1.5))
  }

  g$edges_df$rel <- gsub(";.*$", "", g$edges_df$rel)
  g$nodes_df$label <- gsub(";.*$", "", g$nodes_df$label)

  DiagrammeR::render_graph(g, layout = "tree", output = "graph", title = "Ontology Tree Visualization", as_svg = T)
}

#' Concatenate Unique Authors
#'
#' Concatenates unique author names from ontology information.
#'
#' @param OntologyInfo_t Data frame containing ontology information.
#' @param num_sheets Number of sheets in the ontology information.
#' @return Concatenated unique author names.
#' @noRd
concatenate_unique_authors <- function(OntologyInfo_t, num_sheets) {
  author_set <- c()

  # Helper function to clean and split author names
  clean_and_split_authors <- function(authors) {
    # Remove newlines and trim whitespace
    authors <- gsub("\n", "", authors)
    authors <- trimws(authors)
    # Split by commas
    author_list <- unlist(strsplit(authors, ",\\s*"))
    return(author_list)
  }

  # Initial authors from the first sheet
  authors_ont <- clean_and_split_authors(OntologyInfo_t[3, 2])
  author_set <- unique(c(author_set, authors_ont))

  # Process additional sheets
  for (j in 1:(num_sheets - 1)) {
    additional_authors <- clean_and_split_authors(OntologyInfo_t[5 * j + 3, 2])
    author_set <- unique(c(author_set, additional_authors))
  }

  # Reassemble the unique authors into a single string
  unique_authors <- paste(author_set, collapse = ", ")

  return(unique_authors)
}

#' Add Ontology to RDF Merge
#'
#' Adds ontology information to an RDF object from multiple ontology sources.
#'
#' @param rdf_obj RDF object to update.
#' @param OntologyInfo_t Data frame containing ontology information.
#' @param mergeTitle Optional title for the merged ontology.
#' @param mergeAuthor Optional author for the merged ontology.
#' @param mergeVersion Optional version for the merged ontology.
#' @param mergeURL Optional URL for the merged ontology.
#' @param mergedescription Optional description for the merged ontology.
#' @return Updated RDF object.
#' @noRd
add_ontology_to_rdf_merge <- function(rdf_obj, OntologyInfo_t, mergeTitle = NULL, mergeAuthor = NULL, mergeVersion = NULL, mergeURL = NULL, mergedescription = NULL) {

  num_sheets <- nrow(as.data.frame(OntologyInfo_t))/5

    subject_uri_ont <- subject_uri_ont <- paste0(mergeURL, "Ontology")
    url_ont <- mergeURL

  if (is.null(mergeTitle)) {
    title_ont <- "Merged"
    for (j in (1:num_sheets) - 1) {
      title_ont <- paste0(OntologyInfo_t[[5 * j + 5, 2]], "_", title_ont)
    }
  }else{
    title_ont <- mergeTitle
  }
  if (is.null(mergeAuthor)) {
    authors_ont <- concatenate_unique_authors(OntologyInfo_t, num_sheets = num_sheets)
  }else{
    authors_ont <- mergeAuthor
  }
  if (is.null(mergeVersion)) {
    version_ont <- "_"
  }else{
    version_ont <- mergeVersion
  }
  if (is.null(mergedescription)) {
    description_ont <- paste0(OntologyInfo_t[5,2], ": ", OntologyInfo_t[4,2])
    for (j in (2:num_sheets) - 1) {
      description_ont <- paste0(OntologyInfo_t[5 * j + 5,2], ": ", OntologyInfo_t[[5 * j + 4, 2]], "   ", description_ont)
    }
  }else{
    description_ont <- mergedescription
  }

  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    object = "http://www.w3.org/2002/07/owl#Ontology"
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://purl.org/dc/terms/creator",
    object = authors_ont
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#label",
    object = url_ont
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://purl.org/dc/terms/description",
    object = description_ont
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://purl.org/dc/terms/title",
    object = title_ont
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://www.w3.org/2002/07/owl#versionInfo",
    object = version_ont
  )

  return(rdf_obj)
}

#' Add Ontology to RDF Single
#'
#' Adds ontology information to an RDF object from a single ontology source.
#'
#' @param rdf_obj RDF object to update.
#' @param OntologyInfo_t Data frame containing ontology information.
#' @return Updated RDF object.
#' @noRd
add_ontology_to_rdf_single <- function(rdf_obj, OntologyInfo_t) {

  subject_uri_ont <- paste0(OntologyInfo_t[1,2], "Ontology")

  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    object = "http://www.w3.org/2002/07/owl#Ontology"
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://purl.org/dc/terms/creator",
    object = OntologyInfo_t[3, 2]
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://www.w3.org/1999/02/22-rdf-syntax-ns#label",
    object = OntologyInfo_t[1,2]
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://purl.org/dc/terms/description",
    object = OntologyInfo_t[4,2]
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://purl.org/dc/terms/title",
    object = OntologyInfo_t[5, 2]
  )
  rdflib::rdf_add(
    rdf_obj,
    subject = subject_uri_ont,
    predicate = "http://www.w3.org/2002/07/owl#versionInfo",
    object = OntologyInfo_t[2, 2]
  )

  return(rdf_obj)
}

#' Process Individual Ontology CSV Files
#'
#' Reads, processes, and combines ontology CSV files from a specified list of files.
#' Generates an ontology tree plot, saves it as SVG, and serializes the RDF object
#' to Turtle and JSON-LD formats with a specified output prefix.
#'
#' @param files A vector of file paths to the ontology CSV files.
#' @param output_dir Directory where the output files will be saved.
#' @param output_prefix A prefix to be added to the output files.
#' @param update_missing Logical indicating whether to update missing information in RDF.
#' @param include_valuetype Logical indicating whether to include value types in the plot.
#' @param mergeTitle A string containing Title for merged ontology metadata
#' @param mergeAuthor A string containing Author for merged ontology metadata
#' @param mergeVersion A string containing Version for merged ontology metadata
#' @param mergeURL A string containing URL for merged ontology metadata
#' @param mergedescription A string containing description for merged ontology metadata
#' @return NULL
#'
#' @importFrom dplyr bind_rows %>%
#' @importFrom tidyr replace_na
#' @importFrom DiagrammeR create_graph render_graph add_node add_edge add_global_graph_attrs
#' @importFrom rdflib rdf rdf_add rdf_serialize
#' @importFrom grDevices svg dev.off
#' @importFrom readr read_csv
#' @import jsonld
#' @noRd
process_files <- function(files, output_dir, output_prefix = "", include_valuetype, update_missing, mergeTitle = NULL, mergeAuthor = NULL, mergeVersion = NULL, mergeURL = NULL, mergedescription = NULL) {
  NameSpace_list <- list()
  VariableDefinitions_list <- list()
  ValueTypeDefinitions_list <- list()
  RelationshipDefinitions_list <- list()
  OntologyInfo_list <- list()

  suppressWarnings(suppressMessages({
    for (file in files) {
      data <- tryCatch(readr::read_csv(file), error = function(e) NULL)
      if (!is.null(data)) {
        col_names <- colnames(data)
        if (length(col_names) == 0) next
        first_col <- col_names[1]
        if (first_col == "Prefix Name") {
          NameSpace_list <- append(NameSpace_list, list(data))
        } else if (first_col == "Variable Name") {
          VariableDefinitions_list <- append(VariableDefinitions_list, list(data))
        } else if (first_col == "ValueType Name") {
          ValueTypeDefinitions_list <- append(ValueTypeDefinitions_list, list(data))
        } else if (first_col == "Relationship Name") {
          RelationshipDefinitions_list <- append(RelationshipDefinitions_list, list(data))
        } else if (first_col == "Ontology Name\n*Name of the ontology*") {
          OntologyInfo_list <- append(OntologyInfo_list, list(data))
        } else {
          next
        }
      }
    }
  }))

  # Check if all required data frames are populated
  if (length(NameSpace_list) == 0 | length(VariableDefinitions_list) == 0 |
      length(ValueTypeDefinitions_list) == 0 | length(RelationshipDefinitions_list) == 0 |
      length(OntologyInfo_list) == 0) {
    stop("Missing required CSV files in the folder.")
  }

  NameSpace_t <- data.frame()
  VariableDefinitions_t <- data.frame()
  ValueTypeDefinitions_t <- data.frame()
  RelationshipDefinitions_t <- data.frame()
  OntologyInfo_t <- data.frame()

  rdf_temp <- rdf()
  for (i in 1:length(NameSpace_list)) {
    suppressWarnings(suppressMessages({
      cleaned_data <- clean_data_frames(as.data.frame(NameSpace_list[[i]]), as.data.frame(VariableDefinitions_list[[i]]), as.data.frame(ValueTypeDefinitions_list[[i]]), as.data.frame(RelationshipDefinitions_list[[i]]), as.data.frame(OntologyInfo_list[[i]]))

      NameSpace <- cleaned_data$NameSpace
      VariableDefinitions <- cleaned_data$VariableDefinitions
      ValueTypeDefinitions <- cleaned_data$ValueTypeDefinitions
      RelationshipDefinitions <- cleaned_data$RelationshipDefinitions
      OntologyInfo <- cleaned_data$OntologyInfo

      NameSpace_t <- dplyr::bind_rows(NameSpace_t, cleaned_data$NameSpace)
      VariableDefinitions_t <- dplyr::bind_rows(VariableDefinitions_t, VariableDefinitions)
      ValueTypeDefinitions_t <- dplyr::bind_rows(ValueTypeDefinitions_t, ValueTypeDefinitions)
      RelationshipDefinitions_t <- dplyr::bind_rows(RelationshipDefinitions_t, RelationshipDefinitions)
      OntologyInfo_t <- dplyr::bind_rows(OntologyInfo_t, OntologyInfo)
    }))

    rdf_temp <- c(generate_rdf_obj(NameSpace, ValueTypeDefinitions, RelationshipDefinitions, VariableDefinitions, OntologyInfo, update_missing = update_missing), rdf_temp)
  }

  #rdf_temp <- generate_rdf_obj(NameSpace_t, ValueTypeDefinitions_t, RelationshipDefinitions_t, VariableDefinitions_t, OntologyInfo, update_missing = update_missing)

  if (length(NameSpace_list) > 1) {
    rdf_temp <- add_ontology_to_rdf_merge(rdf_temp, OntologyInfo_t, mergeTitle = mergeTitle, mergeAuthor = mergeAuthor, mergeVersion = mergeVersion, mergeURL = mergeURL, mergedescription = mergedescription)
    base <-  mergeURL
  }else{
    rdf_temp <- add_ontology_to_rdf_single(rdf_temp, OntologyInfo_t)
    base <- OntologyInfo_t[1,2]
  }

  # Plot ontology tree
  plot <- plot_ontology_tree2(ValueTypeDefinitions_t, RelationshipDefinitions_t, VariableDefinitions_t, include_valuetype = include_valuetype)
  svg_code <- DiagrammeRsvg::export_svg(plot)
  svg_path <- normalizePath(file.path(output_dir, paste0(output_prefix, "ontology_plot-output.svg")), mustWork = FALSE)
  xml2::write_xml(xml2::read_xml(svg_code), svg_path)

  # Serialize RDF object
  turtle_path <- normalizePath(file.path(output_dir, paste0(output_prefix, "ontology_data-output.ttl")), mustWork = FALSE)
  jsonld_path <- normalizePath(file.path(output_dir, paste0(output_prefix, "ontology_data-output.jsonld")), mustWork = FALSE)
  namespace <- generate_namespace(NameSpace_t, OntologyInfo_t, mergeURL = mergeURL, mergeTitle = mergeTitle)
  serialize_rdf_obj(rdf_temp, namespace = namespace, turtle_path, "turtle", base = base)
  serialize_rdf_obj(rdf_temp, namespace = namespace, jsonld_path, "jsonld", base = base)
}

#' Generate Namespace from Data Frame
#'
#' @param NameSpace1 Data frame containing prefix names and ontology URLs.
#' @param OntologyInfo_t Data frame containing Ontology Info
#' @param mergeURL string URL for merged data set (optional)
#' @param mergeTitle string title for merged data set (optional)
#' @return Combined namespace vector.
#' @noRd
generate_namespace <- function(NameSpace1, OntologyInfo_t, mergeURL = NULL, mergeTitle = NULL) {

  default_ns <- c(sd = "http://www.w3.org/2001/XMLSchema#",
                  owl = "http://www.w3.org/2002/07/owl#",
                  rdfs = "http://www.w3.org/2000/01/rdf-schema#",
                  rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  xsd = "http://www.w3.org/2001/XMLSchema#",
                  skos = "http://www.w3.org/2004/02/skos/core#",
                  pmd = "https://w3id.org/pmd/co/",
                  PMDCo = "https://w3id.org/pmd/co#",
                  QUDT = "https://qudt.org/vocab/unit/",
                  dcterms = "http://purl.org/dc/terms/"
  )

  num_sheets <- nrow(as.data.frame(OntologyInfo_t))/5
  for (j in (1:num_sheets) - 1) {
    default_ns[as.character(OntologyInfo_t[5 * j + 5,2])] <- as.character(OntologyInfo_t[5 * j + 1,2])
  }

  # Function to extract namespaces from a single data frame
  extract_from_df <- function(NameSpace) {
    ns_vector <- base::vector()
    for (x in 1:base::nrow(NameSpace)) {
      ns_vector[NameSpace$PrefixName[x]] <- NameSpace$OntologyURL[x]
    }

    num_sheets <- nrow(as.data.frame(OntologyInfo_t))/5

    if (!is.null(mergeURL)) {
      if (!is.null(mergeTitle)) {
        ns_vector[mergeTitle] <- mergeURL
      }
      else{
        itle_ont <- "Merged"
        for (j in (1:num_sheets) - 1) {
          title_ont <- paste(OntologyInfo_t[[5 * j + 5, 2]], title_ont)
        }
        ns_vector[title_ont] <- mergeURL
      }
    }

    ns_vector <- c(ns_vector, default_ns)
    ns_vector <- ns_vector[!duplicated(names(ns_vector), fromLast = TRUE)]

    return(ns_vector)
  }

  # Extract namespaces from the first data frame
  namespace <- extract_from_df(NameSpace1)

  return(namespace)
}

#' Get RDF Data
#'
#' Retrieves RDF data from a specified subject URI.
#'
#' @param subject Subject URI to retrieve data from.
#' @return RDF model.
#' @noRd
get_rdf_data <- function(subject) {
  base_url <- substr(subject, 0, stringr::str_length(subject) - (stringr::str_length(extract_term(subject)) + 1))
  response <- httr::GET(base_url)
  content_type <- httr::http_type(response)

  if (content_type %in% c("text/turtle", "application/rdf+xml")) {
    ext <- if (content_type == "text/turtle") ".ttr" else ".xml"
    temp_file <- base::tempfile(fileext = ext)

    base::writeBin(httr::content(response, "raw"), temp_file)
    rdf_model <- rdflib::rdf_parse(temp_file)
    base::unlink(temp_file)

    return(rdf_model)
  } else {
    stop("Unsupported content type")
  }
}

#' Add Info
#'
#' Adds information from a subject URI to an RDF object.
#'
#' @param subject Subject URI to retrieve information from.
#' @param predicate Predicate URI to retrieve information from.
#' @param rdf_obj RDF object to update.
#' @return Updated RDF object.
#' @noRd
add_info <- function(subject, predicate, rdf_obj) {
  s <- NULL
  namespace_model <- tryCatch({
    get_rdf_data(subject)
  }, error = function(e) {
    stop("Error retrieving RDF data")
  })

  namespace_model_triples <- rdflib::rdf_query(namespace_model, "SELECT ?s ?p ?o WHERE { ?s ?p ?o }")
  rdflib::rdf_free(namespace_model)

  namespace_model_triples <- dplyr::filter(namespace_model_triples, stringr::str_ends(s, extract_term(subject)))

  if (nrow(namespace_model_triples) == 0) {
    message("No additional information found")
  } else {
    apply(namespace_model_triples, 1, function(row) {
      if (!stringr::str_starts(row["o"], "_:r")) {
        rdflib::rdf_add(rdf_obj, row["s"], row["p"], row["o"])
        message(paste0(extract_term(row["o"]), " added to ", extract_term(row["s"]), " ", extract_term(row["p"])))
      }
    })
  }
  return(rdf_obj)
}


#' Update Missing Info
#'
#' Updates missing information in an RDF object using namespaces.
#'
#' @param rdf_obj RDF object to update.
#' @param namespace1 List of namespaces.
#' @return Updated RDF object.
#' @noRd
update_missing_info <- function(rdf_obj, namespace1) {
  s <- NULL
  triples <- rdflib::rdf_query(rdf_obj, "SELECT ?s ?p ?o WHERE { ?s ?p ?o }")
  updated_rdf <- rdflib::rdf()  # Create a new RDF object to store updated triples

  unique_subjects <- unique(triples$s)

  for (subject in unique_subjects) {
    subject_triples <- dplyr::filter(triples, s == subject)

    for (row in seq_len(nrow(subject_triples))) {
      predicate <- as.character(subject_triples$p[row])
      object <- as.character(subject_triples$o[row])

      if (object == "_") {
        message(paste(extract_term(subject), ": "))
        updated_rdf <- tryCatch({
          add_info(subject, predicate, updated_rdf)
        }, error = function(e) {
          message(paste("Error parsing namespace:", subject, ". Ensure URL in Name Space leads to owl/ttr or xml/rdf file."))
          updated_rdf
        })
      } else {
        rdflib::rdf_add(updated_rdf, subject, predicate, object)
      }
    }
  }

  return(updated_rdf)
}



