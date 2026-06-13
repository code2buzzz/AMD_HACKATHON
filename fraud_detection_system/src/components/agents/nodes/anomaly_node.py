from src.components.models.predictor import Predictor

predictor = Predictor()


def anomaly_node(state):
    tx = state["transaction"]
    prediction = predictor.predict(tx)
    state["anomaly_result"] = prediction
    return state
