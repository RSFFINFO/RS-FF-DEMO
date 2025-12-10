from flask import Flask, render_template, request, jsonify
import requests
import random

app = Flask(__name__)

# ইন-মেমোরি ডাটাবেস (Vercel এ ডাটা পার্মানেন্ট রাখতে হলে MongoDB বা Firebase লাগবে)
# আপাতত লিস্ট ব্যবহার করা হচ্ছে
ACCOUNTS = [] 

# API URLs
ADD_API = "https://rs-ff-friend-api.vercel.app/add_friend"
REMOVE_API = "https://rs-ff-friend-api.vercel.app/remove_friend"

@app.route('/')
def user_panel():
    return render_template('user.html', accounts=ACCOUNTS)

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

# --- API Endpoints ---

@app.route('/api/stats')
def get_stats():
    # ড্যাশবোর্ড স্ট্যাটস (লজিক সিমুলেট করা হয়েছে)
    total = len(ACCOUNTS)
    # রিয়াল চেক API না থাকায় র‍্যান্ডম স্ট্যাটাস দেখানো হচ্ছে
    online = len([a for a in ACCOUNTS if 'active' in a]) 
    offline = total - online
    banned = 0 
    
    return jsonify({
        "total": total,
        "online": total, # আপাতত সব অনলাইন ধরা হলো
        "offline": 0,
        "banned": 0
    })

@app.route('/api/add_account', methods=['POST'])
def add_account():
    data = request.json
    uid = data.get('uid')
    password = data.get('password')
    name = data.get('name', uid)

    if not uid or not password:
        return jsonify({"status": "error", "message": "UID & Password required"}), 400

    # ডুপ্লিকেট চেক
    for acc in ACCOUNTS:
        if acc['uid'] == uid:
            return jsonify({"status": "error", "message": "Account already exists"}), 400

    new_acc = {"uid": uid, "password": password, "name": name, "status": "Active"}
    ACCOUNTS.append(new_acc)
    return jsonify({"status": "success", "message": "Account Added Successfully!"})

@app.route('/api/get_accounts')
def get_accounts_api():
    return jsonify(ACCOUNTS)

@app.route('/api/execute', methods=['POST'])
def execute_action():
    data = request.json
    sender_uid = data.get('sender_uid') # যেই অ্যাকাউন্ট থেকে রিকোয়েস্ট যাবে
    target_uid = data.get('target_uid')
    action = data.get('action') # 'add' or 'remove'

    # অ্যাডমিনের লিস্ট থেকে সেন্ডার একাউন্ট খোঁজা
    sender_acc = next((a for a in ACCOUNTS if a['uid'] == sender_uid), None)

    if not sender_acc:
        return jsonify({"status": "error", "message": "Sender account not found in database!"}), 400

    target_url = ADD_API if action == "add" else REMOVE_API
    
    params = {
        "uid": sender_acc['uid'],
        "password": sender_acc['password'],
        "player_id": target_uid
    }

    try:
        response = requests.get(target_url, params=params)
        if "success" in response.text.lower() or response.status_code == 200:
             return jsonify({"status": "success", "response": response.text})
        else:
             return jsonify({"status": "error", "message": response.text})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)