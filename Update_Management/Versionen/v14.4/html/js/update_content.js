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
 * 📝 Update bearbeiten (Platzhalter)
 */
function editUpdate(updateId) {
    alert(`Update mit ID ${updateId} bearbeiten...`);
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
