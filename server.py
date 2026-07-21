from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import random
import string

app = Flask(__name__)

# Baza danych kont zespołu
USERS_DB = {
    "maxikk": {
        "username": "maxikk",
        "password": "21288371",
        "role": "Właściciel",
        "package": "WŁAŚCICIEL (OWNER)"
    },
    "olafekk7": {
        "username": "olafekk7",
        "password": "Emo14578",
        "role": "Marketing Team",
        "package": "MARKETING TEAM"
    }
}

# Baza danych kluczy licencyjnych
KEYS_DB = {
    "MINT-PRO-2026-X7K9": {"key": "MINT-PRO-2026-X7K9", "status": "Aktywny", "package": "PRO", "created_at": "2026-07-01 10:00:00"},
    "MINT-PREM-9999-ABCD": {"key": "MINT-PREM-9999-ABCD", "status": "Aktywny", "package": "PREMIUM", "created_at": "2026-07-10 14:20:00"}
}

# Historia logowań (ostatnich 10)
LOGIN_HISTORY = []

def record_login(username, role):
    entry = {
        "username": username,
        "role": role,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    LOGIN_HISTORY.insert(0, entry)
    if len(LOGIN_HISTORY) > 10:
        LOGIN_HISTORY.pop()

# Panel Administracyjny w HTML + Tailwind + Alpine.js z obsługą zakładek
PANEL_HTML = """
<!DOCTYPE html>
<html lang="pl" class="dark">
<head>
    <meta charset="UTF-8">
    <title>Panel Zarządzania - Mint Server</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: { 500: '#10b981', 600: '#059669', 400: '#34d399' }
                    }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-[#090d16] text-slate-100 min-h-screen flex flex-col items-center justify-center p-6 selection:bg-brand-500 selection:text-white" x-data="panelApp()">

    <!-- EKRAN LOGOWANIA -->
    <div x-show="!isLoggedIn" class="max-w-md w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-8 shadow-2xl backdrop-blur-xl flex flex-col gap-6">
        <div class="text-center flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 text-xl font-bold shadow-lg shadow-brand-500/10">⚡</div>
            <h1 class="text-lg font-bold text-white tracking-tight">Panel Serwera Mint</h1>
            <p class="text-xs text-slate-400">Zaloguj się na swoje konto</p>
        </div>

        <form @submit.prevent="login()" class="flex flex-col gap-4">
            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Login</label>
                <input type="text" x-model="username" required placeholder=""
                    class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Hasło</label>
                <input type="password" x-model="password" required placeholder=""
                    class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div x-show="errorMsg" class="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3.5 py-2.5 rounded-xl font-medium text-center" x-text="errorMsg"></div>

            <button type="submit" class="w-full py-3.5 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-bold text-sm rounded-xl shadow-lg shadow-brand-500/20 transition-all cursor-pointer">
                Zaloguj do Panelu
            </button>
        </form>
    </div>

    <!-- GŁÓWNY PANEL Z ZAKŁADKAMI -->
    <div x-show="isLoggedIn" class="max-w-4xl w-full flex flex-col gap-6" style="display: none;" :style="isLoggedIn ? 'display: flex;' : 'display: none;'">
        
        <header class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold">⚡</div>
                <div>
                    <h1 class="text-lg font-bold text-white flex items-center gap-2">
                        <span>Zarządzanie Serwerem</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2.5 py-0.5 rounded-full uppercase" x-text="role"></span>
                    </h1>
                    <p class="text-xs text-slate-400">Zalogowany jako: <b class="text-slate-200" x-text="username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all">
                Wyloguj się
            </button>
        </header>

        <!-- Nawigacja zakładkami -->
        <div class="flex gap-2 border-b border-slate-800/60 pb-2">
            <button @click="activeTab = 'team'" :class="activeTab === 'team' ? 'bg-brand-500/10 border-brand-500/30 text-brand-400' : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl border text-xs font-semibold transition-all">
                👥 Zespół i Audyt Logowań
            </button>
            <button @click="activeTab = 'licenses'" :class="activeTab === 'licenses' ? 'bg-brand-500/10 border-brand-500/30 text-brand-400' : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl border text-xs font-semibold transition-all">
                🔑 Klucze i Licencje
            </button>
        </div>

        <!-- ZAKŁADKA 1: ZESPÓŁ I OSTATNIE LOGOWANIA -->
        <div x-show="activeTab === 'team'" class="flex flex-col gap-6">
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
                <div class="flex items-center justify-between">
                    <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Struktura Zespołu</h2>
                    <button @click="loadData()" class="px-3 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">Odśwież</button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                                <th class="py-3 px-3">Użytkownik</th>
                                <th class="py-3 px-3">Rola</th>
                                <th class="py-3 px-3">Hasło</th>
                                <th class="py-3 px-3 text-right">Dostęp</th>
                            </tr>
                        </thead>
                        <tbody class="text-xs divide-y divide-slate-800/40">
                            <template x-for="user in users" :key="user.username">
                                <tr class="hover:bg-slate-800/30 transition-colors">
                                    <td class="py-3 px-3 font-semibold text-slate-200" x-text="user.username"></td>
                                    <td class="py-3 px-3 text-brand-400 font-medium" x-text="user.role"></td>
                                    <td class="py-3 px-3 font-mono text-slate-400" x-text="user.password"></td>
                                    <td class="py-3 px-3 text-right">
                                        <span class="px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" x-text="user.access"></span>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Historia logowań (ostatnich 10) -->
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">📜 Ostatnie 10 logowań do panelu</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                                <th class="py-2.5 px-3">Użytkownik</th>
                                <th class="py-2.5 px-3">Rola</th>
                                <th class="py-2.5 px-3 text-right">Data i czas</th>
                            </tr>
                        </thead>
                        <tbody class="text-xs divide-y divide-slate-800/40">
                            <template x-for="entry in history" :key="entry.timestamp + entry.username">
                                <tr class="hover:bg-slate-800/30 transition-colors">
                                    <td class="py-2.5 px-3 font-medium text-slate-200" x-text="entry.username"></td>
                                    <td class="py-2.5 px-3 text-brand-400" x-text="entry.role"></td>
                                    <td class="py-2.5 px-3 text-right font-mono text-slate-400" x-text="entry.timestamp"></td>
                                </tr>
                            </template>
                            <template x-if="history.length === 0">
                               <tr><td colspan="3" class="py-4 text-center text-slate-600 italic">Brak wpisów w historii.</td></tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ZAKŁADKA 2: KLUCZE I LICENCJE -->
        <div x-show="activeTab === 'licenses'" class="flex flex-col gap-6" style="display: none;">
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-6">
                <div class="flex items-center justify-between">
                    <div>
                        <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aktywne Klucze Licencyjne</h2>
                        <p class="text-[11px] text-slate-500">Zarządzaj kluczami dostępu dla klientów oprogramowania</p>
                    </div>
                    <button @click="generateKey()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-brand-500 hover:bg-brand-600 text-white shadow-lg shadow-brand-500/20 transition-all">
                        + Generuj Nowy Klucz
                    </button>
                </div>

                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                                <th class="py-3 px-3">Klucz Licencyjny</th>
                                <th class="py-3 px-3">Pakiet</th>
                                <th class="py-3 px-3">Data utworzenia</th>
                                <th class="py-3 px-3 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody class="text-xs divide-y divide-slate-800/40">
                            <template x-for="item in keysList" :key="item.key">
                                <tr class="hover:bg-slate-800/30 transition-colors">
                                    <td class="py-3 px-3 font-mono text-brand-400 font-semibold" x-text="item.key"></td>
                                    <td class="py-3 px-3 text-slate-200" x-text="item.package"></td>
                                    <td class="py-3 px-3 text-slate-400" x-text="item.created_at"></td>
                                    <td class="py-3 px-3 text-right">
                                        <span class="px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" x-text="item.status"></span>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>

    <script>
        function panelApp() {
            return {
                isLoggedIn: false,
                activeTab: 'team',
                username: '',
                password: '',
                role: '',
                errorMsg: '',
                users: [],
                history: [],
                keysList: [],
                async login() {
                    this.errorMsg = '';
                    try {
                        let res = await fetch('/api/verify', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username: this.username, password: this.password})
                        });
                        let data = await res.json();
                        if (data.status === 'valid') {
                            this.isLoggedIn = true;
                            this.role = data.role;
                            this.loadData();
                        } else {
                            this.errorMsg = data.error || 'Nieprawidłowe dane logowania.';
                        }
                    } catch(e) {
                        this.errorMsg = 'Błąd połączenia z serwerem.';
                    }
                },
                async loadData() {
                    try {
                        let res = await fetch('/api/data', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username: this.username})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.users = data.users;
                            this.history = data.history || [];
                            this.keysList = data.keys || [];
                        }
                    } catch(e) {}
                },
                async generateKey() {
                    try {
                        let res = await fetch('/api/keys/generate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username: this.username})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.keysList = data.keys;
                        }
                    } catch(e) {}
                },
                logout() {
                    this.isLoggedIn = false;
                    this.username = '';
                    this.password = '';
                    this.users = [];
                    this.history = [];
                    this.keysList = [];
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

    # 1. Logowanie kont administracyjnych
    if username in USERS_DB:
        user = USERS_DB[username]
        if user["password"] == password:
            record_login(username, user["role"])
            return jsonify({
                "status": "valid",
                "package": user["package"],
                "role": user["role"]
            })
        else:
            return jsonify({
                "status": "invalid",
                "error": "Nieprawidłowe hasło dla tego konta."
            }), 200

    # 2. Weryfikacja kluczy licencyjnych
    if key in KEYS_DB:
        record_login(f"Klucz: {key[:10]}...", "Użytkownik")
        return jsonify({
            "status": "valid",
            "package": KEYS_DB[key]["package"],
            "role": "Użytkownik"
        })

    return jsonify({
        "status": "invalid",
        "error": "Nieprawidłowy login, hasło lub klucz licencyjny."
    }), 200


@app.route('/api/data', methods=['POST'])
def get_dashboard_data():
    data = request.get_json() or {}
    current_username = data.get("username", "").strip()

    base_accounts = [
        {"username": "maxikk", "role": "Właściciel", "password": "21288371", "access": "Pełny dostęp właścicielski"},
        {"username": "olafekk7", "role": "Marketing Team", "password": "Emo14578", "access": "Zarządzanie kontami"}
    ]

    keys_array = list(KEYS_DB.values())

    # Bezpieczeństwo haseł: każdy widzi siebie, ale tylko Właściciel widzi hasła innych
    users_to_send = []
    for acc in base_accounts:
        user_copy = acc.copy()
        if current_username != "maxikk" and user_copy["username"] != current_username:
            user_copy["password"] = "********"  # Ukrywanie hasła innych użytkowników
        users_to_send.append(user_copy)

    # Filtracja historii (Właściciel widzi wszystko, inni widzą bez Właściciela)
    if current_username == "maxikk":
        history_to_send = LOGIN_HISTORY
    else:
        history_to_send = [h for h in LOGIN_HISTORY if h["username"] != "maxikk"]

    return jsonify({
        "status": "success",
        "users": users_to_send,
        "history": history_to_send,
        "keys": keys_array
    })


@app.route('/api/keys/generate', methods=['POST'])
def generate_new_key():
    data = request.get_json() or {}
    username = data.get("username", "").strip()

    if username not in USERS_DB:
        return jsonify({"status": "error", "message": "Brak uprawnień"}), 403

    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    new_key_str = f"MINT-PRO-{datetime.now().strftime('%Y')}-{random_suffix}"
    
    KEYS_DB[new_key_str] = {
        "key": new_key_str,
        "status": "Aktywny",
        "package": "PRO",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return jsonify({
        "status": "success",
        "keys": list(KEYS_DB.values())
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
