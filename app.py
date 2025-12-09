from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# API URLs
ADD_API = "https://rs-ff-friend-api.vercel.app/add_friend"
REMOVE_API = "https://rs-ff-friend-api.vercel.app/remove_friend"
BIO_API = "https://add-bio-api.vercel.app/bio_upload"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute_action():
    data = request.json
    
    # Common fields
    my_uid = data.get('my_uid')
    password = data.get('password')
    action = data.get('action') # 'add', 'remove', or 'bio'

    if not my_uid or not password:
        return jsonify({"status": "error", "message": "UID and Password required"}), 400

    # --- Action: Friend Request (Add/Remove) ---
    if action in ['add', 'remove']:
        target_uid = data.get('target_uid')
        if not target_uid:
            return jsonify({"status": "error", "message": "Target UID required for friend request"}), 400
            
        target_url = ADD_API if action == "add" else REMOVE_API
        params = {
            "uid": my_uid,
            "password": password,
            "player_id": target_uid
        }
        
        try:
            response = requests.get(target_url, params=params)
            if response.status_code == 200:
                return jsonify({"status": "success", "response": response.text})
            else:
                return jsonify({"status": "error", "message": "Friend API Error", "details": response.text})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    # --- Action: Bio Update ---
    elif action == 'bio':
        bio_text = data.get('bio_text')
        if not bio_text:
            return jsonify({"status": "error", "message": "Bio text is empty"}), 400

        # Bio API Parameters
        params = {
            "uid": my_uid,
            "pass": password, # Note: API parameter is 'pass'
            "bio": bio_text
        }
        
        try:
            response = requests.get(BIO_API, params=params)
            if response.status_code == 200:
                return jsonify({"status": "success", "response": response.text})
            else:
                return jsonify({"status": "error", "message": "Bio API Error", "details": response.text})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    return jsonify({"status": "error", "message": "Invalid Action"}), 400

if __name__ == '__main__':
    app.run(debug=True)
