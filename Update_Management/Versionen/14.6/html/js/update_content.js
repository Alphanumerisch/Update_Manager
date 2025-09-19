/**
 * 🟢 Initialisiert die Updates-Ansicht.
 */
async function initUpdates() {
    console.log("📡 update_content.js: Initialisiere Updates-Verwaltung...");

    const updateContainer = document.getElementById("update-content");

    if (!updateContainer) {
        console.error("❌ update_content.js: Fehler - #update-content nicht gefunden!");
        return;
    }

    console.log("✅ update_content.js: #update-content gefunden, lade Daten...");
    await loadUpdates();
}

/**
 * 🟢 Lädt die Updates aus der API und zeigt sie an.
 */
async function loadUpdates() {
    try {
        console.log("📡 update_content.js: API-Request an /api...");
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "list_updates" }),
        });

        const data = await response.json();
        console.log("📡 update_content.js: API-Response:", data);

        if (!response.ok) throw new Error(data.detail || "Fehler beim Laden der Updates");

        const updatesArray = data.updates;
        if (!Array.isArray(updatesArray)) {
            console.error("❌ update_content.js: API hat kein gültiges 'updates'-Array zurückgegeben!", data);
            return;
        }
        window.updatesData = updatesArray;

        console.log("✅ update_content.js: Updates erfolgreich geladen:", updatesArray);
        renderUpdates(updatesArray);
    } catch (error) {
        console.error(`❌ update_content.js: Fehler beim Laden der Updates:`, error);
    }
}

/**
 * 🔹 Erstellt dynamisch die Update-Container mit Bootstrap.
 */
function renderUpdates(updates) {
    if (!Array.isArray(updates)) {
        console.error("❌ update_content.js: Fehler - 'updates' ist keine gültige Liste!", updates);
        return;
    }

    console.log("📡 update_content.js: Erstelle Update-Container für", updates.length, "Updates...");

    const updateContainer = document.getElementById("update-content");
    updateContainer.innerHTML = ""; // Vorherige Inhalte leeren

    updates.forEach(update => {
        console.log("📡 update_content.js: Erstelle Container für:", update);

        // Status umwandeln
        const statusText = update.updates_send ? "✅ Update gesendet" : "⚠ Update noch nicht gesendet";
        const statusClass = update.updates_send ? "text-success" : "text-danger";

        const updateCard = document.createElement("div");
        updateCard.classList.add("card", "mb-4", "shadow-sm");

        updateCard.innerHTML = `
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0"><i class="fas fa-file-alt"></i> ${update.title}</h5>
                <div>
                    <button class="btn btn-outline-secondary btn-sm edit-update-btn" data-id="${update.id}" title="Bearbeiten">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-sm delete-update-btn" data-id="${update.id}" title="Löschen">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <p><i class="fas fa-info-circle"></i> ${update.description}</p>
                <p class="${statusClass}"><i class="fas fa-check-circle"></i> ${statusText}</p>
                <h6><b>Kunden:</b></h6>
                <div class="row" id="update-${update.id}-customers"></div>
            </div>
        `;

        updateContainer.appendChild(updateCard);

        // Kunden für dieses Update rendern
        const customerContainer = document.getElementById(`update-${update.id}-customers`);
        update.customers.forEach(customer => {
            createCustomerCard(customerContainer, update.id, customer);
        });
    });

    console.log("✅ update_content.js: Updates erfolgreich dargestellt!");

    // Event-Listener für Bearbeiten & Löschen setzen
    document.querySelectorAll(".edit-update-btn").forEach(btn =>
        btn.addEventListener("click", event => {
            const updateId = event.currentTarget.dataset.id; // FIX: Sicherstellen, dass die ID vom Button stammt
            console.log(`📡 customer_content.js: Klicke auf Bearbeiten für Update ID ${updateId}...`);
            editUpdate(updateId);
        })
    );

    document.querySelectorAll(".delete-update-btn").forEach(btn =>
        btn.addEventListener("click", event => {
            const updateId = event.currentTarget.dataset.id; // FIX: Sicherstellen, dass die ID vom Button stammt
            console.log(`📡 customer_content.js: Klicke auf Löschen für Update ID ${updateId}...`);
            deleteUpdate(updateId);
        })
    );
}

/**
 * 🟢 Erstellt eine Kundenkarte innerhalb eines Updates.
 */
function createCustomerCard(container, updateId, customer) {
    console.log(`📡 update_content.js: Erstelle Kundenkarte für Update ${updateId} - Kunde:`, customer);

    const customerCard = document.createElement("div");
    customerCard.classList.add("col-md-4", "mb-3");

    customerCard.innerHTML = `
        <div class="card shadow-sm">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0"><i class="fas fa-user"></i> ${customer.name}</h6>
                <button class="btn btn-outline-danger btn-sm remove-customer-btn" data-update-id="${updateId}" data-customer-id="${customer.id}" title="Kunde entfernen">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="card-body">
                <p class="card-text">
                    <i class="fas fa-envelope"></i> ${customer.email}
                </p>
            </div>
        </div>
    `;

    container.appendChild(customerCard);
}

/**
 * Ersetzt den bisherigen Alert-Platzhalter in editUpdate() durch ein Bootstrap-Modal,
 * in dem der Update-Titel und die Beschreibung bearbeitet werden können.
 * Zusätzlich können Kunden dynamisch zugewiesen bzw. entfernt werden.
 */
function editUpdate(updateId) {
    console.log(`📡 update_content.js: Bearbeiten für Update ID ${updateId} angefordert...`);

    // Suche das Update in den global gespeicherten Daten
    const update = window.updatesData && window.updatesData.find(u => u.id == updateId);
    if (!update) {
        console.error(`❌ update_content.js: Update mit ID ${updateId} nicht gefunden!`);
        return;
    }

    // Lade alle Kunden via API
    fetchWithAuth("/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "list_customers" })
    })
    .then(response => response.json())
    .then(customersData => {
        const allCustomers = customersData["customer:"] || [];
        // Erstelle eine Liste der aktuell zugewiesenen Kunden-IDs
        const originalAssignedIds = update.customers.map(c => c.id);
        // Diese Liste wird in unserem Modal dynamisch verändert
        let assignedCustomerIds = [...originalAssignedIds];

        // Erstelle das Modal dynamisch, falls es noch nicht existiert
        let modalContainer = document.getElementById("editUpdateModal");
        if (!modalContainer) {
            modalContainer = document.createElement("div");
            modalContainer.id = "editUpdateModal";
            modalContainer.innerHTML = `
                <div class="modal fade" id="editUpdateModalDialog" tabindex="-1" aria-labelledby="editUpdateModalLabel" aria-hidden="true">
                  <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                      <div class="modal-header">
                        <h5 class="modal-title" id="editUpdateModalLabel">Update bearbeiten</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                      </div>
                      <div class="modal-body">
                        <form id="editUpdateForm">
                          <div class="mb-3">
                            <label for="updateTitle" class="form-label">Titel</label>
                            <input type="text" class="form-control" id="updateTitle" required>
                          </div>
                          <div class="mb-3">
                            <label for="updateDescription" class="form-label">Beschreibung</label>
                            <textarea class="form-control" id="updateDescription" rows="3" required></textarea>
                          </div>
                          <div class="mb-3">
                            <h6>Kunden zuweisen/entfernen</h6>
                            <div id="customerListContainer" class="list-group">
                              <!-- Dynamisch generierte Kundenliste -->
                            </div>
                          </div>
                        </form>
                      </div>
                      <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Abbrechen</button>
                        <button type="button" class="btn btn-primary" id="saveUpdateBtn">Speichern</button>
                      </div>
                    </div>
                  </div>
                </div>
            `;
            document.body.appendChild(modalContainer);
        }

        // Vorbefüllen der Formularfelder
        document.getElementById("updateTitle").value = update.title;
        document.getElementById("updateDescription").value = update.description;

        // Erstelle die Kundenliste im Modal
        const customerListContainer = document.getElementById("customerListContainer");
        customerListContainer.innerHTML = "";
        allCustomers.forEach(customer => {
            const isAssigned = assignedCustomerIds.includes(customer.id);
            const buttonIcon = isAssigned ? '–' : '+';
            const buttonClass = isAssigned ? 'btn-danger' : 'btn-success';
            const customerItem = document.createElement("div");
            customerItem.classList.add("list-group-item", "d-flex", "justify-content-between", "align-items-center");
            customerItem.innerHTML = `
                <span>${customer.name} (${customer.email})</span>
                <button type="button" class="btn ${buttonClass} btn-sm toggle-customer-btn" data-customer-id="${customer.id}">
                    ${buttonIcon}
                </button>
            `;
            customerListContainer.appendChild(customerItem);
        });

        // Event-Listener für die Toggle-Buttons (zum Hinzufügen/Entfernen)
        document.querySelectorAll(".toggle-customer-btn").forEach(btn => {
            btn.addEventListener("click", function() {
                const custId = parseInt(this.getAttribute("data-customer-id"));
                if (assignedCustomerIds.includes(custId)) {
                    // Kunde entfernen
                    assignedCustomerIds = assignedCustomerIds.filter(id => id !== custId);
                    this.textContent = '+';
                    this.classList.remove('btn-danger');
                    this.classList.add('btn-success');
                    console.log(`🔄 update_content.js: Kunde ${custId} entfernt.`);
                } else {
                    // Kunde hinzufügen
                    assignedCustomerIds.push(custId);
                    this.textContent = '–';
                    this.classList.remove('btn-success');
                    this.classList.add('btn-danger');
                    console.log(`🔄 update_content.js: Kunde ${custId} hinzugefügt.`);
                }
            });
        });

        // Bootstrap Modal anzeigen
        const modalElement = new bootstrap.Modal(document.getElementById("editUpdateModalDialog"));
        modalElement.show();

        // Speichern-Button: Beim Klicken wird der API-Request zum Aktualisieren ausgeführt
        document.getElementById("saveUpdateBtn").onclick = function() {
            const newTitle = document.getElementById("updateTitle").value.trim();
            const newDescription = document.getElementById("updateDescription").value.trim();

            if (!newTitle || !newDescription) {
                alert("Titel und Beschreibung dürfen nicht leer sein!");
                return;
            }

            console.log(`🔄 update_content.js: Speichere Update ${updateId} mit neuen Daten...`);

            // Berechne die Differenz: Welche Kunden sind neu hinzugefügt, welche wurden entfernt?
            const addIds = assignedCustomerIds.filter(id => !originalAssignedIds.includes(id));
            const delIds = originalAssignedIds.filter(id => !assignedCustomerIds.includes(id));

            // API-Request an update_update
            fetchWithAuth("/api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "update_update",
                    update_id: updateId,
                    title: newTitle,
                    description: newDescription,
                    add_customer_id: addIds,
                    del_customer_id: delIds
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.message) {
                    throw new Error(data.detail || "Unbekannter Fehler");
                }
                console.log(`✅ update_content.js: Update erfolgreich aktualisiert:`, data);
                modalElement.hide();
                loadUpdates(); // Aktualisiere die Update-Ansicht
            })
            .catch(error => {
                console.error("❌ update_content.js: Fehler beim Aktualisieren des Updates:", error);
                alert("Fehler beim Aktualisieren des Updates. Bitte erneut versuchen.");
            });
        };
    })
    .catch(error => {
        console.error("❌ update_content.js: Fehler beim Abrufen der Kundenliste:", error);
    });
}



/**
 * ❌ Update löschen
 */
async function deleteUpdate(updateId) {
    if (!confirm("Möchtest du dieses Update wirklich löschen?")) return;

    try {
        console.log(`📡 update_content.js: Lösche Update ${updateId}...`);
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "delete_update", update_id: updateId }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Fehler beim Löschen des Updates");

        console.log(`✅ update_content.js: Update ${updateId} gelöscht.`);
        loadUpdates(); // Updates neu laden
    } catch (error) {
        console.error(`❌ update_content.js: Fehler beim Löschen des Updates:`, error);
    }
}

/**
 * ❌ Kunde aus Update entfernen (Platzhalter)
 */
async function removeCustomerFromUpdate(updateId, customerId) {
    if (!confirm(`Möchtest du Kunde ${customerId} aus Update ${updateId} entfernen?`)) return;

    try {
        console.log(`📡 update_content.js: Entferne Kunde ${customerId} aus Update ${updateId}...`);
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "remove_customer_from_update", update_id: updateId, customer_id: customerId }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Fehler beim Entfernen des Kunden");

        console.log(`✅ update_content.js: Kunde ${customerId} aus Update ${updateId} entfernt.`);
        loadUpdates(); // Updates neu laden
    } catch (error) {
        console.error(`❌ update_content.js: Fehler beim Entfernen des Kunden:`, error);
    }
}
