export function loadUpdates() {
    fetch("/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "list_updates" }),
        credentials: "include"
    })
    .then(response => response.json())
    .then(data => {
        let content = document.getElementById("content");
        content.innerHTML = "<h2>Updates</h2>";
        // Updates-Logik hier
    })
    .catch(error => console.error("Fehler beim Laden der Updates:", error));
}
