document.addEventListener("DOMContentLoaded", async () => {
    console.log("📡 Lade Kundendaten...");

    // Container für Kundeninhalte
    const customerContainer = document.getElementById("customer-content");
    customerContainer.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2>Kundenverwaltung</h2>
            <button id="add-customer-btn" class="btn btn-success">
                <i class="fas fa-plus"></i> Kunde hinzufügen
            </button>
        </div>
        <div id="customer-list" class="row"></div>
    `;

    // "+ Kunde" Button Event-Listener
    document.getElementById("add-customer-btn").addEventListener("click", () => {
        alert("Hier könnte ein Kunden-Formular erscheinen.");
    });

    // Kunden laden & anzeigen
    await loadCustomers();
});

/**
 * 🟢 Lädt die Kunden aus der API und zeigt sie als Cards an.
 */
async function loadCustomers() {
    try {
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "list_customers" }),
        });

        const data = await response.json();
        console.log("🟡 API Rohdaten:", data);

        if (!response.ok) throw new Error(data.detail || "Fehler beim Laden der Kunden");

        // ❌ Falscher API-Response Key abfangen
        const customersArray = data.customers || data["customer:"] || [];

        console.log("🔍 Verarbeitete Kunden:", customersArray);

        if (customersArray.length === 0) {
            console.warn("⚠ Keine Kunden gefunden.");
            return;
        }

        renderCustomers(customersArray);
    } catch (error) {
        console.error("❌ Fehler beim Laden der Kunden:", error);
    }
}


/**
 * 🔹 Erstellt dynamisch die Kundenkarten.
 */
function renderCustomers(customers) {
    const customerList = document.getElementById("customer-list");
    customerList.innerHTML = "";

    customers.forEach(customer => {
        const customerCard = document.createElement("div");
        customerCard.classList.add("col-md-4", "mb-3");

        customerCard.innerHTML = `
            <div class="card shadow-sm">
                <div class="card-body">
                    <h5 class="card-title">
                        <i class="fas fa-user"></i> ${customer.name}
                    </h5>
                    <p class="card-text">
                        <i class="fas fa-envelope"></i> ${customer.email}
                    </p>
                    <div class="d-flex justify-content-between">
                        <button class="btn btn-primary btn-sm edit-btn" data-id="${customer.id}">
                            <i class="fas fa-edit"></i> Bearbeiten
                        </button>
                        <button class="btn btn-danger btn-sm delete-btn" data-id="${customer.id}">
                            <i class="fas fa-trash-alt"></i> Löschen
                        </button>
                    </div>
                </div>
            </div>
        `;

        customerList.appendChild(customerCard);
    });

    // Event-Listener für Bearbeiten & Löschen setzen
    document.querySelectorAll(".edit-btn").forEach(btn =>
        btn.addEventListener("click", event => editCustomer(event.target.dataset.id))
    );

    document.querySelectorAll(".delete-btn").forEach(btn =>
        btn.addEventListener("click", event => deleteCustomer(event.target.dataset.id))
    );

    console.log("✅ Kunden erfolgreich gerendert!");
}

/**
 * 📝 Kunde bearbeiten
 */
function editCustomer(customerId) {
    alert(`Kunde mit ID ${customerId} bearbeiten...`);
    // Hier könnte ein Bearbeitungsformular aufgerufen werden.
}

/**
 * ❌ Kunde löschen
 */
async function deleteCustomer(customerId) {
    if (!confirm("Möchtest du diesen Kunden wirklich löschen?")) return;

    try {
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "delete_customer", customer_id: customerId }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Fehler beim Löschen des Kunden");

        console.log(`✅ Kunde ${customerId} gelöscht.`);
        loadCustomers(); // Kundenliste neu laden
    } catch (error) {
        console.error("❌ Fehler beim Löschen des Kunden:", error);
    }
}
