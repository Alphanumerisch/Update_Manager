export function loadUpdates() {
    fetch('/api', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'list_updates' })  // API-Action für Updates
    })
    .then(response => response.json())
    .then(data => {
        let content = document.getElementById("content");
        content.innerHTML = "<h2>Update-Verwaltung</h2>";

        let table = document.createElement("table");
        table.innerHTML = `<tr>
            <th>ID</th>
            <th>Title</th>
            <th>Description</th>
            <th>Aktion</th>
        </tr>`;

        data.forEach(update => {
            let row = table.insertRow();
            row.innerHTML = `
                <td>${update.id}</td>
                <td>${update.title}</td>
                <td>${update.description}</td>
                <td>
                    <button onclick="sendUpdate(${update.id})">Bearbeiten</button>
                    <button onclick="deleteUpdate(${update.id})">Löschen</button>
                </td>
            `;
        });
        content.appendChild(table);
    })
    .catch(error => console.error("Fehler beim Laden der Updates:", error));
}
