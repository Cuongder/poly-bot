import sqlite3
import datetime
import logging
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager for trading data.
    Handles trades, logs, and system events.
    """

    def __init__(self, db_path="trades.db"):
        self.db_path = db_path
        self._init_db()
        logger.info(f"Database initialized at {db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Trades table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market TEXT NOT NULL,
                direction TEXT NOT NULL,
                size REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                fee_paid REAL DEFAULT 0,
                gross_pnl REAL DEFAULT 0,
                net_pnl REAL DEFAULT 0,
                status TEXT DEFAULT 'OPEN',
                close_reason TEXT,
                open_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                close_time TIMESTAMP
            )
            ''')

            # System logs table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,
                source TEXT,
                message TEXT NOT NULL
            )
            ''')

            # API keys table for authentication
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT,
                permissions TEXT DEFAULT 'read',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
            ''')

            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_open_time ON trades(open_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)')

            conn.commit()
            logger.debug("Database tables initialized")

    def log_trade(self, trade_data: dict) -> int:
        """
        Log a new trade to the database.

        Args:
            trade_data: Dictionary containing trade information

        Returns:
            The ID of the newly created trade
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO trades (market, direction, size, entry_price, status, open_time)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                trade_data.get('market'),
                trade_data.get('direction'),
                trade_data.get('size'),
                trade_data.get('entry_price'),
                'OPEN',
                datetime.datetime.now()
            ))

            trade_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Logged new trade with ID {trade_id}")
            return trade_id

    def close_trade(self, trade_id: int, close_data: dict):
        """
        Update a trade when it is closed.

        Args:
            trade_id: The ID of the trade to close
            close_data: Dictionary containing close information
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            UPDATE trades
            SET exit_price = ?, fee_paid = ?, gross_pnl = ?, net_pnl = ?, status = ?, close_time = ?, close_reason = ?
            WHERE id = ?
            ''', (
                close_data.get('exit_price'),
                close_data.get('fee_paid'),
                close_data.get('gross_pnl'),
                close_data.get('net_pnl'),
                'CLOSED',
                datetime.datetime.now(),
                close_data.get('close_reason', 'SIGNAL'),
                trade_id
            ))

            conn.commit()
            logger.debug(f"Closed trade {trade_id}")

    def get_trade_by_id(self, trade_id: int) -> Optional[Dict]:
        """Get a single trade by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_trades(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get all trades with pagination.

        Args:
            limit: Maximum number of trades to return
            offset: Number of trades to skip

        Returns:
            List of trade dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM trades
            ORDER BY open_time DESC
            LIMIT ? OFFSET ?
            ''', (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_open_trades(self) -> List[Dict]:
        """Get all currently open trades"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM trades WHERE status = ? ORDER BY open_time DESC', ('OPEN',))
            return [dict(row) for row in cursor.fetchall()]

    def get_closed_trades(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all closed trades with pagination"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM trades WHERE status = ?
            ORDER BY close_time DESC
            LIMIT ? OFFSET ?
            ''', ('CLOSED', limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_trade_stats(self) -> Dict:
        """
        Get trading statistics.

        Returns:
            Dictionary containing aggregated trade statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total trades
            cursor.execute('SELECT COUNT(*) as total FROM trades WHERE status = ?', ('CLOSED',))
            total_trades = cursor.fetchone()['total']

            # Winning trades
            cursor.execute('SELECT COUNT(*) as wins FROM trades WHERE status = ? AND net_pnl > 0', ('CLOSED',))
            wins = cursor.fetchone()['wins']

            # Losing trades
            cursor.execute('SELECT COUNT(*) as losses FROM trades WHERE status = ? AND net_pnl <= 0', ('CLOSED',))
            losses = cursor.fetchone()['losses']

            # Total PnL
            cursor.execute('SELECT COALESCE(SUM(net_pnl), 0) as total_pnl FROM trades WHERE status = ?', ('CLOSED',))
            total_pnl = cursor.fetchone()['total_pnl']

            # Gross profit (only winning trades)
            cursor.execute('SELECT COALESCE(SUM(gross_pnl), 0) as gross_profit FROM trades WHERE status = ? AND gross_pnl > 0', ('CLOSED',))
            gross_profit = cursor.fetchone()['gross_profit']

            # Total fees
            cursor.execute('SELECT COALESCE(SUM(fee_paid), 0) as total_fees FROM trades WHERE status = ?', ('CLOSED',))
            total_fees = cursor.fetchone()['total_fees']

            # Average trade metrics
            cursor.execute('SELECT AVG(net_pnl) as avg_pnl, MAX(net_pnl) as max_pnl, MIN(net_pnl) as min_pnl FROM trades WHERE status = ?', ('CLOSED',))
            row = cursor.fetchone()

            return {
                'total_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': (wins / total_trades * 100) if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'gross_profit': gross_profit,
                'total_fees': total_fees,
                'avg_pnl': row['avg_pnl'] or 0,
                'max_pnl': row['max_pnl'] or 0,
                'min_pnl': row['min_pnl'] or 0
            }

    def get_trades_by_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[Dict]:
        """Get trades within a date range"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM trades
            WHERE open_time BETWEEN ? AND ?
            ORDER BY open_time DESC
            ''', (start_date, end_date))
            return [dict(row) for row in cursor.fetchall()]

    def log_system_message(self, level: str, message: str, source: str = None):
        """
        Log a system message.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            source: Source of the log message
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO logs (timestamp, level, source, message)
            VALUES (?, ?, ?, ?)
            ''', (datetime.datetime.now(), level, source, message))
            conn.commit()

    def get_logs(self, level: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get system logs with optional filtering.

        Args:
            level: Filter by log level
            limit: Maximum number of logs to return

        Returns:
            List of log dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if level:
                cursor.execute('''
                SELECT * FROM logs WHERE level = ?
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (level, limit))
            else:
                cursor.execute('''
                SELECT * FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def clear_old_logs(self, days: int = 30):
        """Clear logs older than specified days"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM logs WHERE timestamp < ?', (cutoff_date,))
            conn.commit()
            logger.info(f"Cleared {cursor.rowcount} old log entries")

    # API Key management for authentication
    def add_api_key(self, key_hash: str, name: str = None, permissions: str = 'read') -> int:
        """Add a new API key"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO api_keys (key_hash, name, permissions)
            VALUES (?, ?, ?)
            ''', (key_hash, name, permissions))
            conn.commit()
            return cursor.lastrowid

    def validate_api_key(self, key_hash: str) -> Optional[Dict]:
        """Validate an API key and return its permissions"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1
            ''', (key_hash,))
            row = cursor.fetchone()

            if row:
                # Update last_used timestamp
                cursor.execute('''
                UPDATE api_keys SET last_used = ? WHERE id = ?
                ''', (datetime.datetime.now(), row['id']))
                conn.commit()
                return dict(row)
            return None

    def revoke_api_key(self, key_id: int):
        """Revoke an API key"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE api_keys SET is_active = 0 WHERE id = ?', (key_id,))
            conn.commit()

    def list_api_keys(self) -> List[Dict]:
        """List all API keys"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, permissions, is_active, created_at, last_used FROM api_keys')
            return [dict(row) for row in cursor.fetchall()]
