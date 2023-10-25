import mysql.connector
from database import config


class User():
    def __init__(self, id, first_name, last_name, email, password, account_number):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.account_number = account_number

        @classmethod
        def get(cls, user_id):
            pass

def add_user(first_name, last_name, email, password, account_number):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        cursor.execute("INSERT INTO users(first_name, last_name, email, password, account_number) VALUES (%s, %s, %s, %s, %s)", (first_name, last_name, email, password, account_number))
        connection.commit()
    except mysql.connector.Error as err:
        if err.errno == 1062: 
            return {"status": "error", "message": "Duplicate account number"}
        print("Error: ", err)
    finally:
        cursor.close()
        connection.close()




def get_user(email):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute('SELECT * FROM `wallet_api`.`users` WHERE email=%s', (email,))

        user_record = cursor.fetchone()
        
        if user_record:
            return User(
                id=user_record['id'],
                first_name=user_record['first_name'],
                last_name=user_record['last_name'],
                email=user_record['email'],
                password=user_record['password'],
                account_number=user_record['account_number']
            )
        return None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
    finally:
        if cursor: cursor.close()
        if connection: connection.close()





def deposit(account_number, deposit_amount):
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        insert_query = """
        INSERT INTO deposits(account_number, deposit_amount) 
        VALUES (%s, %s)
        """
        cursor.execute(insert_query, (account_number, deposit_amount))
        connection.commit()

        return {"status": "success", "message": "Deposit successful"}

    except mysql.connector.Error as err:
        if err.errno == 1062:
            return {"status": "error", "message": "Duplicate deposit entry"}
        print("Error: ", err)
        return {"status": "error", "message": "An unexpected error occurred"}

    finally:
        cursor.close()
        connection.close()



