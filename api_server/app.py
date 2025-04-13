from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    return jsonify({"status": "success", "message": "API 서버가 실행 중입니다"})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # 테스트용 간단한 조건
    if username == 'testuser' and password == 'password123':
        return jsonify({
            "status": "success",
            "message": "로그인 성공",
            "token": "sample-token-123"
        }), 200
    else:
        return jsonify({
            "status": "failed",
            "message": "로그인 실패: 아이디 또는 비밀번호가 일치하지 않습니다."
        }), 401

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    
    # 테스트용 간단한 조건
    if email == 'test@example.com':
        return jsonify({
            "status": "failed",
            "message": "회원가입 실패: 이메일이 already exists"
        }), 400
    else:
        return jsonify({
            "status": "success",
            "message": "회원가입 성공"
        }), 201

@app.route('/api/payment', methods=['POST'])
def payment():
    data = request.json
    card_number = data.get('card_number')
    
    # 테스트용 간단한 조건
    if card_number.startswith('1234'):
        return jsonify({
            "status": "failed",
            "message": "결제 실패: 유효하지 않은 카드 정보"
        }), 400
    else:
        return jsonify({
            "status": "success",
            "message": "결제 성공"
        }), 200

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    product_id = data.get('product_id')
    
    # 테스트용 간단한 조건
    if product_id == 'OUT_OF_STOCK_ITEM':
        return jsonify({
            "status": "failed",
            "message": "주문 실패: insufficient stock"
        }), 400
    else:
        return jsonify({
            "status": "success",
            "message": "주문이 성공적으로 생성되었습니다."
        }), 201

if __name__ == '__main__':
    app.run(debug=True, port=5001) 