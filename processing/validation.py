def validate_data(data):

    required = [
        "machine_id",
        "timestamp",
        "temperature",
        "production_count",
        "status"
    ]

    for key in required:
        if key not in data:
            raise ValueError(f"Missing required field: {key}")

    if data["status"] not in [0, 1]:
        raise ValueError("Invalid machine status")

    try:
        data["temperature"] = float(data["temperature"])
        data["production_count"] = int(data["production_count"])
    except (ValueError, TypeError):
        raise ValueError("Invalid numeric data")

    return data