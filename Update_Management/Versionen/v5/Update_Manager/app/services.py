from fastapi import HTTPException
from .database import get_db_connection
from typing import Optional, List
import uuid

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

def list_customers():
    """Gibt alle Kunden zurück."""
    conn = get_db_connection()
    customers = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()
    return [dict(row) for row in customers]

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

def list_updates():
    """Gibt alle Updates zurück."""
    conn = get_db_connection()
    updates = conn.execute("SELECT id, title, description FROM updates").fetchall()
    conn.close()
    return [dict(update) for update in updates]

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