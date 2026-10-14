"""
Database schema definitions for persistent hotel shortlist in SQLite.
"""

CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS shortlist (
    place_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    formatted_address TEXT,
    street TEXT,
    city TEXT,
    state TEXT,
    postcode TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    distance_meters REAL,
    category TEXT,
    website TEXT,
    phone TEXT,
    search_zip TEXT,
    saved_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shortlist_postcode ON shortlist(postcode);
CREATE INDEX IF NOT EXISTS idx_shortlist_saved_at ON shortlist(saved_at);
"""
