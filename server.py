from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import sqlite3

app = FastAPI()
security = HTTPBasic()

# Konfiguracja logowania do Twojego Panelu Administratora
ADMIN_USER = "admin"
ADMIN_PASS = "TwojeTajneHaslo123"  # Możesz tu wpisać własne hasło

def init_db():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            package TEXT,
            active INTEGER
        )
    """)
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

# Endpoint, który sprawdza aplikacja klienta
@app.get("/api/verify/{key}")
def verify_key(key: str):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT package, active FROM licenses WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row[1] == 1:
        return {"status": "valid", "package": row[0]}
    return {"status": "invalid"}

# Panel Administratora
@app.get("/admin", response_class=HTMLResponse)
def admin_panel(admin: str = Depends(verify_admin)):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT key, package, active FROM licenses")
    rows = cursor.fetchall()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="pl" class="dark">
    <head>
        <meta charset="UTF-8">
        <title>Panel Licencji - Mint Pro</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-[#090d16] text-slate-100 min-h-screen p-8 font-sans">
        <div class="max-w-4xl mx-auto flex flex-col gap-6">
            <header class="flex justify-between items-center border-b border-slate-800 pb-4">
                <h1 class="text-xl font-bold text-white">🔑 Panel Administratora Licencji</h1>
                <span class="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-3 py-1 rounded-full">Online</span>
            </header>

            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
                <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Generuj nowy klucz</h2>
                <form action="/admin/add" method="post" class="flex gap-4">
                    <input type="text" name="key" placeholder="Wpisz lub wygeneruj klucz (np. MINT-PRO-XYZ)" required 
                           class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500">
                    <input type="text" name="package" value="PRO" readonly 
                           class="w-28 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-center text-slate-400">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-emerald-600/20">Dodaj klucz</button>
                </form>
            </div>

            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
                <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Aktywne klucze w bazie</h2>
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-xs text-slate-500 font-semibold">
                            <th class="py-3">Klucz licencyjny</th>
                            <th class="py-3 text-center">Pakiet</th>
                            <th class="py-3 text-center">Status</th>
                            <th class="py-3 text-right">Akcja</th>
                        </tr>
                    </thead>
                    <tbody class="text-xs divide-y divide-slate-800/40">
    """
    for r in rows:
        status_badge = '<span class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded-full font-semibold">Aktywny</span>' if r[2] == 1 else '<span class="bg-rose-500/10 text-rose-400 border border-rose-500/20 px-2.5 py-0.5 rounded-full font-semibold">Zablokowany</span>'
        html += f"""
                        <tr class="hover:bg-slate-800/30">
                            <td class="py-3 font-mono text-emerald-300 font-semibold">{r[0]}</td>
                            <td class="py-3 text-center font-mono">{r[1]}</td>
                            <td class="py-3 text-center">{status_badge}</td>
                            <td class="py-3 text-right">
                                <a href="/admin/delete?key={r[0]}" class="text-rose-400 hover:text-rose-300 font-semibold px-3 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20">Usuń</a>
                            </td>
                        </tr>
        """
    if not rows:
        html += '<tr><td colspan="4" class="py-8 text-center text-slate-600 italic">Brak kluczy w bazie. Wygeneruj pierwszy powyżej!</td></tr>'

    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.post("/admin/add")
def admin_add(key: str = Form(...), package: str = Form(...), admin: str = Depends(verify_admin)):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO licenses (key, package, active) VALUES (?, ?, 1)", (key, package))
        conn.commit()
    except:
        pass
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
