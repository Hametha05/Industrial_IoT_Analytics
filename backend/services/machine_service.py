from backend.database import get_connection


def get_machine_history(machine_id):

    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:

                cursor.execute("""
                    SELECT recorded_at, temperature,
                           production_count, status,
                           stop_reason_code, is_anomaly
                    FROM machine_data
                    WHERE machine_id = %s
                    ORDER BY recorded_at DESC
                    LIMIT 100
                """, (machine_id,))

                rows = cursor.fetchall()

        return [
            {
                "timestamp": row[0].isoformat(),
                "temperature": row[1],
                "production_count": row[2],
                "status": row[3],
                "stop_reason_code": row[4],
                "is_anomaly": row[5]
            }
            for row in rows
        ]

    finally:
        connection.close()