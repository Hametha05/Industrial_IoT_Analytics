def transform_data(data):

    processed_data = data.copy()

    processed_data["machine_id"] = str(data["machine_id"])
    processed_data["temperature"] = float(data["temperature"])
    processed_data["production_count"] = int(data["production_count"])
    processed_data["status"] = int(data["status"])

    return processed_data