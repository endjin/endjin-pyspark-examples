from datetime import date as date_type

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, LongType, IntegerType, ByteType, IntegerType,
    DoubleType, FloatType, BooleanType, DateType, TimestampType, DecimalType,
)


def behave_table_to_spark_dataframe(spark: SparkSession, table) -> DataFrame:
    if ":" in table.headings[0]:
        return _with_explicit_schema(spark, table)
    else:
        return _with_inferred_schema(spark, table)


def _with_explicit_schema(spark: SparkSession, table) -> DataFrame:
    cols = [h.split(":", 1) for h in table.headings]
    schema = StructType([
        StructField(name, _to_spark_type(field_type), True)
        for name, field_type in cols
    ])

    rows = []
    for row in table:
        record = {}
        for (name, field_type), cell in zip(cols, row.cells):
            if cell in ("", "null"):
                record[name] = None
            elif field_type.lower().startswith("date"):
                record[name] = date_type.fromisoformat(cell)
            elif field_type.lower() in ("int", "integer", "long", "integer32", "integer8"):
                record[name] = int(cell)
            elif field_type.lower() in ("float", "double"):
                record[name] = float(cell)
            elif field_type.lower() in ("bool", "boolean"):
                record[name] = cell.lower() == "true"
            else:
                record[name] = cell
        rows.append(record)

    if not rows:
        return spark.createDataFrame([], schema)
    return spark.createDataFrame(rows, schema)


def _with_inferred_schema(spark: SparkSession, table) -> DataFrame:
    headings = table.headings
    rows = [
        {headings[i]: (cell if cell != "" else None) for i, cell in enumerate(row.cells)}
        for row in table
    ]
    return spark.createDataFrame(rows)


def compare_spark_dataframes(expected: DataFrame, actual: DataFrame):
    """Compare two DataFrames ignoring column order and row order, using string equality."""
    cols = sorted(expected.columns)

    def to_sorted_tuples(df: DataFrame):
        rows = [
            tuple(str(v) if v is not None else None for v in r)
            for r in df.select(cols).collect()
        ]
        return sorted(rows, key=lambda t: tuple("\x00" if v is None else v for v in t))

    expected_rows = to_sorted_tuples(expected)
    actual_rows = to_sorted_tuples(actual)

    assert expected_rows == actual_rows, (
        f"DataFrames don't match.\nExpected:\n{expected_rows}\nActual:\n{actual_rows}"
    )


def _to_spark_type(type_name: str):
    t = type_name.lower()
    if t.startswith("date"):
        return DateType()
    return {
        "int": LongType(),
        "integer": LongType(),
        "long": LongType(),
        "integer8": ByteType(),
        "integer32": IntegerType(),
        "float": DoubleType(),
        "double": DoubleType(),
        "boolean": BooleanType(),
        "bool": BooleanType(),
        "timestamp": TimestampType(),
        "string": StringType(),
        "str": StringType(),
        "decimal": DecimalType(10, 2),
    }.get(t, StringType())
