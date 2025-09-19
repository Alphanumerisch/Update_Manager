export function loadCustomers() {
    fetch("/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "list_customers" }),
        credentials: "include"
    })
    .then(response => response.json())
    .then(data => {
        let content = document.getElementById("content");
        content.innerHTML = "<h2>Kunden</h2>";
        // Kunden-Logik hier
    })
    .catch(error => console.error("Fehler beim Laden der Kunden:", error));
}
