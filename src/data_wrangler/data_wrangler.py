from datetime import date

from pyspark.sql import DataFrame, SparkSession
import pyspark.sql.functions as F


def _get_spark() -> SparkSession:
    return SparkSession.getActiveSession() or (
        SparkSession.builder
        .master("local")
        .appName("DataWrangler")
        .getOrCreate()
    )


class DataWrangler:

    COLUMN_NAMES = [
        "id", "price", "date", "postcode", "property_type",
        "old_new", "duration", "paon", "saon", "street",
        "locality", "town_city", "district", "county",
        "ppd_category", "record_type",
    ]

    @staticmethod
    def load_data(data_folder: str) -> DataFrame:
        """
        Scans all pp-*.csv files in data_folder as a lazy DataFrame, naming columns
        per the Land Registry positional schema and casting price/date to their
        native types.
        """
        spark = _get_spark()
        return (
            spark.read
            .option("header", False)
            .option("nullValue", "")
            .csv(f"{data_folder}/pp-*.csv")
            .toDF(*DataWrangler.COLUMN_NAMES)
            .withColumn("price", F.col("price").cast("long"))
            .withColumn("date", F.to_date("date", "yyyy-MM-dd HH:mm"))
        )

    @classmethod
    def run_pipeline(cls, data_folder: str) -> DataFrame:
        """
        Loads all CSVs from data_folder and runs the full transformation and
        summarisation pipeline, returning a summary DataFrame.
        """
        return (
            cls.load_data(data_folder)
            .transform(cls.drop_records_without_postcode)
            .transform(cls.drop_records_without_date)
            .transform(cls.filter_other_property_types)
            .transform(cls.extract_year_from_date)
            .transform(cls.rename_property_type)
            .transform(cls.rename_duration)
            .transform(cls.rename_old_new)
            .transform(cls.extract_postcode_area)
            .transform(cls.summarise_by_year_and_property_type)
            .transform(cls.sort_by_year_and_property_type)
        )

    @staticmethod
    def filter_other_property_types(df: DataFrame) -> DataFrame:
        return df.filter(F.col("property_type") != "O")

    @staticmethod
    def extract_year_from_date(df: DataFrame) -> DataFrame:
        return df.withColumn("year", F.year("date"))

    @staticmethod
    def build_date_dimension_table(start_date: date, end_date: date) -> DataFrame:
        """
        Builds a date dimension table for the inclusive range [start_date, end_date].
        Returns a DataFrame with one row per date and columns: date, year, month,
        month_name, day, day_name, weekday (ISO: Mon=1, Sun=7), is_weekend, is_leap_year.
        """
        spark = _get_spark()
        days = (end_date - start_date).days + 1
        return (
            spark.range(days)
            .select(
                F.date_add(F.lit(start_date.isoformat()), F.col("id").cast("int")).alias("date")
            )
            .withColumn("year", F.year("date"))
            .withColumn("month", F.month("date"))
            .withColumn("day", F.dayofmonth("date"))
            # PySpark dayofweek: Sun=1, Mon=2, ..., Sat=7  →  ISO Mon=1, Sun=7
            .withColumn("weekday", ((F.dayofweek("date") + 5) % 7 + 1))
            .withColumn("is_weekend", F.dayofweek("date").isin(1, 7))
            .withColumn(
                "is_leap_year",
                F.when(
                    (F.year("date") % 400 == 0) |
                    ((F.year("date") % 4 == 0) & (F.year("date") % 100 != 0)),
                    True,
                ).otherwise(False),
            )
            .withColumn("month_name", F.date_format("date", "MMMM"))
            .withColumn("day_name", F.date_format("date", "EEEE"))
        )

    @staticmethod
    def extract_postcode_area(df: DataFrame) -> DataFrame:
        """
        Extracts the postcode area (outward code) using strict UK postcode validation.
        Returns null for postcodes that do not match the standard format.
        """
        pattern = r"^([A-Z]{1,2}[0-9R][0-9A-Z]?) [0-9][ABD-HJLNP-UW-Z]{2}$"
        extracted = F.regexp_extract(F.col("postcode"), pattern, 1)
        return df.withColumn(
            "postcode_area",
            F.when(extracted != "", extracted).otherwise(F.lit(None).cast("string")),
        )

    @staticmethod
    def extract_postcode_district(df: DataFrame) -> DataFrame:
        """
        Extracts the postcode district (outward code) from the postcode column.
        Returns null for null or empty postcodes.
        """
        pattern = r"^([A-Z]{1,2}[0-9R][0-9A-Z]?)\s"
        extracted = F.regexp_extract(F.col("postcode"), pattern, 1)
        return df.withColumn(
            "postcode_district",
            F.when(extracted != "", extracted).otherwise(F.lit(None).cast("string")),
        )

    @staticmethod
    def drop_records_without_postcode(df: DataFrame) -> DataFrame:
        return df.filter(F.col("postcode").isNotNull() & (F.col("postcode") != ""))

    @staticmethod
    def drop_records_without_date(df: DataFrame) -> DataFrame:
        return df.filter(F.col("date").isNotNull())

    @staticmethod
    def rename_property_type(df: DataFrame) -> DataFrame:
        return df.withColumn(
            "property_type",
            F.when(F.col("property_type") == "D", "Detached")
             .when(F.col("property_type") == "S", "Semi-Detached")
             .when(F.col("property_type") == "T", "Terraced")
             .when(F.col("property_type") == "F", "Flat")
             .when(F.col("property_type") == "O", "Other")
             .otherwise(F.col("property_type")),
        )

    @staticmethod
    def rename_duration(df: DataFrame) -> DataFrame:
        return df.withColumn(
            "duration",
            F.when(F.col("duration") == "F", "Freehold")
             .when(F.col("duration") == "L", "Leasehold")
             .when(F.col("duration") == "U", "Unknown")
             .otherwise(F.col("duration")),
        )

    @staticmethod
    def rename_old_new(df: DataFrame) -> DataFrame:
        return df.withColumn(
            "old_new",
            F.when(F.col("old_new") == "Y", "New")
             .when(F.col("old_new") == "N", "Old")
             .otherwise(F.col("old_new")),
        )

    @staticmethod
    def sort_by_year_and_property_type(df: DataFrame) -> DataFrame:
        return df.orderBy("year", "property_type")

    @staticmethod
    def summarise_by_year_and_property_type(df: DataFrame) -> DataFrame:
        return df.groupBy("year", "property_type").agg(
            F.countDistinct("id").alias("total_sales"),
            F.max("price").alias("max_price"),
            F.min("price").alias("min_price"),
            F.expr("percentile(price, 0.5)").alias("median_price"),
        )
