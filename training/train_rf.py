import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from training.utils import engine
from sklearn.metrics import accuracy_score
import pickle
import mlflow
import time



mlflow.set_tracking_uri("http://mlflow:5000")

for i in range(10):
    try:
        mlflow.set_experiment("Stock Prediction")
        break
    except Exception:
        print("Waiting for MLflow...")
        time.sleep(5)

def load_data():
    print("Loading data...")
    df = pd.read_sql("SELECT * FROM stocks", engine)
    print(df.columns)
    df = df.sort_values("date")
    df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
    df = df.dropna()

    features = [
        "return_1d",
        "log_return",
        "high_low",
        "close_open",
        "sma_20",
        "rsi"
    ]

    X = df[features]
    y = df["target"]

    split = int(len(df) * 0.8)
    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    return X_train, y_train, X_test, y_test


def train_and_log_model(
    n_estimators: int = 100,
    max_depth: int = 10,
    min_samples_split: int = 2,
    min_samples_leaf: int = 1
    ):

    X_train, y_train, X_test, y_test = load_data()

    with mlflow.start_run():
        run_name = f"rf_est{n_estimators}_depth{max_depth}_{datetime.now().strftime('%H%M%S')}"
        mlflow.set_tag("mlflow.runName", run_name)

        # log All hyperparamaters
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("min_samples_split", min_samples_split)
        mlflow.log_param("min_samples_leaf", min_samples_leaf)
        mlflow.log_param("model_type", "RandomForestClassifier")

        # Log data information
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))

        # Train the model
        print(f"\nTraining model: n_estimators={n_estimators}, max_depth={max_depth}")

        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        for dataset_name, X, y in [("train", X_train, y_train), ("test",X_test,y_test)]:
            y_pred = model.predict(X)
            y_prob = model.predict_proba(X)


            accuracy = accuracy_score(y, y_pred)
            precision = precision_score(y, y_pred, zero_division=0)
            recall = recall_score(y, y_pred, zero_division=0)
            f1 = f1_score(y, y_pred, zero_division=0)
            roc_auc = roc_auc_score(y, y_prob)

            mlflow.log_metric(f"{dataset_name}_accuracy", accuracy)
            mlflow.log_metric(f"{dataset_name}_precision", precision)
            mlflow.log_metric(f"{dataset_name}_recall", recall)
            mlflow.log_metric(f"{dataset_name}_f1", f1)
            mlflow.log_metric(f"{dataset_name}_roc_auc", roc_auc)

            print(f"    {dataset_name.upper()} - Accuracy: {accuracy:.4f}, F1: {f1:.4f}, ROC-AUC: {roc_auc:.4f}")

        for feature, importance in zip(['date', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'return_1d', 'log_return', 'high_low', 'close_open', 'sma_20', 'rsi'], model.features_importances_):
            print(f"importance_{feature}: {importance}")
            mlflow.log_metrics(f"importance_{feature}", importance)

        print("\n Registering model in MLflow Model Registry...")
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name="fraud-detection-model",
            input_example=X_train.iloc[:5]
        )

        run_id = mlflow.active_run().info.run_id
        print(f"\nMLflow Run ID: {run_id}")
        print(f"View this run: http://localhost:5000/#/experiments/1/runs/{run_id}")

        return model





def run_experiments_sweep():
	print("="*60)
	print("training model on different hyperparameters")
	print("="*60)

	experiments = [
        	{"n_estimators": 50, "max_depth": 5},
        	{"n_estimators": 100, "max_depth": 10},
        	{"n_estimators": 100, "max_depth": 15},
        	{"n_estimators": 200, "max_depth": 10},
        	{"n_estimators": 200, "max_depth": 20},
    	]

	for i, params in enumerate(experiments, 1):
		print(f"Experiment {i}/{len(experiments)}")
		train_and_log_model(**params)
	print("\n" + "="*60)
    	print("EXPERIMENT SWEEP COMPLETE!")
    	print("="*60)



if __name__ == "__main__":
    run_experiments_sweep()
