import os
import sys
from pyspark.sql import SparkSession

os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


def before_all(context):
    context.spark = (
        SparkSession.builder
        .master("local[1]")
        .appName("bdd-tests")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    context.spark.sparkContext.setLogLevel("ERROR")


def after_all(context):
    context.spark.stop()
