import mysql.connector

def get_agent_connection():
    return mysql.connector.connect(
        host="localhost",
        user="agent_user",
        password="strong_password",
        database="CSDLDoAnCN"
    )
