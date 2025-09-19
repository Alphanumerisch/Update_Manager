export function loadUpdates() {
    fetch('/api', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
            `;

            let actionCell = row.insertCell();

            // ✅ Bearbeiten-Button mit `addEventListener()`
            let editButton = document.createElement("button");
            editButton.innerText = "Bearbeiten";
            editButton.classList.add("edit-button"); // Falls CSS vorhanden ist
            editButton.addEventListener("click", () => sendUpdate(update.id));

            // ✅ Löschen-Button mit `addEventListener()`
            let deleteButton = document.createElement("button");
            deleteButton.innerText = "Löschen";
            deleteButton.classList.add("delete-button");
            deleteButton.addEventListener("click", () => deleteUpdate(update.id));

            // Buttons in die Aktion-Zelle einfügen
            actionCell.appendChild(editButton);
            actionCell.appendChild(deleteButton);
            
            table.appendChild(row);
        });

        content.appendChild(table);
    })
    .catch(error => console.error("Fehler beim Laden der Updates:", error));
}