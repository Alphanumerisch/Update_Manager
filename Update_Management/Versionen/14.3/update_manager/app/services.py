import os
import sys
import uuid
import jwt
import hashlib
import logging
import smtplib
import sqlite3
import datetime
from datetime import datetime, timedelta
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException, Depends, Body, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from .database import get_db_connection
from app.config import ROLE_PERMISSIONS, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MIN, REFRESH_TOKEN_EXPIRE_DAYS
from fastapi import Body
from app.models import BusinessTimeRequest, SelectDateRequest

# FastAPI Security Bearer
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()




def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Holt Benutzerinformationen aus dem JWT-Token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Kein Token gefunden")

    token = credentials.credentials  # 🔹 Extrahiere Token korrekt
    token_data = decode_token(token)  # 🔹 Token dekodieren

    if not token_data:
        raise HTTPException(status_code=401, detail="Ungültiges Token")

    return {
        "id": token_data.get("user_id"),
        "name": token_data.get("name"),
        "role": token_data.get("role"),
    }

def invalidate_token(user_id: int):
    #Macht das Token sofort ungültig."""
    invalid_token.add(user_id)

# Passwort-Hashing
def hash_password(password: str) -> str:
    """Erstellt einen sicheren bcrypt-Hash des Passworts."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 🔐 JWT-Token erstellen (Access & Refresh)
def create_token(user_id: int, name: str, role: str):
    """Erstellt ein JWT-Access-Token & ein Refresh-Token mit Sicherheitsverbesserungen"""

    now = datetime.utcnow()

    # 🟢 Access-Token (15 Min gültig)
    access_token_payload = {
        "sub": str(user_id),
        "name": name,
        "role": role,
        "iat": now,  # Zeitpunkt der Erstellung
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN),
        "jti": str(uuid.uuid4())  # Eindeutige Token-ID für Tracking/Blacklist
    }
    access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    # 🔄 Refresh-Token (7 Tage gültig)
    refresh_token_payload = {
        "sub": str(user_id),
        "name": name,
        "role": role,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4())  # Eindeutige ID für mögliche Blacklist
    }
    refresh_token = jwt.encode(refresh_token_payload, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": access_token, "refresh_token": refresh_token}

# Token entschlüsseln
def decode_token(token: str):
    """JWT Token entschlüsseln und Benutzer- oder Kundeninfos extrahieren"""

    if not token:
        print("⛔ decode_token: Kein Token erhalten!")  # Debugging
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        print(f"🔍 decode_token: Token-Dekodierung: {payload}", file=sys.stderr)

        # **Unterscheidung zwischen Benutzer-JWT & Kunden-JWT**
        if "customer_id" in payload and "update_id" in payload:
            return {
                "customer_id": payload["customer_id"],
                "update_id": payload["update_id"],
                "role": "customer"  # **Kunde bekommt `customer` als Rolle**
            }
        else:
            return {
                "user_id": payload.get("sub"),
                "role": payload.get("role"),
                "name": payload.get("name")
            }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token abgelaufen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ungültiges Token")

def check_permission(allowed_roles: str, token: str = Depends(security)):
    """Prüft, ob der Benutzer die erforderliche Rolle hat."""
    user_data = decode_token(token.credentials)
    user_role = user_data.get("role")

    if user_role not in allowed_roles and user_role != "admin":
        raise HTTPException(status_code=403, detail="Zugriff verweigert")
    
    return user_data  # Gibt Benutzerinformationen zurück

# Benutzer registrieren
def register_user(name: str, email: str, password: str, role: str):
    """Registriert einen neuen Benutzer mit einer bestimmten Rolle."""

    # Eingaben validieren
    if not name or not email or not password or not role:
        raise HTTPException(status_code=400, detail="Alle Felder erforderlich")

    # Zulässige Rollen prüfen
    allowed_roles = ["admin", "user", "viewer"]
    if role.lower() not in allowed_roles:
        raise HTTPException(status_code=400, detail="Ungültige Rolle. Erlaubt: admin, user, viewer")

    # Passwort hashen
    hashed_password = hash_password(password)
    conn = get_db_connection()
    
    try:
        # Neuen Benutzer in die DB einfügen mit Rolle
        conn.execute("INSERT INTO user (name, email, password, role) VALUES (?, ?, ?, ?)", 
                     (name, email, hashed_password, role.lower()))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Benutzer existiert bereits")
    finally:
        conn.close()

    return {"message": f"Benutzer {name} erfolgreich registriert mit Rolle {role}"}

#Login
def login(email: str, password: str, response: Response):
    """Meldet den Benutzer an und gibt ein JWT-Token zurück."""
    
    conn = get_db_connection()
    user = conn.execute("SELECT id, name, role, password FROM user WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Falsche Anmeldedaten")

    # JWT erstellen
    tokens = create_token(user["id"], user["name"], user["role"])
    
    # Setze das Token als Cookie
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,  # Verhindert Zugriff durch JavaScript
        secure=False,  # Nur über HTTPS senden
        samesite="Lax"
        
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,  # Verhindert Zugriff durch JavaScript
        secure=False,  # Nur über HTTPS senden
        samesite="Lax",
        
    )

    return {"message": "Login erfolgreich", "Token": tokens}

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
def create_update(title: str, description: str, user_id: int):
    """Erstellt ein neues Update mit Ersteller-ID (creator_id)."""
    if not title or not description:
        raise HTTPException(status_code=400, detail="Titel und Beschreibung erforderlich")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO updates (title, description, creator_id) VALUES (?, ?, ?)", 
            (title, description, user_id)
        )
        update_id = cursor.lastrowid
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Datenbankfehler: {str(e)}")
    finally:
        conn.close()

    return {"message": "Update erstellt", "update_id": update_id, "creator_id": user_id}

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
def delete_update(update_id: int, user_id: int, role: str):
    """Löscht ein Update, wenn der Benutzer berechtigt ist."""

    conn = get_db_connection()
    cursor = conn.cursor()

    # 🟢 Debugging: Zeige den aktuellen Stand des Updates
    cursor.execute("SELECT id, title, creator_id FROM updates WHERE id = ?", (update_id,))
    update = cursor.fetchone()

    if not update:
        conn.close()
        raise HTTPException(status_code=404, detail="Update nicht gefunden")

    creator_id = update["creator_id"]

    # 🔍 Debugging: Zeige die relevanten Werte
    print(f"🛠 DEBUG: Versuch, Update zu löschen -> update_id={update_id}, user_id={user_id}, role={role}, creator_id={creator_id}", file=sys.stderr)
    sys.stderr.flush()

    # 🎭 Berechtigungsprüfung
    if role != "admin" and int(creator_id) != int(user_id):
        conn.close()
        raise HTTPException(status_code=403, detail="Keine Berechtigung, dieses Update zu löschen")

    # 🟢 Debugging: Prüfe, ob das DELETE ausgeführt wird
    cursor.execute("DELETE FROM updates WHERE id = ?", (update_id,))
    rows_deleted = cursor.rowcount  # Anzahl gelöschter Zeilen speichern
    conn.commit()

    print(f"✅ DEBUG: Update gelöscht (rows_deleted={rows_deleted})", file=sys.stderr)
    sys.stderr.flush()

    conn.close()

    if rows_deleted == 0:
        raise HTTPException(status_code=500, detail="Löschen fehlgeschlagen, kein Update entfernt")

    return {"message": "Update gelöscht"}

# Dashboard laden
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Alle Updates und Kunden in einer einzigen Abfrage holen
    cursor.execute("""
        SELECT u.id, u.title, u.description, c.name, c.email, cu.status, cu.selected_date, cu.note
        FROM updates u
        JOIN customer_updates cu ON u.id = cu.update_id
        JOIN customers c ON cu.customer_id = c.id
        ORDER BY u.id, c.name
    """)

    rows = cursor.fetchall()
    conn.close()

    updates_dict = {}

    # Daten in die neue Struktur bringen
    for row in rows:
        update_id = row["id"]
        if update_id not in updates_dict:
            updates_dict[update_id] = {
                "id": update_id,
                "title": row["title"],
                "description": row["description"],
                "customers": []
            }

        updates_dict[update_id]["customers"].append({
            "name": row["name"],
            "email": row["email"],
            "status": row["status"],
            "selected_date": row["selected_date"],
            "note": row["note"]
        })

    return {"updates": list(updates_dict.values())}

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

def select_date(request: SelectDateRequest, credentials: HTTPAuthorizationCredentials = Depends(security) ):
    """Speichert das vom Kunden gewählte Datum mit Notiz."""

    # 🔓 Token dekodieren & Benutzerinformationen abrufen
    token_data = decode_token(credentials.credentials)
    customer_id = token_data.get("customer_id")

    if not customer_id:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    # 🛠 Überprüfen, ob die erforderlichen Werte vorhanden sind
    if not request.selected_date:
        raise HTTPException(status_code=400, detail="Datum erforderlich")

    conn = get_db_connection()

    # 🔍 Prüfen, ob der Kunde in `customer_updates` existiert
    existing_entry = conn.execute(
        "SELECT id FROM customer_updates WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()

    if not existing_entry:
        conn.close()
        raise HTTPException(status_code=400, detail="Ungültiger Kunde oder kein zugehöriges Update gefunden")

    # 📌 Standard-Notiz setzen, falls nicht übermittelt
    note = request.note if request.note else "KEINE_NOTIZ_ÜBERMITTELT"

    # 💾 Termin speichern
    result = conn.execute(
        """
        UPDATE customer_updates 
        SET selected_date = ?, note = ?, status = 'bestätigt' 
        WHERE customer_id = ?
        """,
        (request.selected_date, note, customer_id),
    )

    conn.commit()
    conn.close()

    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="Fehler beim Speichern des Termins")

    return {"message": "Termin erfolgreich gespeichert", "note": note}
    
#  Update an Kunden senden
def send_update(update_id: int):
    """Sendet eine E-Mail mit einem dynamischen JWT-Token an alle Kunden eines Updates"""

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

    # SMTP-Einstellungen abrufen
    email_settings = conn.execute("""
        SELECT smtp_server, smtp_server_port, smtp_user, smtp_pw, sender_mail 
        FROM email_settings 
        WHERE setting_id = (SELECT id FROM settings WHERE category = 'email')
        LIMIT 1
    """).fetchone()

    if not email_settings:
        conn.close()
        raise HTTPException(status_code=500, detail="Keine SMTP-Einstellungen gefunden")

    # Kunden abrufen, die mit dem Update verknüpft sind
    customers = conn.execute("""
        SELECT c.id, c.name, c.email
        FROM customer_updates cu
        JOIN customers c ON cu.customer_id = c.id
        WHERE cu.update_id = ?
    """, (update_id,)).fetchall()

    if not customers:
        conn.close()
        raise HTTPException(status_code=400, detail="Keine Kunden für dieses Update gefunden")

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
                # 🟢 JWT-Token generieren
                token = generate_customer_token(customer["id"], update_id)

                # 🟢 JWT-Token in die URL einfügen
                update_link = f"http://192.168.168.160/update?token={token}"

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

                Der Link ist **48 Stunden gültig**.

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
            
            conn.execute(
                "INSERT INTO customer_updates (customer_id, update_id) VALUES (?, ?)",
                (customer_id, update_id)
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

def get_business_time(request: BusinessTimeRequest, credentials: HTTPAuthorizationCredentials = Depends(security) ):
    """Prüft, ob die gewählte Uhrzeit innerhalb der Öffnungszeiten liegt."""

    # 🛠 Debugging
    print(f"🔑 get_business_time: Empfangener Token: {credentials.credentials}", file=sys.stderr)
    print(f"📅 get_business_time: Empfangene Daten: {request.date}, {request.start_time}", file=sys.stderr)
    sys.stderr.flush()

    if credentials is None:
        print("⛔ get_business_time: Kein Token im Header erhalten!", file=sys.stderr)
        raise HTTPException(status_code=401, detail="get_business_time: Nicht authentifiziert")

    print(f"🔑 get_business_time: Empfangener Token: {credentials.credentials}", file=sys.stderr)
    sys.stderr.flush()
    # 🔓 Token dekodieren & Benutzerinformationen abrufen
    token_data = decode_token(credentials.credentials)
    customer_id = token_data.get("customer_id")

    if not customer_id:
        raise HTTPException(status_code=401, detail="get_business_time: Nicht authentifiziert")

    conn = get_db_connection()

    # Datum & Uhrzeit verarbeiten
    try:
        date_obj = datetime.strptime(request.date, "%Y-%m-%d")  # Datum in Objekt umwandeln
        start_time_obj = datetime.strptime(request.start_time, "%H:%M").time()  # Zeit in Objekt umwandeln
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
            "requested_time": {"date": request.date, "start_time": request.start_time, "valid_timeframe": False},
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
            "requested_time": {"date": request.date, "start_time": request.start_time, "valid_timeframe": True},
            "message": "Termin kann gebucht werden."
        }
    else:
        return {
            "requested_time": {"date": request.date, "start_time": request.start_time, "valid_timeframe": False},
            "message": "Ihr gewähltes Zeitfenster liegt außerhalb der regulären Öffnungszeiten.",
            "extra_cost": extra_cost
        }

def get_update_info(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Gibt die Update-Informationen für den Kunden zurück"""

    if credentials is None:
        print("⛔ get_update_info: Kein Token im Header erhalten!", file=sys.stderr)
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")

    print(f"🔑 get_update_info: Empfangener Token: {credentials.credentials}", file=sys.stderr)
    sys.stderr.flush()

    # 🛠 Token entschlüsseln
    token_data = decode_token(credentials.credentials)

    if not token_data:
        raise HTTPException(status_code=401, detail="Ungültiges oder abgelaufenes Token")

    customer_id = token_data.get("customer_id")
    update_id = token_data.get("update_id")

    # 🔹 Berechtigungsprüfung (KEIN Admin/User-Check, sondern nur `customer_id` validieren!)
    if "get_update_info" not in ROLE_PERMISSIONS or "customer" not in ROLE_PERMISSIONS["get_update_info"]:
        raise HTTPException(status_code=403, detail="Zugriff verweigert")

    conn = get_db_connection()

    # 🔹 Kunden-Update-Daten abrufen (jetzt mit `customer_id` statt `token`)
    result = conn.execute("""
        SELECT 
            u.title, 
            u.description, 
            c.name AS customer_name,
            cu.selected_date
        FROM customer_updates cu
        JOIN updates u ON cu.update_id = u.id
        JOIN customers c ON cu.customer_id = c.id
        WHERE cu.customer_id = ? AND cu.update_id = ?
        LIMIT 1
    """, (customer_id, update_id)).fetchone()

    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Keine passenden Update-Infos gefunden")

    date_is_set = result["selected_date"] is not None

    return {
        "title": result["title"],
        "description": result["description"],
        "customer_name": result["customer_name"],
        "date_is_set": date_is_set,
        "selected_date": result["selected_date"] if date_is_set else None
    }

def generate_customer_token(customer_id: int, update_id: int) -> str:
    """Generiert ein JWT für den Kunden-Link"""
    expiration = datetime.utcnow() + timedelta(hours=48)  # 🔥 48h gültig
    payload = {
        "customer_id": customer_id,
        "update_id": update_id,
        "exp": expiration
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


