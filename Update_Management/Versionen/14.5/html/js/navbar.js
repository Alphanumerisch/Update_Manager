document.addEventListener("DOMContentLoaded", async function () {
    console.log("📌 navbar.js wurde geladen!");

    // Lade die Navbar nur, wenn sie noch nicht existiert
    if (!document.getElementById("nav-links")) {
        fetch("/modules/navbar.html")
            .then(response => response.text())
            .then(data => {
                document.getElementById("navbar-container").innerHTML = data;
                initNavbar(); // Navbar initialisieren
            })
            .catch(error => console.error("❌ Fehler beim Laden der Navbar:", error));
    }
});

/**
 * Initialisiert die Navbar mit dynamischen Links und Logout.
 */
async function initNavbar() {
    console.log("🔄 Initialisiere Navbar...");

    try {
        const response = await fetch("/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action: "get_current_user" }),
            credentials: "include"
        });

        if (!response.ok) {
            throw new Error("Nicht authentifiziert");
        }

        const userData = await response.json();
        console.log("✅ Benutzer erfolgreich geladen:", userData);

        const role = userData.role;
        const navLinks = document.getElementById("nav-links");
        const logoutBtn = document.getElementById("logout-btn");

        if (!navLinks) {
            console.error("❌ navbar.js: #nav-links nicht gefunden!");
            return;
        }

        // Definierte Navigationspunkte basierend auf der Rolle
        const routes = {
            "admin": [
                { name: "Dashboard", url: "dashboard.html", icon: "fas fa-home" },
                { name: "Kunden", url: "customers.html", icon: "fas fa-users" },
                { name: "Updates", url: "updates.html", icon: "fas fa-edit" },
                { name: "Einstellungen", url: "settings.html", icon: "fas fa-cogs" }
            ],
            "user": [
                { name: "Dashboard", url: "dashboard.html", icon: "fas fa-home" },
                { name: "Kunden", url: "customers.html", icon: "fas fa-users" },
                { name: "Updates", url: "updates.html", icon: "fas fa-edit" }
            ],
            "viewer": [
                { name: "Dashboard", url: "dashboard.html", icon: "fas fa-home" }
            ]
        };

        console.log("🔍 Navbar wird für Rolle:", role, "geladen");

        // Navigation leeren und Links hinzufügen
        navLinks.innerHTML = "";
        routes[role]?.forEach(link => {
            const li = document.createElement("li");
            li.classList.add("nav-item");
            li.innerHTML = `<a class="nav-link" href="#" onclick="loadModule('${link.url}')">
                                <i class="${link.icon}"></i> ${link.name}
                            </a>`;
            navLinks.appendChild(li);
        });

        console.log("✅ Navbar erfolgreich geladen!");

        // Logout-Button aktivieren
        if (logoutBtn) {
            logoutBtn.addEventListener("click", async () => {
                await fetch("/logout", { method: "POST", credentials: "include" });
                window.location.href = "/login.html";
            });
        }
    } catch (error) {
        console.error("❌ Fehler beim Laden der Navbar:", error);
        window.location.href = "/login.html"; // Falls nicht eingeloggt → Login-Seite
    }
}
