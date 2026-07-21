from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import random
import string

app = Flask(__name__)

# Baza danych kont zespołu administracyjnego
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

# Baza kluczy licencyjnych
KEYS_DB = {}

# Historia logowań do panelu administracyjnego (zapamiętuje ostatnich 10)
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

# Panel Administracyjny w HTML + Tailwind + Alpine.js
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
            <p class="text-xs text-slate-400">Zaloguj się na swoje konto administracyjne</p>
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
    <div x-show="isLoggedIn" class="max-w-6xl w-full flex flex-col gap-6" style="display: none;" :style="isLoggedIn ? 'display: flex;' : 'display: none;'">
        
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
                🔑 Klucze i Licencje Użytkowników
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

            <!-- Historia logowań administracyjnych (ostatnich 10) -->
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">📜 Ostatnie 10 logowań do panelu administratorów</h2>
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
                <div class="flex items-center justify-between flex-wrap gap-4">
                    <div>
                        <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Zarządzanie Kluczami Licencyjnymi</h2>
                        <p class="text-[11px] text-slate-500">Dodawaj klucze powiązane z nazwami użytkowników, hasłami i notatkami</p>
                    </div>
                </div>

                <!-- Formularz dodawania nowego klucza -->
                <form @submit.prevent="addKey()" class="grid grid-cols-1 md:grid-cols-5 gap-3 bg-slate-950/60 p-4 border border-slate-800 rounded-xl">
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Nazwa użytkownika</label>
                        <input type="text" x-model="newKeyForm.username" required placeholder=""
                            class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Hasło</label>
                        <input type="text" x-model="newKeyForm.password" required placeholder=""
                            class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <div class="flex items-center justify-between">
                            <label class="text-[10px] font-semibold text-slate-400 uppercase">Klucz</label>
                            <button type="button" @click="generateKeyFormat()" class="text-[10px] text-brand-400 hover:underline">Generuj</button>
                        </div>
                        <input type="text" x-model="newKeyForm.key" required placeholder=""
                            class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs font-mono text-brand-400 focus:outline-none focus:border-brand-500 uppercase">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Notatki (opcjonalne)</label>
                        <input type="text" x-model="newKeyForm.notes" placeholder=""
                            class="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex items-end">
                        <button type="submit" class="w-full py-2 bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs rounded-lg shadow-md transition-all">
                            + Dodaj Klucz
                        </button>
                    </div>
                </form>

                <!-- Tabela kluczy z oddzielną kolumną statusu i zarządzania -->
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                                <th class="py-3 px-3">Użytkownik</th>
                                <th class="py-3 px-3">Hasło</th>
                                <th class="py-3 px-3">Klucz Licencyjny</th>
                                <th class="py-3 px-3">Notatki</th>
                                <th class="py-3 px-3 text-center">Status</th>
                                <th class="py-3 px-3 text-right">Zarządzanie</th>
                            </tr>
                        </thead>
                        <tbody class="text-xs divide-y divide-slate-800/40">
                            <template x-for="item in keysList" :key="item.key">
                                <tr class="hover:bg-slate-800/30 transition-colors">
                                    <td class="py-3 px-3 font-semibold text-slate-200" x-text="item.username"></td>
                                    <td class="py-3 px-3 font-mono text-slate-400" x-text="item.password"></td>
                                    <td class="py-3 px-3 font-mono text-brand-400 font-semibold" x-text="item.key"></td>
                                    <td class="py-3 px-3 text-slate-300 italic" x-text="item.notes || 'Brak'"></td>
                                    <td class="py-3 px-3 text-center">
                                        <span class="px-2.5 py-1 rounded-lg text-[10px] font-semibold"
                                            :class="{
                                                'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': item.status === 'Aktywny',
                                                'bg-amber-500/10 text-amber-400 border border-amber-500/20': item.status === 'Wstrzymany',
                                                'bg-rose-500/10 text-rose-400 border border-rose-500/20': item.status === 'Anulowany'
                                            }" x-text="item.status"></span>
                                    </td>
                                    <td class="py-3 px-3 text-right flex items-center justify-end gap-1.5">
                                        <button @click="changeKeyStatus(item.key, 'Aktywny')" x-show="item.status !== 'Aktywny'" class="px-2 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded text-[10px] font-semibold transition-all">Aktywuj</button>
                                        <button @click="changeKeyStatus(item.key, 'Wstrzymany')" x-show="item.status === 'Aktywny'" class="px-2 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded text-[10px] font-semibold transition-all">Wstrzymaj</button>
                                        <button @click="changeKeyStatus(item.key, 'Anulowany')" x-show="item.status !== 'Anulowany'" class="px-2 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 rounded text-[10px] font-semibold transition-all">Anuluj</button>
                                        <button @click="deleteKey(item.key)" class="px-2 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded text-[10px] font-semibold transition-all">Usuń</button>
                                    </td>
                                </tr>
                            </template>
                            <template x-if="keysList.length === 0">
                                <tr><td colspan="6" class="py-6 text-center text-slate-600 italic">Brak kluczy w bazie. Dodaj pierwszy powyżej.</td></tr>
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
                newKeyForm: {
                    username: '',
                    password: '',
                    key: '',
                    notes: ''
                },
                generateKeyFormat() {
                    let part = () => Math.random().toString(36).substring(2, 6).toUpperCase();
                    this.newKeyForm.key = `${part()}-${part()}-${part()}`;
                },
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
                async addKey() {
                    try {
                        let res = await fetch('/api/keys/add', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                admin_username: this.username,
                                ...this.newKeyForm
                            })
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.keysList = data.keys;
                            this.newKeyForm = { username: '', password: '', key: '', notes: '' };
                        } else {
                            alert(data.message || 'Nie udało się dodać klucza.');
                        }
                    } catch(e) {}
                },
                async changeKeyStatus(keyStr, newStatus) {
                    try {
                        let res = await fetch('/api/keys/status', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                admin_username: this.username,
                                key: keyStr,
                                status: newStatus
                            })
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.keysList = data.keys;
                        }
                    } catch(e) {}
                },
                async deleteKey(keyStr) {
                    if (!confirm('Czy na pewno chcesz bezpowrotnie usunąć ten klucz?')) return;
                    try {
                        let res = await fetch('/api/keys/delete', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                admin_username: this.username,
                                key: keyStr
                            })
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

    # 1. Logowanie kont administracyjnych w panelu /admin (zapisywane w historii)
    if username in USERS_DB and not key:
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
                "error": "Nieprawidłowe hasło dla konta administracyjnego."
            }), 200

    # 2. Weryfikacja kluczy licencyjnych dla klientów (brak wpisów w historii logowań panelu)
    if key in KEYS_DB:
        ldata = KEYS_DB[key]
        if ldata["status"] == "Aktywny" and ldata["username"] == username and ldata["password"] == password:
            return jsonify({
                "status": "valid",
                "package": "PRO",
                "role": "Użytkownik"
            })
        else:
            return jsonify({
                "status": "invalid",
                "error": "Licencja jest wstrzymana, anulowana lub dane logowania są błędne."
            }), 200

    return jsonify({
        "status": "invalid",
        "error": "Nieprawidłowy klucz licencyjny, login lub hasło."
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

    users_to_send = []
    for acc in base_accounts:
        user_copy = acc.copy()
        if current_username != "maxikk" and user_copy["username"] != current_username:
            user_copy["password"] = "********"
        users_to_send.append(user_copy)

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


@app.route('/api/keys/add', methods=['POST'])
def add_new_key():
    data = request.get_json() or {}
    admin_username = data.get("admin_username", "").strip()

    if admin_username not in USERS_DB:
        return jsonify({"status": "error", "message": "Brak uprawnień"}), 403

    k_val = data.get("key", "").strip().upper()
    u_val = data.get("username", "").strip()
    p_val = data.get("password", "").strip()
    n_val = data.get("notes", "").strip()

    if not k_val or not u_val or not p_val:
        return jsonify({"status": "error", "message": "Wypełnij wymagane pola klucza!"}), 400

    KEYS_DB[k_val] = {
        "key": k_val,
        "username": u_val,
        "password": p_val,
        "notes": n_val,
        "status": "Aktywny",
        "package": "PRO",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return jsonify({
        "status": "success",
        "keys": list(KEYS_DB.values())
    })


@app.route('/api/keys/status', methods=['POST'])
def change_key_status():
    data = request.get_json() or {}
    admin_username = data.get("admin_username", "").strip()
    key = data.get("key", "").strip().upper()
    new_status = data.get("status", "").strip()

    if admin_username not in USERS_DB:
        return jsonify({"status": "error", "message": "Brak uprawnień"}), 403

    if key in KEYS_DB and new_status in ["Aktywny", "Wstrzymany", "Anulowany"]:
        KEYS_DB[key]["status"] = new_status
        return jsonify({"status": "success", "keys": list(KEYS_DB.values())})

    return jsonify({"status": "error", "message": "Nie znaleziono klucza"}), 404


@app.route('/api/keys/delete', methods=['POST'])
def delete_key():
    data = request.get_json() or {}
    admin_username = data.get("admin_username", "").strip()
    key = data.get("key", "").strip().upper()

    if admin_username not in USERS_DB:
        return jsonify({"status": "error", "message": "Brak uprawnień"}), 403

    if key in KEYS_DB:
        del KEYS_DB[key]
        return jsonify({"status": "success", "keys": list(KEYS_DB.values())})

    return jsonify({"status": "error", "message": "Nie znaleziono klucza"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
