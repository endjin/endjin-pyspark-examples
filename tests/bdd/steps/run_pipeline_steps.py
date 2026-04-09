import os
from behave import given, when, then
import pyspark.sql.functions as F
from data_wrangler import DataWrangler


TEST_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "test_data")


@given('land registry CSV files exist in the test data folder')
def step_given_test_data_exists(context):
    csv_files = [f for f in os.listdir(TEST_DATA_FOLDER) if f.endswith(".csv")]
    assert csv_files, f"No CSV files found in {TEST_DATA_FOLDER}"
    context.test_data_folder = TEST_DATA_FOLDER


@when('I run the pipeline')
def step_when_run_pipeline(context):
    context.result = DataWrangler.run_pipeline(context.test_data_folder)


@then('the result should be a non-empty summary DataFrame')
def step_then_non_empty(context):
    assert context.result is not None
    assert context.result.count() > 0, "Pipeline returned an empty DataFrame"


@then('the summary should contain the columns {columns}')
def step_then_columns(context, columns):
    expected = [c.strip() for c in columns.split(",")]
    actual = context.result.columns
    missing = [c for c in expected if c not in actual]
    assert not missing, f"Missing columns: {missing}"


@then('all property_type values should be from the renamed set {values}')
def step_then_property_type_values(context, values):
    allowed = {v.strip() for v in values.split(",")}
    actual = {
        r["property_type"]
        for r in context.result.select("property_type").dropna().collect()
    }
    unexpected = actual - allowed
    assert not unexpected, f"Unexpected property_type values: {unexpected}"


@then('all year values should be positive integers')
def step_then_year_positive(context):
    assert context.result.filter(F.col("year") <= 0).count() == 0, \
        "Found non-positive year values"


@then('all total_sales values should be greater than zero')
def step_then_total_sales_positive(context):
    assert context.result.filter(F.col("total_sales") <= 0).count() == 0, \
        "Found zero total_sales"


@then('all max_price values should be greater than or equal to min_price')
def step_then_max_gte_min(context):
    assert context.result.filter(F.col("max_price") < F.col("min_price")).count() == 0, \
        "Found rows where max_price < min_price"
