import os
import psycopg2

def get_connection():

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database="industrial_iot",
        user="iot_user",
        password="iot_password_change_me"
    )