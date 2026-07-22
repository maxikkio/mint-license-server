import uuid
import json
from flask import Flask, request, jsonify, render_template_string, Response
from datetime import datetime

app = Flask(__name__)

ELEVATED_USERS = {
    "maxikk": {
        "password": "21288371",
        "role": "Właściciel",
        "package": "WŁAŚCICIEL (OWNER)",
        "rank": 3
    },
    "olafekk7": {
        "password": "Emo14578",
        "role": "Marketing Team",
        "package": "MARKETING",
        "rank": 2
    }
}

KEYS_DB = {
    "klient_testowy": {
        "password": "haslo123",
        "key": "ABCD-1234-EFGH-5678",
        "notes": "Pierwszy klient testowy",
        "status": "Aktywny",
        "created_at": "2026-07-22 12:00:00"
    }
}

LOGIN_HISTORY = []

PANEL_HTML = """
<!DOCTYPE html>
<html lang="pl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Mint Server - Panel Zarządzania i Klienta</title>
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
    </style>
</head>
<body class="bg-[#07090e] text-slate-100 min-h-screen flex flex-col items-center justify-start sm:justify-center p-3 sm:p-6 selection:bg-brand-500 selection:text-white" x-data="app()">

    <!-- EKRAN LOGOWANIA -->
    <div x-show="!isLoggedIn" class="w-full max-w-md bg-slate-900/90 border border-slate-800/80 rounded-3xl p-5 sm:p-8 shadow-2xl backdrop-blur-xl flex flex-col gap-6 my-auto">
        <div class="text-center flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 text-xl font-bold shadow-lg shadow-brand-500/10">⚡</div>
            <h1 class="text-base sm:text-lg font-bold text-white tracking-tight">Logowanie do Systemu</h1>
            <p class="text-xs text-slate-400">Wpisz swój login i hasło</p>
        </div>

        <form @submit.prevent="login()" class="flex flex-col gap-4">
            <div class="flex flex-col gap-1.5">
                <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Login</label>
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

        <div class="border-t border-slate-800/80 pt-4 text-center">
            <p class="text-xs text-slate-400">Nie masz konta lub klucza?</p>
            <p class="text-xs text-brand-400 mt-1 font-medium">Napisz: <a href="mailto:mbxryt24@zohomail.eu" class="underline">mbxryt24@zohomail.eu</a></p>
        </div>
    </div>

    <!-- PANEL KLIENTA -->
    <div x-show="isLoggedIn && userData.role === 'Klient'" class="w-full max-w-2xl flex flex-col gap-6 my-auto" style="display: none;" :style="(isLoggedIn && userData.role === 'Klient') ? 'display: flex;' : 'display: none;'">
        <header class="flex items-center justify-between border-b border-slate-800 pb-4 gap-2">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold shrink-0">⚡</div>
                <div>
                    <h1 class="text-sm sm:text-lg font-bold text-white flex items-center gap-2 flex-wrap">
                        <span>Panel Klienta</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded-full uppercase">PRO</span>
                    </h1>
                    <p class="text-xs text-slate-400 truncate max-w-[180px] sm:max-w-none">Witaj, <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all shrink-0">Wyloguj</button>
        </header>

        <div class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-5">
            <div>
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Twój Klucz Licencyjny Pro</h2>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-3.5 sm:p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                    <span class="font-mono text-brand-400 text-sm sm:text-base font-bold tracking-wider break-all" x-text="userData.key"></span>
                    <span class="text-[10px] px-2.5 py-1 rounded-lg font-semibold shrink-0"
                          :class="userData.status === 'Aktywny' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'"
                          x-text="userData.status"></span>
                </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Status konta</span>
                    <span class="text-slate-200 font-medium">Subskrypcja Pro</span>
                </div>
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Notatki</span>
                    <span class="text-slate-300 font-mono break-all" x-text="userData.notes || 'Brak uwag'"></span>
                </div>
            </div>
        </div>
    </div>

    <!-- PANEL ADMINISTRACYJNY -->
    <div x-show="isLoggedIn && userData.role !== 'Klient'" class="w-full max-w-5xl flex flex-col gap-5 my-auto" style="display: none;" :style="(isLoggedIn && userData.role !== 'Klient') ? 'display: flex;' : 'display: none;'">
        <header class="flex items-center justify-between border-b border-slate-800 pb-4 gap-2">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold shrink-0">⚡</div>
                <div>
                    <h1 class="text-sm sm:text-lg font-bold text-white flex items-center gap-2 flex-wrap">
                        <span>Panel Admina</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded-full uppercase" x-text="userData.role"></span>
                    </h1>
                    <p class="text-xs text-slate-400 truncate max-w-[160px] sm:max-w-none">Admin: <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-3 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all shrink-0">Wyloguj</button>
        </header>

        <!-- Zakładki mobilne -->
        <div class="flex gap-1.5 border-b border-slate-800 pb-3 overflow-x-auto no-scrollbar">
            <button @click="activeTab = 'keys'" :class="activeTab === 'keys' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all shrink-0">🔑 Klucze</button>
            <button @click="activeTab = 'create'" :class="activeTab === 'create' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all shrink-0">➕ Nowy</button>
            <button @click="activeTab = 'history'" :class="activeTab === 'history' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all shrink-0">📜 Historia</button>
            <button @click="activeTab = 'admins'" :class="activeTab === 'admins' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-3.5 py-2 rounded-xl text-xs transition-all shrink-0">🛡️ Zespół</button>
        </div>
        <!-- 1. Baza Kluczy (Wersja Mobilna - Karty / Desktop - Tabela) -->
        <div x-show="activeTab === 'keys'" class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <div class="flex items-center justify-between flex-wrap gap-3">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Zarządzanie kluczami</h2>
                <div class="flex gap-2 flex-wrap w-full sm:w-auto">
                    <button @click="loadData()" class="flex-1 sm:flex-none px-3 py-2 text-xs rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">Odśwież</button>
                    <button @click="downloadBackup()" class="flex-1 sm:flex-none px-3 py-2 text-xs rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600/30 transition-all flex items-center justify-center gap-1">📥 Pobierz</button>
                    <button @click="triggerUpload()" class="flex-1 sm:flex-none px-3 py-2 text-xs rounded-xl bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 transition-all flex items-center justify-center gap-1">📤 Wgraj</button>
                    <input type="file" id="backupFile" @change="uploadBackup($event)" class="hidden" accept=".json">
                </div>
            </div>

            <!-- Widok mobilny w formie kart (Flex / Grid) -->
            <div class="flex flex-col gap-3">
                <template x-for="(data, username) in keysList" :key="username">
                    <div class="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 flex flex-col gap-3 shadow-md">
                        <div class="flex items-center justify-between gap-2 border-b border-slate-800/60 pb-2.5">
                            <div class="flex items-center gap-2 truncate">
                                <span class="font-bold text-slate-200 text-sm" x-text="username"></span>
                                <span class="font-mono text-xs text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800" x-text="data.password"></span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-semibold shrink-0"
                                  :class="{
                                      'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': data.status === 'Aktywny',
                                      'bg-amber-500/10 text-amber-400 border border-amber-500/20': data.status === 'Wstrzymany',
                                      'bg-rose-500/10 text-rose-400 border border-rose-500/20': data.status === 'Anulowany'
                                  }" x-text="data.status"></span>
                        </div>

                        <div class="flex flex-col gap-1">
                            <span class="text-[10px] font-semibold text-slate-500 uppercase">Klucz licencyjny</span>
                            <span class="font-mono text-xs text-brand-400 font-bold break-all bg-slate-900/80 p-2 rounded-lg border border-slate-800/50" x-text="data.key"></span>
                        </div>

                        <div class="flex flex-col gap-1" x-show="data.notes">
                            <span class="text-[10px] font-semibold text-slate-500 uppercase">Notatki</span>
                            <span class="text-xs text-slate-300" x-text="data.notes"></span>
                        </div>

                        <!-- Przyciski akcji dostosowane do telefonu -->
                        <div class="flex items-center justify-end gap-1.5 pt-2 border-t border-slate-800/60 flex-wrap">
                            <button @click="openEdit(username, data)" class="px-2.5 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 rounded-lg text-[11px] font-medium">Edytuj</button>
                            <button x-show="data.status !== 'Aktywny'" @click="changeStatus(username, 'Aktywny')" class="px-2.5 py-1.5 bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 rounded-lg text-[11px] font-medium">Aktywuj</button>
                            <button x-show="data.status !== 'Wstrzymany'" @click="changeStatus(username, 'Wstrzymany')" class="px-2.5 py-1.5 bg-amber-500/15 hover:bg-amber-500/25 text-amber-400 rounded-lg text-[11px] font-medium">Wstrzymaj</button>
                            <button x-show="data.status !== 'Anulowany'" @click="changeStatus(username, 'Anulowany')" class="px-2.5 py-1.5 bg-rose-500/15 hover:bg-rose-500/25 text-rose-400 rounded-lg text-[11px] font-medium">Anuluj</button>
                            <template x-if="form.username === 'maxikk'">
                                <button @click="deleteKey(username)" class="px-2.5 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-[11px] font-bold">Usuń</button>
                            </template>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <!-- MODAL EDYCJI KLUCZA -->
        <div x-show="showEditModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto" style="display: none;">
            <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 sm:p-6 w-full max-w-md shadow-2xl flex flex-col gap-4 my-auto">
                <h3 class="text-sm font-bold text-white uppercase tracking-wider">Edycja Klucza / Klienta</h3>
                <form @submit.prevent="updateKey()" class="flex flex-col gap-3">
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Nazwa użytkownika</label>
                        <input type="text" x-model="editForm.username" required class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Hasło</label>
                        <input type="text" x-model="editForm.password" required class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Klucz licencyjny</label>
                        <input type="text" x-model="editForm.key" required class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs font-mono text-brand-400 uppercase focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex flex-col gap-1">
                        <label class="text-[10px] font-semibold text-slate-400 uppercase">Notatki</label>
                        <input type="text" x-model="editForm.notes" class="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-brand-500">
                    </div>
                    <div class="flex gap-2 mt-3">
                        <button type="submit" class="flex-1 py-3 bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all">Zapisz</button>
                        <button type="button" @click="showEditModal = false" class="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-xl transition-all">Anuluj</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- 2. Utwórz Klucz -->
        <div x-show="activeTab === 'create'" class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4 max-w-lg mx-auto w-full">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Generator i Tworzenie Klienta</h2>
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
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Klucz licencyjny (zostaw puste lub losuj)</label>
                    <div class="flex gap-2">
                        <input type="text" x-model="newKeyForm.key" placeholder="XXXX-XXXX-XXXX-XXXX"
                            class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm font-mono text-brand-400 focus:outline-none focus:border-brand-500 uppercase">
                        <button type="button" @click="generateKeyString()" class="px-3 bg-slate-800 hover:bg-slate-700 text-xs rounded-xl border border-slate-700 shrink-0">🎲 Losuj</button>
                    </div>
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Notatki (opcjonalnie)</label>
                    <input type="text" x-model="newKeyForm.notes" placeholder=""
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div x-show="createMessage" class="text-xs px-3 py-2.5 rounded-xl text-center" :class="createSuccess ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'" x-text="createMessage"></div>
                <button type="submit" class="py-3.5 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all">Utwórz Klucz</button>
            </form>
        </div>

        <!-- 3. Historia Logowań -->
        <div x-show="activeTab === 'history'" class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Historia logowań</h2>
            <div class="flex flex-col gap-2">
                <template x-for="item in historyList" :key="item.timestamp + item.username">
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
        <div x-show="activeTab === 'admins'" class="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lista zespołu</h2>
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
    <script>
        function app() {
            return {
                isLoggedIn: false,
                activeTab: 'keys',
                form: { username: '', password: '' },
                userData: {},
                message: '',
                keysList: {},
                historyList: [],
                adminsList: [],
                newKeyForm: { username: '', password: '', key: '', notes: '' },
                showEditModal: false,
                editForm: { old_username: '', username: '', password: '', key: '', notes: '' },
                createMessage: '',
                createSuccess: false,

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
                                this.loadData();
                            }
                        } else {
                            this.message = data.error || 'Nieprawidłowy login lub hasło.';
                        }
                    } catch(e) {
                        this.message = 'Błąd połączenia z serwerem.';
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
                            this.createMessage = 'Klucz został pomyślnie utworzony!';
                            this.newKeyForm = { username: '', password: '', key: '', notes: '' };
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
                        password: data.password,
                        key: data.key,
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

                async deleteKey(targetUser) {
                    if(!confirm(`Czy na pewno chcesz usunąć klucz użytkownika ${targetUser}?`)) return;
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
                    const pwd = prompt("Podaj hasło Właściciela, aby pobrać backup:");
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
                            a.download = 'mint_keys_backup.json';
                            a.click();
                        } else {
                            let err = await res.json();
                            alert(err.error || 'Błąd autoryzacji.');
                        }
                    } catch(e) {
                        alert('Błąd pobierania backupu.');
                    }
                },

                triggerUpload() {
                    document.getElementById('backupFile').click();
                },

                async uploadBackup(event) {
                    const file = event.target.files[0];
                    if(!file) return;
                    const pwd = prompt("Podaj hasło Właściciela, aby wgrać backup:");
                    if (!pwd) {
                        event.target.value = '';
                        return;
                    }
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
                            alert(data.error || 'Błąd wczytywania backupu.');
                        }
                    } catch(e) {
                        alert('Błąd przesyłania pliku.');
                    }
                    event.target.value = '';
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

    if username in ELEVATED_USERS:
        user = ELEVATED_USERS[username]
        if user["password"] == password:
            LOGIN_HISTORY.insert(0, {
                "username": username,
                "role": user["role"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return jsonify({
                "status": "valid",
                "package": user["package"],
                "role": user["role"]
            })

    if username in KEYS_DB:
        client = KEYS_DB[username]
        if client["password"] == password:
            if client.get("status", "Aktywny") != "Aktywny":
                return jsonify({"status": "invalid", "error": f"Konto jest w stanie: {client['status']}"}), 200

            LOGIN_HISTORY.insert(0, {
                "username": username,
                "role": "Klient",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return jsonify({
                "status": "valid",
                "package": "PRO",
                "role": "Klient",
                "key": client["key"],
                "status": client.get("status", "Aktywny"),
                "notes": client.get("notes", "")
            })

    for c_name, c_data in KEYS_DB.items():
        if c_data["key"] == key:
            if c_data.get("status", "Aktywny") != "Aktywny":
                return jsonify({"status": "invalid", "error": f"Ten klucz jest {c_data['status']}"}), 200
            return jsonify({
                "status": "valid",
                "package": "PRO",
                "role": "Klient"
            })

    return jsonify({
        "status": "invalid",
        "error": "Nieprawidłowy login, hasło lub klucz."
    }), 200


@app.route('/api/keys/create', methods=['POST'])
def create_key():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    key = data.get("key", "").strip().upper()
    notes = data.get("notes", "").strip()

    if not username or not password:
        return jsonify({"status": "error", "error": "Login i hasło są wymagane."}), 400

    if username in ELEVATED_USERS or username in KEYS_DB:
        return jsonify({"status": "error", "error": "Taki użytkownik już istnieje."}), 400

    if not key:
        r = lambda: uuid.uuid4().hex[:4].upper()
        key = f"{r()}-{r()}-{r()}-{r()}"

    KEYS_DB[username] = {
        "password": password,
        "key": key,
        "notes": notes,
        "status": "Aktywny",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return jsonify({"status": "success", "key": key})


@app.route('/api/keys/edit', methods=['POST'])
def edit_key():
    data = request.get_json() or {}
    old_username = data.get("old_username", "").strip()
    new_username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    key = data.get("key", "").strip().upper()
    notes = data.get("notes", "").strip()

    if not old_username or not new_username or not password or not key:
        return jsonify({"status": "error", "error": "Wszystkie pola oprócz notatek są wymagane."}), 400

    if old_username not in KEYS_DB:
        return jsonify({"status": "error", "error": "Nie znaleziono użytkownika."}), 404

    if old_username != new_username:
        if new_username in ELEVATED_USERS or new_username in KEYS_DB:
            return jsonify({"status": "error", "error": "Użytkownik o tej nazwie już istnieje."}), 400
        key_data = KEYS_DB.pop(old_username)
        key_data["password"] = password
        key_data["key"] = key
        key_data["notes"] = notes
        KEYS_DB[new_username] = key_data
    else:
        KEYS_DB[old_username]["password"] = password
        KEYS_DB[old_username]["key"] = key
        KEYS_DB[old_username]["notes"] = notes

    return jsonify({"status": "success"})


@app.route('/api/keys/status', methods=['POST'])
def change_key_status():
    data = request.get_json() or {}
    username = data.get("username")
    new_status = data.get("status")

    if username in KEYS_DB and new_status in ["Aktywny", "Wstrzymany", "Anulowany"]:
        KEYS_DB[username]["status"] = new_status
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "error": "Nie znaleziono klucza lub zły status."}), 400


@app.route('/api/keys/delete', methods=['POST'])
def delete_key():
    data = request.get_json() or {}
    admin_username = data.get("admin_username")
    username_to_delete = data.get("username")

    if admin_username != "maxikk":
        return jsonify({"status": "error", "error": "Brak uprawnień właścicielskich do usuwania."}), 403

    if username_to_delete in KEYS_DB:
        del KEYS_DB[username_to_delete]
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "error": "Nie znaleziono użytkownika."}), 404


@app.route('/api/backup/download', methods=['POST'])
def download_backup():
    data = request.get_json() or {}
    password = data.get("password")

    if password != "21288371":
        return jsonify({"error": "Nieprawidłowe hasło Właściciela."}), 403

    backup_json = json.dumps(KEYS_DB, indent=2, ensure_ascii=False)
    return Response(
        backup_json,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=mint_keys_backup.json"}
    )


@app.route('/api/backup/upload', methods=['POST'])
def upload_backup():
    data = request.get_json() or {}
    password = data.get("password")

    if password != "21288371":
        return jsonify({"status": "error", "error": "Nieprawidłowe hasło Właściciela."}), 403

    try:
        raw_data = data.get("backup_data")
        parsed = json.loads(raw_data)
        if isinstance(parsed, dict):
            KEYS_DB.clear()
            KEYS_DB.update(parsed)
            return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": f"Błąd parsowania JSON: {str(e)}"}), 400

    return jsonify({"status": "error", "error": "Nieprawidłowy format."}), 400


@app.route('/api/admin/data', methods=['POST'])
def get_admin_data():
    data = request.get_json() or {}
    current_username = data.get("username", "").strip()

    current_user = ELEVATED_USERS.get(current_username)
    current_rank = current_user["rank"] if current_user else 0

    admins_filtered = []
    for uname, udata in ELEVATED_USERS.items():
        target_rank = udata["rank"]
        credential = udata["password"] if current_rank >= target_rank else "********"
        admins_filtered.append({
            "username": uname,
            "role": udata["role"],
            "credential": credential
        })

    return jsonify({
        "status": "success",
        "keys": KEYS_DB,
        "history": LOGIN_HISTORY[:50],
        "admins": admins_filtered
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
