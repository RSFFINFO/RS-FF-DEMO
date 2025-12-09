from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# ফ্রেন্ড রিকোয়েস্ট API গুলো
ADD_API = "https://rs-ff-friend-api.vercel.app/add_friend"
REMOVE_API = "https://rs-ff-friend-api.vercel.app/remove_friend"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute_action():
    data = request.json
    my_uid = data.get('my_uid')
    password = data.get('password')
    target_uid = data.get('target_uid')
    action = data.get('action') # 'add' or 'remove'

    if not all([my_uid, password, target_uid, action]):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    # API URL সিলেক্ট করা
    target_url = ADD_API if action == "add" else REMOVE_API
    
    # প্যারামিটার সেট করা
    params = {
        "uid": my_uid,
        "password": password,
        "player_id": target_uid
    }

    try:
        # এক্সটারনাল API কল করা
        response = requests.get(target_url, params=params)
        
        # রেসপন্স চেক করা
        if response.status_code == 200:
            return jsonify({"status": "success", "response": response.text})
        else:
            return jsonify({"status": "error", "message": "API Error", "details": response.text})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)