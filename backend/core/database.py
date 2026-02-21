import sqlite3
import datetime

class Database:
    def __init__(self, db_path="trades.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market TEXT,
            direction TEXT,
            size REAL,
            entry_price REAL,
            exit_price REAL,
            fee_paid REAL,
            gross_pnl REAL,
            net_pnl REAL,
            status TEXT,
            open_time TIMESTAMP,
            close_time TIMESTAMP
        )
        ''')
        
        # System status/logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            level TEXT,
            message TEXT
        )
        ''')
        
        conn.commit()
        conn.close()

    def log_trade(self, trade_data: dict) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        
        cursor.execute('''
        INSERT INTO trades (market, direction, size, entry_price, status, open_time)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('market'),
            trade_data.get('direction'),
            trade_data.get('size'),
            trade_data.get('entry_price'),
            'OPEN',
            now
        ))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trade_id

    def close_trade(self, trade_id: int, close_data: dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        
        cursor.execute('''
        UPDATE trades 
        SET exit_price = ?, fee_paid = ?, gross_pnl = ?, net_pnl = ?, status = ?, close_time = ?
        WHERE id = ?
        ''', (
            close_data.get('exit_price'),
            close_data.get('fee_paid'),
            close_data.get('gross_pnl'),
            close_data.get('net_pnl'),
            'CLOSED',
            now,
            trade_id
        ))
        
        conn.commit()
        conn.close()
