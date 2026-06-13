from config.settings import MAX_ITERATIONS


def confidence_router(state):

    confidence = state.get("confidence_score", 0)
    iteration = state.get("iteration_count", 0)

    if confidence < 0.80 and iteration < MAX_ITERATIONS:
        return "retry"

    return "approved"
