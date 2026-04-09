from behave import when, then
from common_steps import behave_table_to_spark_dataframe
from data_wrangler import DataWrangler


@when('I sort by year and property type')
def step_when_sort_by_year_and_property_type(context):
    context.df = DataWrangler.sort_by_year_and_property_type(context.df)


@then('the resulting dataset should be in the following order')
def step_then_ordered(context):
    expected = behave_table_to_spark_dataframe(context.spark, context.table)
    cols = expected.columns

    expected_rows = [
        tuple(str(v) if v is not None else None for v in r)
        for r in expected.collect()
    ]
    actual_rows = [
        tuple(str(v) if v is not None else None for v in r)
        for r in context.df.select(cols).collect()
    ]
    assert expected_rows == actual_rows, (
        f"DataFrames not in expected order.\nExpected:\n{expected_rows}\nActual:\n{actual_rows}"
    )
