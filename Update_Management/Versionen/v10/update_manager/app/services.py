from fastapi import HTTPException
from .database import get_db_connection
from typing import Optional, List
import uuid
from passlib.context import CryptContext
import jwt
import datetime
import logging
import sqlite3
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


SECRET_KEY = "Quest2014$$"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user(token: str):
    #Überprüft, ob ein Benutzer eingeloggt ist und gibt seine Daten zurück."""
    if not token:
        raise HTTPException(status_code=400, detail="Kein Token übergeben")

    conn = get_db_connection()
    
    # Überprüfen, ob das Token ungültig ist
    invalid = conn.execute("SELECT id FROM invalid_tokens WHERE token = ?", (token,)).fetchone()
    if invalid:
        conn.close()
        raise HTTPException(status_code=401, detail="Token ist ungültig")

    user = conn.execute("SELECT id, name, email FROM user WHERE token = ?", (token,)).fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Benutzer nicht gefunden oder nicht eingeloggt")

    conn.close()
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


def invalidate_token(user_id: int):
    #Macht das Token sofort ungültig."""
    invalid_tokens.add(user_id)

# Passwort-Hashing
def hash_password(password: str) -> str:
    #Erstellt einen SHA256 Hash des Passworts."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# JWT-Token erstellen
def create_token(user_id: int):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    token = jwt.encode({"sub": str(user_id), "exp": expiration}, SECRET_KEY, algorithm=ALGORITHM)
    
    conn = get_db_connection()
    conn.execute("INSERT INTO active_tokens (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    conn.close()
    return token

# Token entschlüsseln
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        conn = get_db_connection()
        result = conn.execute("SELECT user_id FROM active_tokens WHERE token = ?", (token,)).fetchone()
        conn.close()
        if result is None:
            raise HTTPException(status_code=401, detail="Token ungültig oder abgelaufen")
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token abgelaufen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ungültiger Token")

# Benutzer registrieren
def register_user(name: str, email: str, password: str):
    #Registriert einen neuen Benutzer."""
    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Alle Felder erforderlich")

    hashed_password = hash_password(password)
    conn = get_db_connection()
    
    try:
        conn.execute("INSERT INTO user (name, email, password) VALUES (?, ?, ?)", 
                     (name, email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Benutzer existiert bereits")
    finally:
        conn.close()

    return {"message": "Benutzer erfolgreich registriert"}

def login(email: str, password: str):
    #Meldet den Benutzer an und gibt ein Token zurück."""
    hashed_password = hash_password(password)
    conn = get_db_connection()

    user = conn.execute("SELECT id FROM user WHERE email = ? AND password = ?", 
                        (email, hashed_password)).fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="Falsche Anmeldedaten")

    token = str(uuid.uuid4())
    conn.execute("UPDATE user SET token = ? WHERE id = ?", (token, user["id"]))
    conn.commit()
    conn.close()

    return {"message": "Login erfolgreich", "token": token}

def logout(token: str):
    #Meldet den Benutzer ab und speichert das Token als ungültig."""
    if not token:
        raise HTTPException(status_code=400, detail="Kein Token übergeben")

    conn = get_db_connection()
    conn.execute("INSERT INTO invalid_tokens (token) VALUES (?)", (token,))
    conn.commit()
    conn.close()

    return {"message": "Logout erfolgreich"}

# Benutzer-Authentifizierung
def authenticate_user(username: str, password: str):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user and verify_password(password, user["password"]):
        return create_token(user["id"])
    return None

# Kunde hinzufügen
def add_customer(name: Optional[str], email: Optional[str]):
    """Fügt einen neuen Kunden hinzu."""
    if not name or not email:
        raise HTTPException(status_code=400, detail="Name und Email erforderlich")

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO customers (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        return {"message": "Kunde hinzugefügt"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="E-Mail bereits vorhanden")
    finally:
        conn.close()

# Kunden auflisten
def list_customers():
    """Gibt alle Kunden zurück."""
    conn = get_db_connection()
    customers = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()

    if not customers:
        raise HTTPException(status_code=404, detail="Keine Kunden gefunden")

    return [dict(row) for row in customers]

# Update erstellen
def create_update(title: str, description: str):
    """Erstellt ein neues Update."""
    if not title or not description:
        raise HTTPException(status_code=400, detail="Titel und Beschreibung erforderlich")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO updates (title, description) VALUES (?, ?)", (title, description))
    update_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Update erstellt", "update_id": update_id}

# Updates auflisten
def list_updates():
    """Gibt alle Updates mit zugewiesenen Kunden zurück."""
    conn = get_db_connection()
    
    updates = conn.execute("SELECT id, title, description, updates_send FROM updates").fetchall()
    updates_list = []

    for update in updates:
        update_dict = dict(update)
        
        # Kunden abrufen, die mit dem Update verknüpft sind
        customers = conn.execute("""
            SELECT c.id, c.name, c.email 
            FROM customer_updates cu
            JOIN customers c ON cu.customer_id = c.id
            WHERE cu.update_id = ?
        """, (update["id"],)).fetchall()
        
        update_dict["customers"] = [dict(customer) for customer in customers]
        updates_list.append(update_dict)

    conn.close()
    return updates_list

# Kunde löschen
def delete_customer(customer_id: int):
    """Löscht einen Kunden."""
    conn = get_db_connection()
    customer_exists = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
    
    if not customer_exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    
    return {"message": f"Kunde mit ID {customer_id} wurde gelöscht"}

# Update löschen
def delete_update(update_id: int):
    conn = get_db_connection()
    update_exists = conn.execute("SELECT id FROM updates WHERE id = ?", (update_id,)).fetchone()
    if not update_exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Update nicht gefunden")

    conn.execute("DELETE FROM customer_updates WHERE update_id = ?", (update_id,))
    conn.execute("DELETE FROM updates WHERE id = ?", (update_id,))
    
    conn.commit()
    conn.close()

    return {"message": f"Update mit ID {update_id} wurde gelöscht"}

# Dashboard laden
def dashboard():
    conn = get_db_connection()
    results = conn.execute("""
        SELECT u.id AS update_id, u.title, u.description, c.name, c.email, cu.status, cu.selected_date, cu.note
        FROM customer_updates cu
        JOIN customers c ON cu.customer_id = c.id
        JOIN updates u ON cu.update_id = u.id
    """).fetchall()
    conn.close()

    return [dict(row) for row in results]

# Webseite für den Kunden im Termin zu wählen
def customer_page(token: str):
    conn = get_db_connection()
    customer = conn.execute("""
        SELECT c.name, u.title, cu.status, cu.selected_date, cu.note
        FROM customer_updates cu
        JOIN customers c ON cu.customer_id = c.id
        JOIN updates u ON cu.update_id = u.id
        WHERE cu.token = ?
    """, (token,)).fetchone()

    conn.close()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Ungültiger Token")

    response = dict(customer)

    if customer["selected_date"]:
        response["message"] = "Ein Termin wurde bereits gewählt. Möchten Sie ihn ändern?"

    return response

def select_date(token: str, selected_date: str, note: Optional[str] = None):
    if not token or not selected_date:
        raise HTTPException(status_code=400, detail="Token und Datum erforderlich")

    conn = get_db_connection()

    existing_entry = conn.execute("SELECT id FROM customer_updates WHERE token = ?", (token,)).fetchone()

    if not existing_entry:
        conn.close()
        raise HTTPException(status_code=400, detail="Ungültiger Token")

    if note is None:
        note = "KEINE_NOTIZ_ÜBERMITTELT"

    result = conn.execute(
        "UPDATE customer_updates SET selected_date = ?, note = ?, status = 'bestätigt' WHERE token = ?",
        (selected_date, note, token),
    )
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="Fehler beim Speichern des Termins")

    return {"message": "Termin erfolgreich gespeichert", "note": note}

#  Update an Kunden senden & Token generieren**
def send_update(update_id: int):
    """Sendet eine E-Mail mit dem bereits gespeicherten Token an alle Kunden eines Updates und setzt `updates_send` auf `true`."""

    if not update_id:
        raise HTTPException(status_code=400, detail="Update-ID erforderlich")

    conn = get_db_connection()

    # Prüfen, ob das Update existiert und ob es bereits gesendet wurde
    update_exists = conn.execute("SELECT id, title, description, updates_send FROM updates WHERE id = ?", (update_id,)).fetchone()
    
    if not update_exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Update-ID existiert nicht")

    if update_exists["updates_send"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Update wurde bereits gesendet")

    # SMTP-Einstellungen aus der Datenbank abrufen
    email_settings = conn.execute("""
        SELECT smtp_server, smtp_server_port, smtp_user, smtp_pw, sender_mail 
        FROM email_settings 
        WHERE setting_id = (SELECT id FROM settings WHERE category = 'email')
        LIMIT 1
    """).fetchone()

    if not email_settings:
        conn.close()
        raise HTTPException(status_code=500, detail="Keine SMTP-Einstellungen gefunden")

    # Kunden abrufen, die mit dem Update verknüpft sind und ein Token haben
    customers = conn.execute("""
        SELECT c.id, c.name, c.email, cu.token
        FROM customer_updates cu
        JOIN customers c ON cu.customer_id = c.id
        WHERE cu.update_id = ? AND cu.token IS NOT NULL
    """, (update_id,)).fetchall()

    if not customers:
        conn.close()
        raise HTTPException(status_code=400, detail="Keine Kunden mit gültigem Token für dieses Update gefunden")

    # SMTP-Variablen setzen
    smtp_server = email_settings["smtp_server"]
    smtp_port = email_settings["smtp_server_port"]
    smtp_user = email_settings["smtp_user"]
    smtp_pw = email_settings["smtp_pw"]
    sender_mail = email_settings["sender_mail"]

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pw)

            for customer in customers:
                update_link = f"https://example.com/update?token={customer['token']}"

                # E-Mail erstellen
                message = MIMEMultipart()
                message["From"] = sender_mail
                message["To"] = customer["email"]
                message["Subject"] = f"Neues Update: {update_exists['title']}"
                
                email_body = f"""
                Hallo {customer['name']},

                Es gibt ein neues Update für Sie:

                Titel: {update_exists['title']}
                Beschreibung: {update_exists['description']}

                Sie können das Update unter folgendem Link einsehen:
                {update_link}

                Mit freundlichen Grüßen,
                Ihr Team
                """
                message.attach(MIMEText(email_body, "plain"))

                # E-Mail senden
                server.sendmail(sender_mail, customer["email"], message.as_string())

        # `updates_send` auf `true` setzen, da alle E-Mails gesendet wurden
        conn.execute("UPDATE updates SET updates_send = 1 WHERE id = ?", (update_id,))
        conn.commit()

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"E-Mail-Versand fehlgeschlagen: {str(e)}")

    conn.close()
    return {"message": "E-Mails gesendet und Update-Status aktualisiert"}
    
# Kunde einem Update hinzufügen
def add_customer_to_update(update_id: int, customer_ids: List[int]):
    """Fügt Kunden zu einem bestehenden Update hinzu."""
    if not update_id or not customer_ids:
        raise HTTPException(status_code=400, detail="Update-ID und Kunden-IDs erforderlich")

    conn = get_db_connection()

    # Prüfen, ob das Update existiert
    update_exists = conn.execute("SELECT id FROM updates WHERE id = ?", (update_id,)).fetchone()
    if not update_exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Update nicht gefunden")

    # Kunden hinzufügen, falls sie noch nicht verknüpft sind
    for customer_id in customer_ids:
        existing_entry = conn.execute(
            "SELECT 1 FROM customer_updates WHERE update_id = ? AND customer_id = ?",
            (update_id, customer_id)
        ).fetchone()

        if not existing_entry:
            token = str(uuid.uuid4())[:16]  # ✅ Generiere ein Token, falls erforderlich
            conn.execute(
                "INSERT INTO customer_updates (customer_id, update_id, token) VALUES (?, ?, ?)",
                (customer_id, update_id, token)
            )

    conn.commit()
    conn.close()

    return {"message": "Kunden zum Update hinzugefügt"}

def get_settings(setting_type: str):
    """Liest die gewünschten Einstellungen aus der Datenbank."""
    conn = get_db_connection()

    if setting_type == "email_settings":
        settings = conn.execute("""
            SELECT smtp_server, smtp_server_port, smtp_user, sender_mail 
            FROM email_settings 
            WHERE setting_id = (SELECT id FROM settings WHERE category = 'email')
            LIMIT 1
        """).fetchone()
    
    elif setting_type == "extra_costs":
        settings = conn.execute("""
            SELECT key, value FROM settings WHERE category = 'appointment_settings'
        """).fetchall()

    elif setting_type == "business_time":
        settings = conn.execute("""
            SELECT day_of_week, open_time, close_time, is_open 
            FROM opening_hours 
            WHERE setting_id = (SELECT id FROM settings WHERE category = 'business_hours')
        """).fetchall()
    
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Ungültige Einstellungen-Kategorie")

    conn.close()

    if settings:
        if setting_type == "email_settings":
            return dict(settings)
        elif setting_type == "extra_costs":
            return {setting["key"]: setting["value"] for setting in settings}
        elif setting_type == "business_time":
            return [{"day_of_week": s["day_of_week"], "open_time": s["open_time"], "close_time": s["close_time"], "is_open": s["is_open"]} for s in settings]
    else:
        raise HTTPException(status_code=404, detail=f"Keine Einstellungen für {setting_type} gefunden")



def set_settings(setting_type: str, new_settings: dict):
    """Setzt neue Einstellungen für die gewünschte Kategorie."""
    conn = get_db_connection()
    cursor = conn.cursor()  # <--- Cursor hinzufügen
    if setting_type == "email_settings":
        conn.execute("""
            UPDATE email_settings 
            SET smtp_server = ?, smtp_server_port = ?, smtp_user = ?, smtp_pw = ?, sender_mail = ? 
            WHERE setting_id = (SELECT id FROM settings WHERE category = 'email')
        """, (
            new_settings.get("smtp_server"),
            new_settings.get("smtp_server_port"),
            new_settings.get("smtp_user"),
            new_settings.get("smtp_pw"),
            new_settings.get("sender_mail")
        ))

    elif setting_type == "extra_costs":
        for key, value in new_settings.items():
            cursor.execute("""
                SELECT COUNT(*) FROM settings WHERE category = 'appointment_settings' AND key = ?
            """, (key,))
            exists = cursor.fetchone()[0]

            if exists:
                cursor.execute("""
                    UPDATE settings SET value = ? WHERE category = 'appointment_settings' AND key = ?
                """, (value, key))
            else:
                cursor.execute("""
                    INSERT INTO settings (category, key, value) VALUES ('appointment_settings', ?, ?)
                """, (key, value))

    elif setting_type == "business_time":
        setting_id = cursor.execute("""
            SELECT id FROM settings WHERE category = 'business_hours'
        """).fetchone()

        if not setting_id:
            conn.close()
            raise HTTPException(status_code=400, detail="Kategorie 'business_hours' nicht gefunden.")

        setting_id = setting_id[0]

        for day in new_settings.get("days", []):
            cursor.execute("""
                SELECT COUNT(*) FROM opening_hours WHERE setting_id = ? AND day_of_week = ?
            """, (setting_id, day["day_of_week"]))
            exists = cursor.fetchone()[0]

            if exists:
                cursor.execute("""
                    UPDATE opening_hours 
                    SET open_time = ?, close_time = ?, is_open = ? 
                    WHERE setting_id = ? AND day_of_week = ?
                """, (day["open_time"], day["close_time"], day["is_open"], setting_id, day["day_of_week"]))
            else:
                cursor.execute("""
                    INSERT INTO opening_hours (setting_id, day_of_week, open_time, close_time, is_open) 
                    VALUES (?, ?, ?, ?, ?)
                """, (setting_id, day["day_of_week"], day["open_time"], day["close_time"], day["is_open"]))
    
    else:
        conn.close()
        raise HTTPException(status_code=400, detail="Ungültige Einstellungen-Kategorie")

    conn.commit()
    conn.close()

    return {"message": f"{setting_type} erfolgreich aktualisiert"}

def get_business_time(token: str, date: str, start_time: str):
    """Prüft, ob die gewählte Uhrzeit innerhalb der Öffnungszeiten liegt."""

    conn = get_db_connection()

    # Prüfen, ob das Token existiert
    token_check = conn.execute("""
        SELECT customer_id FROM customer_updates WHERE token = ?
    """, (token,)).fetchone()

    if not token_check:
        conn.close()
        raise HTTPException(status_code=401, detail="Ungültiges Token")

    # Datum & Uhrzeit verarbeiten
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")  # Datum in Objekt umwandeln
        start_time_obj = datetime.strptime(start_time, "%H:%M").time()  # Zeit in Objekt umwandeln
    except ValueError:
        conn.close()
        raise HTTPException(status_code=400, detail="Ungültiges Datums- oder Zeitformat")

    # Wochentag aus Datum extrahieren
    weekday_map = {
        0: "Montag", 1: "Dienstag", 2: "Mittwoch", 3: "Donnerstag",
        4: "Freitag", 5: "Samstag", 6: "Sonntag"
    }
    weekday = weekday_map[date_obj.weekday()]

    # Öffnungszeiten für den gewählten Tag abrufen
    business_hours = conn.execute("""
        SELECT open_time, close_time, is_open 
        FROM opening_hours 
        WHERE setting_id = (SELECT id FROM settings WHERE category = 'business_hours')
        AND day_of_week = ?
    """, (weekday,)).fetchone()

    # Extra Kosten abrufen
    extra_costs = conn.execute("""
        SELECT value FROM settings WHERE category = 'appointment_settings' AND key = 'extra_cost'
    """).fetchone()

    conn.close()

    # Extra-Kosten aus der Datenbank holen (Standardwert: 50.0 falls nicht gesetzt)
    extra_cost = float(extra_costs["value"]) if extra_costs and extra_costs["value"] is not None else 50.0

    if not business_hours:
        raise HTTPException(status_code=404, detail=f"Keine Öffnungszeiten für {weekday} gefunden.")

    # Wenn an diesem Tag geschlossen ist
    if not business_hours["is_open"]:
        return {
            "requested_time": {"date": date, "start_time": start_time, "valid_timeframe": False},
            "message": f"Am {weekday} ist geschlossen.",
            "extra_cost": extra_cost
        }

    # Öffnungs- und Schließzeiten sicher extrahieren
    open_time_str = business_hours["open_time"]
    close_time_str = business_hours["close_time"]

    if not open_time_str or not close_time_str:
        raise HTTPException(status_code=500, detail="Fehlende Öffnungszeiten in der Datenbank.")

    try:
        open_time = datetime.strptime(open_time_str, "%H:%M").time()
        close_time = datetime.strptime(close_time_str, "%H:%M").time()
    except ValueError:
        raise HTTPException(status_code=500, detail="Ungültiges Zeitformat in der Datenbank.")

    # Prüfen, ob Startzeit innerhalb der Öffnungszeiten liegt
    if open_time <= start_time_obj <= close_time:
        return {
            "requested_time": {"date": date, "start_time": start_time, "valid_timeframe": True},
            "message": "Ihr Termin wurde gebucht."
        }
    else:
        return {
            "requested_time": {"date": date, "start_time": start_time, "valid_timeframe": False},
            "message": "Ihr gewähltes Zeitfenster liegt außerhalb der regulären Öffnungszeiten.",
            "extra_cost": extra_cost
        }


