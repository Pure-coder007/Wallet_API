from flask import Flask, Blueprint, jsonify, request, session
import mysql.connector
from database import config
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import random
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from models import get_user, add_user
from decimal import Decimal

app = Flask(__name__)

bcrypt = Bcrypt(app)
jwt = JWTManager()
auth = Blueprint("auth", __name__)

app.config.from_pyfile('config.py')

mail = Mail(app)



def create_app(test_config=None):
    app = Flask(__name__,instance_relative_config=True)
    app.secret_key = 'language007'        
    jwt.init_app(app)
    app.register_blueprint(auth, url_prefix='/auth/v1')
    mail.init_app(app)
    return app



def email_exists(email):
    user = get_user(email)  
    return user is not None


def send_acc(email, num):
    msg = Message('Account number', sender='Anonymous@gmail.com', recipients=[email])
    msg.body = f'You account number is {num}'
    print('Account_num :', num)
    mail.send(msg)

def generate_account():
    acc_num = random.randint(1000000000, 2147483646)
    return acc_num




@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if request.method == 'POST':
        first_name = data['first_name']
        last_name = data['last_name']
        email = data['email']
        password = data['password']

        if email_exists(email):
            return jsonify({
                'message' : 'Email already exists', 
                'status' : 400
            })
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        acc_number = generate_account()
        print(acc_number, 'huuuuuuuuuuuuu')

        add_user(first_name, last_name, email, hashed_password, account_number=acc_number)

        return jsonify({
            'Message': 'User created',
            'email' : email,
            'User account number': acc_number
        })




@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message' : 'Missing email or password', 'status': 400}), 400
    
    user = get_user(email)

    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.account_number)


        return jsonify ({
            'message': 'Login successful',
            'access_token': access_token,
            'status':200
        }), 200
    
    return jsonify({'message' : 'Invalid email or password', 'status':400}), 400



@auth.route('/deposit', methods=['POST'])
@jwt_required()  
def deposit():
    data = request.get_json()

    
    if not data or 'deposit_amount' not in data:
        return jsonify({
            'message': 'Invalid data provided.',
            'status': 400
        })

    authenticated_account_number = get_jwt_identity()

    deposit_amount = data['deposit_amount']

    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        cursor.execute("INSERT INTO deposits(account_number, amount) VALUES (%s, %s)", (authenticated_account_number, deposit_amount))
        cursor.execute("UPDATE users SET balance = balance + %s WHERE account_number=%s", (deposit_amount, authenticated_account_number))
        connection.commit()
        return jsonify({
            'message' : 'Deposit successful',
            'status' : 200
        })
    except mysql.connector.Error as err:
        print("Error: ", err)
        return jsonify({
            'message' : 'There was an error processing your request.',
            'status' : 500
        })
    finally:
        cursor.close()
        connection.close()



@auth.route('/balance', methods=['GET'])
@jwt_required()
def balance():
    authenticated_account_number = get_jwt_identity()

    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        cursor.execute("SELECT balance FROM users WHERE account_number=%s", (authenticated_account_number,))
        balance = cursor.fetchone()[0]

        if balance:
            return jsonify({
                'message': 'Balance retrieved successfully',
                'balance': balance,
                'status': 200
            })
        return jsonify({
            'message': 'Balance retrieved successfully',
            'balance': 0,
            'status': 200
        })
    except mysql.connector.Error as err:
        print("Error: ", err)
        return jsonify({
            'message' : 'There was an error processing your request.',
            'status' : 500
        })
    finally:
        cursor.close()
        connection.close()



@auth.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    data = request.get_json()

    
    if not data or 'amount' not in data or 'receiver_account_number' not in data:
        return jsonify({
            'message': 'Invalid data provided.',
            'status': 400
        })
    
    

    sender_account_number = get_jwt_identity()

    

    print(sender_account_number)
    receiver_account_number = data['receiver_account_number']
    amount = Decimal(data['amount'])

    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    try:

        print(type(sender_account_number), type(receiver_account_number))
        if int(data['receiver_account_number']) == sender_account_number:
            return jsonify({
                'message': 'You cannot transfer to yourself.',
                'status': 400
            })
    # Check sender's balance
        cursor.execute("SELECT balance FROM users WHERE account_number=%s", (sender_account_number,))
        sender_balance = cursor.fetchone()[0]

        if not sender_balance or sender_balance < amount:
            return jsonify({
            'message': 'Insufficient funds',
            'status': 400
        })

        # Check if receiver exists and fetch their balance
        cursor.execute("SELECT balance FROM users WHERE account_number=%s", (receiver_account_number,))
        receiver_record = cursor.fetchone()

        if not receiver_record:
            return jsonify({
                'message': 'Receiver account does not exist.',
                'status': 400
            })
        print(data['receiver_account_number'], sender_account_number)
       

        receiver_balance = receiver_record[0] if receiver_record[0] else 0

        # Begin transaction

        # Deduct from sender's balance
        cursor.execute("UPDATE users SET balance = balance - %s WHERE account_number = %s", (amount, sender_account_number))

        # Add to receiver's balance
        cursor.execute("UPDATE users SET balance = balance + %s WHERE account_number = %s", (amount, receiver_account_number))

        # Insert transfer record
        cursor.execute("INSERT INTO transfers(sender_account_number, receiver_account_number, amount) VALUES (%s, %s, %s)", (sender_account_number, receiver_account_number, -amount))

        # Add to receiver's deposits 
        cursor.execute("INSERT INTO deposits(account_number, amount) VALUES (%s, %s)", (receiver_account_number, amount))

        connection.commit()

        return jsonify({
            'message': 'Transfer successful',
            'status': 200
        })

    except mysql.connector.Error as err:
        connection.rollback()
        print("Error: ", err)
        return jsonify({
            'message': 'There was an error processing your request.',
            'status': 500
        })

    finally:
        cursor.close()
        connection.close()



@auth.route('/transactions', methods=['GET'])
@jwt_required()
def transactions():
    authenticated_account_number = get_jwt_identity()

    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)

        # Fetch user's current balance
        cursor.execute("SELECT balance FROM users WHERE account_number=%s", (authenticated_account_number,))
        balance_record = cursor.fetchone()
        balance = balance_record['balance'] if balance_record and 'balance' in balance_record else 0

        # Fetch user's transfers
        cursor.execute("SELECT * FROM transfers WHERE sender_account_number=%s OR receiver_account_number=%s", (authenticated_account_number, authenticated_account_number))
        transfers = cursor.fetchall()

        # Fetch user's deposits
        cursor.execute("SELECT * FROM deposits WHERE account_number=%s", (authenticated_account_number,))
        deposits = cursor.fetchall()

        return jsonify({
            'message': 'Transactions retrieved successfully',
            'transfers': transfers,
            'deposits': deposits,
            'balance': balance,  # Including the current balance here
            'status': 200
        })
    except mysql.connector.Error as err:
        print("Error: ", err)
        return jsonify({
            'message' : 'There was an error processing your request.',
            'status' : 500
        })
    finally:
        cursor.close()
        connection.close()



