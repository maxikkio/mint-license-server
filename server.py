from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Baza danych użytkowników i uprawnień na serwerze
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
        "role": "Admin",
        "package": "ADMIN"
    }
}

# Wbudowany Panel Administracyjny w przeglądarce (HTML + Tailwind + Alpine.js)
PANEL_HTML = """
<!DOCTYPE html>
<html lang="pl" class="dark">
<head>
    <meta charset="UTF-8">
    <title>Panel Zarządzania Licencjami - Mint Server</title>
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

    <!-- EKRAN LOGOWANIA DO PANELU SERWERA -->
    <div x-show="!isLoggedIn" class="max-w-md w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-8 shadow-2xl backdrop-blur-xl flex flex-col gap-6">
        <div class="text-center flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 text-xl font-bold shadow-lg shadow-brand-500/10">⚡</div>
            <h1 class="text-lg font-bold text-white tracking-tight">Panel Administracyjny Serwera</h1>
            <p class="text-xs text-slate-400">Zaloguj się jako Właściciel lub Administrator</p>
        </div>

        <form @submit.prevent="login()" class="flex flex-col gap-4">
            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Login</label>
                <input type="text" x-model="username" required placeholder="np. maxikk"
                    class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Hasło</label>
                <input type="password" x-model="password" required placeholder="••••••••"
                    class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div x-show="errorMsg" class="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-3.5 py-2.5 rounded-xl font-medium text-center" x-text="errorMsg"></div>

            <button type="submit" class="w-full py-3.5 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 hover:to-emerald-700 text-white font-bold text-sm rounded-xl shadow-lg shadow-brand-500/20 transition-all cursor-pointer">
                Zaloguj do Panelu
            </button>
        </form>
    </div>

    <!-- GŁÓWNY PANEL ZARZĄDZANIA KONTAMI -->
    <div x-show="isLoggedIn" class="max-w-4xl w-full flex flex-col gap-6" style="display: none;" :style="isLoggedIn ? 'display: flex;' : 'display: none;'">
        
        <header class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold">⚡</div>
                <div>
                    <h1 class="text-lg font-bold text-white flex items-center gap-2">
                        <span>Zarządzanie Dostępami</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2.5 py-0.5 rounded-full uppercase" x-text="role"></span>
                    </h1>
                    <p class="text-xs text-slate-400">Zalogowany jako: <b class="text-slate-200" x-text="username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all">
                Wyloguj się
            </button>
        </header>

        <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <div class="flex items-center justify-between">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lista użytkowników i poziomów uprawnień</h2>
                <button @click="loadUsers()" class="px-3 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">Odśwież listę</button>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Użytkownik</th>
                            <th class="py-3 px-3">Rola</th>
                            <th class="py-3 px-3">Hasło / Klucz</th>
                            <th class="py-3 px-3 text-right">Status / Uprawnienia</th>
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
            
            <div class="mt-2 p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-400 flex items-center gap-2">
                <span>🔒</span>
                <span><b>Bezpieczeństwo RBAC:</b> Zgodnie z konfiguracją, Właściciel widzi pełną strukturę, natomiast Administrator widzi wyłącznie swój zespół i użytkowników, mając całkowicie ukryte konto oraz hasło Właściciela.</span>
            </div>
        </div>

    </div>

    <script>
        function panelApp() {
            return {
                isLoggedIn: false,
                username: '',
                password: '',
                role: '',
                errorMsg: '',
                users: [],
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
                            this.loadUsers();
                        } else {
                            this.errorMsg = data.error || 'Nieprawidłowe dane logowania.';
                        }
                    } catch(e) {
                        this.errorMsg = 'Błąd połączenia z serwerem.';
                    }
                },
                async loadUsers() {
                    try {
                        let res = await fetch('/api/users', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username: this.username})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.users = data.users;
                        }
                    } catch(e) {}
                },
                logout() {
                    this.isLoggedIn = false;
                    this.username = '';
                    this.password = '';
                    this.users = [];
                }
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def serve_panel():
    """Serwuje wizualny Panel Administracyjny pod adresem głównym serwera"""
    return render_template_string(PANEL_HTML)


@app.route('/api/verify', methods=['POST'])
def verify_license():
    """Endpoint używany zarówno przez aplikację kliencką, jak i przez Panel"""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if username in USERS_DB:
        user = USERS_DB[username]
        if user["password"] == password:
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

    return jsonify({
        "status": "invalid",
        "error": "Nie znaleziono takiego użytkownika."
    }), 200


@app.route('/api/users', methods=['POST'])
def get_manageable_users():
    """Endpoint zwracający listę kont z uwzględnieniem restrykcji poziomu dostępu (RBAC)"""
    data = request.get_json() or {}
    current_username = data.get("username", "").strip()

    all_accounts = [
        {"username": "maxikk", "role": "Właściciel", "password": "21288371", "access": "Pełny dostęp właścicielski"},
        {"username": "olafekk7", "role": "Admin", "password": "Emo14578", "access": "Zarządzanie bez wglądu w Właściciela"}
    ]

    # Reguły zabezpieczeń RBAC po stronie serwera:
    if current_username == "maxikk":
        # Właściciel widzi wszystko
        return jsonify({"status": "success", "users": all_accounts})
    
    elif current_username == "olafekk7":
        # Admin widzi tylko siebie / zwykłych użytkowników — KONTO WŁAŚCICIELA JEST CAŁKOWICIE UKRYTE
        filtered_accounts = [u for u in all_accounts if u["username"] != "maxikk"]
        return jsonify({"status": "success", "users": filtered_accounts})
    
    else:
        return jsonify({"status": "success", "users": []})


if __name__ == '__main__':
    # Uruchomienie lokalne
    app.run(host='0.0.0.0', port=5000)