from datetime import datetime, timedelta
import json
import sqlite3
import uuid
from flask import Flask, Response, jsonify, render_template_string, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

DB_NAME = "mint_server.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            package TEXT NOT NULL,
            rank INTEGER NOT NULL
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys_db (
            username TEXT PRIMARY KEY COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            password_plain TEXT DEFAULT '',
            key TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'Aktywny',
            created_at TEXT,
            expires_at TEXT,
            hwid TEXT DEFAULT ''
        )
    """)
  try:
    cursor.execute(
        "ALTER TABLE keys_db ADD COLUMN password_plain TEXT DEFAULT ''"
    )
    conn.commit()
  except sqlite3.OperationalError:
    pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            timestamp TEXT
        )
    """)
  cursor.execute("SELECT COUNT(*) FROM admins")
  if cursor.fetchone()[0] == 0:
    default_admins = [
        (
            "maxikk",
            generate_password_hash("21288371"),
            "Właściciel",
            "WŁAŚCICIEL (OWNER)",
            3,
        ),
        (
            "olafekk7",
            generate_password_hash("Emo14578"),
            "Marketing Team",
            "MARKETING",
            2,
        ),
    ]
    cursor.executemany(
        "INSERT INTO admins VALUES (?, ?, ?, ?, ?)", default_admins
    )

  # Usunięto automatyczne tworzenie "klient_testowy",
  # aby aktualizacje nie ingerowały w Twoją bazę klientów.

  conn.commit()
  conn.close()


init_db()

PANEL_HTML = """
<!DOCTYPE html>
<html lang="pl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Mint Server - Komercyjny Panel Licencji</title>
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
        body { font-family: 'Plus Jakarta Sans', sans-serif; -webkit-tap-highlight-color: transparent; }
        [x-cloak] { display: none !important; }
    </style>
</head>
<body class="bg-[#05070a] text-slate-100 min-h-screen flex flex-col items-center justify-start sm:justify-center p-3 sm:p-6 selection:bg-brand-500 selection:text-white" x-data="app()">

    <!-- EKRAN LOGOWANIA -->
    <div x-show="!isLoggedIn" x-cloak class="w-full max-w-md bg-slate-900/80 border border-slate-800/80 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-2xl flex flex-col gap-6 my-auto">
        <div class="text-center flex flex-col items-center gap-3">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-500/20 to-emerald-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 text-2xl font-bold shadow-xl shadow-brand-500/10">⚡</div>
            <div>
                <h1 class="text-lg font-bold text-white tracking-tight">Mint License System</h1>
                <p class="text-xs text-slate-400 mt-0.5">Zaloguj się do panelu zarządzania</p>
            </div>
        </div>

        <form @submit.prevent="login()" class="flex flex-col gap-4">
            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Login</label>
                <input type="text" x-model="form.username" required placeholder=""
                    class="bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Hasło</label>
                <input type="password" x-model="form.password" required placeholder=""
                    class="bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500 transition-all">
            </div>

            <div x-show="message" x-cloak class="text-xs px-3.5 py-2.5 rounded-xl font-medium text-center bg-rose-500/10 border border-rose-500/20 text-rose-400 animate-pulse" x-text="message"></div>

            <button type="submit" :disabled="loading" class="w-full py-3.5 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 text-white font-bold text-sm rounded-xl shadow-lg shadow-brand-500/20 transition-all cursor-pointer flex items-center justify-center gap-2">
                <span x-show="loading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span x-text="loading ? 'Logowanie...' : 'Zaloguj się'"></span>
            </button>
        </form>

        <div class="border-t border-slate-800/80 pt-4 text-center">
            <p class="text-xs text-slate-400">Nie masz konta ani licencji?</p>
            <p class="text-xs text-brand-400 mt-1 font-medium">Skontaktuj się z nami: <a href="mailto:mbxryt24@zohomail.eu" class="hover:underline">mbxryt24@zohomail.eu</a></p>
        </div>
    </div>

    <!-- PANEL KLIENTA -->
    <div x-show="isLoggedIn && userData.role === 'Klient'" x-cloak class="w-full max-w-2xl flex flex-col gap-6 my-auto">
        <header class="flex items-center justify-between border-b border-slate-800 pb-4 gap-2">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold shrink-0">⚡</div>
                <div>
                    <h1 class="text-sm sm:text-base font-bold text-white flex items-center gap-2 flex-wrap">
                        <span>Panel Klienta</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded-full uppercase">PRO</span>
                    </h1>
                    <p class="text-xs text-slate-400 truncate">Witaj, <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all cursor-pointer">Wyloguj</button>
        </header>

        <div class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-5">
            <div>
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Twój Klucz Licencyjny</h2>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <span class="font-mono text-brand-400 text-sm sm:text-base font-bold tracking-wider break-all" x-text="userData.key"></span>
                    <div class="flex items-center gap-2">
                        <button @click="copyToClipboard(userData.key)" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-all">📋 Kopiuj</button>
                        <span class="text-[10px] px-2.5 py-1 rounded-lg font-semibold"
                              :class="userData.account_status === 'Aktywny' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'"
                              x-text="userData.account_status"></span>
                    </div>
                </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Ważność subskrypcji</span>
                    <span class="text-slate-200 font-mono font-medium" x-text="userData.expires_at || 'Bez limitu'"></span>
                </div>
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Powiązany HWID (Sprzęt)</span>
                    <span class="text-slate-300 font-mono truncate" x-text="userData.hwid || 'Brak (przypisze się z aplikacji)'"></span>
                </div>
            </div>
        </div>
    </div>

    <!-- PANEL ADMINISTRACYJNY -->
    <div x-show="isLoggedIn && userData.role !== 'Klient'" x-cloak class="w-full max-w-5xl flex flex-col gap-5 my-auto">
        <header class="flex items-center justify-between border-b border-slate-800 pb-4 gap-2">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold shrink-0">⚡</div>
                <div>
                    <h1 class="text-sm sm:text-lg font-bold text-white flex items-center gap-2 flex-wrap">
                        <span>Panel Admina</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded-full uppercase" x-text="userData.role"></span>
                    </h1>
                    <p class="text-xs text-slate-400 truncate">Zalogowany: <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all cursor-pointer">Wyloguj</button>
        </header>

        <!-- STATYSTYKI DASHBOARDU -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3.5 flex flex-col gap-1">
                <span class="text-[10px] font-semibold text-slate-500 uppercase">Wszystkie Klucze</span>
                <span class="text-lg font-bold text-white" x-text="Object.keys(keysList).length"></span>
            </div>
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3.5 flex flex-col gap-1">
                <span class="text-[10px] font-semibold text-emerald-500/80 uppercase">Aktywne</span>
                <span class="text-lg font-bold text-emerald-400" x-text="Object.values(keysList).filter(k => k.status === 'Aktywny').length"></span>
            </div>
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3.5 flex flex-col gap-1">
                <span class="text-[10px] font-semibold text-amber-500/80 uppercase">Wstrzymane</span>
                <span class="text-lg font-bold text-amber-400" x-text="Object.values(keysList).filter(k => k.status === 'Wstrzymany').length"></span>
            </div>
            <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-3.5 flex flex-col gap-1">
                <span class="text-[10px] font-semibold text-rose-500/80 uppercase">Wygasłe / Anulowane</span>
                <span class="text-lg font-bold text-rose-400" x-text="Object.values(keysList).filter(k => k.status === 'Wygasł' || k.status === 'Anulowany').length"></span>
            </div>
        </div>

        <!-- Zakładki -->
        <div class="flex gap-1.5 border-b border-slate-800 pb-3 overflow-x-auto no-scrollbar">
            <button @click="activeTab = 'keys'" :class="activeTab === 'keys' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer shrink-0">🔑 Klucze</button>
            <button @click="activeTab = 'create'" :class="activeTab === 'create' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer shrink-0">➕ Nowy Klucz</button>
            <button @click="activeTab = 'history'" :class="activeTab === 'history' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer shrink-0">📜 Historia</button>
            <button @click="activeTab = 'admins'" :class="activeTab === 'admins' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer shrink-0">🛡️ Zespół</button>
        </div>

        <!-- 1. Baza Kluczy -->
        <div x-show="activeTab === 'keys'" class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <div class="flex items-center justify-between flex-wrap gap-3">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Zarządzanie kluczami i subskrypcjami</h2>
                <div class="flex gap-2 flex-wrap w-full sm:w-auto">
                    <button @click="loadData()" class="flex-1 sm:flex-none px-3 py-2 text-xs rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all cursor-pointer">Odśwież</button>
                    <button @click="downloadBackup()" class="flex-1 sm:flex-none px-3 py-2 text-xs rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600/30 transition-all flex items-center justify-center gap-1 cursor-pointer">📥 Pobierz</button>
                    <button @click="triggerUpload()" class="flex-1 sm:flex-none px-3 py-2 text-xs rounded-xl bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 transition-all flex items-center justify-center gap-1 cursor-pointer">📤 Wgraj</button>
                    <input type="file" id="backupFile" @change="uploadBackup($event)" class="hidden" accept=".json">
                </div>
            </div>

            <!-- Karty kluczy -->
            <div class="flex flex-col gap-3">
                <template x-for="(data, username) in keysList" :key="username">
                    <div class="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 flex flex-col gap-3 shadow-md">
                        <div class="flex items-center justify-between gap-2 border-b border-slate-800/60 pb-2.5">
                            <div class="flex items-center gap-2 truncate">
                                <span class="font-bold text-slate-200 text-sm" x-text="username"></span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-semibold shrink-0"
                                  :class="{
                                      'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': data.status === 'Aktywny',
                                      'bg-amber-500/10 text-amber-400 border border-amber-500/20': data.status === 'Wstrzymany',
                                      'bg-rose-500/10 text-rose-400 border border-rose-500/20': data.status === 'Anulowany' || data.status === 'Wygasł'
                                  }" x-text="data.status"></span>
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                            <div class="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/50 flex items-center justify-between gap-2">
                                <div class="flex flex-col gap-0.5 truncate">
                                    <span class="text-[10px] font-semibold text-slate-500 uppercase">Klucz licencyjny</span>
                                    <span class="font-mono text-brand-400 font-bold truncate" x-text="data.key"></span>
                                </div>
                                <button @click="copyToClipboard(data.key)" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[10px] shrink-0 cursor-pointer">📋</button>
                            </div>
                            <div class="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/50 flex flex-col gap-1">
                                <span class="text-[10px] font-semibold text-slate-500 uppercase">Hasło użytkownika</span>
                                <span class="font-mono text-slate-200 font-bold truncate" x-text="data.password"></span>
                            </div>
                            <div class="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/50 flex flex-col gap-1">
                                <span class="text-[10px] font-semibold text-slate-500 uppercase">Ważność (Wygasa)</span>
                                <span class="font-mono text-slate-300 truncate" x-text="data.expires_at || 'Bez limitu'"></span>
                            </div>
                        </div>

                        <div class="flex items-center justify-between text-xs bg-slate-900/30 px-2.5 py-1.5 rounded-lg border border-slate-800/40">
                            <span class="text-slate-500 text-[10px] uppercase font-semibold">HWID (Sprzęt):</span>
                            <span class="font-mono text-slate-300 truncate max-w-[220px]" x-text="data.hwid || 'Brak przypisania'"></span>
                        </div>

                        <div class="flex flex-col gap-1" x-show="data.notes">
                            <span class="text-[10px] font-semibold text-slate-500 uppercase">Notatki</span>
                            <span class="text-xs text-slate-300" x-text="data.notes"></span>
                        </div>

                        <!-- Przyciski akcji -->
                        <div class="flex items-center justify-end gap-1.5 pt-2 border-t border-slate-800/60 flex-wrap">
                            <button @click="resetHwid(username)" class="px-2.5 py-1.5 bg-yellow-600/20 hover:bg-yellow-600/30 text-yellow-400 rounded-lg text-[11px] font-medium cursor-pointer">Reset HWID</button>
                            <button @click="openEdit(username, data)" class="px-2.5 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 rounded-lg text-[11px] font-medium cursor-pointer">Edytuj</button>
                            <button x-show="data.status !== 'Aktywny'" @click="changeStatus(username, 'Aktywny')" class="px-2.5 py-1.5 bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 rounded-lg text-[11px] font-medium cursor-pointer">Aktywuj</button>
                            <button x-show="data.status !== 'Wstrzymany'" @click="changeStatus(username, 'Wstrzymany')" class="px-2.5 py-1.5 bg-amber-500/15 hover:bg-amber-500/25 text-amber-400 rounded-lg text-[11px] font-medium cursor-pointer">Wstrzymaj</button>
                            <button x-show="data.status !== 'Anulowany'" @click="changeStatus(username, 'Anulowany')" class="px-2.5 py-1.5 bg-rose-500/15 hover:bg-rose-500/25 text-rose-400 rounded-lg text-[11px] font-medium cursor-pointer">Anuluj</button>
                            <template x-if="form.username.toLowerCase() === 'maxikk'">
                                <button @click="deleteKey(username)" class="px-2.5 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-[11px] font-bold cursor-pointer">Usuń</button>
                            </template>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <!-- MODAL EDYCJI KLUCZA -->
        <div x-show="showEditModal" x-cloak class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
            <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 sm:p-6 w-full max-w-md shadow-2xl flex flex-col gap-4 my-auto">
                <h3 class="text-sm font-bold text-white uppercase tracking-wider">Edycja Klucza / Klienta</h3>
                <form @submit.prevent="updateKey()" class="flex flex-col gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Nazwa użytkownika</label>
                        <input type="text" x-model="editForm.username" required class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Nowe hasło (zostaw puste by nie zmieniać)</label>
                        <input type="text" x-model="editForm.password" placeholder="" class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Klucz licencyjny</label>
                        <input type="text" x-model="editForm.key" required class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs font-mono text-brand-400 uppercase focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Data wygaśnięcia (YYYY-MM-DD HH:MM:SS lub puste)</label>
                        <input type="text" x-model="editForm.expires_at" class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs font-mono text-slate-300 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Notatki</label>
                        <input type="text" x-model="editForm.notes" class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex gap-2 mt-3">
                        <button type="submit" class="flex-1 py-3 bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all cursor-pointer">Zapisz</button>
                        <button type="button" @click="showEditModal = false" class="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-xl transition-all cursor-pointer">Anuluj</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- 2. Utwórz Klucz -->
        <div x-show="activeTab === 'create'" x-cloak class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4 max-w-lg mx-auto w-full">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Generator Kluczy i Subskrypcji</h2>
            <form @submit.prevent="createKey()" class="flex flex-col gap-4">
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Nazwa użytkownika klienta</label>
                    <input type="text" x-model="newKeyForm.username" required placeholder=""
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Hasło użytkownika</label>
                    <input type="text" x-model="newKeyForm.password" required placeholder=""
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Klucz licencyjny (zostaw puste by wylosować)</label>
                    <div class="flex gap-2">
                        <input type="text" x-model="newKeyForm.key" placeholder="XXXX-XXXX-XXXX-XXXX"
                            class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm font-mono text-brand-400 focus:outline-none focus:border-brand-500 uppercase">
                        <button type="button" @click="generateKeyString()" class="px-3 bg-slate-800 hover:bg-slate-700 text-xs rounded-xl border border-slate-700 shrink-0 cursor-pointer">🎲 Losuj</button>
                    </div>
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Liczba dni ważności (0 = bez limitu)</label>
                    <input type="number" x-model="newKeyForm.days" required min="0" value="30"
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Notatki (opcjonalnie)</label>
                    <input type="text" x-model="newKeyForm.notes" placeholder=""
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div x-show="createMessage" x-cloak class="text-xs px-3 py-2.5 rounded-xl text-center" :class="createSuccess ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'" x-text="createMessage"></div>
                <button type="submit" class="py-3.5 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all cursor-pointer">Utwórz Klucz</button>
            </form>
        </div>

        <!-- 3. Historia Logowań -->
        <div x-show="activeTab === 'history'" x-cloak class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Historia logowań</h2>
            <div class="flex flex-col gap-2">
                <template x-for="item in historyList" :key="item.id">
                    <div class="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3 flex items-center justify-between gap-2 text-xs">
                        <div class="flex flex-col gap-0.5 truncate">
                            <span class="font-semibold text-slate-200" x-text="item.username"></span>
                            <span class="text-brand-400 text-[10px]" x-text="item.role"></span>
                        </div>
                        <span class="font-mono text-slate-400 text-[10px] shrink-0" x-text="item.timestamp"></span>
                    </div>
                </template>
            </div>
        </div>

        <!-- 4. Zespół i Admini -->
        <div x-show="activeTab === 'admins'" x-cloak class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lista zespołu administracyjnego</h2>
            <div class="flex flex-col gap-2">
                <template x-for="user in adminsList" :key="user.username">
                    <div class="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between gap-2 text-xs">
                        <div class="flex flex-col gap-0.5 truncate">
                            <span class="font-semibold text-slate-200" x-text="user.username"></span>
                            <span class="text-brand-400 text-[10px]" x-text="user.role"></span>
                        </div>
                        <span class="font-mono text-slate-400 bg-slate-900 px-2 py-1 rounded border border-slate-800 text-[11px] shrink-0" x-text="user.credential"></span>
                    </div>
                </template>
            </div>
        </div>
    </div>

    <!-- POWIADOMIENIE O SKOPIOWANIU -->
    <div x-show="toastMessage" x-cloak x-transition class="fixed bottom-6 right-6 bg-brand-500 text-white text-xs font-bold px-4 py-3 rounded-xl shadow-2xl z-50 flex items-center gap-2">
        <span>⚡</span> <span x-text="toastMessage"></span>
    </div>

    <script>
        function app() {
            return {
                isLoggedIn: false,
                loading: false,
                activeTab: 'keys',
                form: { username: '', password: '' },
                userData: {},
                message: '',
                toastMessage: '',
                keysList: {},
                historyList: [],
                adminsList: [],
                newKeyForm: { username: '', password: '', key: '', days: 30, notes: '' },
                showEditModal: false,
                editForm: { old_username: '', username: '', password: '', key: '', expires_at: '', notes: '' },
                createMessage: '',
                createSuccess: false,

                async login() {
                    this.message = '';
                    this.loading = true;

                    try {
                        let res = await fetch('/api/verify', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({...this.form, hwid: ""})
                        });
                        let data = await res.json();
                        if (data.status === 'valid') {
                            this.isLoggedIn = true;
                            this.userData = data;
                            if (data.role !== 'Klient') {
                                this.loadData();
                            }
                        } else {
                            this.message = data.error || 'Błąd logowania.';
                        }
                    } catch(e) {
                        this.message = 'Błąd połączenia z serwerem.';
                    } finally {
                        this.loading = false;
                    }
                },

                async loadData() {
                    try {
                        let res = await fetch('/api/admin/data', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({username: this.form.username})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.keysList = data.keys;
                            this.historyList = data.history;
                            this.adminsList = data.admins;
                        }
                    } catch(e) {}
                },

                generateKeyString() {
                    const r = () => Math.random().toString(36).substring(2, 6).toUpperCase();
                    this.newKeyForm.key = `${r()}-${r()}-${r()}-${r()}`;
                },

                async createKey() {
                    this.createMessage = '';
                    try {
                        let res = await fetch('/api/keys/create', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({admin_username: this.form.username, ...this.newKeyForm})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.createSuccess = true;
                            this.createMessage = 'Klucz utworzony pomyślnie!';
                            this.newKeyForm = { username: '', password: '', key: '', days: 30, notes: '' };
                            this.loadData();
                        } else {
                            this.createSuccess = false;
                            this.createMessage = data.error || 'Błąd tworzenia klucza.';
                        }
                    } catch(e) {
                        this.createSuccess = false;
                        this.createMessage = 'Błąd połączenia.';
                    }
                },

                openEdit(username, data) {
                    this.editForm = {
                        old_username: username,
                        username: username,
                        password: '',
                        key: data.key,
                        expires_at: data.expires_at || '',
                        notes: data.notes || ''
                    };
                    this.showEditModal = true;
                },

                async updateKey() {
                    try {
                        let res = await fetch('/api/keys/edit', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({admin_username: this.form.username, ...this.editForm})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.showEditModal = false;
                            this.loadData();
                        } else {
                            alert(data.error || 'Błąd edycji.');
                        }
                    } catch(e) {
                        alert('Błąd połączenia.');
                    }
                },

                async changeStatus(targetUser, newStatus) {
                    try {
                        let res = await fetch('/api/keys/status', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({admin_username: this.form.username, username: targetUser, status: newStatus})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.loadData();
                        }
                    } catch(e) {}
                },

                async resetHwid(targetUser) {
                    if(!confirm(`Zresetować powiązanie HWID dla klienta ${targetUser}?`)) return;
                    try {
                        let res = await fetch('/api/keys/reset_hwid', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({admin_username: this.form.username, username: targetUser})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.showToast('HWID został zresetowany pomyślnie!');
                            this.loadData();
                        } else {
                            alert(data.error || 'Błąd resetowania.');
                        }
                    } catch(e) {}
                },

                async deleteKey(targetUser) {
                    if(!confirm(`Czy na pewno chcesz usunąć użytkownika ${targetUser}?`)) return;
                    try {
                        let res = await fetch('/api/keys/delete', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({admin_username: this.form.username, username: targetUser})
                        });
                        let data = await res.json();
                        if (data.status === 'success') {
                            this.loadData();
                        } else {
                            alert(data.error || 'Nie udało się usunąć.');
                        }
                    } catch(e) {}
                },

                async downloadBackup() {
                    const pwd = prompt("Podaj hasło Właściciela do pobrania backupu:");
                    if (!pwd) return;
                    try {
                        let res = await fetch('/api/backup/download', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({admin_username: this.form.username, password: pwd})
                        });
                        if (res.ok) {
                            let blob = await res.blob();
                            let url = window.URL.createObjectURL(blob);
                            let a = document.createElement('a');
                            a.href = url;
                            a.download = 'mint_server_backup.json';
                            a.click();
                        } else {
                            let err = await res.json();
                            alert(err.error || 'Błąd autoryzacji.');
                        }
                    } catch(e) {
                        alert('Błąd pobierania.');
                    }
                },

                triggerUpload() {
                    document.getElementById('backupFile').click();
                },

                async uploadBackup(event) {
                    const file = event.target.files[0];
                    if(!file) return;
                    const pwd = prompt("Podaj hasło Właściciela do wgrania backupu:");
                    if (!pwd) { event.target.value = ''; return; }
                    const text = await file.text();
                    try {
                        let res = await fetch('/api/backup/upload', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({admin_username: this.form.username, password: pwd, backup_data: text})
                        });
                        let data = await res.json();
                        if(data.status === 'success') {
                            alert('Backup wgrany pomyślnie!');
                            this.loadData();
                        } else {
                            alert(data.error || 'Błąd wgrywania.');
                        }
                    } catch(e) {
                        alert('Błąd przesyłania.');
                    }
                    event.target.value = '';
                },

                copyToClipboard(text) {
                    navigator.clipboard.writeText(text);
                    this.showToast('Skopiowano do schowka!');
                },

                showToast(text) {
                    this.toastMessage = text;
                    setTimeout(() => { this.toastMessage = ''; }, 3000);
                },

                logout() {
                    this.isLoggedIn = false;
                    this.form = { username: '', password: '' };
                    this.userData = {};
                }
            }
        }
    </script>
</body>
</html>
"""


@app.route("/")
@app.route("/admin")
def serve_panel():
  return render_template_string(PANEL_HTML)


@app.route("/api/verify", methods=["POST"])
def verify_license():
  data = request.get_json() or {}
  login_input = data.get("username", "").strip()
  password = data.get("password", "").strip()
  input_key = data.get("key", "").strip().upper()
  hwid = data.get("hwid", "").strip()

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute(
      "SELECT username, password_hash, role, package, rank FROM admins WHERE"
      " username COLLATE NOCASE = ?",
      (login_input,),
  )
  admin = cursor.fetchone()
  if admin and check_password_hash(admin[1], password):
    cursor.execute(
        "INSERT INTO history (username, role, timestamp) VALUES (?, ?, ?)",
        (admin[0], admin[2], datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()
    session["user"] = admin[0]
    return jsonify({"status": "valid", "package": admin[3], "role": admin[2]})

  cursor.execute(
      "SELECT username, password_hash, key, notes, status, created_at,"
      " expires_at, hwid FROM keys_db WHERE username COLLATE NOCASE = ?",
      (login_input,),
  )
  client = cursor.fetchone()

  if client:
    (
        c_username,
        c_pwd_hash,
        c_key,
        c_notes,
        c_status,
        c_created,
        c_expires,
        c_hwid,
    ) = client

    if not check_password_hash(c_pwd_hash, password):
      conn.close()
      return jsonify({"status": "invalid", "error": "Nieprawidłowe hasło."}), 200

    if input_key and input_key != c_key.upper():
      conn.close()
      return (
          jsonify(
              {"status": "invalid", "error": "Nieprawidłowy klucz licencyjny."}
          ),
          200,
      )

    if c_expires:
      exp_dt = datetime.strptime(c_expires, "%Y-%m-%d %H:%M:%S")
      if datetime.now() > exp_dt:
        cursor.execute(
            "UPDATE keys_db SET status = 'Wygasł' WHERE username = ?",
            (c_username,),
        )
        conn.commit()
        conn.close()
        return (
            jsonify(
                {"status": "invalid", "error": "Twoja subskrypcja wygasła."}
            ),
            200,
        )

    if c_status != "Aktywny":
      conn.close()
      return (
          jsonify(
              {"status": "invalid", "error": f"Konto jest w stanie: {c_status}"}
          ),
          200,
      )

    if not c_hwid and hwid:
      cursor.execute(
          "UPDATE keys_db SET hwid = ? WHERE username = ?", (hwid, c_username)
      )
      conn.commit()
      c_hwid = hwid
    elif c_hwid and hwid and c_hwid != hwid:
      conn.close()
      return (
          jsonify({
              "status": "invalid",
              "error": (
                  "Konto jest przypisane do innego urządzenia (HWID mismatch)."
              ),
          }),
          200,
      )

    cursor.execute(
        "INSERT INTO history (username, role, timestamp) VALUES (?, ?, ?)",
        (c_username, "Klient", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    session["user"] = c_username
    return jsonify({
        "status": "valid",
        "package": "PRO",
        "role": "Klient",
        "key": c_key,
        "account_status": c_status,
        "notes": c_notes,
        "expires_at": c_expires,
        "hwid": c_hwid,
    })

  conn.close()
  return (
      jsonify({"status": "invalid", "error": "Nieprawidłowy login lub hasło."}),
      200,
  )


@app.route("/api/keys/create", methods=["POST"])
def create_key():
  data = request.get_json() or {}
  username = data.get("username", "").strip()
  password = data.get("password", "").strip()
  key = data.get("key", "").strip().upper()
  days = int(data.get("days", 30))
  notes = data.get("notes", "").strip()

  if not username or not password:
    return (
        jsonify({"status": "error", "error": "Login i hasło są wymagane."}),
        400,
    )

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute(
      "SELECT username FROM admins WHERE username COLLATE NOCASE = ?",
      (username,),
  )
  if cursor.fetchone():
    conn.close()
    return (
        jsonify({"status": "error", "error": "Nazwa zajęta przez admina."}),
        400,
    )

  cursor.execute(
      "SELECT username FROM keys_db WHERE username COLLATE NOCASE = ?",
      (username,),
  )
  if cursor.fetchone():
    conn.close()
    return (
        jsonify({"status": "error", "error": "Taki klient już istnieje."}),
        400,
    )

  if not key:
    r = lambda: uuid.uuid4().hex[:4].upper()
    key = f"{r()}-{r()}-{r()}-{r()}"

  created_at = datetime.now()
  expires_at = (
      (created_at + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
      if days > 0
      else ""
  )
  pwd_hash = generate_password_hash(password)

  cursor.execute(
      "INSERT INTO keys_db VALUES (?, ?, ?, ?, ?, 'Aktywny', ?, ?, '')",
      (
          username,
          pwd_hash,
          password,
          key,
          notes,
          created_at.strftime("%Y-%m-%d %H:%M:%S"),
          expires_at,
      ),
  )
  conn.commit()
  conn.close()

  return jsonify({"status": "success", "key": key})


@app.route("/api/keys/edit", methods=["POST"])
def edit_key():
  data = request.get_json() or {}
  old_username = data.get("old_username", "").strip()
  new_username = data.get("username", "").strip()
  password = data.get("password", "").strip()
  key = data.get("key", "").strip().upper()
  expires_at = data.get("expires_at", "").strip()
  notes = data.get("notes", "").strip()

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute(
      "SELECT password_hash, password_plain FROM keys_db WHERE username = ?",
      (old_username,),
  )
  row = cursor.fetchone()
  if not row:
    conn.close()
    return (
        jsonify({"status": "error", "error": "Nie znaleziono użytkownika."}),
        404,
    )

  pwd_hash = generate_password_hash(password) if password else row[0]
  pwd_plain = password if password else row[1]

  if old_username.lower() != new_username.lower():
    cursor.execute(
        "SELECT username FROM keys_db WHERE username COLLATE NOCASE = ?",
        (new_username,),
    )
    if cursor.fetchone():
      conn.close()
      return (
          jsonify({
              "status": "error",
              "error": "Nazwa użytkownika już istnieje.",
          }),
          400,
      )
    cursor.execute("DELETE FROM keys_db WHERE username = ?", (old_username,))
    cursor.execute(
        "INSERT INTO keys_db (username, password_hash, password_plain, key,"
        " notes, status, created_at, expires_at, hwid) SELECT ?, ?, ?, key,"
        " notes, status, created_at, expires_at, hwid FROM keys_db WHERE"
        " username = ?",
        (new_username, pwd_hash, pwd_plain, old_username),
    )

  cursor.execute(
      "UPDATE keys_db SET username = ?, password_hash = ?, password_plain = ?,"
      " key = ?, expires_at = ?, notes = ? WHERE username = ?",
      (
          new_username,
          pwd_hash,
          pwd_plain,
          key,
          expires_at if expires_at else None,
          notes,
          (
              old_username
              if old_username.lower() == new_username.lower()
              else new_username
          ),
      ),
  )
  conn.commit()
  conn.close()
  return jsonify({"status": "success"})


@app.route("/api/keys/status", methods=["POST"])
def change_key_status():
  data = request.get_json() or {}
  username = data.get("username")
  new_status = data.get("status")

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE keys_db SET status = ? WHERE username = ?", (new_status, username)
  )
  conn.commit()
  conn.close()
  return jsonify({"status": "success"})


@app.route("/api/keys/reset_hwid", methods=["POST"])
def reset_hwid():
  data = request.get_json() or {}
  username = data.get("username")

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("UPDATE keys_db SET hwid = '' WHERE username = ?", (username,))
  conn.commit()
  conn.close()
  return jsonify({"status": "success"})


@app.route("/api/keys/delete", methods=["POST"])
def delete_key():
  data = request.get_json() or {}
  admin_username = data.get("admin_username")
  username_to_delete = data.get("username")

  if admin_username.lower() != "maxikk":
    return (
        jsonify(
            {"status": "error", "error": "Brak uprawnień właścicielskich."}
        ),
        403,
    )

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "DELETE FROM keys_db WHERE username = ?", (username_to_delete,)
  )
  conn.commit()
  conn.close()
  return jsonify({"status": "success"})


@app.route("/api/backup/download", methods=["POST"])
def download_backup():
  data = request.get_json() or {}
  password = data.get("password")

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT password_hash FROM admins WHERE username = 'maxikk'")
  row = cursor.fetchone()
  conn.close()

  if not row or not check_password_hash(row[0], password):
    return jsonify({"error": "Nieprawidłowe hasło Właściciela."}), 403

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      "SELECT username, password_hash, password_plain, key, notes, status,"
      " created_at, expires_at, hwid FROM keys_db"
  )
  rows = cursor.fetchall()
  conn.close()

  backup_dict = {}
  for r in rows:
    backup_dict[r[0]] = {
        "password_hash": r[1],
        "password_plain": r[2],
        "key": r[3],
        "notes": r[4],
        "status": r[5],
        "created_at": r[6],
        "expires_at": r[7],
        "hwid": r[8],
    }

  return Response(
      json.dumps(backup_dict, indent=2, ensure_ascii=False),
      mimetype="application/json",
      headers={
          "Content-Disposition": (
              "attachment;filename=mint_server_backup.json"
          )
      },
  )


@app.route("/api/backup/upload", methods=["POST"])
def upload_backup():
  data = request.get_json() or {}
  password = data.get("password")

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute("SELECT password_hash FROM admins WHERE username = 'maxikk'")
  row = cursor.fetchone()

  if not row or not check_password_hash(row[0], password):
    conn.close()
    return jsonify({"status": "error", "error": "Nieprawidłowe hasło Właściciela."}), 403

  try:
    raw_data = data.get("backup_data")
    parsed = json.loads(raw_data)
    if isinstance(parsed, dict):
      cursor.execute("DELETE FROM keys_db")
      for uname, udata in parsed.items():
        p_hash = udata.get("password_hash")
        p_plain = udata.get("password_plain", "")
        cursor.execute(
            "INSERT INTO keys_db VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                uname,
                p_hash,
                p_plain,
                udata.get("key"),
                udata.get("notes"),
                udata.get("status", "Aktywny"),
                udata.get("created_at"),
                udata.get("expires_at"),
                udata.get("hwid", ""),
            ),
        )
      conn.commit()
      conn.close()
      return jsonify({"status": "success"})
  except Exception as e:
    conn.close()
    return jsonify({"status": "error", "error": f"Błąd: {str(e)}"}), 400

  conn.close()
  return jsonify({"status": "error", "error": "Nieprawidłowy format."}), 400


@app.route("/api/admin/data", methods=["POST"])
def get_admin_data():
  data = request.get_json() or {}
  current_username = data.get("username", "").strip()

  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()

  cursor.execute(
      "SELECT rank FROM admins WHERE username COLLATE NOCASE = ?",
      (current_username,),
  )
  res = cursor.fetchone()
  current_rank = res[0] if res else 0

  cursor.execute(
      "SELECT username, role, package, rank, password_hash FROM admins"
  )
  admins_rows = cursor.fetchall()

  admins_filtered = []
  for a in admins_rows:
    uname, urole, upackage, urank, upwd_hash = a
    credential = "Zabezpieczone (Hash)" if current_rank >= urank else "********"
    admins_filtered.append(
        {"username": uname, "role": urole, "credential": credential}
    )

  cursor.execute(
      "SELECT username, key, password_plain, notes, status, created_at,"
      " expires_at, hwid FROM keys_db"
  )
  keys_rows = cursor.fetchall()
  keys_dict = {}
  for k in keys_rows:
    keys_dict[k[0]] = {
        "key": k[1],
        "password": k[2],
        "notes": k[3],
        "status": k[4],
        "created_at": k[5],
        "expires_at": k[6],
        "hwid": k[7],
    }

  cursor.execute(
      "SELECT id, username, role, timestamp FROM history ORDER BY id DESC"
      " LIMIT 50"
  )
  hist_rows = cursor.fetchall()
  history_list = [
      {"id": h[0], "username": h[1], "role": h[2], "timestamp": h[3]}
      for h in hist_rows
  ]

  conn.close()

  return jsonify({
      "status": "success",
      "keys": keys_dict,
      "history": history_list,
      "admins": admins_filtered,
  })


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
