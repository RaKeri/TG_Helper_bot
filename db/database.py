import sqlite3
import json
import time

class DatabaseManager:
    def __init__(self, db_name="database.db"):
        """Инициализация подключения к БД."""
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_table()

    def close(self):
        """Закрытие подключения к БД."""
        self.connection.commit()
        self.connection.close()

    def fetch_accounts(self, user_id):
        """Получение всех аккаунтов по ID."""
        self.cursor.execute("SELECT * FROM accounts WHERE user_id=?", (user_id,))
        return self.cursor.fetchall()

    def accounts_from_phone(self, phone):
        """Получение аккаунта по номеру."""
        self.cursor.execute("SELECT * FROM accounts WHERE phone=?", (phone,))
        return self.cursor.fetchone()

    def log_from_phone(self, phone):
        """Получение логов по номеру."""
        self.cursor.execute("SELECT * FROM accounts WHERE phone=?", (phone,))
        return self.cursor.fetchone()


    def fetch_user(self, user_id):
        """Получение пользователя по ID."""
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def add_user(self, user_data):
        """Добавление нового пользователя в БД."""
        self.cursor.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, timestamp, accounts, balance, balance_all)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, user_data)
        self.connection.commit()

    def update_user(self, user_id, username=None, first_name=None, last_name=None):
        """Обновление данных пользователя (если переданы новые значения)."""
        if username:
            self.cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        if first_name:
            self.cursor.execute("UPDATE users SET first_name = ? WHERE user_id = ?", (first_name, user_id))
        if last_name:
            self.cursor.execute("UPDATE users SET last_name = ? WHERE user_id = ?", (last_name, user_id))
        self.connection.commit()

    def fetch_all_users(self):
        """Получение всех пользователей из БД."""
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()

    def add_subscription(self, user_id, subscription):
        """Добавление новой подписки пользователю."""
        self.cursor.execute("SELECT passHistory FROM users WHERE user_id = ?", (user_id,))
        current_subs = json.loads(self.cursor.fetchone()[0] or "[]")
        current_subs.append(subscription)
        self.cursor.execute("UPDATE users SET passHistory = ? WHERE user_id = ?", (json.dumps(current_subs), user_id))
        self.connection.commit()

    def update_user_status(self, user_id, status):
        """Обновление статуса пользователя (например, бан)."""
        self.cursor.execute("UPDATE users SET ban = ? WHERE user_id = ?", (status, user_id))
        self.connection.commit()

    def add_account(self, phone, user_id, username, first_name, device_model, system_version, app_version):
        """Добавление нового аккаунта в БД."""
        self.cursor.execute("""
            INSERT INTO accounts (phone, user_id, username, first_name, device_model, system_version, app_version)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (phone, user_id, username, first_name, device_model, system_version, app_version))
        self.connection.commit()

    def fetch_user_logs(self, phone):
        """Получение логов пользователя по номеру телефона."""
        self.cursor.execute("SELECT * FROM logs WHERE phone = ?", (phone,))
        return self.cursor.fetchone()

    def update_account_status(self, status, timestamp=None, phone=None):
        """Обновление статуса аккаунта."""
        self.cursor.execute("""
            UPDATE accounts SET status = ?, workingTimestamp = ? WHERE phone = ?
        """, (status, timestamp, phone))
        self.connection.commit()

    def update_url_status(self, url_id, new_status):
        """Обновление информации о URL."""
        self.cursor.execute("UPDATE url SET booli = ? WHERE id = ?", (new_status, url_id))
        self.connection.commit()

    def add_to_db_account(self, phone, user_id, username, name, device_model, system_version, app_version):
        """Добавление нового аккаунта пользователя."""
        self.cursor.execute("SELECT accounts FROM users WHERE user_id=?", (user_id,))
        accounts = self.cursor.fetchone()[0]

        self.cursor.execute("UPDATE users SET accounts = ? WHERE user_id = ?", (accounts + 1, user_id))
        self.cursor.execute("""
            INSERT INTO accounts (user_id, phone, timestamp, status, name, username, deviceModel, systemVersion, appVersion) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, phone, time.time(), "DISABLE", name, username, device_model, system_version, app_version))

        self.cursor.execute("INSERT INTO logs (user_id, phone) VALUES (?, ?)", (user_id, phone))
        self.connection.commit()

    def start_accounts(self, workingTimestamp, chats, status, id_from, id_to, filters, action, phone):
        """Добавление фильтров для аккаунта."""
        self.cursor.execute("""
            UPDATE accounts SET workingTimestamp = ?,chats = ?, status = ?, idFrom = ?, idTo = ?, Filters = ?, action = ? WHERE phone = ?
        """, (workingTimestamp, chats, status, id_from, id_to, filters, action, phone))
        self.connection.commit()

    def update_proxy(self, proxy, phone):
        """Обновление прокси."""
        self.cursor.execute("""
            UPDATE accounts SET proxy = ? WHERE phone = ?
        """, (proxy, phone))
        self.connection.commit()


    def del_to_db_account(self, phone, user_id):
        """Удаление аккаунта и связанных логов."""
        self.cursor.execute("SELECT accounts FROM users WHERE user_id=?", (user_id,))
        accounts = self.cursor.fetchone()[0]

        self.cursor.execute("UPDATE users SET accounts = ? WHERE user_id = ?", (accounts - 1, user_id))
        self.cursor.execute("DELETE FROM accounts WHERE phone = ?", (phone,))
        self.cursor.execute("DELETE FROM logs WHERE phone = ?", (phone,))
        self.connection.commit()

    def clear_logs(self, error, done, photoSend, videoSend, documentSend, GCSend, VCSend, freqChannel, freqTime, freqMessage, phone):
        self.cursor.execute("""
        UPDATE logs SET error = ?, done = ?, photoSend = ?, videoSend = ?, documentSend = ?, GCSend = ?, VCSend = ?, freqChannel = ?, freqTime = ?, freqMessage = ?  WHERE phone = ?
        """,
        (error, done, photoSend, videoSend, documentSend, GCSend, VCSend, freqChannel, freqTime, freqMessage, phone))
        self.connection.commit()

    def commit(self):
        """Принудительное сохранение изменений в БД."""
        self.connection.commit()

    def create_table(self):
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    timestamp LONGINT,
                    accounts INTEGER,
                    balance INTEGER,
                    balance_all INTEGER,
                    passHistory TEXT DEFAULT "[]",
                    passFreeGet INTEGER DEFAULT 0,
                    admin INTEGER DEFAULT 0,
                    ban INTEGER NOT NULL DEFAULT 0
                )
            """)
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    user_id INTEGER,
                    name TEXT,
                    username TEXT,
                    phone TEXT,
                    timestamp INTEGER,
                    status TEXT,
                    workingTimestamp INTEGER,
                    chats TEXT,
                    idFrom TEXT,
                    idTo TEXT,
                    Filters TEXT,
                    action INTEGER,
                    proxy TEXT,
                    deviceModel TEXT,
                    systemVersion TEXT,
                    appVersion TEXT   
                )
            """)
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    user_id INTEGER,
                    phone TEXT,
                    error INTEGER DEFAULT 0,
                    done INTEGER DEFAULT 0,
                    photoSend INTEGER DEFAULT 0,
                    videoSend INTEGER DEFAULT 0,
                    documentSend INTEGER DEFAULT 0,     
                    GCSend INTEGER DEFAULT 0,
                    VCSend INTEGER DEFAULT 0,
                    freqChannel TEXT DEFAULT "[]",
                    freqTime TEXT DEFAULT "[]",
                    freqMessage TEXT DEFAULT "[]"
                )
            """)
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS keysEden (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tokenApi TEXT,
                    tokenUsers TEXT,
                    login TEXT,
                    password TEXT,
                    credit INTEGER
                )
            """)
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pass (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    passName TEXT NOT NULL,
                    passNameEN TEXT NOT NULL,
                    desc TEXT,
                    price INTEGER,
                    oldPrice INTEGER,
                    currency TEXT DEFAULT "USD",
                    duration TEXT,
                    timestamp INTEGER
                )
            """)
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS url (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    badURL TEXT NOT NULL,
                    booli TEXT 
                )
            """)

