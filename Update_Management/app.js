document.addEventListener("DOMContentLoaded", function() {
     loadDashboard();
});

function loadDashboard() {
    fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'dashboard' })
    })
    .then(response => response.json())
    .then(data => {
        let content = document.getElementById("content");
        content.innerHTML = "<h2>Dashboard</h2>";

        let groupedUpdates = {};

        // Gruppiere Updates nach Update-ID
        data.forEach(update => {
            if (!groupedUpdates[update.update_id]) {
                groupedUpdates[update.update_id] = {
                    title: update.title,
                    customers: []
                };
            }
            groupedUpdates[update.update_id].customers.push(update);
        });

        // Erstelle eine eigene Tabelle für jede Update-ID
        Object.keys(groupedUpdates).forEach(update_id => {
            let updateData = groupedUpdates[update_id];

            // Abstand zwischen Tabellen
            let tableContainer = document.createElement("div");
            tableContainer.style.marginBottom = "30px"; // Mehr Abstand zwischen den Update-Tabellen

            let tableTitle = document.createElement("h3");
            tableTitle.innerText = `Update: ${updateData.title} (ID: ${update_id})`;
            tableContainer.appendChild(tableTitle);

            let table = document.createElement("table");

            let row;
            updateData.customers.forEach((customer, index) => {
                // Neue Zeile alle 4 Kunden
                if (index % 4 === 0) {
                    row = table.insertRow();
                }

                let cell = row.insertCell();
                cell.classList.add("customer-cell");
                cell.innerHTML = `
                    <b>${customer.name}</b> <br>
                    <button class="date-button">${customer.selected_date || "Kein Datum"}</button> <br>
                    ${customer.note || "-"} <br>
                    ${customer.selected_date ? "✅ Bestätigt" : "❌ Ausstehend"}
                `;
            });

            tableContainer.appendChild(table);
            content.appendChild(tableContainer);
        });
    })
    .catch(error => console.error("Fehler beim Laden des Dashboards:", error));
}
//
document.addEventListener("DOMContentLoaded", function() {
    loadDashboard();
});

// 🔹 Funktion zum Laden der Kundenliste & Hinzufügen des Buttons
function loadCustomers() {
    fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'list_customers' })
    })
    .then(response => response.json())
    .then(data => {
        let content = document.getElementById("content");

        // Kundenverwaltung mit "+ Kunde"-Button
        content.innerHTML = `
            <div class="customer-header">
                <h2>Kundenverwaltung</h2>
                <button id="addCustomerBtn" class="add-button">+ Kunde</button>
            </div>
        `;

        let addCustomerBtn = document.getElementById("addCustomerBtn");
        if (addCustomerBtn) {
            addCustomerBtn.addEventListener("click", showCustomerForm);
        } else {
            console.error("Fehler: Der Button '+ Kunde' wurde nicht gefunden.");
        }

        let table = document.createElement("table");
        table.innerHTML = `<tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Aktion</th>
        </tr>`;

        data.forEach(customer => {
            let row = table.insertRow();
            row.innerHTML = `
                <td>${customer.id}</td>
                <td>${customer.name}</td>
                <td>${customer.email}</td>
                <td><button class="delete-button" onclick="deleteCustomer(${customer.id})">Löschen</button></td>

            `;
        });

        content.appendChild(table);
    })
    .catch(error => console.error("Fehler beim Laden der Kunden:", error));
}

function showCustomerForm() {
    console.log("showCustomerForm() aufgerufen");

    // Falls das Formular bereits existiert, nicht erneut hinzufügen
    if (document.getElementById("customer-form-overlay")) return;

    let overlay = document.createElement("div");
    overlay.id = "customer-form-overlay";
    overlay.className = "overlay";

    let form = document.createElement("div");
    form.className = "customer-form";
    form.innerHTML = `
        <h3>Neuen Kunden hinzufügen</h3>
        <input type="text" id="customerName" placeholder="Name eingeben">
        <input type="email" id="customerEmail" placeholder="E-Mail eingeben">
        <span id="emailError" style="color: red; font-size: 12px; display: none;">Ungültige E-Mail-Adresse</span>
        <div class="form-buttons">
            <button id="saveCustomerBtn" disabled>Speichern</button>
            <button onclick="closeCustomerForm()">Abbrechen</button>
        </div>
    `;

    overlay.addEventListener("click", function(event) {
        if (event.target === overlay) {
            closeCustomerForm();
        }
    });

    overlay.appendChild(form);
    document.body.appendChild(overlay);
    overlay.style.display = "flex"; // Sicherstellen, dass das Formular sichtbar ist

    // E-Mail-Feld & "Speichern"-Button holen
    let emailInput = document.getElementById("customerEmail");
    let saveButton = document.getElementById("saveCustomerBtn");

    // Live-Validierung aktivieren
    emailInput.addEventListener("input", function () {
        validateEmailInput(emailInput, saveButton);
    });

    // Klick-Event für Speichern setzen
    saveButton.addEventListener("click", addCustomer);
}



// 🔹 Kundenformular schließen
function closeCustomerForm() {
    let overlay = document.getElementById("customer-form-overlay");
    if (overlay) {
        overlay.remove();
    }
}

function validateEmail(email) {
    let emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateEmailInput(emailInput, saveButton) {
    let emailError = document.getElementById("emailError");

    if (!validateEmail(emailInput.value)) {
        emailInput.style.border = "2px solid red";
        emailError.style.display = "block"; // Fehler anzeigen
        saveButton.disabled = true; // Speichern-Button deaktivieren
    } else {
        emailInput.style.border = "2px solid green";
        emailError.style.display = "none"; // Fehler ausblenden
        saveButton.disabled = false; // Speichern-Button aktivieren
    }
}


// Kunde hinzufügen (API-Call)
function addCustomer() {
    let name = document.getElementById("customerName").value.trim();
    let email = document.getElementById("customerEmail").value.trim();

    if (!name || !email) {
        alert("Bitte Name und E-Mail eingeben.");
        return;
    }

   // Letzte Validierung vor dem Absenden
    if (!validateEmail(email)) {
        alert("Bitte eine gültige E-Mail-Adresse eingeben.");
        return;
    }
    
    fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'add_customer', name: name, email: email })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        closeCustomerForm();
        loadCustomers(); // Aktualisiere die Liste
    })
    .catch(error => console.error("Fehler beim Hinzufügen des Kunden:", error));
}






//
function deleteCustomer(customerId) {
    if (!confirm("Möchtest du diesen Kunden wirklich löschen?")) return;
    
    fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'delete_customer', customer_id: customerId })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadCustomers(); // Aktualisiere die Liste nach dem Löschen
    })
    .catch(error => console.error("Fehler beim Löschen des Kunden:", error));
}

function loadUpdates() {
    fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'list_updates' })  // API-Action für Updates
    })
    .then(response => response.json())
    .then(data => {
        let content = document.getElementById("content");
        content.innerHTML = "<h2>Update-Verwaltung</h2>";

        let table = document.createElement("table");
        table.innerHTML = `<tr>
            <th>ID</th>
            <th>Title</th>
            <th>Description</th>
            <th>Aktion</th>
        </tr>`;

        data.forEach(update => {
            let row = table.insertRow();
            row.innerHTML = `
                <td>${update.id}</td>
                <td>${update.title}</td>
                <td>${update.description}</td>
                <td>
                    <button onclick="sendUpdate(${update.id})">Senden</button>
                    <button onclick="deleteUpdate(${update.id})">Löschen</button>
                </td>
            `;
        });
        content.appendChild(table);
    })
    .catch(error => console.error("Fehler beim Laden der Updates:", error));
}


