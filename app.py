from flask import Flask, jsonify, request, abort
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from functools import wraps
import jwt
import datetime
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)

# MySQL config
app.config['MYSQL_HOST'] = os.getenv('DB_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('DB_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('DB_PASSWORD', 'root')
app.config['MYSQL_DB'] = os.getenv('DB_NAME', 'devopsdb')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devopssecretkey')


mysql = MySQL(app)

# --- IP Whitelisting ---
WHITELISTED_IPS = ['127.0.0.1', '::1', '172.18.0.1' , '172.19.0.1']



@app.before_request
def limit_remote_addr():
    forwarded_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    real_ip = forwarded_ip.split(',')[0].strip()
    print(f"🔍 Client IP: {real_ip}")
    if real_ip not in WHITELISTED_IPS:
        abort(403)

# --- JWT Role Decorator ---
def token_required(role_name=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'msg': 'Token missing'}), 403
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                user_id = data['user_id']
                role_id = data['role_id']

                cur = mysql.connection.cursor()
                cur.execute("SELECT name FROM roles WHERE id=%s", (role_id,))
                user_role = cur.fetchone()[0]
                cur.close()

                if role_name and user_role != role_name:
                    return jsonify({'msg': 'Access denied'}), 403

                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'msg': 'Token expired'}), 403
            except:
                return jsonify({'msg': 'Invalid token'}), 403
        return wrapper
    return decorator

# --- Auth Routes ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    role = data['role']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM roles WHERE name=%s", (role,))
    role_id = cur.fetchone()
    if not role_id:
        return jsonify({'msg': 'Invalid role'}), 400

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        cur.execute("INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
                    (username, password_hash, role_id[0]))
        mysql.connection.commit()
        return jsonify({'msg': 'User registered'}), 201
    except:
        return jsonify({'msg': 'Username already exists'}), 400
    finally:
        cur.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password_hash, role_id FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.check_password_hash(user[1], password):
        token = jwt.encode({
            'user_id': user[0],
            'role_id': user[2],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'msg': 'Invalid credentials'}), 401

# --- Test Endpoint ---
@app.route('/')
def index():
    return '🚀 DevOps Security App Running'

# --- Messages Routes (Protected) ---
@app.route('/messages', methods=['GET'])
@token_required(role_name='admin')
def get_messages():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM test")
    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)

@app.route('/messages', methods=['POST'])
@token_required(role_name='admin')
def add_message():
    message = request.json.get('message')
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO test (message) VALUES (%s)", (message,))
    mysql.connection.commit()
    cur.close()
    return jsonify({"status": "Message added"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)