export function loadDashboard() {
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

