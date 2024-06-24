library(testthat)

test_that("The output files are correctly generated for PV data", {
  # Create test folder path for PV data
  pv_test_folder <- system.file("extdata", "PV", package = "FAIRmaterials")

  # Process the CSV files in the PV folder
  process_ontology_files(pv_test_folder, add_external_onto_info = FALSE)

  # Check if the expected TTL output file exists
  expect_true(file.exists(file.path(pv_test_folder, "ontology_data-output.ttl")),
              "TTL output file is missing for PV data")

  # Check if the expected JSON-LD output file exists
  expect_true(file.exists(file.path(pv_test_folder, "ontology_data-output.jsonld")),
              "JSON-LD output file is missing for PV data")

  # Check if the expected SVG plot output file exists
  expect_true(file.exists(file.path(pv_test_folder, "ontology_plot-output.svg")),
              "SVG plot output file is missing for PV data")
})

test_that("The output files are correctly generated for XRay data", {
  # Create test folder path for XRay data
  xray_test_folder <- system.file("extdata", "XRay", package = "FAIRmaterials")

  # Process the CSV files in the XRay folder
  process_ontology_files(xray_test_folder, add_external_onto_info = FALSE)

  # Check if the expected TTL output file exists
  expect_true(file.exists(file.path(xray_test_folder, "ontology_data-output.ttl")),
              "TTL output file is missing for XRay data")

  # Check if the expected JSON-LD output file exists
  expect_true(file.exists(file.path(xray_test_folder, "ontology_data-output.jsonld")),
              "JSON-LD output file is missing for XRay data")

  # Check if the expected SVG plot output file exists
  expect_true(file.exists(file.path(xray_test_folder, "ontology_plot-output.svg")),
              "SVG plot output file is missing for XRay data")
})
