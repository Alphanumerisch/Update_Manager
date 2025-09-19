-- Erstellt die Kunden-Tabelle
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

-- Erstellt die Updates-Tabelle
CREATE TABLE IF NOT EXISTS updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Erstellt die Kunden-Updates-Tabelle (Verknüpfung zwischen Kunden und Updates)
CREATE TABLE IF NOT EXISTS customer_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    update_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'offen',
    selected_date TEXT DEFAULT NULL,
    note TEXT DEFAULT NULL,  -- Neue Spalte für Notizen
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (update_id) REFERENCES updates(id) ON DELETE CASCADE
);

-- Erstellt die Benutzer-Tabelle
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    token TEXT
);

CREATE TABLE IF NOT EXISTS invalid_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL
);


