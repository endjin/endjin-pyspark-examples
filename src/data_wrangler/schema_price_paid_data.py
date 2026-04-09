from typing import Any

import pandera.pyspark as pa
from pyspark.sql import DataFrame


class SchemaValidationError(Exception):
    pass


def _raise_if_errors(result: DataFrame) -> DataFrame:
    """Check the pandera error accessor and raise SchemaValidationError if any errors exist."""
    errors: Any = result.pandera.errors  # type: ignore[union-attr]
    if errors:
        messages = []
        for category, checks in errors.items():
            for check_name, failures in checks.items():
                for failure in failures:
                    messages.append(
                        f"[{category}/{check_name}] column='{failure['column']}' "
                        f"check='{failure['check']}': {failure['error']}"
                    )
        raise SchemaValidationError("\n".join(messages))
    return result


class _PricePaidDataSchema:

    _schema = pa.DataFrameSchema(
        {
            "id": pa.Column("string", nullable=False),
            "price": pa.Column("long", checks=pa.Check.greater_than(0), nullable=False),
            "date": pa.Column("date", nullable=False),
            "postcode": pa.Column("string", nullable=True),
            "property_type": pa.Column(
                "string",
                checks=pa.Check.isin(["D", "S", "T", "F", "O"]),
                nullable=False,
            ),
            "old_new": pa.Column(
                "string",
                checks=pa.Check.isin(["Y", "N"]),
                nullable=False,
            ),
            "duration": pa.Column("string", nullable=False),
            "paon": pa.Column("string", nullable=True),
            "saon": pa.Column("string", nullable=True),
            "street": pa.Column("string", nullable=True),
            "locality": pa.Column("string", nullable=True),
            "town_city": pa.Column("string", nullable=True),
            "district": pa.Column("string", nullable=True),
            "county": pa.Column("string", nullable=True),
            "ppd_category": pa.Column(
                "string",
                checks=pa.Check.isin(["A", "B"]),
                nullable=False,
            ),
            "record_type": pa.Column(
                "string",
                checks=pa.Check.isin(["A", "C", "D"]),
                nullable=False,
            ),
        }
    )

    def validate(self, df: DataFrame) -> DataFrame:
        result = self._schema.validate(df)
        return _raise_if_errors(result)


price_paid_data_schema = _PricePaidDataSchema()
