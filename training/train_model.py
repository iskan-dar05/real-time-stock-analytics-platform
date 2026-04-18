import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from .utils import engine


df = pd.read_sql("SELECT * FROM stocks", engine)

print(df)


