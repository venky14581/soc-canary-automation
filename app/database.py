import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT UNIQUE,
                    ip_address TEXT,
                    domain TEXT,
                    method TEXT,
                    status TEXT,
                    last_seen TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT,
                    ip_address TEXT,
                    file_name TEXT,
                    deployment_path TEXT,
                    method TEXT,
                    status TEXT,
                    timestamp TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deployment_id INTEGER,
                    file_exists INTEGER,
                    size_match INTEGER,
                    hash_match INTEGER,
                    status TEXT,
                    timestamp TIMESTAMP
                )
            """)
            conn.commit()

    def upsert_host(self, hostname, ip, domain, method, status):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hosts (hostname, ip_address, domain, method, status, last_seen)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(hostname) DO UPDATE SET
                    ip_address=excluded.ip_address,
                    domain=excluded.domain,
                    method=excluded.method,
                    status=excluded.status,
                    last_seen=excluded.last_seen
            """, (hostname, ip, domain, method, status, datetime.now().isoformat()))
            conn.commit()

    def log_deployment(self, hostname, ip, file_name, path, method, status):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deployments (hostname, ip_address, file_name, deployment_path, method, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (hostname, ip, file_name, path, method, status, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid

    def log_validation(self, deployment_id, exists, size_m, hash_m, status):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO validation_results (deployment_id, file_exists, size_match, hash_match, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (deployment_id, int(exists), int(size_m), int(hash_m), status, datetime.now().isoformat()))
            conn.commit()