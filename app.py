from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# --- ডাটাবেস (মেমোরিতে থাকবে) ---
ACCOUNTS = [] 

# --- API URLs ---
ADD_API = "https://rs-ff-friend-api.vercel.app/add_friend"
REMOVE_API = "https://rs-ff-friend-api.vercel.app/remove_friend"

# --- HTML TEMPLATES (সরাসরি কোডের ভেতর) ---

USER_PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Panel</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0d1117; color: #e6edf3; font-family: 'Poppins', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #161b22; padding: 30px; border-radius: 15px; width: 90%; max-width: 450px; box-shadow: 0 0 20px rgba(0,0,0,0.5); border: 1px solid #30363d; }
        h2 { text-align: center; color: #58a6ff; margin-bottom: 20px; }
        select, input { width: 100%; padding: 12px; margin-bottom: 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: white; box-sizing: border-box; }
        select:focus, input:focus { border-color: #58a6ff; outline: none; }
        .profile-card { display: none; background: #21262d; padding: 10px; border-radius: 8px; margin-top: 20px; border: 1px solid #30363d; align-items: center; gap: 15px; }
        .banner-img { width: 70%; border-radius: 5px; border: 1px solid #555; }
        .actions { display: flex; flex-direction: column; gap: 10px; justify-content: center; }
        .icon-btn { width: 40px; height: 40px; border-radius: 50%; border: none; display: flex; align-items: center; justify-content: center; font-size: 18px; cursor: pointer; transition: 0.3s; color: white; }
        .btn-add { background: #238636; } .btn-reject { background: #da3633; }
        .btn-search { width: 100%; padding: 12px; background: #1f6feb; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
<div class="container">
    <h2><i class="fas fa-robot"></i> User Panel</h2>
    <label>Select Sender Account:</label>
    <select id="senderAccount">
        <option value="">-- Choose Account --</option>
        {% for acc in accounts %}
        <option value="{{ acc.uid }}">{{ acc.name }} ({{ acc.uid }})</option>
        {% endfor %}
    </select>
    <label>Target Player UID:</label>
    <input type="text" id="targetUid" placeholder="Enter Target UID">
    <button class="btn-search" onclick="showProfile()">Check Profile</button>

    <div class="profile-card" id="profileCard">
        <img src="" id="bannerImg" class="banner-img" alt="Banner">
        <div class="actions">
            <button class="icon-btn btn-add" onclick="sendRequest('add')"><i class="fas fa-user-plus"></i></button>
            <button class="icon-btn btn-reject" onclick="sendRequest('remove')"><i class="fas fa-trash"></i></button>
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<script>
    function showProfile() {
        let uid = document.getElementById('targetUid').value;
        if(!uid) return Swal.fire('Oops', 'Enter Target UID', 'warning');
        document.getElementById('bannerImg').src = `https://profile-banner-api.vercel.app/banner?uid=${uid}&region=BD`;
        document.getElementById('profileCard').style.display = 'flex';
    }
    async function sendRequest(action) {
        let sender = document.getElementById('senderAccount').value;
        let target = document.getElementById('targetUid').value;
        if(!sender) return Swal.fire('Error', 'Select Sender Account', 'error');
        Swal.fire({ title: 'Processing...', didOpen: () => Swal.showLoading() });
        try {
            let res = await fetch('/api/execute', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ sender_uid: sender, target_uid: target, action: action })
            });
            let data = await res.json();
            if(data.status === 'success') Swal.fire('Success!', action === 'add' ? 'Request Sent!' : 'Removed!', 'success');
            else Swal.fire('Failed', data.message, 'error');
        } catch(e) { Swal.fire('Error', 'Server Error', 'error'); }
    }
</script>
</body>
</html>
"""

ADMIN_PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #121212; color: white; }
        .sidebar { height: 100vh; width: 250px; position: fixed; top: 0; left: 0; background-color: #1f1f1f; padding-top: 20px; }
        .sidebar a { padding: 15px; text-decoration: none; font-size: 18px; color: #ccc; display: block; }
        .sidebar a:hover { background: #333; color: #fff; }
        .content { margin-left: 250px; padding: 20px; }
        .stat-card { background: #252525; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #333; }
        .stat-num { font-size: 2rem; font-weight: bold; }
        .add-box { background: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #444; max-width: 500px; margin: auto; }
        input { background: #333; border: 1px solid #555; color: white; margin-bottom: 10px; }
        input:focus { background: #444; color: white; box-shadow: none; border-color: #00ff7f; }
    </style>
</head>
<body>
<div class="sidebar">
    <h4 class="text-center text-white mb-4">Admin Panel</h4>
    <a href="/admin"><i class="fas fa-tachometer-alt me-2"></i> Dashboard</a>
    <a href="/"><i class="fas fa-globe me-2"></i> User Panel</a>
</div>
<div class="content">
    <h2>Dashboard</h2>
    <div class="row mt-4">
        <div class="col-md-3"><div class="stat-card"><h3 class="stat-num text-info" id="total">0</h3><p>Total Accounts</p></div></div>
        <div class="col-md-3"><div class="stat-card"><h3 class="stat-num text-success" id="online">0</h3><p>Online</p></div></div>
    </div>
    <div class="add-box mt-5">
        <h5 class="text-center text-success mb-3">Add New Account</h5>
        <input type="text" id="uid" class="form-control" placeholder="UID">
        <input type="text" id="pass" class="form-control" placeholder="Password/Token">
        <input type="text" id="name" class="form-control" placeholder="Name">
        <button class="btn btn-success w-100" onclick="addAccount()">Add Account</button>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<script>
    async function loadStats() {
        let res = await fetch('/api/stats');
        let data = await res.json();
        document.getElementById('total').innerText = data.total;
        document.getElementById('online').innerText = data.online;
    }
    async function addAccount() {
        let uid = document.getElementById('uid').value;
        let pass = document.getElementById('pass').value;
        let name = document.getElementById('name').value;
        if(!uid || !pass) return Swal.fire('Error', 'UID & Password Required', 'error');
        let res = await fetch('/api/add_account', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({uid, password: pass, name})
        });
        let result = await res.json();
        if(result.status === 'success'){
            Swal.fire('Success', 'Account Added!', 'success');
            document.getElementById('uid').value = '';
            loadStats();
        } else Swal.fire('Error', result.message, 'error');
    }
    loadStats();
</script>
</body>
</html>
"""

# --- FLASK ROUTES ---

@app.route('/')
def user_panel():
    return render_template_string(USER_PANEL_HTML, accounts=ACCOUNTS)

@app.route('/admin')
def admin_panel():
    return render_template_string(ADMIN_PANEL_HTML)

# --- API ENDPOINTS ---

@app.route('/api/stats')
def get_stats():
    return jsonify({"total": len(ACCOUNTS), "online": len(ACCOUNTS)})

@app.route('/api/add_account', methods=['POST'])
def add_account():
    data = request.json
    uid = data.get('uid')
    if any(a['uid'] == uid for a in ACCOUNTS):
        return jsonify({"status": "error", "message": "Account already exists"}), 400
    
    ACCOUNTS.append({
        "uid": uid, 
        "password": data.get('password'), 
        "name": data.get('name', uid)
    })
    return jsonify({"status": "success"})

@app.route('/api/execute', methods=['POST'])
def execute_action():
    data = request.json
    sender_uid = data.get('sender_uid')
    target_uid = data.get('target_uid')
    action = data.get('action')

    sender_acc = next((a for a in ACCOUNTS if a['uid'] == sender_uid), None)
    if not sender_acc:
        return jsonify({"status": "error", "message": "Sender account not found!"}), 400

    target_url = ADD_API if action == "add" else REMOVE_API
    try:
        response = requests.get(target_url, params={
            "uid": sender_acc['uid'],
            "password": sender_acc['password'],
            "player_id": target_uid
        })
        return jsonify({"status": "success", "response": response.text})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # কোড রান করার পর এই পোর্টে সার্ভার চলবে
    print("User Panel: http://127.0.0.1:5000/")
    print("Admin Panel: http://127.0.0.1:5000/admin")
    app.run(debug=True, port=5000)
