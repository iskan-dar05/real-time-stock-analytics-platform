from minio import Minio
from spark.jobs.load_preprocess import load_ingested_data, clean_preprocess
from spark.utils.spark_session import get_spark_session
import time






client = Minio(
	    "minio:9000",
	    access_key="admin",
	    secret_key="password123",
	    secure=False
	)


def wait_for_minio(client, bucket_name="stock-data", retries=10, delay=3):
	for i in range(retries):
		try:
			if client.list_buckets():
				print("✅ MinIO is ready")
				return True
		except:
			print(f"⏳ Waiting for MinIO... ({i+1}/{retries})")
			time.sleep(delay)
	raise RuntimeError("❌ MinIO not available after retries")













if __name__ == '__main__':
	wait_for_minio(client)
	spark = get_spark_session()
	files = load_ingested_data(client)
	combined_df = clean_preprocess(spark, files)

	# Step 3: inspect
	combined_df.show(5)
	print("Total rows:", combined_df.count())

