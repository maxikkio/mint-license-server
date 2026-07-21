import uuid
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Baza danych ról administracyjnych i wyższych szczebli
ELEVATED_USERS = {
    "maxikk": {
        "password": "21288371",
        "role": "Właściciel",
        "package": "WŁAŚCICIEL (OWNER)"
    },
    "olafekk7": {
        "password": "Emo14578",
        "role": "Admin",
        "package": "ADMIN"
    },
    "marketing": {
        "password": "market123",
        "role": "Marketing Team",
        "package": "MARKETING"
    }
}

# Przykładowi klienci (możesz ich dopisywać lub zarządzać)
CLIENTS_DB = {
    # "janek": {"password": "haslo", "key": "MINT-ABCD-1234-EFGH", "package": "PRO", "role": "Klient"}
}

PANEL_HTML = """
<!DOCTYPE html>
<html lang="pl" class="dark">
<head>
    <meta charset="UTF-8">
    <title>Mint Server - Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: { brand: { 500: '#10b981', 600: '#059669', 400: '#34d399' } }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-[#090d16] text-slate-100 min-h-screen flex flex-col items-center justify-center p-6 selection:bg-brand-500 selection:text-white" x-data="app()">

    <!-- EKRAN LOGOWANIA -->
    <div x-show="!isLoggedIn" class="max-w-md w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-8 shadow-2xl backdrop-blur-xl flex flex-col gap-6">
        <div class="text-center flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 text-xl font-bold shadow-lg shadow-brand-500/10">⚡</div>
            <h1 class="text-lg font-bold text-white tracking-tight">Logowanie do Systemu</h1>
            <p class="text-xs text-slate-400">Wpisz swoje dane dostępu</p>
        </div>

        <form @submit.prevent="login()" class="flex flex-col gap-4">
            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Login / Nazwa użytkownika</label>
                <input type="text" x-model="form.username" required placeholder=""
                    class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Hasło</label>
                <input type="password" x-model="form.password" required placeholder=""
                    class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div x-show="message" class="text-xs px-3.5 py-2.5 rounded-xl font-medium text-center bg-rose-500/10 border border-rose-500/20 text-rose-400" x-text="message"></div>

            <button type="submit" class="w-full py-3.5 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-bold text-sm rounded-xl shadow-lg shadow-brand-500/20 transition-all cursor-pointer">
                Zaloguj się
            </button>
        </form>

        <div class="border-t border-slate-800 pt-4 text-center">
            <p class="text-xs text-slate-400">Nie masz konta lub klucza?</p>
            <p class="text-xs text-brand-400 mt-1 font-medium">Napisz wiadomość na: <a href="mailto:mbxryt24@zohomail.eu" class="underline">mbxryt24@zohomail.eu</a></p>
        </div>
    </div>

    <!-- PANEL GŁÓWNY (ROZDZIELENIE NA KLIENTA I ADMINA) -->
    <div x-show="isLoggedIn" class="max-w-4xl w-full flex flex-col gap-6" style="display: none;" :style="isLoggedIn ? 'display: flex;' : 'display: none;'">
        
        <header class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold">⚡</div>
                <div>
                    <h1 class="text-lg font-bold text-white flex items-center gap-2">
                        <span x-text="userData.role === 'Klient' ? 'Panel Klienta' : 'Panel Administratora'"></span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2.5 py-0.5 rounded-full uppercase" x-text="userData.role"></span>
                    </h1>
                    <p class="text-xs text-slate-400">Zalogowany: <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all">
                Wyloguj się
            </button>
        </header>

        <!-- 1. PANEL KLIENTA (Widoczny TYLKO dla Klienta) -->
        <div x-show="userData.role === 'Klient'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Twój Klucz Licencyjny Pro</h2>
            <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                <span class="font-mono text-brand-400 text-sm font-bold tracking-wider" x-text="userData.key"></span>
                <span class="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-lg">Aktywny</span>
            </div>
            <p class="text-xs text-slate-400">Skopiuj powyższy klucz i wklej go do aplikacji desktopowej Mint Video Downloader, aby w pełni ją aktywować.</p>
        </div>

        <!-- 2. PANEL ADMINA / ZARZĄDZANIA (Widoczny dla Właściciela, Admina i Marketingu) -->
        <div x-show="userData.role !== 'Klient'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <div class="flex items-center justify-between">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Zarządzanie Użytkownikami i Licencjami</h2>
                <button @click="loadUsers()" class="px-3 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">Odśwież</button>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Użytkownik</th>
                            <th class="py-3 px-3">Rola</th>
                            <th class="py-3 px-3">Klucz / Dane dostępu</th>
                        </tr>
                    </thead>
                    <tbody class="text-xs divide-y divide-slate-800/40">
                        <template x-for="user in users" :key="user.username">
                            <tr class="hover:bg-slate-800/30 transition-colors">
                                <td class="py-3 px-3 font-semibold text-slate-200" x-text="user.username"></td>
                                <td class="py-3 px-3 text-brand-400 font-medium" x-text="user.role"></td>
                                <td class="py-3 px-3 font-mono text-slate-400" x-text="user.credential"></td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

    </div>

    <script>
        function app() {
            return {
                isLoggedIn: false,
                form: { username: '', password: '' },
                userData: {},
                message: '',
                users: [],

                async login() {
                    this.message = '';
                    try {
                        let res = await fetch('/api/verify', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(this.form)
                        });
                        let data = await res.json();
                        if (data.status === 'valid') {
                            this.isLoggedIn = true;
                            this.userData = data;
                            if (data.role !== 'Klient') {
                                this.loadUsers();
                            }
                        } else {
                            this.message = data.error || 'Błąd logowania.';
                        }
                    } catch(e) {
                        this.message = 'Błąd połączenia z serwerem.';
                    }
                },

                async loadUsers() {
                    try {
                        let res = await fetch('/api/users', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username: this.form.username})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.users = data.users;
                        }
                    } catch(e) {}
                },

                logout() {
                    this.isLoggedIn = false;
                    this.form = { username: '', password: '' };
                    this.userData = {};
                    this.users = [];
                }
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
@app.route('/admin')
def serve_panel():
    return render_template_string(PANEL_HTML)


@app.route('/api/verify', methods=['POST'])
def verify_license():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    key = data.get("key", "").strip().upper()

    # 1. Sprawdzenie ról wyższych (Właściciel, Admin, Marketing)
    if username in ELEVATED_USERS:
        user = ELEVATED_USERS[username]
        if user["password"] == password:
            return jsonify({
                "status": "valid",
                "package": user["package"],
                "role": user["role"]
            })

    # 2. Sprawdzenie kont klientów
    if username in CLIENTS_DB:
        client = CLIENTS_DB[username]
        if client["password"] == password:
            return jsonify({
                "status": "valid",
                "package": client["package"],
                "role": client["role"],
                "key": client["key"]
            })

    # 3. Weryfikacja po samym kluczu (dla aplikacji desktopowej)
    for c_name, c_data in CLIENTS_DB.items():
        if c_data["key"] == key:
            return jsonify({
                "status": "valid",
                "package": c_data["package"],
                "role": c_data["role"]
            })

    return jsonify({
        "status": "invalid",
        "error": "Nieprawidłowy login lub hasło."
    }), 200


@app.route('/api/users', methods=['POST'])
def get_manageable_users():
    data = request.get_json() or {}
    current_username = data.get("username", "").strip()

    elevated_list = [
        {"username": "maxikk", "role": "Właściciel", "credential": "21288371"},
        {"username": "olafekk7", "role": "Admin", "credential": "Emo14578"},
        {"username": "marketing", "role": "Marketing Team", "credential": "market123"}
    ]

    clients_list = [{"username": uname, "role": "Klient", "credential": cdata["key"]} for uname, cdata in CLIENTS_DB.items()]
    all_accounts = elevated_list + clients_list

    # Restrykcje widoczności RBAC
    if current_username == "maxikk":
        return jsonify({"status": "success", "users": all_accounts})
    elif current_username in ["olafekk7", "marketing"]:
        filtered = [u for u in all_accounts if u["username"] != "maxikk"]
        return jsonify({"status": "success", "users": filtered})
    
    return jsonify({"status": "success", "users": []})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
