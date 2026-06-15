import joblib
import pandas as pd
import numpy as np
import json
from config.settings import MODEL_CONFIG
import __main__


def log_transform(x):
    return np.log1p(x)


def cyclical_hour_sine(x):
    return np.sin(2 * np.pi * x / 24.0)


def cyclical_hour_cosine(x):
    return np.cos(2 * np.pi * x / 24.0)


__main__.log_transform = log_transform
__main__.cyclical_hour_sine = cyclical_hour_sine
__main__.cyclical_hour_cosine = cyclical_hour_cosine


class Predictor:
    def __init__(self):
        self.preprocessor = joblib.load(MODEL_CONFIG["preprocessor_path"])
        self.classifier = joblib.load(MODEL_CONFIG["classifier_path"])
        self.regressor = joblib.load(MODEL_CONFIG["regressor_path"])

    def _build_feature_dataframe(self, event: dict) -> pd.DataFrame:

        f_class = event["features_for_classifier"]

        g_agent = event["agent_pipelines_telemetry"]["graph_agent_context"]

        b_agent = event["agent_pipelines_telemetry"]["behavioral_agent_context"]

        raw_record = {
            "transaction_amount": event["transaction_amount"],
            "avg_transaction_amount_7d": f_class["avg_transaction_amount_7d"],
            "hour_of_day": event["hour_of_day"],
            "account_age_days": f_class["account_age_days"],
            "transaction_frequency_24h": f_class["transaction_frequency_24h"],
            "failed_transaction_count_24h": f_class["failed_transaction_count_24h"],
            "session_duration_minutes": f_class["session_duration_minutes"],
            "device_risk_score": f_class["device_risk_score"],
            "shared_device_mule_count": g_agent["shared_device_mule_count"],
            "is_international": event["is_international"],
            "unusual_amount_flag": f_class["unusual_amount_flag"],
            "unusual_location_flag": f_class["unusual_location_flag"],
            "typing_speed_flag": f_class["typing_speed_flag"],
            "known_fraud_ring_edge": g_agent["known_fraud_ring_edge"],
            "biometric_anomaly_detected": b_agent["biometric_anomaly_detected"],
            "automation_script_suspected": b_agent["automation_script_suspected"],
        }

        return pd.DataFrame([raw_record])

    def predict(self, event: dict) -> dict:
        df = self._build_feature_dataframe(event)

        transformed_vector = self.preprocessor.transform(df)
        fraud_prediction = self.classifier.predict(transformed_vector)[0]
        risk_score = self.regressor.predict(transformed_vector)[0]

        return {
            "transaction_id": event["transaction_id"],
            "system_action": (
                "TERMINATE_TRANSACTION"
                if fraud_prediction == 1
                else "ALLOW_TRANSACTION"
            ),
            "realtime_risk_score": round(
                float(risk_score),
                2,
            ),
            "fraud_prediction": int(fraud_prediction),
        }
