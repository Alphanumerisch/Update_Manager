/**
 * 🟢 Initialisiert das Dashboard. Diese Funktion wird nach dem Laden aufgerufen.
 */
async function initDashboard() {
    console.log("📡 dashboard_content.js: Initialisiere Dashboard...");

    const dashboardContainer = document.getElementById("dashboard-content");

    if (!dashboardContainer) {
        console.error("❌ dashboard_content.js: Fehler - #dashboard-content nicht gefunden!");
        return;
    }

    console.log("✅ dashboard_content.js: #dashboard-content gefunden, lade Daten...");
    await loadDashboardData();
}

/**
 * 🟢 Lädt die Dashboard-Daten von der API und zeigt sie an.
 */
async function loadDashboardData() {
    try {
        console.log("📡 dashboard_content.js: API-Request an /api...");

        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "dashboard" }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Fehler beim Laden des Dashboards");

        console.log("✅ dashboard_content.js: Dashboard-Daten erhalten:", data);
        renderDashboard(data);
    } catch (error) {
        console.error(`❌ dashboard_content.js: Fehler beim Laden der Dashboard-Daten: ${error}`);
    }
}

/**
 * 🟢 Stellt die Dashboard-Daten als Bootstrap-Kartenstruktur dar.
 */
function renderDashboard(data) {
    const container = document.getElementById("dashboard-content");
    container.innerHTML = "";

    data.updates.forEach(update => {
        const updateCard = document.createElement("div");
        updateCard.classList.add("card", "mb-4", "shadow-sm");

        updateCard.innerHTML = `
            <div class="card-header text-white bg-primary">
                <h5 class="mb-0">
                    <i class="fas fa-info-circle"></i> ${update.title}
                </h5>
                <small>${update.description}</small>
            </div>
            <div class="card-body">
                <h6><b>Kunden:</b></h6>
                <div class="row" id="update-${update.id}"></div>
            </div>
        `;

        container.appendChild(updateCard);

        // Kunden innerhalb des Updates einfügen
        const updateContainer = document.getElementById(`update-${update.id}`);
        update.customers.forEach(customer => {
            createOrUpdateCustomerCard(updateContainer, customer);
        });
    });

    console.log("✅ dashboard_content.js: Dashboard erfolgreich gerendert!");
}

/**
 * 🟢 Erstellt oder aktualisiert eine Kundenkarte innerhalb eines Updates.
 */
function createOrUpdateCustomerCard(updateContainer, customer) {
    let statusColor = customer.status === "bestätigt" ? "green" : "red";
    let statusIcon = customer.status === "bestätigt" ? "check-circle" : "times-circle";
    let statusText = customer.status === "bestätigt" ? "Bestätigt" : "Offen";
    let dateInfo = customer.selected_date
        ? `<i class="fas fa-calendar-alt"></i> Termin: ${customer.selected_date}`
        : `<i class="fas fa-exclamation-circle text-danger"></i> Kein Termin gewählt`;

    let customerCard = document.createElement("div");
    customerCard.classList.add("col-md-6", "mb-3", "customer-card");

    customerCard.innerHTML = `
        <div class="card p-3 border">
            <h6><i class="fas fa-user"></i> <b>${customer.name}</b></h6>
            <p><i class="fas fa-envelope"></i> ${customer.email}</p>
            <p><i class="fas fa-${statusIcon}" style="color: ${statusColor}"></i> Status: ${statusText}</p>
            <p>${dateInfo}</p>
        </div>
    `;

    updateContainer.appendChild(customerCard);
}
