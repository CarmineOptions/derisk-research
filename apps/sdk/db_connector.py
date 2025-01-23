import psycopg2
from dotenv import load_dotenv
import os

class DBConnector:
    def __init__(self):     
  
        load_dotenv()
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        try:
            self.conn = psycopg2.connect(
                host=host,
                database=database,
                user=user,
                password=password
            )
            self.cur = self.conn.cursor()
            print("connected to PostgreSQL successfully.")
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL:", error)

    def get_user_debt(self, protocol_id, wallet_id):
       
        try:
            sql = """
                SELECT debt 
                FROM user_data 
                WHERE protocol_id = %s AND user = %s;
            """
            self.cur.execute(sql, (protocol_id, wallet_id))
            result = self.cur.fetchone()
            if result:
                return result[0]
            else:
                return None
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching user debt:", error)
            return None

    def get_user_collateral(self, protocol_id, wallet_id):
        
        try:
            sql = """
                SELECT collateral 
                FROM user_data 
                WHERE protocol_id = %s AND user = %s;
            """
            self.cur.execute(sql, (protocol_id, wallet_id))
            result = self.cur.fetchone()
            if result:
                return result[0]
            else:
                return None
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching user collateral:", error)
            return None

    def get_loan_state(self, protocol_id, wallet_id):
        # loan_state not in the test file 
        try:
            sql = """
                SELECT loan_state 
                FROM user_data 
                WHERE protocol_id = %s AND user = %s;
            """
            self.cur.execute(sql, (protocol_id, wallet_id))
            result = self.cur.fetchone()
            if result:
                return result[0]
            else:
                return None
        except (Exception, psycopg2.Error) as error:
            print("Error while fetching user loan state:", error)
            return None

    def close_connection(self):
        
        if self.conn:
            self.cur.close()
            self.conn.close()
            print("postgre sql connection closed.")
