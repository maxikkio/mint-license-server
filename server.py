import uuid
import json
from flask import Flask, request, jsonify, render_template_string, Response
from datetime import datetime

app = Flask(__name__)

# Baza danych ról administracyjnych (Marketing przejęty przez olafekk7, usunięto marketing)
ELEVATED_USERS = {
    "maxikk": {
        "password": "21288371",
        "role": "Właściciel",
        "package": "WŁAŚCICIEL (OWNER)"
    },
    "olafekk7": {
        "password": "Emo14578",
        "role": "Marketing Team",
        "package": "MARKETING"
    }
}

# Baza danych kluczy i kont klientów
KEYS_DB = {
    "klient_testowy": {
        "password": "haslo123",
        "key": "ABCD-1234-EFGH-5678",
        "notes": "Pierwszy klient testowy",
        "status": "Aktywny",  # Aktywny, Wstrzymany, Anulowany
        "created_at": "2026-07-22 12:00:00"
    }
}

# Historia logowań
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

        <div class="border-t border-slate-800 pt-4 text-center">
            <p class="text-xs text-slate-400">Nie masz konta lub klucza?</p>
            <p class="text-xs text-brand-400 mt-1 font-medium">Napisz wiadomość na: <a href="mailto:mbxryt24@zohomail.eu" class="underline">mbxryt24@zohomail.eu</a></p>
        </div>
    </div>

    <!-- PANEL KLIENTA -->
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
            <button @click="logout()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all">Wyloguj się</button>
        </header>

        <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-5">
            <div>
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Twój Klucz Licencyjny Pro</h2>
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
                    <span class="font-mono text-brand-400 text-base font-bold tracking-wider" x-text="userData.key"></span>
                    <span class="text-[10px] px-2.5 py-1 rounded-lg font-semibold"
                          :class="userData.status === 'Aktywny' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'"
                          x-text="userData.status"></span>
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Status konta</span>
                    <span class="text-slate-200 font-medium">Subskrypcja Pro</span>
                </div>
                <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 flex flex-col gap-1">
                    <span class="text-slate-500 font-semibold uppercase text-[10px]">Notatki</span>
                    <span class="text-slate-300 font-mono" x-text="userData.notes || 'Brak uwag'"></span>
                </div>
            </div>
        </div>
    </div>

    <!-- PANEL ADMINISTRACYJNY -->
    <div x-show="isLoggedIn && userData.role !== 'Klient'" class="max-w-5xl w-full flex flex-col gap-6" style="display: none;" :style="(isLoggedIn && userData.role !== 'Klient') ? 'display: flex;' : 'display: none;'">
        <header class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/30 flex items-center justify-center text-brand-400 font-bold">⚡</div>
                <div>
                    <h1 class="text-lg font-bold text-white flex items-center gap-2">
                        <span>Panel Administracyjny</span>
                        <span class="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2.5 py-0.5 rounded-full uppercase" x-text="userData.role"></span>
                    </h1>
                    <p class="text-xs text-slate-400">Zalogowany jako: <b class="text-slate-200" x-text="form.username"></b></p>
                </div>
            </div>
            <button @click="logout()" class="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 transition-all">Wyloguj się</button>
        </header>

        <!-- Zakładki -->
        <div class="flex gap-2 border-b border-slate-800 pb-3 flex-wrap">
            <button @click="activeTab = 'keys'" :class="activeTab === 'keys' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">🔑 Baza Kluczy</button>
            <button @click="activeTab = 'create'" :class="activeTab === 'create' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">➕ Utwórz Klucz</button>
            <button @click="activeTab = 'history'" :class="activeTab === 'history' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">📜 Historia Logowań</button>
            <button @click="activeTab = 'admins'" :class="activeTab === 'admins' ? 'bg-brand-500 text-white font-bold shadow-lg shadow-brand-500/20' : 'bg-slate-900 text-slate-400 hover:text-slate-200'" class="px-4 py-2 rounded-xl text-xs transition-all">🛡️ Zespół i Admini</button>
        </div>

        <!-- 1. Baza Kluczy -->
        <div x-show="activeTab === 'keys'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <div class="flex items-center justify-between flex-wrap gap-2">
                <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Aktywne klucze i zarządzanie</h2>
                <div class="flex gap-2">
                    <button @click="loadData()" class="px-3 py-1.5 text-xs rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-all">Odśwież</button>
                    <!-- Opcje backupu dostępne dla Właściciela -->
                    <template x-if="form.username === 'maxikk'">
                        <div class="flex gap-2">
                            <a href="/api/backup/download" class="px-3 py-1.5 text-xs rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600/30 transition-all flex items-center">📥 Pobierz Backup</a>
                            <label class="px-3 py-1.5 text-xs rounded-lg bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 transition-all cursor-pointer flex items-center">
                                📤 Wgraj Backup <input type="file" @change="uploadBackup($event)" class="hidden" accept=".json">
                            </label>
                        </div>
                    </template>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Użytkownik</th>
                            <th class="py-3 px-3">Hasło</th>
                            <th class="py-3 px-3">Klucz</th>
                            <th class="py-3 px-3">Status</th>
                            <th class="py-3 px-3">Notatki</th>
                            <th class="py-3 px-3 text-right">Akcje</th>
                        </tr>
                    </thead>
                    <tbody class="text-xs divide-y divide-slate-800/40">
                        <template x-for="(data, username) in keysList" :key="username">
                            <tr class="hover:bg-slate-800/30 transition-colors">
                                <td class="py-3 px-3 font-semibold text-slate-200" x-text="username"></td>
                                <td class="py-3 px-3 font-mono text-slate-400" x-text="data.password"></td>
                                <td class="py-3 px-3 font-mono text-brand-400 font-bold" x-text="data.key"></td>
                                <td class="py-3 px-3">
                                    <span class="px-2 py-0.5 rounded text-[10px] font-semibold"
                                          :class="{
                                              'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20': data.status === 'Aktywny',
                                              'bg-amber-500/10 text-amber-400 border border-amber-500/20': data.status === 'Wstrzymany',
                                              'bg-rose-500/10 text-rose-400 border border-rose-500/20': data.status === 'Anulowany'
                                          }" x-text="data.status"></span>
                                </td>
                                <td class="py-3 px-3 text-slate-400" x-text="data.notes || '-'"></td>
                                <td class="py-3 px-3 text-right flex items-center justify-end gap-1.5">
                                    <button @click="changeStatus(username, 'Aktywny')" class="px-2 py-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded text-[10px]">Aktywuj</button>
                                    <button @click="changeStatus(username, 'Wstrzymany')" class="px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 rounded text-[10px]">Wstrzymaj</button>
                                    <button @click="changeStatus(username, 'Anulowany')" class="px-2 py-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded text-[10px]">Anuluj</button>
                                    <!-- Usuń widoczne tylko dla Właściciela (maxikk) -->
                                    <template x-if="form.username === 'maxikk'">
                                        <button @click="deleteKey(username)" class="px-2 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-[10px] font-bold">Usuń</button>
                                    </template>
                                </td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 2. Utwórz Klucz -->
        <div x-show="activeTab === 'create'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4 max-w-lg">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Generator i Tworzenie Klienta</h2>
            <form @submit.prevent="createKey()" class="flex flex-col gap-4">
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Nazwa użytkownika klienta</label>
                    <input type="text" x-model="newKeyForm.username" required placeholder=""
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Hasło użytkownika</label>
                    <input type="text" x-model="newKeyForm.password" required placeholder=""
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Klucz licencyjny (zostaw puste lub wpisz własny)</label>
                    <div class="flex gap-2">
                        <input type="text" x-model="newKeyForm.key" placeholder="XXXX-XXXX-XXXX-XXXX"
                            class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm font-mono text-brand-400 focus:outline-none focus:border-brand-500 uppercase">
                        <button type="button" @click="generateKeyString()" class="px-3 bg-slate-800 hover:bg-slate-700 text-xs rounded-xl border border-slate-700">🎲 Losuj</button>
                    </div>
                </div>
                <div class="flex flex-col gap-1.5">
                    <label class="text-[11px] font-semibold text-slate-400 uppercase">Notatki (opcjonalnie)</label>
                    <input type="text" x-model="newKeyForm.notes" placeholder=""
                        class="bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-brand-500">
                </div>
                <div x-show="createMessage" class="text-xs px-3 py-2 rounded-xl text-center" :class="createSuccess ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'" x-text="createMessage"></div>
                <button type="submit" class="py-3 bg-gradient-to-r from-brand-500 to-emerald-600 hover:from-brand-600 text-white font-bold text-xs rounded-xl shadow-lg transition-all">Zapisz i Utwórz Klucz</button>
            </form>
        </div>

        <!-- 3. Historia Logowań -->
        <div x-show="activeTab === 'history'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Historia logowań</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Użytkownik</th>
                            <th class="py-3 px-3">Rola</th>
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

        <!-- 4. Zespół i Admini -->
        <div x-show="activeTab === 'admins'" class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-xl flex flex-col gap-4">
            <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lista zespołu</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-slate-800 text-[11px] text-slate-500 font-semibold">
                            <th class="py-3 px-3">Użytkownik</th>
                            <th class="py-3 px-3">Rola</th>
                            <th class="py-3 px-3 text-right">Hasło</th>
                        </tr>
                    </thead>
                    <tbody class="text-xs divide-y divide-slate-800/40">
     