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
    
    updates = conn.execute("SELECT id, title, description FROM updates").fetchall()
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
def send_update(update_id: int, customer_ids: Optional[List[int]] = None, confirm: bool = False):
    if not update_id:
        raise HTTPException(status_code=400, detail="Update-ID erforderlich")

    conn = get_db_connection()

    # Prüfen, ob die `update_id` existiert
    update_exists = conn.execute("SELECT id, title, description FROM updates WHERE id = ?", (update_id,)).fetchone()
    
    if update_exists is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Update-ID existiert nicht")

    # Neu: Konvertiere das Ergebnis in ein Dictionary, um direkte Zugriffe zu vermeiden
    update_info = dict(update_exists)

    # Prüfen, ob bereits geplante Updates für diese `update_id` existieren
    existing_entries = conn.execute("SELECT COUNT(*) as count FROM customer_updates WHERE update_id = ?", (update_id,)).fetchone()
    if existing_entries["count"] > 0:
        conn.close()
        raise HTTPException(status_code=409, detail=f"Es gibt bereits geplante Updates für update_id {update_id}.")

    # **Wichtiger Fix: Sicherstellen, dass `customers` immer existiert**
    if customer_ids is None:
        customers = conn.execute("SELECT id, name, email FROM customers").fetchall()
    else:
        placeholders = ",".join(["?"] * len(customer_ids))
        query = f"SELECT id, name, email FROM customers WHERE id IN ({placeholders})"
        customers = conn.execute(query, tuple(customer_ids)).fetchall()

    if confirm:
        conn.close()
        return {
            "message": "Bitte bestätigen Sie das Senden, bevor die Links erstellt werden.",
            "update_info": {
                "update_id": update_info["id"],
                "title": update_info["title"],
                "description": update_info["description"]
            },
            "customers": [dict(c) for c in customers]
        }

    # Falls `confirm: false`, dann Update-Links erstellen
    update_links = []
    for customer in customers:  # **Jetzt existiert `customers` immer**
        token = str(uuid.uuid4())[:16]
        conn.execute(
            "INSERT INTO customer_updates (customer_id, update_id, token) VALUES (?, ?, ?)",
            (customer["id"], update_id, token),
        )
        update_links.append({
            "customer_id": customer["id"],
            "name": customer["name"],
            "email": customer["email"],
            "link": f"https://example.com/update?token={token}"
        })

    conn.commit()
    conn.close()

    return {"message": "Update-Links erstellt", "links": update_links}

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