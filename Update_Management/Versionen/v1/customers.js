// Funktion zum Laden der Kundenliste & Hinzufügen des Buttons
export function loadCustomers() {
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

// Kunde hinzufügen - Formular
export function showCustomerForm() {
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



//Kundenformular schließen
export function closeCustomerForm() {
    let overlay = document.getElementById("customer-form-overlay");
    if (overlay) {
        overlay.remove();
    }
}
// E-Mail Eingabe Prüfen 
export function validateEmail(email) {
    let emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// E-Mail Eingabe Prüfen 
export function validateEmailInput(emailInput, saveButton) {
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
export function addCustomer() {
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






// Kunde löschen (API-Call)
export function deleteCustomer(customerId) {
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