/**
 * 🟢 Initialisiert die Kundenverwaltung. Wird nach dem Laden des Moduls aufgerufen.
 */
async function initCustomers() {
    console.log("📡 customer_content.js: Initialisiere Kundenverwaltung...");

    const customerContainer = document.getElementById("customer-content");

    if (!customerContainer) {
        console.error("❌ customer_content.js: Fehler - #customer-content nicht gefunden!");
        return;
    }

    console.log("✅ customer_content.js: #customer-content gefunden, lade Daten...");
    await loadCustomers();
}

/**
 * 🟢 Lädt die Kunden aus der API und zeigt sie als Bootstrap Cards an.
 */
async function loadCustomers() {
    try {
        console.log("📡 customer_content.js: API-Request an /api...");
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "list_customers" }),
        });

        const data = await response.json();
        console.log("📡 customer_content.js: API-Response:", data);

        if (!response.ok) throw new Error(data.detail || "Fehler beim Laden der Kunden");

        // ✅ Fix: Falls API `customer:` zurückgibt, umbenennen in `customers`
        const customersArray = data["customer:"];
        if (!Array.isArray(customersArray)) {
            console.error("❌ customer_content.js: API hat kein gültiges 'customers'-Array zurückgegeben!", data);
            return;
        }

        console.log("✅ customer_content.js: Kunden erfolgreich geladen:", customersArray);
        renderCustomers(customersArray);
    } catch (error) {
        console.error(`❌ customer_content.js: Fehler beim Laden der Kunden:`, error);
    }
}

/**
 * 🔹 Erstellt dynamisch die Kundenkarten mit Bootstrap.
 */
function renderCustomers(customers) {
    if (!Array.isArray(customers)) {
        console.error("❌ customer_content.js: Fehler - 'customers' ist keine gültige Liste!", customers);
        return;
    }

    console.log("📡 customer_content.js: Erstelle Kundenkarten für", customers.length, "Kunden...");

    const customerList = document.getElementById("customer-content");
    customerList.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h2>Kundenverwaltung</h2>
            <button id="add-customer-btn" class="btn btn-success">
                <i class="fas fa-plus"></i> Kunde hinzufügen
            </button>
        </div>
        <div id="customer-list" class="row"></div>
    `;

    document.getElementById("add-customer-btn").addEventListener("click", () => {
        alert("Hier könnte ein Kunden-Formular erscheinen.");
    });

    const customerCardsContainer = document.getElementById("customer-list");

    customers.forEach(customer => {
        console.log("📡 customer_content.js: Erstelle Karte für:", customer);

        const customerCard = document.createElement("div");
        customerCard.classList.add("col-md-4", "mb-3");

        customerCard.innerHTML = `
            <div class="card shadow-sm">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-user"></i> ${customer.name}</h5>
                    <div>
                        <button class="btn btn-outline-secondary btn-sm edit-btn" data-id="${customer.id}" title="Bearbeiten">
                            <i class="fas fa-cog"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm delete-btn" data-id="${customer.id}" title="Löschen">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <p class="card-text">
                        <i class="fas fa-envelope"></i> ${customer.email}
                    </p>
                </div>
            </div>
        `;

        customerCardsContainer.appendChild(customerCard);
    });

    console.log("✅ customer_content.js: Kundenkarten erfolgreich dargestellt!");

    document.querySelectorAll(".edit-btn").forEach(btn =>
        btn.addEventListener("click", event => {
            const customerId = event.currentTarget.dataset.id; // FIX: Sicherstellen, dass die ID vom Button stammt
            console.log(`📡 customer_content.js: Klicke auf Bearbeiten für Kunde ID ${customerId}...`);
            editCustomer(customerId);
        })
    );

    document.querySelectorAll(".delete-btn").forEach(btn =>
        btn.addEventListener("click", event => {
            const customerId = event.currentTarget.dataset.id; // FIX: Sicherstellen, dass die ID vom Button stammt
            console.log(`📡 customer_content.js: Klicke auf Löschen für Kunde ID ${customerId}...`);
            deleteCustomer(customerId);
        })
    );
    
}

/**
 * 📝 Kunde bearbeiten (Platzhalter)
 */
function editCustomer(customerId) {
    alert(`Kunde mit ID ${customerId} bearbeiten...`);
}

/**
 * ❌ Kunde löschen
 */
async function deleteCustomer(customerId) {
    if (!confirm("Möchtest du diesen Kunden wirklich löschen?")) return;

    try {
        console.log(`📡 customer_content.js: Lösche Kunde ${customerId}...`);
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "delete_customer", customer_id: customerId }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Fehler beim Löschen des Kunden");

        console.log(`✅ customer_content.js: Kunde ${customerId} gelöscht.`);
        loadCustomers(); // Kundenliste neu laden
    } catch (error) {
        console.error(`❌ customer_content.js: Fehler beim Löschen des Kunden:`, error);
    }
}
