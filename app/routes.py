from flask import request, jsonify
import json
import os

DATA_FILE = "app/storage.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

def register_routes(app):
    @app.route('/register', methods=['POST'])
    def register():
        users = load_data()
        data = request.json
        if any(u["email"] == data["email"] for u in users):
            return jsonify({"status": "fail", "message": "User already exists"}), 400
        users.append(data)
        save_data(users)
        return jsonify({"status": "success", "message": "User registered"})

    @app.route('/login', methods=['POST'])
    def login():
        users = load_data()
        data = request.json
        user = next((u for u in users if u["email"] == data["email"] and u["password"] == data["password"]), None)
        if user:
            return jsonify({"status": "success", "message": "Login successful"})
        else:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

    @app.route('/users', methods=['GET'])
    def get_users():
        users = load_data()
        return jsonify(users)

    @app.route('/reset', methods=['POST'])
    def reset():
        save_data([])  # 빈 리스트로 초기화
        return jsonify({"status": "success", "message": "Data reset"})

