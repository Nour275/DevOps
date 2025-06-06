from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# MySQL config — adjust these to your database settings
app.config['MYSQL_HOST'] = 'db'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'devopsdb'

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not username or not password or not role:
        return jsonify({"error": "username, password and role are required"}), 400

    cur = mysql.connection.cursor()

    # Check if username exists
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        return jsonify({"error": "Username already exists"}), 409

    # Get role id
    cur.execute("SELECT id FROM roles WHERE name=%s", (role,))
    role_id = cur.fetchone()
    if not role_id:
        return jsonify({"error": "Invalid role"}), 400
    role_id = role_id[0]

    # Hash password and insert new user
    password_hash = generate_password_hash(password)
    cur.execute("INSERT INTO users (username, password, role_id) VALUES (%s, %s, %s)", (username, password_hash, role_id))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password, role_id FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    user_id, password_hash, role_id = user

    if not check_password_hash(password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM roles WHERE id=%s", (role_id,))
    role = cur.fetchone()
    cur.close()

    role_name = role[0] if role else "user"

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user_id,
            "username": username,
            "role": role_name
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
