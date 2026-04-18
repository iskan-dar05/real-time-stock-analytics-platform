from pyspark.sql import SparkSession



def get_spark_session():
	spark = SparkSession.builder.appName('Stock Analytics').config("spark.jars.packages", "org.postgresql:postgresql:42.7.3").getOrCreate()
	return spark












