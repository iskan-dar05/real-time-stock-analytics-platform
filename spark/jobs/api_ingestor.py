import requests
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from minio import Minio
import time


# Load .env file

load_dotenv()

# get api key

API_KEY = os.getenv("API_KEY")


main_companies = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL", # Alphabet
    "AMZN",  # Amazon
    "TSLA",  # Tesla
    "META",  # Meta/Facebook
    "NVDA",  # NVIDIA
]







def load_data(symbol: str):
	# Fetch Data
	url = "https://www.alphavantage.co/query"
	params = {
    	"function": "TIME_SERIES_DAILY",
    	"symbol": symbol,
    	"apikey": API_KEY
	}
	data = requests.get(url, params=params).json()

	# Get time_series
	time_series = data.get("Time Series (Daily)")
	if not time_series:
		raise ValueError(f"No data returned for symbol {symbol}")


	df = pd.DataFrame(time_series).T

	df = df.rename(columns={
		"1. open": "open",
		"2. high": "high",
		"3. low": "low",
		"4. close": "close",
		"5. volume": "volume"
	})

	df.index.name = "date"
	df.reset_index(inplace=True)

	for col in ["open", "high", "low", "close", "volume"]:
		df[col] = pd.to_numeric(df[col])

	df["symbol"] = symbol

	return df



def ingest_data(df, bucket_name="stock-data"):
    """Save DataFrame to CSV and upload to MinIO"""
    # Create MinIO client
    client = Minio(
        "minio:9000",
        access_key="admin",
        secret_key="password123",
        secure=False
    )

    # Create bucket if it doesn't exist
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    # Save CSV locally
    now = datetime.now()
    symbol = df["symbol"].iloc[0]
    filename = now.strftime("%Y-%m-%d_%H-%M") + f"_{symbol}.csv"
    df.to_csv(filename, index=False)

    # Upload CSV to MinIO
    client.fput_object(
        bucket_name,
        f"raw/{filename}",
        filename
    )

    print(f"✅ Uploaded {filename} to bucket '{bucket_name}'")




if __name__ == "__main__":

	while True:
		for symbol in main_companies:
			try:
				df = load_data(symbol)
				ingest_data(df)
				print("Ingestion finished successfully ✅")
			except Exception as e:
				print("Error: ", e)







print("Is Finish Success")