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
        addCustomerModal();
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
            const customerId = event.target.closest("button").dataset.id;
            console.log(`📡 customer_content.js: Klicke auf Bearbeiten für Kunde ID ${customerId}...`);

            editCustomer(customerId, customers);
        })
    );

    document.querySelectorAll(".delete-btn").forEach(btn =>
        btn.addEventListener("click", event => {
            const customerId = event.target.closest("button").dataset.id;
            console.log(`📡 customer_content.js: Klicke auf Löschen für Kunde ID ${customerId}...`);
            deleteCustomer(customerId);
        })
    );
}

/**
 * 📝 Kunde bearbeiten - Dynamisches Bootstrap Modal
 */
function editCustomer(customerId, customers) {
    const customer = customers.find(c => c.id == customerId);
    if (!customer) {
        console.error(`❌ customer_content.js: Kunde mit ID ${customerId} nicht gefunden!`);
        return;
    }

    console.log(`📡 customer_content.js: Bearbeite Kunde ${customerId}...`);

    // **Prüfen, ob das Modal schon existiert**
    let modalContainer = document.getElementById("editCustomerModal");
    if (!modalContainer) {
        modalContainer = document.createElement("div");
        modalContainer.innerHTML = `
            <div class="modal fade" id="editCustomerModal" tabindex="-1" aria-labelledby="editCustomerLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="editCustomerLabel">Kunde bearbeiten</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="editCustomerForm">
                                <div class="mb-3">
                                    <label for="editCustomerName" class="form-label">Name</label>
                                    <input type="text" class="form-control" id="editCustomerName" required>
                                </div>
                                <div class="mb-3">
                                    <label for="editCustomerEmail" class="form-label">E-Mail</label>
                                    <input type="email" class="form-control" id="editCustomerEmail" required>
                                </div>
                                <input type="hidden" id="editCustomerId">
                                <button type="submit" class="btn btn-primary">Speichern</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modalContainer);
    }

    // **Formular mit Daten füllen**
    document.getElementById("editCustomerName").value = customer.name;
    document.getElementById("editCustomerEmail").value = customer.email;
    document.getElementById("editCustomerId").value = customer.id;

    // **Bootstrap Modal anzeigen**
    const editModal = new bootstrap.Modal(document.getElementById("editCustomerModal"));
    editModal.show();

    // **Formular-EventListener für Speichern**
    document.getElementById("editCustomerForm").onsubmit = async function (event) {
        event.preventDefault();
        console.log("📡 customer_content.js: Speichere Änderungen...");

        const updatedCustomer = {
            customer_id: document.getElementById("editCustomerId").value,
            name: document.getElementById("editCustomerName").value,
            email: document.getElementById("editCustomerEmail").value
        };

        console.log("📡 customer_content.js: Aktualisierte Daten:", updatedCustomer);

        try {
            const response = await fetchWithAuth("/api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: "update_customer",
                    customer_id: updatedCustomer.customer_id,
                    name: updatedCustomer.name,
                    email: updatedCustomer.email
                }),
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || "Fehler beim Aktualisieren des Kunden");

            console.log("✅ customer_content.js: Kunde erfolgreich aktualisiert!");
            loadCustomers(); // Kundenliste neu laden
            editModal.hide(); // Modal schließen
        } catch (error) {
            console.error("❌ customer_content.js: Fehler beim Speichern der Änderungen:", error);
        }
    };
}

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

/**
 * 🟢 Zeigt ein Bootstrap Modal zum Hinzufügen eines Kunden
 */
function addCustomerModal() {
    let modalContainer = document.getElementById("addCustomerModal");
    if (!modalContainer) {
        modalContainer = document.createElement("div");
        modalContainer.innerHTML = `
            <div class="modal fade" id="addCustomerModal" tabindex="-1" aria-labelledby="addCustomerLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="addCustomerLabel">Neuen Kunden hinzufügen</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="addCustomerForm">
                                <div class="mb-3">
                                    <label for="addCustomerName" class="form-label">Name</label>
                                    <input type="text" class="form-control" id="addCustomerName" required>
                                </div>
                                <div class="mb-3">
                                    <label for="addCustomerEmail" class="form-label">E-Mail</label>
                                    <input type="email" class="form-control" id="addCustomerEmail" required>
                                </div>
                                <button type="submit" class="btn btn-primary">Speichern</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modalContainer);
    }

    const addModal = new bootstrap.Modal(document.getElementById("addCustomerModal"));
    addModal.show();

    document.getElementById("addCustomerForm").onsubmit = async function (event) {
        event.preventDefault();

        const newCustomer = {
            name: document.getElementById("addCustomerName").value,
            email: document.getElementById("addCustomerEmail").value
        };

        try {
            const response = await fetchWithAuth("/api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "add_customers", name: newCustomer.name, email: newCustomer.email }),
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.detail || "Fehler beim Hinzufügen des Kunden");

            console.log("✅ customer_content.js: Kunde erfolgreich hinzugefügt!");
            loadCustomers(); // Kundenliste neu laden
            addModal.hide(); // Modal schließen
        } catch (error) {
            console.error("❌ customer_content.js: Fehler beim Speichern des neuen Kunden:", error);
        }
    };
}