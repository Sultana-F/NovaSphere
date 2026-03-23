import mysql.connector

def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="nims",
            password="Nims2019",
            database="nimsdb"
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

if __name__ == '__main__':
    # Test connection
    conn = get_connection()
    if conn:
        print("Successfully connected to the database!")
        conn.close()
    else:
        print("Failed to connect to the database.")

