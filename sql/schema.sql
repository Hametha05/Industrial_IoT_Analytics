CREATE TABLE IF NOT EXISTS machines (
    machine_id VARCHAR(50) PRIMARY KEY,
    machine_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS machine_data (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(50) REFERENCES machines(machine_id),
    recorded_at TIMESTAMPTZ NOT NULL,
    power FLOAT,
    current FLOAT,
    temperature FLOAT,
    production_count INTEGER,
    status INTEGER,
    product_name VARCHAR(100),
    product_code VARCHAR(50),
    stop_reason_code VARCHAR(20),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_machine_timestamp
ON machine_data(machine_id, recorded_at);