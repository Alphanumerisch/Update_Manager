from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, constr, conint
import sqlite3
import uuid
#from typing import Optional
from typing import List, Optional
from passlib.context import CryptContext
import jwt
import datetime
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(docs_url="/api/docs",  
    redoc_url="/api/redoc",  
    openapi_url="/api/openapi.json"  
    
    )

DB_PATH = "database.db"


# Hilfsfunktion für DB-Verbindung
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# **Model für JSON-Requests**
class RequestModel(BaseModel):
    action: str
    name: Optional[constr(max_length=255)] = None
    email: Optional[constr(max_length=255)] = None
    title: Optional[constr(max_length=255)] = None
    description: Optional[constr(max_length=255)] = None
    token: Optional[constr(max_length=255)] = None
    selected_date: Optional[constr(max_length=255)] = None
    note: Optional[constr(max_length=255)] = None
    update_id: Optional[conint(ge=1, le=1000000)] = None
    customer_ids: Optional[List[conint(ge=1, le=1000000)]] = None
    customer_id: Optional[conint(ge=1, le=1000000)] = None
    confirm: bool = False 

    
@app.post("/api")
def api_handler(request: RequestModel):
    if request.action == "add_customer":
        return add_customer(request.name, request.email)
    elif request.action == "list_customers":
        return list_customers()
    elif request.action == "create_update":
        return create_update(request.title, request.description)
    elif request.action == "send_update":
        return send_update(request.update_id, request.customer_ids, request.confirm)
    elif request.action == "select_date":
        return select_date(request.token, request.selected_date, request.note)
    elif request.action == "dashboard":
        return dashboard()
    elif request.action == "delete_update":
        return delete_update(request.update_id)  # Neuer Endpunkt
    elif request.action == "delete_customer":
        return delete_customer(request.customer_id)  # Neuer Endpunkt
    elif request.action == "list_updates":
        return list_updates()
    else:
        raise HTTPException(status_code=400, detail="Ungültige Aktion")

# **Liste aller Updates abrufen**
def list_updates():
    conn = get_db_connection()
    updates = conn.execute("SELECT id, title, description FROM updates").fetchall()
    conn.close()
    return [dict(update) for update in updates]
    
# **1. Kunde hinzufügen**
def add_customer(name: Optional[str], email: Optional[str]):
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

# **2. Kundenliste abrufen**
def list_customers():
    conn = get_db_connection()
    customers = conn.execute("SELECT * FROM customers").fetchall()
    conn.close()
    return [dict(row) for row in customers]

# **3. Update erstellen**
def create_update(title: Optional[str], description: Optional[str]):
    if not title or not description:
        raise HTTPException(status_code=400, detail="Titel und Beschreibung erforderlich")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO updates (title, description) VALUES (?, ?)", (title, description))
    update_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"message": "Update erstellt", "update_id": update_id}

# **4. Update an Kunden senden & Token generieren**
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

# **5. Kundenseite anzeigen (Token-Validierung)**
@app.get("/customer_page")
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

    # Falls Kunde schon einen Termin gewählt hat, weisen wir darauf hin
    if customer["selected_date"]:
        response["message"] = "Ein Termin wurde bereits gewählt. Möchten Sie ihn ändern?"

    return response


# **6. Kunde wählt Termin**
def select_date(token: str, selected_date: str, note: Optional[str] = None):
    if not token or not selected_date:
        raise HTTPException(status_code=400, detail="Token und Datum erforderlich")

    # Debugging: Eingehenden Wert von `note` ausgeben
    print(f"DEBUG: `note` empfangen von API: {note}")

    conn = get_db_connection()

    existing_entry = conn.execute(
        "SELECT id FROM customer_updates WHERE token = ?", (token,)
    ).fetchone()

    if not existing_entry:
        conn.close()
        raise HTTPException(status_code=400, detail="Ungültiger Token")

    # Falls `note` nicht übergeben wurde, setze sie auf `NULL`
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


# **6.1 Updates Löschen**

def delete_update(update_id: int):
    if not update_id:
        raise HTTPException(status_code=400, detail="Update-ID erforderlich")

    conn = get_db_connection()

    # Überprüfen, ob das Update existiert
    update_exists = conn.execute("SELECT id FROM updates WHERE id = ?", (update_id,)).fetchone()
    if not update_exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Update nicht gefunden")

    # Zuerst alle zugehörigen `customer_updates` löschen (Foreign Key Restriction vermeiden)
    conn.execute("DELETE FROM customer_updates WHERE update_id = ?", (update_id,))
    # Dann das eigentliche Update löschen
    conn.execute("DELETE FROM updates WHERE id = ?", (update_id,))
    
    conn.commit()
    conn.close()

    return {"message": f"Update mit ID {update_id} wurde gelöscht"}



# **7. Dashboard anzeigen**
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

# **8. Kunde löschen**
def delete_customer(customer_id: int):
    if not customer_id:
        raise HTTPException(status_code=400, detail="Customer-ID erforderlich")

    conn = get_db_connection()

    # Prüfen, ob der Kunde existiert
    customer_exists = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if not customer_exists:
        conn.close()
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    # Lösche den Kunden (alle zugehörigen `customer_updates` werden durch `ON DELETE CASCADE` automatisch gelöscht)
    conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()

    return {"message": f"Kunde mit ID {customer_id} wurde gelöscht"}


