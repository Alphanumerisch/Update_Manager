CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
CREATE TABLE updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
, updates_send BOOLEAN DEFAULT 0);
CREATE TABLE customer_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    update_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'offen',
    selected_date TEXT DEFAULT NULL, note TEXT DEFAULT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (update_id) REFERENCES updates(id) ON DELETE CASCADE
);
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    token TEXT
);
CREATE TABLE invalid_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL
);
CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL UNIQUE
, key TEXT, value TEXT);
CREATE TABLE email_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_id INTEGER NOT NULL,
    smtp_server TEXT NOT NULL,
    smtp_server_port INTEGER NOT NULL,
    smtp_user TEXT NOT NULL,
    smtp_pw TEXT NOT NULL,
    sender_mail TEXT NOT NULL,
    FOREIGN KEY (setting_id) REFERENCES settings(id) ON DELETE CASCADE
);
CREATE TABLE opening_hours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL, -- Montag, Dienstag, etc.
    open_time TEXT NOT NULL, -- Format HH:MM (z.B. 09:00)
    close_time TEXT NOT NULL, -- Format HH:MM (z.B. 18:00)
    is_open BOOLEAN DEFAULT 1, -- 1 = geöffnet, 0 = geschlossen
    FOREIGN KEY (setting_id) REFERENCES settings(id) ON DELETE CASCADE
);

INSERT INTO settings (category) VALUES ('email');
INSERT INTO settings (category) VALUES ('business_hours');
INSERT INTO settings (category) VALUES ('appointment_settings');

INSERT INTO email_settings (setting_id, smtp_server, smtp_server_port, smtp_user, smtp_pw, sender_mail)
VALUES (
    (SELECT id FROM settings WHERE category = 'email'),
    'smtp.example.com', 587, 'user@example.com', 'securepassword', 'noreply@example.com'
);

UPDATE settings 
SET key = 'extra_cost', value = '1' 
WHERE category = 'appointment_settings';
