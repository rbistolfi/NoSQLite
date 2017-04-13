# coding: utf-8


import sqlite3


_conn = None


def init_data_store(dbconnection):
    """Create system tables"""
    query = """CREATE TABLE IF NOT EXISTS entities (
        added_id INTEGER PRIMARY KEY,
        id TEXT NOT NULL UNIQUE,
        updated TEXT NOT NULL,
        type TEXT NOT NULL,
        body BLOB
    );
    """
    c = dbconnection.cursor()
    c.execute(query)
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS entities_by_added_id ON entities(added_id)")
    c.execute("CREATE INDEX IF NOT EXISTS entities_by_id ON entities(id)")
    c.execute("CREATE INDEX IF NOT EXISTS entities_by_id_type ON entities(id, type)")
    dbconnection.commit()


def init(dbname=':memory:'):
    """Create a connection and initialize db"""
    global _conn
    _conn = sqlite3.connect(dbname)
    init_data_store(_conn)
    return _conn


def get_connection():
    """Return the current connection"""
    global _conn
    return _conn


def reset_database():
    """Delete all data from active db"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entities")
    conn.commit()
