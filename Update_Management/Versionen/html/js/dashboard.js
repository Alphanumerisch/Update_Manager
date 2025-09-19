export function loadDashboard() {
    fetch("/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "dashboard" }),
        credentials: "include"
    })
    .then(response => response.json())
    .then(data => {
        let content = document.getElementById("content");
        content.innerHTML = "<h2>Dashboard</h2>";
        // Dashboard-Logik hier
    })
    .catch(error => console.error("Fehler beim Laden des Dashboards:", error));
}
