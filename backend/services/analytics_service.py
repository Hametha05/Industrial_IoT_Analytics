
from backend.database import get_connection


def get_machine_summary():

    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:

                cursor.execute("""
                    SELECT
                        m.machine_id,
                        m.machine_name,
                        COUNT(d.id),
                        COALESCE(
                            MAX(d.production_count)
                            - MIN(d.production_count), 0
                        ),
                        ROUND(AVG(d.temperature)::numeric, 2),
                        SUM(CASE WHEN d.status = 1 THEN 5 ELSE 0 END),
                        SUM(CASE WHEN d.status = 0 THEN 5 ELSE 0 END),
                        ROUND(
                            100.0 * SUM(
                                CASE WHEN d.status = 1 THEN 1 ELSE 0 END
                            ) / NULLIF(COUNT(d.id), 0), 2
                        )
                    FROM machines m
                    LEFT JOIN machine_data d
                    ON m.machine_id = d.machine_id
                    GROUP BY m.machine_id, m.machine_name
                    ORDER BY m.machine_id
                """)

                rows = cursor.fetchall()

        columns = [
            "machine_id",
            "machine_name",
            "total_readings",
            "production",
            "average_temperature",
            "running_seconds",
            "stopped_seconds",
            "utilization"
        ]

        return [
            dict(zip(columns, row))
            for row in rows
        ]

    finally:
        connection.close()
