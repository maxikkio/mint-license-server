import uuid
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

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

# Baza danych kluczy i kont klientów tworzonych przez adminów
# Format: { username: { "password": "...", "key": "...", "notes": "...", "created_at": "..." } }
KEYS_DB = {
    "klient_testowy": {
        "password": "haslo123",
        "key": "ABCD-1234-EFGH-5678",
        "notes": "Pierwszy klient testowy",
        "created_at": "2026-07-22 12:00:00"
    }
}

# Historia logowań dla panelu admina
LOGIN_HISTORY = []

PANEL_HTML = """
<!DOCTYPE html>
<html lang="pl" class="dark">
<head>
    <meta charset="UTF-8">
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
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-[#090d16] text-slate-100 min-h-screen flex flex-col items-center justify-center p-6 selection:bg-brand-500 selection:text-white" x-data="app()">

    <!-- EKRAN LOGOWANIA -->
    <div x-show="!isLoggedIn" class="max-w-md w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-8 shadow-2xl backdrop-blur-xl flex flex-col gap-6">
        <div class="text-center flex flex-col items-center gap-2">
            <div class="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 text-xl font-bold shadow-lg shadow-brand-500/10">⚡</div>
            <h1 class="text-lg font-bold text-white tracking-tight">Logowanie do Systemu</h1>
            <p class="text-xs text-slate-400">Wpisz swój login i hasło (Admin lub Klient)</p>
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

    <!-- ========================================== -->
    <!-- PANEL KLIENTA (Widoczny tylko dla klientów) -->
    <!-- ========================================== -->
    <div x-show="isLoggedIn && userData.role === 'Klient'" class="max-w-2xl w-full flex flex-col gap-6" style="display: none;" :style="(isLoggedIn && userData.role === 'Klient') ? 'display: flex;' : 'display: none;'">
        
        <header class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold">⚡</div>
                <div>
                    <h1 class="text-lg font-bold text-white flex items-center gap-2">
                        <span>Panel Klienta</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2.5 py-0.5 rounded-full uppercase">PRO</span>
                    </h1>
                    <p class="text-xs text-slate-400">Witaj, <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all">
                Wyloguj się
            </button>
        </header>

        <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-5">
            <div>
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Twój Klucz Licencyjny Pro</h2>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                    <span class="font-mono text-brand-400 text-base font-bold tracking-wider" x-text="userData.key"></span>
                    <span class="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-lg font-semibold">Aktywny</span>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Status konta</span>
                    <span class="text-slate-200 font-medium">Subskrypcja Pro (Bez limitu)</span>
                </div>
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Notatki administratora</span>
                    <span class="text-slate-300 font-mono" x-text="userData.notes || 'Brak dodatkowych uwag'"></span>
                </div>
            </div>

            <p class="text-xs text-slate-400 bg-brand-500/5 border border-brand-500/10 p-3.5 rounded-xl">
                💡 <b>Wskazówka:</b> Skopiuj swój klucz licencyjny i wklej go do aplikacji desktopowej Mint Video Downloader przy pierwszym uruchomieniu, aby odblokować pełny dostęp.
            </p>
        </div>
    </div>


    <!-- ============================================== -->
    <!-- PANEL ADMINISTRACYJNY (Admin, Właściciel, Marketing) -->
    <!-- ============================================== -->
    <div x-show="isLoggedIn && userData.role !== 'Klient'" class="max-w-5xl w-full flex flex-col gap-6" style="display: none;" :style="(isLoggedIn && userData.role !== 'Klient') ? 'display: flex;' : 'display: none;'">
        
        <header class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold">⚡</div>
                <div>
                    <h1 class="text-lg font-bold text-white flex items-center gap-2">
                        <span>Panel Administratora</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2.5 py-0.5 rounded-full uppercase" x-text="userData.role"></span>
                    </h1>
                    <p class="text-xs text-slate-400">Zalogowany jako: <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all">
                Wyloguj się
            </button>
        </header>

        <!-- Zakładki w Panelu Admina -->
        <div class="flex gap-2 border-b border-slate-800 pb-3">
            <button @click="activeTab = 'keys'" :class="activeTab === 'keys' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">🔑 Baza Kluczy</button>
            <button @click="activeTab = 'create'" :class="activeTab === 'create' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">➕ Utwórz Klucz</button>
            <button @click="activeTab = 'history'" :class="activeTab === 'history' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">📜 Historia Logowań</button>
            <button @click="activeTab = 'admins'" :class="activeTab === 'admins' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">🛡️ Zespół i Admini</button>
        </div>

        <!-- 1. ZAKŁADKA: Baza Kluczy -->
        <div x-show="activeTab === 'keys'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <div class="flex items-center justify-between">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Wszystkie aktywne klucze i konta klientów</h2>
                <button @click="loadData()" class="px-3 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">Odśwież</button>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Użytkownik</th>
                            <th class="py-3 px-3">Hasło</th>
                            <th class="py-3 px-3">Klucz licencyjny</th>
                            <th class="py-3 px-3">Notatki</th>
                            <th class="py-3 px-3 text-right">Data utworzenia</th>
                        </tr>
                    </thead>
                    <tbody class="text-xs divide-y divide-slate-800/40">
                        <template x-for="(data, username) in keysList" :key="username">
                            <tr class="hover:bg-slate-800/30 transition-colors">
                                <td class="py-3 px-3 font-semibold text-slate-200" x-text="username"></td>
                                <td class="py-3 px-3 font-mono text-slate-400" x-text="data.password"></td>
                                <td class="py-3 px-3 font-mono text-brand-400 font-bold" x-text="data.key"></td>
                                <td class="py-3 px-3 text-slate-400" x-text="data.notes || '-'"></td>
                                <td class="py-3 px-3 text-right font-mono text-slate-500" x-text="data.created_at"></td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 2. ZAKŁADKA: Utwórz Klucz -->
        <div x-show="activeTab === 'create'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4 max-w-lg">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Generator i Tworzenie Klienta</h2>
            <form @submit.prevent="createKey()" class="flex flex-col gap-4">
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Nazwa użytkownika klienta</label>
                    <input type="text" x-model="newKeyForm.username" required placeholder="np. olaf_klient"
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Hasło użytkownika</label>
                    <input type="text" x-model="newKeyForm.password" required placeholder="haslo123"
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Klucz licencyjny (zostaw puste, aby wygenerować)</label>
                    <div class="flex gap-2">
                        <input type="text" x-model="newKeyForm.key" placeholder="XXXX-XXXX-XXXX-XXXX"
                            class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm font-mono text-brand-400 focus:outline-none focus:border-brand-500 uppercase">
                        <button type="button" @click="generateKeyString()" class="px-3 bg-slate-800 hover:bg-slate-700 text-xs rounded-xl border border-slate-700">🎲 Losuj</button>
                    </div>
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Notatki (opcjonalnie)</label>
                    <input type="text" x-model="newKeyForm.notes" placeholder="np. Klient z Allegro / opłacone na miesiąc"
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div x-show="createMessage" class="text-xs px-3 py-2 rounded-xl text-center" :class="createSuccess ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'" x-text="createMessage"></div>
                <button type="submit" class="py-3 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all">Zapisz i Utwórz Klucz</button>
            </form>
        </div>

        <!-- 3. ZAKŁADKA: Historia Logowań -->
        <div x-show="activeTab === 'history'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Historia logowań do systemu</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Użytkownik / Admin</th>
                            <th class="py-3 px-3">Rola / Typ</th>
                            <th class="py-3 px-3 text-right">Data i Czas</th>
                        </tr>
                    </thead>
                    <tbody class="text-xs divide-y divide-slate-800/40">
                        <template x-for="item in historyList" :key="item.timestamp + item.username">
                            <tr class="hover:bg-slate-800/30 transition-colors">
                                <td class="py-3 px-3 font-semibold text-slate-200" x-text="item.username"></td>
                                <td class="py-3 px-3 text-brand-400 font-medium" x-text="item.role"></td>
                                <td class="py-3 px-3 text-right font-mono text-slate-400" x-text="item.timestamp"></td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 4. ZAKŁADKA: Zespół i Admini -->
        <div x-show="activeTab === 'admins'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lista administratorów i osób zarządzających</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Admin</th>
                            <th class="py-3 px-3">Rola</th>
                            <th class="py-3 px-3 text-right">Hasło</th>
                        </tr>
                    </thead>
                    <tbody class="text-xs divide-y divide-slate-800/40">
                        <template x-for="user in adminsList" :key="user.username">
                            <tr class="hover:bg-slate-800/30 transition-colors">
                                <td class="py-3 px-3 font-semibold text-slate-200" x-text="user.username"></td>
                                <td class="py-3 px-3 text-brand-400 font-medium" x-text="user.role"></td>
                                <td class="py-3 px-3 text-right font-mono text-slate-400" x-text="user.credential"></td>
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
                activeTab: 'keys',
                form: { username: '', password: '' },
                userData: {},
                message: '',
                keysList: {},
                historyList: [],
                adminsList: [],
                newKeyForm: { username: '', password: '', key: '', notes: '' },
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
                                thi