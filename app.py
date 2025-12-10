import os
import json
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = "RS_SECRET_KEY_@123"  # সেশন এর জন্য সিক্রেট কি

# --- কনফিগারেশন ---
ADMIN_EMAIL = "admin@rs.com"   # আপনার অ্যাডমিন ইমেইল
ADMIN_PASS = "rs1234"          # আপনার অ্যাডমিন পাসওয়ার্ড
DB_FILE = "accounts.json"      # অ্যাকাউন্ট সেভ রাখার ফাইল
HISTORY_FILE = "history.json"  # রিকোয়েস্ট হিস্ট্রি ফাইল

# API URLs
ADD_API = "https://rs-ff-friend-api.vercel.app/add_friend"
REMOVE_API = "https://rs-ff-friend-api.vercel.app/remove_friend"

# --- ডাটাবেস ফাংশন ---
def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_history(data):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- HTML TEMPLATES ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { background: #0f0f12; color: white; font-family: 'Poppins', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1a1a1f; padding: 40px; border-radius: 15px; width: 300px; text-align: center; border: 1px solid #333; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #25252a; border: 1px solid #444; color: white; border-radius: 5px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #00ff7f; border: none; font-weight: bold; cursor: pointer; border-radius: 5px; margin-top: 10px; }
        .error { color: #ff4d4d; font-size: 0.9rem; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 style="color: #00ff7f;">Admin Panel</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        {% if error %} <div class="error">{{ error }}</div> {% endif %}
    </div>
</body>
</html>
"""

USER_PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RS User Panel</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0d1117; color: #e6edf3; font-family: 'Poppins', sans-serif; margin: 0; overflow-x: hidden; }
        
        /* Header & Sidebar */
        .header { background: #161b22; padding: 15px; display: flex; align-items: center; border-bottom: 1px solid #30363d; position: fixed; width: 100%; top: 0; z-index: 1000; }
        .menu-btn { font-size: 24px; cursor: pointer; color: #58a6ff; margin-right: 15px; }
        .sidebar { height: 100%; width: 250px; position: fixed; top: 0; left: -250px; background-color: #161b22; transition: 0.3s; padding-top: 60px; z-index: 999; border-right: 1px solid #30363d; }
        .sidebar.active { left: 0; }
        .sidebar a { padding: 15px 25px; text-decoration: none; font-size: 16px; color: #c9d1d9; display: flex; align-items: center; gap: 10px; transition: 0.2s; }
        .sidebar a:hover { background: #21262d; color: #58a6ff; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: none; z-index: 900; }
        .overlay.active { display: block; }

        /* Main Content */
        .container { padding: 80px 20px 20px 20px; max-width: 500px; margin: auto; }
        .card { background: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { text-align: center; color: #58a6ff; margin-bottom: 20px; }

        /* Inputs */
        label { font-size: 0.9rem; color: #8b949e; margin-bottom: 5px; display: block; }
        select, input { width: 100%; padding: 12px; margin-bottom: 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: white; box-sizing: border-box; font-family: inherit; }
        select:focus, input:focus { border-color: #58a6ff; outline: none; }
        
        /* Account Stats Badge */
        .acc-stats { font-size: 0.8rem; color: #2ea043; float: right; margin-top: -35px; margin-right: 10px; pointer-events: none; }

        /* Profile & Buttons */
        .profile-card { display: none; flex-direction: column; align-items: center; gap: 15px; margin-top: 20px; animation: fadeIn 0.5s; }
        .banner-img { width: 100%; border-radius: 8px; border: 2px solid #30363d; }
        .actions { display: flex; gap: 15px; width: 100%; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; color: white; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s; }
        .btn-check { width: 100%; background: #1f6feb; }
        .btn-add { background: #238636; } 
        .btn-remove { background: #da3633; }
        .btn:active { transform: scale(0.98); }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>

<div class="overlay" onclick="toggleMenu()"></div>
<div class="header">
    <i class="fas fa-bars menu-btn" onclick="toggleMenu()"></i>
    <h3 style="margin:0; color: white;">RS Tools</h3>
</div>

<div class="sidebar" id="sidebar">
    <h3 style="text-align:center; color: #58a6ff; margin-bottom: 20px;">Menu</h3>
    <a href="/"><i class="fas fa-robot"></i> User FF Bot</a>
    <a href="/guild-bot"><i class="fas fa-users"></i> Guild Info Bot</a>
    <a href="/login"><i class="fas fa-lock"></i> Admin Login</a>
</div>

<div class="container">
    <div class="card">
        <h2><i class="fas fa-gamepad"></i> Friend Bot</h2>
        
        <label>Select Sender Account:</label>
        <select id="senderAccount" onchange="updateStats()">
            <option value="" data-count="0">-- Choose Account --</option>
            </select>
        <div id="accStatDisplay" class="acc-stats"></div>

        <label>Target Player UID:</label>
        <input type="number" id="targetUid" placeholder="Enter Target UID">
        
        <button class="btn btn-check" onclick="showProfile()">
            <i class="fas fa-search"></i> Check Profile
        </button>

        <div class="profile-card" id="profileCard">
            <img src="" id="bannerImg" class="banner-img" alt="Banner">
            <div class="actions">
                <button class="btn btn-add" onclick="sendRequest('add')">
                    <i class="fas fa-user-plus"></i> Add
                </button>
                <button class="btn btn-remove" onclick="sendRequest('remove')">
                    <i class="fas fa-trash"></i> Reject
                </button>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<script>
    let accountsData = [];

    function toggleMenu() {
        document.getElementById('sidebar').classList.toggle('active');
        document.querySelector('.overlay').classList.toggle('active');
    }

    async function loadAccounts() {
        let res = await fetch('/api/get_accounts_with_stats');
        accountsData = await res.json();
        let select = document.getElementById('senderAccount');
        
        accountsData.forEach(acc => {
            let opt = document.createElement('option');
            opt.value = acc.uid;
            opt.dataset.count = acc.friend_count;
            opt.innerText = `${acc.name} (${acc.uid})`;
            select.appendChild(opt);
        });
    }

    function updateStats() {
        let select = document.getElementById('senderAccount');
        let count = select.options[select.selectedIndex].dataset.count || 0;
        let display = document.getElementById('accStatDisplay');
        if(select.value) {
            display.innerText = `Added: ${count}`;
        } else {
            display.innerText = "";
        }
    }

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

            if(data.status === 'success') {
                Swal.fire('Success!', action === 'add' ? 'Request Sent!' : 'Removed!', 'success');
                // Reload accounts to update count
                if(action === 'add') {
                     setTimeout(() => location.reload(), 1500); 
                }
            } else {
                Swal.fire('Failed', data.message, 'error');
            }
        } catch(e) { Swal.fire('Error', 'Server Error', 'error'); }
    }

    loadAccounts();
</script>
</body>
</html>
"""

GUILD_BOT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Guild Bot</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0d1117; color: white; font-family: 'Poppins', sans-serif; margin: 0; }
        .header { background: #161b22; padding: 15px; display: flex; align-items: center; border-bottom: 1px solid #30363d; }
        .back-btn { font-size: 24px; color: #58a6ff; margin-right: 15px; text-decoration: none; }
        .container { display: flex; justify-content: center; align-items: center; height: 80vh; flex-direction: column; }
        h2 { color: #58a6ff; }
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="back-btn"><i class="fas fa-arrow-left"></i></a>
        <h3>Guild Info Bot</h3>
    </div>
    <div class="container">
        <h2><i class="fas fa-hammer"></i> Coming Soon</h2>
        <p>Guild Info features will be added here.</p>
    </div>
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
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #0f0f12; color: white; font-family: 'Poppins', sans-serif; }
        .navbar { background: #1a1a1f; border-bottom: 1px solid #333; padding: 15px; }
        .stat-card { background: #1a1a1f; border-radius: 12px; padding: 20px; border: 1px solid #333; text-align: center; margin-bottom: 15px; }
        .stat-num { font-size: 2rem; font-weight: bold; color: #00ff7f; }
        .add-form { background: #1a1a1f; padding: 20px; border-radius: 12px; border: 1px solid #333; margin-top: 20px; }
        .form-control { background: #25252a; border: 1px solid #444; color: white; }
        .form-control:focus { background: #25252a; color: white; border-color: #00ff7f; box-shadow: none; }
        .btn-logout { color: #ff4d4d; border: 1px solid #ff4d4d; }
        .btn-logout:hover { background: #ff4d4d; color: white; }
        
        /* Mobile List View */
        .acc-list { margin-top: 20px; max-height: 400px; overflow-y: auto; }
        .acc-item { background: #25252a; padding: 15px; margin-bottom: 10px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
        .acc-info h5 { margin: 0; font-size: 1rem; color: white; }
        .acc-info small { color: #888; }
    </style>
</head>
<body>

<nav class="navbar">
    <div class="container-fluid">
        <span class="navbar-brand text-white fw-bold">Admin Panel</span>
        <a href="/logout" class="btn btn-sm btn-logout">Logout</a>
    </div>
</nav>

<div class="container mt-4">
    <div class="row">
        <div class="col-6">
            <div class="stat-card">
                <div class="stat-num" id="totalAcc">0</div>
                <small>Total Accounts</small>
            </div>
        </div>
        <div class="col-6">
            <div class="stat-card">
                <div class="stat-num text-info" id="totalReq">0</div>
                <small>Requests Sent</small>
            </div>
        </div>
    </div>

    <div class="add-form">
        <h5 class="mb-3 text-success"><i class="fas fa-plus-circle"></i> Add New Account</h5>
        <div class="mb-2"><input type="text" id="uid" class="form-control" placeholder="Account UID"></div>
        <div class="mb-2"><input type="text" id="pass" class="form-control" placeholder="Password / Token"></div>
        <div class="mb-2"><input type="text" id="name" class="form-control" placeholder="Name (e.g. Main ID)"></div>
        <button class="btn btn-success w-100 fw-bold" onclick="addAccount()">Add to Database</button>
    </div>

    <h5 class="mt-4 mb-3 text-white">Saved Accounts</h5>
    <div class="acc-list" id="accountList">
        </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<script>
    async function loadData() {
        let res = await fetch('/api/get_accounts_with_stats');
        let data = await res.json();
        
        document.getElementById('totalAcc').innerText = data.length;
        
        let list = document.getElementById('accountList');
        list.innerHTML = "";
        let totalReqs = 0;

        data.forEach(acc => {
            totalReqs += acc.friend_count;
            let item = `
                <div class="acc-item">
                    <div class="acc-info">
                        <h5>${acc.name}</h5>
                        <small>UID: ${acc.uid} | Added: ${acc.friend_count}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteAcc('${acc.uid}')"><i class="fas fa-trash"></i></button>
                </div>
            `;
            list.innerHTML += item;
        });
        document.getElementById('totalReq').innerText = totalReqs;
    }

    async function addAccount() {
        let uid = document.getElementById('uid').value;
        let pass = document.getElementById('pass').value;
        let name = document.getElementById('name').value;

        if(!uid || !pass) return Swal.fire('Error', 'UID & Pass Required', 'error');

        let res = await fetch('/api/add_account', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({uid, password: pass, name})
        });

        if(res.ok) {
            Swal.fire('Saved!', 'Account stored in JSON', 'success');
            document.getElementById('uid').value = '';
            document.getElementById('pass').value = '';
            loadData();
        } else {
            let d = await res.json();
            Swal.fire('Error', d.message, 'error');
        }
    }

    async function deleteAcc(uid) {
        if(!confirm("Delete this account permanently?")) return;
        await fetch('/api/delete_account', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({uid})
        });
        loadData();
    }

    loadData();
</script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    return render_template_string(USER_PANEL_HTML)

@app.route('/guild-bot')
def guild_bot():
    return render_template_string(GUILD_BOT_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == ADMIN_EMAIL and password == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = "Invalid Credentials!"
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(ADMIN_PANEL_HTML)

# --- API ENDPOINTS ---

@app.route('/api/add_account', methods=['POST'])
def api_add_account():
    if not session.get('logged_in'): return jsonify({"message": "Unauthorized"}), 403
    
    data = request.json
    accounts = load_db()
    
    # Check duplicate
    for acc in accounts:
        if acc['uid'] == data['uid']:
            return jsonify({"status": "error", "message": "Account exists"}), 400
            
    accounts.append({
        "uid": data['uid'],
        "password": data['password'],
        "name": data.get('name', data['uid'])
    })
    save_db(accounts)
    return jsonify({"status": "success"})

@app.route('/api/delete_account', methods=['POST'])
def api_delete_account():
    if not session.get('logged_in'): return jsonify({"message": "Unauthorized"}), 403
    uid = request.json.get('uid')
    accounts = load_db()
    accounts = [acc for acc in accounts if acc['uid'] != uid]
    save_db(accounts)
    return jsonify({"status": "success"})

@app.route('/api/get_accounts_with_stats')
def get_accounts_stats():
    accounts = load_db()
    history = load_history()
    
    result = []
    for acc in accounts:
        # Count how many targets in history for this sender
        sent_list = history.get(acc['uid'], [])
        result.append({
            "uid": acc['uid'],
            "name": acc['name'],
            "friend_count": len(sent_list)
        })
    return jsonify(result)

@app.route('/api/execute', methods=['POST'])
def execute_action():
    data = request.json
    sender_uid = data.get('sender_uid')
    target_uid = data.get('target_uid')
    action = data.get('action')

    # Load DB to find sender credentials
    accounts = load_db()
    sender_acc = next((a for a in accounts if a['uid'] == sender_uid), None)

    if not sender_acc:
        return jsonify({"status": "error", "message": "Sender account not found!"}), 400

    target_url = ADD_API if action == "add" else REMOVE_API
    
    try:
        response = requests.get(target_url, params={
            "uid": sender_acc['uid'],
            "password": sender_acc['password'],
            "player_id": target_uid
        })
        
        # If Add Friend is successful, save to history
        if action == "add":
            history = load_history()
            if sender_uid not in history:
                history[sender_uid] = []
            
            # Add only if not already in list
            if target_uid not in history[sender_uid]:
                history[sender_uid].append(target_uid)
                save_history(history)

        return jsonify({"status": "success", "response": response.text})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # Initial setup
    if not os.path.exists(DB_FILE): save_db([])
    if not os.path.exists(HISTORY_FILE): save_history({})
    
    app.run(debug=True, port=5000)
