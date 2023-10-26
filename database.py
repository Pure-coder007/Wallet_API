import mysql.connector
from datetime import datetime



config = {
    'user': 'mark_api',
    'password': 'language007',
    'host' : 'db4free.net',
    'port' : '3306',
    'database' : 'wallet_api'
}






# config = {
#     'user': 'root',
#     'password': 'language007',
#     'host' : 'localhost',
#     'port' : '3306',
#     'database' : 'wallet_api'
# }

def setup_database():
    config['database'] = None
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()


# User Table
    cursor.execute("""
    CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    account_number INT(11) UNIQUE NOT NULL
);
""")
    
    cursor.execute("""
    CREATE TABLE deposits (
    deposit_id INT AUTO_INCREMENT PRIMARY KEY,
    account_number INT(11) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    deposit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_number) REFERENCES users(account_number)
);
""")
