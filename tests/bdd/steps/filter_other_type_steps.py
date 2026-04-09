from behave import given, when, then
from common_steps import behave_table_to_spark_dataframe, compare_spark_dataframes
from data_wrangler import DataWrangler


@given('a dataset with the following rows')
def step_given_dataset(context):
    context.df = behave_table_to_spark_dataframe(context.spark, context.table)


@when('I filter out rows where property_type is other')
def step_when_filter_other(context):
    context.df = DataWrangler.filter_other_property_types(context.df)


@then('the resulting dataset should include the following rows')
def step_then_resulting_dataset(context):
    expected = behave_table_to_spark_dataframe(context.spark, context.table)
    compare_spark_dataframes(expected, context.df)
