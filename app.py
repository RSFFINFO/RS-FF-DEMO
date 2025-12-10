import os
import json
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = "RS_SECRET_KEY_@123"

# --- কনফিগারেশন (অবশ্যই পূরণ করবেন) ---
# JSONBin.io থেকে পাওয়া তথ্য এখানে দিন
BIN_ID = "69395d2e43b1c97be9e44e5a"      # উদাহরণ: "675a1b2..."
API_KEY = "$2a$10$9fvgt32SGGgZVT7bJpe2sOscoGzsgpZhY1MZROV25krtWogW4Aqji"  # উদাহরণ: "$2a$10$..."

ADMIN_EMAIL = "admin@rs.com"
ADMIN_PASS = "rs1234"

# API URLs
ADD_API = "https://rs-ff-friend-api.vercel.app/add_friend"
REMOVE_API = "https://rs-ff-friend-api.vercel.app/remove_friend"
INFO_API = "https://rs-ff-info-sn5m.vercel.app/get"

# --- ডাটাবেস ফাংশন (JSONBin) ---
def get_db():
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
    headers = {"X-Master-Key": API_KEY}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("record", {"accounts": [], "history": {}})
        return {"accounts": [], "history": {}}
    except:
        return {"accounts": [], "history": {}}

def update_db(data):
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    headers = {
        "X-Master-Key": API_KEY,
        "Content-Type": "application/json"
    }
    try:
        requests.put(url, json=data, headers=headers)
        return True
    except:
        return False

# --- HTML TEMPLATES ---
# (ডিজাইন আগের মতোই আছে, শুধু লজিক বদলানো হয়েছে)

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
        .header { background: #161b22; padding: 15px; display: flex; align-items: center; border-bottom: 1px solid #30363d; position: fixed; width: 100%; top: 0; z-index: 1000; }
        .menu-btn { font-size: 24px; cursor: pointer; color: #58a6ff; margin-right: 15px; }
        .sidebar { height: 100%; width: 250px; position: fixed; top: 0; left: -250px; background-color: #161b22; transition: 0.3s; padding-top: 60px; z-index: 999; border-right: 1px solid #30363d; }
        .sidebar.active { left: 0; }
        .sidebar a { padding: 15px 25px; text-decoration: none; font-size: 16px; color: #c9d1d9; display: flex; align-items: center; gap: 10px; }
        .sidebar a:hover { background: #21262d; color: #58a6ff; }
        .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: none; z-index: 900; }
        .overlay.active { display: block; }
        .container { padding: 80px 20px 20px 20px; max-width: 500px; margin: auto; }
        .card { background: #161b22; padding: 25px; border-radius: 12px; border: 1px solid #30363d; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        h2 { text-align: center; color: #58a6ff; margin-bottom: 20px; }
        select, input { width: 100%; padding: 12px; margin-bottom: 15px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: white; box-sizing: border-box; }
        select:focus, input:focus { border-color: #58a6ff; outline: none; }
        .profile-card { display: none; flex-direction: column; align-items: center; gap: 15px; margin-top: 20px; }
        .banner-img { width: 100%; border-radius: 8px; border: 2px solid #30363d; }
        .actions { display: flex; gap: 15px; width: 100%; }
        .btn { flex: 1; padding: 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; color: white; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-check { width: 100%; background: #1f6feb; }
        .btn-add { background: #238636; } 
        .btn-remove { background: #da3633; }
        .acc-stats { font-size: 0.8rem; color: #2ea043; float: right; margin-top: -35px; margin-right: 10px; pointer-events: none; }
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
        <label style="color:#aaa; font-size:0.9rem;">Select Account:</label>
        <select id="senderAccount" onchange="updateStats()">
            <option value="" data-count="0">-- Choose Account --</option>
        </select>
        <div id="accStatDisplay" class="acc-stats"></div>
        
        <label style="color:#aaa; font-size:0.9rem;">Target UID:</label>
        <input type="number" id="targetUid" placeholder="Enter Target UID">
        <button class="btn btn-check" onclick="showProfile()"><i class="fas fa-search"></i> Check Profile</button>

        <div class="profile-card" id="profileCard">
            <img src="" id="bannerImg" class="banner-img" alt="Banner">
            <div class="actions">
                <button class="btn btn-add" onclick="sendRequest('add')"><i class="fas fa-user-plus"></i> Add</button>
                <button class="btn btn-remove" onclick="sendRequest('remove')"><i class="fas fa-trash"></i> Reject</button>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<script>
    function toggleMenu() {
        document.getElementById('sidebar').classList.toggle('active');
        document.querySelector('.overlay').classList.toggle('active');
    }
    
    async function loadAccounts() {
        let res = await fetch('/api/get_accounts_with_stats');
        let data = await res.json();
        let select = document.getElementById('senderAccount');
        data.forEach(acc => {
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
        document.getElementById('accStatDisplay').innerText = select.value ? `Added: ${count}` : "";
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
        let res = await fetch('/api/execute', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ sender_uid: sender, target_uid: target, action: action })
        });
        let data = await res.json();
        if(data.status === 'success') {
            Swal.fire('Success!', action=='add'?'Friend Request Sent!':'Player Removed!', 'success');
            if(action === 'add') setTimeout(() => location.reload(), 1500);
        } else Swal.fire('Error', data.message, 'error');
    }
    loadAccounts();
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
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #0f0f12; color: white; font-family: 'Poppins', sans-serif; }
        .navbar { background: #1a1a1f; border-bottom: 1px solid #333; padding: 15px; }
        .stat-card { background: #1a1a1f; border-radius: 12px; padding: 20px; border: 1px solid #333; text-align: center; margin-bottom: 15px; }
        .stat-num { font-size: 2rem; font-weight: bold; color: #00ff7f; }
        .add-form { background: #1a1a1f; padding: 20px; border-radius: 12px; border: 1px solid #333; margin-top: 20px; }
        .form-control { background: #25252a; border: 1px solid #444; color: white; margin-bottom: 10px; }
        .form-control:focus { background: #25252a; color: white; border-color: #00ff7f; box-shadow: none; }
        .acc-list { margin-top: 20px; max-height: 400px; overflow-y: auto; }
        .acc-item { background: #25252a; padding: 15px; margin-bottom: 10px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
    </style>
</head>
<body>

<nav class="navbar">
    <div class="container-fluid">
        <span class="navbar-brand text-white fw-bold">Admin Panel</span>
        <a href="/logout" class="btn btn-sm btn-outline-danger">Logout</a>
    </div>
</nav>

<div class="container mt-4">
    <div class="row">
        <div class="col-6"><div class="stat-card"><div class="stat-num" id="totalAcc">0</div><small>Total Accounts</small></div></div>
        <div class="col-6"><div class="stat-card"><div class="stat-num text-info" id="totalReq">0</div><small>Requests Sent</small></div></div>
    </div>

    <div class="add-form">
        <h5 class="mb-3 text-success"><i class="fas fa-plus-circle"></i> Add Account</h5>
        
        <label class="small text-muted">Required *</label>
        <input type="number" id="uid" class="form-control" placeholder="Account UID">
        <input type="text" id="pass" class="form-control" placeholder="Password / Token">
        
        <label class="small text-muted">Optional (Auto Fetch if Empty)</label>
        <input type="text" id="name" class="form-control" placeholder="Name (Optional)">
        
        <button class="btn btn-success w-100 fw-bold mt-2" onclick="addAccount()">Save Account</button>
    </div>

    <h5 class="mt-4 mb-3 text-white">Saved Accounts</h5>
    <div class="acc-list" id="accountList"></div>
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
            list.innerHTML += `
                <div class="acc-item">
                    <div>
                        <h5 style="margin:0; font-size:1rem;">${acc.name}</h5>
                        <small style="color:#aaa;">UID: ${acc.uid} | Added: ${acc.friend_count}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteAcc('${acc.uid}')"><i class="fas fa-trash"></i></button>
                </div>
            `;
        });
        document.getElementById('totalReq').innerText = totalReqs;
    }

    async function addAccount() {
        let uid = document.getElementById('uid').value;
        let pass = document.getElementById('pass').value;
        let name = document.getElementById('name').value;

        if(!uid || !pass) return Swal.fire('Error', 'UID & Password Required!', 'error');

        Swal.fire({ title: 'Saving...', didOpen: () => Swal.showLoading() });

        let res = await fetch('/api/add_account', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({uid, password: pass, name})
        });

        if(res.ok) {
            Swal.fire('Saved!', 'Account added to cloud', 'success');
            document.getElementById('uid').value = '';
            document.getElementById('pass').value = '';
            document.getElementById('name').value = '';
            loadData();
        } else {
            let d = await res.json();
            Swal.fire('Error', d.message, 'error');
        }
    }

    async function deleteAcc(uid) {
        if(!confirm("Delete this account?")) return;
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
def home(): return render_template_string(USER_PANEL_HTML)

@app.route('/guild-bot')
def guild_bot(): return render_template_string("""<h1 style='color:white;text-align:center;'>Guild Bot Coming Soon</h1>""")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('email') == ADMIN_EMAIL and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(ADMIN_PANEL_HTML)

# --- API ENDPOINTS ---

@app.route('/api/add_account', methods=['POST'])
def api_add_account():
    if not session.get('logged_in'): return jsonify({"message": "Unauthorized"}), 403
    
    data = request.json
    uid = str(data.get('uid'))
    password = data.get('password')
    name = data.get('name')

    db_data = get_db()
    accounts = db_data.get("accounts", [])
    
    # Check duplicate
    for acc in accounts:
        if acc['uid'] == uid:
            return jsonify({"status": "error", "message": "UID already exists!"}), 400

    # Auto Name Fetch
    if not name or name.strip() == "":
        try:
            resp = requests.get(f"{INFO_API}?uid={uid}&region=BD")
            if resp.status_code == 200:
                p_data = resp.json()
                info = p_data.get('AccountInfo', p_data)
                name = info.get('AccountName') or info.get('nickname') or f"User-{uid}"
            else:
                name = f"User-{uid}"
        except:
            name = f"User-{uid}"

    accounts.append({"uid": uid, "password": password, "name": name})
    db_data["accounts"] = accounts
    
    if update_db(db_data):
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Failed to save to cloud"}), 500

@app.route('/api/delete_account', methods=['POST'])
def api_delete_account():
    if not session.get('logged_in'): return jsonify({"message": "Unauthorized"}), 403
    uid = request.json.get('uid')
    
    db_data = get_db()
    accounts = db_data.get("accounts", [])
    
    new_accounts = [acc for acc in accounts if acc['uid'] != str(uid)]
    db_data["accounts"] = new_accounts
    
    update_db(db_data)
    return jsonify({"status": "success"})

@app.route('/api/get_accounts_with_stats')
def get_accounts_stats():
    db_data = get_db()
    accounts = db_data.get("accounts", [])
    history = db_data.get("history", {})
    
    result = []
    for acc in accounts:
        sent_list = history.get(acc['uid'], [])
        result.append({"uid": acc['uid'], "name": acc['name'], "friend_count": len(sent_list)})
    return jsonify(result)

@app.route('/api/execute', methods=['POST'])
def execute_action():
    data = request.json
    sender_uid = str(data.get('sender_uid'))
    target_uid = str(data.get('target_uid'))
    action = data.get('action')

    db_data = get_db()
    accounts = db_data.get("accounts", [])
    
    sender_acc = next((a for a in accounts if a['uid'] == sender_uid), None)
    if not sender_acc: return jsonify({"status": "error", "message": "Sender account missing!"}), 400

    target_url = ADD_API if action == "add" else REMOVE_API
    try:
        requests.get(target_url, params={"uid": sender_acc['uid'], "password": sender_acc['password'], "player_id": target_uid})
        
        if action == "add":
            history = db_data.get("history", {})
            if sender_uid not in history: history[sender_uid] = []
            
            if target_uid not in history[sender_uid]:
                history[sender_uid].append(target_uid)
                db_data["history"] = history
                update_db(db_data)
                
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
