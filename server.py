from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import sqlite3

app = FastAPI()
security = HTTPBasic()

# Twoje dane logowania do panelu administratora
ADMIN_USER = "maxikk"
ADMIN_PASS = "21288371"

def init_db():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            package TEXT,
            status TEXT DEFAULT 'active',
            username TEXT,
            password TEXT,
            notes TEXT
        )
    """)
    # Automatyczne migracje kolumn dla istniejącej bazy
    for col in [("status", "TEXT DEFAULT 'active'"), ("username", "TEXT"), ("password", "TEXT"), ("notes", "TEXT")]:
        try:
            cursor.execute(f"ALTER TABLE licenses ADD COLUMN {col[0]} {col[1]}")
        except:
            pass
    conn.commit()
    conn.close()

init_db()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != ADMIN_USER or credentials.password != ADMIN_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Błędne dane logowania",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Model żądania weryfikacji z aplikacji klienta
class VerifyRequest(BaseModel):
    key: str
    username: str
    password: str

@app.post("/api/verify")
def verify_key(data: VerifyRequest):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT package, status, username, password FROM licenses WHERE key = ?", (data.key.strip(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        pkg, status_val, db_user, db_pass = row
        # Sprawdzamy czy klucz jest aktywny oraz czy zgadza się użytkownik i hasło
        if status_val == 'active' and db_user == data.username.strip() and db_pass == data.password.strip():
            return {"status": "valid", "package": pkg}
            
    return {"status": "invalid"}

# Panel Administratora
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(admin: str = Depends(verify_admin)):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT key, package, status, username, password, notes FROM licenses")
    rows = cursor.fetchall()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="pl" class="dark">
    <head>
        <meta charset="UTF-8">
        <title>Panel Licencji - Mint Pro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            function generateKey() {
                const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
                const seg = () => Array.from({length: 4}, () => chars[Math.floor(Math.random() * chars.length)]).join('');
                document.getElementById('keyInput').value = `MINT-${seg()}-${seg()}-${seg()}`;
            }
        </script>
    </head>
    <body class="bg-[#090d16] text-slate-100 min-h-screen p-8 font-sans">
        <div class="max-w-6xl mx-auto flex flex-col gap-6">
            <header class="flex justify-between items-center border-b border-slate-800 pb-4">
                <h1 class="text-xl font-bold text-white flex items-center gap-2">🔑 Panel Administratora Licencji</h1>
                <span class="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">Online</span>
            </header>

            <!-- Formularz dodawania -->
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
                <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Dodaj nowy klucz i przypisz użytkownika</h2>
                <form action="/admin/add" method="post" class="flex flex-col gap-4">
                    <div class="flex gap-3">
                        <div class="flex-1">
                            <input type="text" id="keyInput" name="key" placeholder="Kliknij losuj lub wpisz klucz..." required 
                                   class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm font-mono text-emerald-300 focus:outline-none focus:border-emerald-500">
                        </div>
                        <button type="button" onclick="generateKey()" class="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-blue-600/20">🎲 Losuj klucz</button>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <input type="text" name="username" placeholder="Nazwa użytkownika (login klienta)" required
                               class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500">
                        <input type="text" name="password" placeholder="Hasło użytkownika klienta" required
                               class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500">
                        <input type="text" name="notes" placeholder="Notatki (np. Allegro / Licencja roczna)" 
                               class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500">
                    </div>
                    <div class="flex justify-between items-center pt-2">
                        <input type="hidden" name="package" value="PRO">
                        <span class="text-xs text-slate-500">Pakiet: <b class="text-slate-300">PRO</b> | Status: <b class="text-emerald-400">Aktywny</b></span>
                        <button type="submit" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-emerald-600/20">💾 Zapisz w bazie</button>
                    </div>
                </form>
            </div>

            <!-- Tabela kluczy -->
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
                <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Zarządzanie licencjami i dostępami</h2>
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr class="border-b border-slate-800 text-xs text-slate-500 font-semibold">
                                <th class="py-3 px-2">Klucz licencyjny</th>
                                <th class="py-3 px-2">Dane użytkownika</th>
                                <th class="py-3 px-2">Notatki</th>
                                <th class="py-3 px-2 text-center">Status</th>
                                <th class="py-3 px-2 text-right">Akcje</th>
                            </tr>
                        </thead>
                        <tbody class="text-xs divide-y divide-slate-800/40">
    """
    for r in rows:
        key, pkg, status_val, user, pwd, notes = r[0], r[1], r[2], r[3] or "-", r[4] or "-", r[5] or ""
        if status_val == 'active':
            status_badge = '<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded-full font-semibold">Aktywny</span>'
            toggle_btn = f'<a href="/admin/status?key={key}&status=paused" class="text-amber-400 hover:text-amber-300 font-semibold px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20">Wstrzymaj</a>'
        else:
            status_badge = '<span class="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded-full font-semibold">Wstrzymany</span>'
            toggle_btn = f'<a href="/admin/status?key={key}&status=active" class="text-emerald-400 hover:text-emerald-300 font-semibold px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">Wznów</a>'

        html += f"""
                        <tr class="hover:bg-slate-800/30">
                            <td class="py-3 px-2 font-mono text-emerald-300 font-bold">{key}</td>
                            <td class="py-3 px-2">
                                <div class="text-slate-200">👤 <b>{user}</b></div>
                                <div class="text-slate-400 font-mono text-[11px]">🔑 {pwd}</div>
                            </td>
                            <td class="py-3 px-2 text-slate-300 max-w-xs truncate">{notes}</td>
                            <td class="py-3 px-2 text-center">{status_badge}</td>
                            <td class="py-3 px-2 text-right space-x-2">
                                {toggle_btn}
                                <a href="/admin/delete?key={key}" class="text-rose-400 hover:text-rose-300 font-semibold px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20">Usuń</a>
                            </td>
                        </tr>
        """
    if not rows:
        html += '<tr><td colspan="5" class="py-8 text-center text-slate-600 italic">Brak kluczy w bazie.</td></tr>'

    html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.post("/admin/add")
def admin_add(key: str = Form(...), package: str = Form(...), username: str = Form(...), password: str = Form(...), notes: str = Form(""), admin: str = Depends(verify_admin)):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO licenses (key, package, status, username, password, notes) VALUES (?, ?, 'active', ?, ?, ?)", (key, package, username, password, notes))
        conn.commit()
    except Exception as e:
        print("Error:", e)
    conn.close()
    return HTMLResponse("<script>window.location='/admin';</script>")

@app.get("/admin/status")
def admin_status(key: str, status: str, admin: str = Depends(verify_admin)):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE licenses SET status = ? WHERE key = ?", (status, key))
    conn.commit()
    conn.close()
    return HTMLResponse("<script>window.location='/admin';</script>")

@app.get("/admin/delete")
def admin_delete(key: str, admin: str = Depends(verify_admin)):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM licenses WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    return HTMLResponse("<script>window.location='/admin';</script>")
