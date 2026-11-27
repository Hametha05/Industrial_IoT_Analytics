def detect_anomaly(data):

    temperature = float(data["temperature"])

    anomaly = temperature < 0 or temperature > 90

    reason = (
        "Temperature outside configured range"
        if anomaly else None
    )

    return anomaly, reason