from minio import Minio
import time
from pyspark.sql import SparkSession
from pyspark.sql.window import Window
import pyspark.sql.functions as F
from pathlib import Path
import os
import numpy as np
from functools import reduce


BASE_DIR = Path(__file__).resolve().parents[2]

BASE_DIR.mkdir(parents=True, exist_ok=True)


DATA_DIR = BASE_DIR / "data"


all_dfs = []


def compute_rsi(df, n=20):
	"""
	Adds a single 'rsi' column to the DataFrame.
	n: number of periods for RSI (default 14)
	"""
	# Define rolling window
	window = Window.orderBy("date").rowsBetween(-n, 0)

    # Compute gains and losses
	df = df.withColumn(
        "gain", F.when(F.col("close") - F.lag("close").over(Window.orderBy("date")) > 0,
                       F.col("close") - F.lag("close").over(Window.orderBy("date"))).otherwise(0)
	).withColumn(
        "loss", F.when(F.lag("close").over(Window.orderBy("date")) - F.col("close") > 0,
                       F.lag("close").over(Window.orderBy("date")) - F.col("close")).otherwise(0)
	)

    # Compute rolling average gain/loss
	df = df.withColumn("avg_gain", F.avg("gain").over(window))
	df = df.withColumn("avg_loss", F.avg("loss").over(window))

    # Compute RSI
	df = df.withColumn("rsi", 100 - (100 / (1 + (F.try_divide(F.col("avg_gain"), F.col("avg_loss"))))))

    # Drop intermediate columns
	df = df.drop("gain", "loss", "avg_gain", "avg_loss")

	return df


def generate_features(df):
	w = Window.orderBy('date')
	# Return 1 Day
	df = df.withColumn("return_1d", (F.col("close") - F.lag("close", 1).over(w)) / F.lag("close", 1).over(w))
	# Log Return
	df = df.withColumn("log_return", F.log(F.col("close") / F.lag("close", 1).over(w)))
	
	df = df.withColumn("high_low", F.col("high") - F.col("low"))

	df = df.withColumn("close_open", F.col("close") - F.col("open"))


	# SMA (Simple Moving Average)
	w_sma = Window.orderBy("date").rowsBetween(-19, 0)
	df = df.withColumn("sma_20", F.avg("close").over(w_sma))
	df = compute_rsi(df)
	df = df.dropna()

	return df

def clean_preprocess(spark, file_paths: list):
	all_dfs = []
	for file_path in file_paths:
		df = spark.read.csv(file_path, sep=',', inferSchema=True, header=True)
		df = generate_features(df)
		all_dfs.append(df)
    
	combined_df = reduce(lambda df1, df2: df1.unionByName(df2), all_dfs)

	jdbc_url = "jdbc:postgresql://postgres:5432/warehouse"

	print(spark.sparkContext._conf.get("spark.jars"))

	combined_df.write \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "stocks") \
    .option("user", "admin") \
    .option("password", "password123") \
    .option("driver", "org.postgresql.Driver") \
    .mode("overwrite") \
    .save()

	return combined_df

	





def load_ingested_data(client, bucket_name="stock-data"):
	

	if not client.bucket_exists(bucket_name):
		raise ValueError(f"Bucket '{bucket_name}' does not exist")

	objects = list(client.list_objects(bucket_name, prefix="raw/", recursive=True))



	

	DATA_DIR.mkdir(parents=True, exist_ok=True)

	downloaded_files = []
	for obj in objects:
		file_name = Path(obj.object_name).name
		local_path = DATA_DIR / file_name

		client.fget_object(bucket_name, obj.object_name, str(local_path))
		print(f"Downloaded : {obj.object_name} --> {str(local_path)}")
		downloaded_files.append(str(local_path))

	return downloaded_files


