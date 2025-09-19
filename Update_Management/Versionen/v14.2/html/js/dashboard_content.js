document.addEventListener("DOMContentLoaded", async function () {
    console.log("📌 dashboard_content.js geladen!");

    try {
        // ✅ API-Aufruf, um Dashboard-Daten zu holen
        const response = await fetchWithAuth("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "dashboard" })
        });

        if (!response.ok) {
            throw new Error("Fehler beim Laden der Dashboard-Daten");
        }

        const data = await response.json();
        console.log("✅ Dashboard-Daten empfangen:", data);

        // ✅ Container für den dynamischen Inhalt holen
        const dashboardContainer = document.getElementById("dashboard-content");

        // 📝 Falls kein Container existiert, abbrechen
        if (!dashboardContainer) {
            console.error("❌ dashboard_content.js: #dashboard-content nicht gefunden!");
            return;
        }

        // 🟢 Inhalt generieren
        dashboardContainer.innerHTML = data.updates.map(update => `
            <div class="card mb-4 shadow">
                <div class="card-header bg-primary text-white">
                    <h5><i class="fas fa-info-circle"></i> ${update.title}</h5>
                    <p class="mb-0">${update.description}</p>
                </div>
                <div class="card-body">
                    <h6>Kunden:</h6>
                    <div class="row">
                        ${update.customers.map(customer => `
                            <div class="col-md-6">
                                <div class="card mb-3 p-2 border">
                                    <strong><i class="fas fa-user"></i> ${customer.name}</strong><br>
                                    <i class="fas fa-envelope"></i> ${customer.email}<br>
                                    <i class="fas fa-check-circle"></i> Status: <strong>${customer.status}</strong><br>
                                    ${customer.selected_date 
                                        ? `<i class="fas fa-calendar"></i> Termin: ${new Date(customer.selected_date).toLocaleString()}`
                                        : `<i class="fas fa-exclamation-circle text-danger"></i> Kein Termin gewählt`}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error("❌ dashboard_content.js Fehler:", error);
    }
});
