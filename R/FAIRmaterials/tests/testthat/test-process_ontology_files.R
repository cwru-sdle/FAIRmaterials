library(testthat)
library(FAIRmaterials)

test_that("The output files are correctly generated for PV data", {
  # Create a temporary directory
  temp_dir <- tempdir()
  PV_test_folder <- file.path(temp_dir, "PV")
  dir.create(PV_test_folder, recursive = TRUE)

  # Copy CSV files from the package's extdata to the temporary directory
  extdata_path <- system.file("extdata", "PV", package = "FAIRmaterials")
  file.copy(from = list.files(extdata_path, full.names = TRUE),
            to = PV_test_folder,
            recursive = TRUE)

  # Process the CSV files in the PV folder
  process_ontology_files(PV_test_folder, add_external_onto_info = FALSE)

  # Check if the expected TTL output file exists
  expect_true(file.exists(file.path(PV_test_folder, "ontology_data-output.ttl")),
              "TTL output file is missing for PV data")

  # Check if the expected JSON-LD output file exists
  expect_true(file.exists(file.path(PV_test_folder, "ontology_data-output.jsonld")),
              "JSON-LD output file is missing for PV data")

  # Check if the expected SVG plot output file exists
  expect_true(file.exists(file.path(PV_test_folder, "ontology_plot-output.svg")),
              "SVG plot output file is missing for PV data")

  # Clean up: Remove temporary directory and all contents
  unlink(temp_dir, recursive = TRUE)
})

test_that("The output files are correctly generated for XRay data", {
  # Create a temporary directory
  temp_dir <- tempdir()
  XRay_test_folder <- file.path(temp_dir, "XRay")
  dir.create(XRay_test_folder, recursive = TRUE)

  # Copy CSV files from the package's extdata to the temporary directory
  extdata_path <- system.file("extdata", "XRay", package = "FAIRmaterials")
  file.copy(from = list.files(extdata_path, full.names = TRUE),
            to = XRay_test_folder,
            recursive = TRUE)

  # Process the CSV files in the XRay folder
  process_ontology_files(XRay_test_folder, add_external_onto_info = FALSE)

  # Check if the expected TTL output file exists
  expect_true(file.exists(file.path(XRay_test_folder, "ontology_data-output.ttl")),
              "TTL output file is missing for XRay data")

  # Check if the expected JSON-LD output file exists
  expect_true(file.exists(file.path(XRay_test_folder, "ontology_data-output.jsonld")),
              "JSON-LD output file is missing for XRay data")

  # Check if the expected SVG plot output file exists
  expect_true(file.exists(file.path(XRay_test_folder, "ontology_plot-output.svg")),
              "SVG plot output file is missing for XRay data")

  # Clean up: Remove temporary directory and all contents
  unlink(temp_dir, recursive = TRUE)
})

test_that("Output files are correctly generated and different with external ontology info for XRay data", {
  # Create a temporary directory
  temp_dir <- tempdir()
  XRay_test_folder <- file.path(temp_dir, "XRay")
  dir.create(XRay_test_folder, recursive = TRUE)

  # Copy CSV files from the package's extdata to the temporary directory
  extdata_path <- system.file("extdata", "XRay", package = "FAIRmaterials")
  file.copy(from = list.files(extdata_path, full.names = TRUE),
            to = XRay_test_folder,
            recursive = TRUE)

  # Process the CSV files in the XRay folder
  process_ontology_files(XRay_test_folder, add_external_onto_info = FALSE)

  original_ttl <- readLines(file.path(XRay_test_folder, "ontology_data-output.ttl"))
  original_jsonld <- readLines(file.path(XRay_test_folder, "ontology_data-output.jsonld"))

  XRay_comp_folder <- file.path(temp_dir, "XRay_comp")
  dir.create(XRay_comp_folder, recursive = TRUE)

  # Copy CSV files from the package's extdata to the temporary directory
  extdata_path <- system.file("extdata", "XRay", package = "FAIRmaterials")
  file.copy(from = list.files(extdata_path, full.names = TRUE),
            to = XRay_comp_folder,
            recursive = TRUE)


  # Re-run processing with external ontology info
  process_ontology_files(XRay_comp_folder, add_external_onto_info = TRUE)

  # Load new outputs
  new_ttl <- readLines(file.path(XRay_comp_folder, "ontology_data-output.ttl"))
  new_jsonld <- readLines(file.path(XRay_comp_folder, "ontology_data-output.jsonld"))

  # Assert that files have changed as expected
  expect_false(identical(original_ttl, new_ttl),
               "TTL file content should change with external ontology information")
  expect_false(identical(original_jsonld, new_jsonld),
               "JSON-LD file content should change with external ontology information")

  # Clean up: Remove temporary directory and all contents
  unlink(temp_dir, recursive = TRUE)
})

test_that("Output files are correctly generated and different with value type inclusion for XRay data", {
  # Create a temporary directory
  temp_dir <- tempdir()
  XRay_test_folder <- file.path(temp_dir, "XRay")
  dir.create(XRay_test_folder, recursive = TRUE)

  # Copy CSV files from the package's extdata to the temporary directory
  extdata_path <- system.file("extdata", "XRay", package = "FAIRmaterials")
  file.copy(from = list.files(extdata_path, full.names = TRUE),
            to = XRay_test_folder,
            recursive = TRUE)

  # Process the CSV files in the XRay folder
  process_ontology_files(XRay_test_folder, include_graph_valuetype = TRUE)

  # Save the SVG output for comparison
  svg_with_value_types <- readLines(file.path(XRay_test_folder, "ontology_plot-output.svg"))

  XRay_comp_folder <- file.path(temp_dir, "XRay_comp")
  dir.create(XRay_comp_folder, recursive = TRUE)

  # Copy CSV files from the package's extdata to the temporary directory
  extdata_path <- system.file("extdata", "XRay", package = "FAIRmaterials")
  file.copy(from = list.files(extdata_path, full.names = TRUE),
            to = XRay_comp_folder,
            recursive = TRUE)


  # Re-run processing with external ontology info
  process_ontology_files(XRay_comp_folder, include_graph_valuetype = FALSE)

  # Load new SVG output
  svg_without_value_types <- readLines(file.path(XRay_comp_folder, "ontology_plot-output.svg"))

  # Assert that SVG files have changed as expected
  expect_false(identical(svg_with_value_types, svg_without_value_types),
               "SVG plot content should change with value type inclusion")

  # Clean up: Remove temporary directory and all contents
  unlink(temp_dir, recursive = TRUE)
})

test_that("The output files are correctly generated for merged data", {
  # Create a temporary directory
  temp_dir <- tempdir()
  test_folder <- file.path(temp_dir, "output")
  dir.create(test_folder, recursive = TRUE)

  # Copy CSV files from the package's extdata to the temporary directory
  extdata_path <- system.file("extdata", package = "FAIRmaterials")
  file.copy(from = list.files(extdata_path, full.names = TRUE),
            to = test_folder,
            recursive = TRUE)

  # Process the CSV files in the mereged folder
  process_ontology_files(test_folder, add_external_onto_info = FALSE,
                         merge_title = "MergedPVandXRay",
                         merge_base_uri = "https://cwrusdle.bitbucket.io/OntologyFilesOwl/Ontology/",
                         merge_version = "1.0")

  # Check if the expected TTL output file exists in subdirectories
  sub_dirs <- list.dirs(test_folder, recursive = TRUE, full.names = TRUE)
  for (sub_dir in sub_dirs) {
    if (sub_dir == test_folder) {next}
    sub_dir_foldername <- basename(sub_dir)
    # Check if the expected TTL output file exists
    expect_true(file.exists(file.path(sub_dir, paste0(sub_dir_foldername, "_ontology_data-output.ttl"))),
                paste("TTL output file is missing in", sub_dir_foldername))

    # Check if the expected JSON-LD output file exists
    expect_true(file.exists(file.path(sub_dir, paste0(sub_dir_foldername, "_ontology_data-output.jsonld"))),
                paste("JSON-LD output file is missing in", sub_dir_foldername))

    # Check if the expected SVG plot output file exists
    expect_true(file.exists(file.path(sub_dir, paste0(sub_dir_foldername, "_ontology_plot-output.svg"))),
                paste("SVG plot output file is missing in", sub_dir_foldername))
  }

  # Check if the expected TTL output file exists
  expect_true(file.exists(file.path(test_folder, "ontology_data-output.ttl")),
              "TTL output file is missing in data")

  # Check if the expected JSON-LD output file exists
  expect_true(file.exists(file.path(test_folder, "ontology_data-output.jsonld")),
             "JSON-LD output file is missing in data")

  # Check if the expected SVG plot output file exists
  expect_true(file.exists(file.path(test_folder, "ontology_plot-output.svg")),
              "SVG plot output file is missing in data")

  # Clean up: Remove temporary directory and all contents
  unlink(temp_dir, recursive = TRUE)
})
