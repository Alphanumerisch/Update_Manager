document.addEventListener("DOMContentLoaded", async () => {
    console.log("📡 Lade Dashboard-Daten...");

    // Dashboard-Daten initial abrufen
    await loadDashboardData();

    // WebSocket-Verbindung starten
    startWebSocket();
});

/**
 * Lädt die Dashboard-Daten von der API und zeigt sie an.
 */
async function loadDashboardData() {
    try {
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "dashboard" }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Fehler beim Laden des Dashboards");

        console.log("📊 Dashboard-Daten erhalten:", data);
        renderDashboard(data);
    } catch (error) {
        console.error("❌ Fehler beim Laden der Dashboard-Daten:", error);
    }
}

/**
 * Stellt die Dashboard-Daten als Kartenstruktur dar.
 */
/**
 * Stellt die Dashboard-Daten als Kartenstruktur dar.
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

    console.log("✅ Dashboard erfolgreich gerendert!");
}


/**
 * Prüft, ob ein Termin in den nächsten 10 Minuten beginnt & markiert ihn.
 */
function checkForPulsing(card, selectedDate) {
    if (!selectedDate) return;

    const now = new Date();
    const diffInMinutes = (selectedDate - now) / (1000 * 60);

    if (diffInMinutes <= 10 && diffInMinutes > 0) {
        card.classList.add("pulse-warning");
    }
}

/**
 * Startet die WebSocket-Verbindung für Live-Updates.
 */
/**
 * Startet die WebSocket-Verbindung für Live-Updates.
 */
function startWebSocket() {
    console.log("📡 WebSocket wird gestartet...");

    const ws = new WebSocket("ws://192.168.168.160/ws/dashboard");

    ws.onopen = () => {
        console.log("✅ WebSocket erfolgreich verbunden!");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("🔔 Live-Update erhalten:", data);

        data.updates.forEach(update => {
            const updateContainer = document.getElementById(`update-${update.id}`);
            update.customers.forEach(customer => {
                createOrUpdateCustomerCard(updateContainer, customer);
            });
        });
    };

    ws.onerror = (error) => {
        console.error("❌ WebSocket Fehler:", error);
    };

    ws.onclose = () => {
        console.log("🔌 WebSocket Verbindung geschlossen. Versuche in 5s erneut...");
        setTimeout(startWebSocket, 5000);
    };
}


/**
 * Erstellt oder aktualisiert eine Kundenkarte innerhalb eines Updates.
 */
function createOrUpdateCustomerCard(updateContainer, customer) {
    let statusColor = customer.status === "bestätigt" ? "green" : "red";
    let statusIcon = customer.status === "bestätigt" ? "check-circle" : "times-circle";
    let statusText = customer.status === "bestätigt" ? "Bestätigt" : "Offen";
    let dateInfo = customer.selected_date
        ? `<i class="fas fa-calendar-alt"></i> Termin: ${customer.selected_date}`
        : `<i class="fas fa-exclamation-circle text-danger"></i> Kein Termin gewählt`;

    // Prüfen, ob eine bestehende Kundenkarte existiert
    let customerCard = document.querySelector(`.customer-card[data-name="${customer.name}"]`);

    if (!customerCard) {
        customerCard = document.createElement("div");
        customerCard.classList.add("col-md-6", "mb-3", "customer-card");
        customerCard.dataset.name = customer.name;
        updateContainer.appendChild(customerCard);
    }

    // Kundenkarte aktualisieren
    customerCard.innerHTML = `
        <div class="card p-3 border">
            <h6><i class="fas fa-user"></i> <b>${customer.name}</b></h6>
            <p><i class="fas fa-envelope"></i> ${customer.email}</p>
            <p><i class="fas fa-${statusIcon}" style="color: ${statusColor}"></i> Status: ${statusText}</p>
            <p>${dateInfo}</p>
        </div>
    `;

    // **Gelber Rahmen für baldige Termine**
    const tenMinutesBefore = new Date();
    tenMinutesBefore.setMinutes(tenMinutesBefore.getMinutes() + 10);
    const updateDate = new Date(customer.selected_date);

    if (customer.selected_date && updateDate <= tenMinutesBefore) {
        customerCard.classList.add("pulse-warning");
    } else {
        customerCard.classList.remove("pulse-warning");
    }
}

