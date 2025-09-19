document.addEventListener("DOMContentLoaded", function () {
    console.log("📌 navbar.js wurde geladen!");

    setTimeout(() => {
        console.log("⏳ Wartezeit vorbei, suche nach #nav-links...");

        const navLinks = document.getElementById("nav-links");
        const logoutBtn = document.getElementById("logout-btn");

        if (!navLinks) {
            console.error("❌ navbar.js: #nav-links nicht gefunden!");
            return;
        }

        console.log("✅ navbar.js: #nav-links gefunden!", navLinks);

        // Statische Navigationspunkte
        const routes = [
            { name: "Dashboard", url: "/modules/dashboard.html", icon: "fas fa-home" },
            { name: "Kunden", url: "/modules/customers.html", icon: "fas fa-users" },
            { name: "Updates", url: "/modules/updates.html", icon: "fas fa-edit" },
            { name: "Einstellungen", url: "/modules/settings.html", icon: "fas fa-cogs" }
        ];

        console.log("🔍 navbar.js: Starte Navigationserstellung...");

        routes.forEach(link => {
            const li = document.createElement("li");
            li.classList.add("nav-item");
            li.innerHTML = `<a class="nav-link" href="${link.url}">
                                <i class="${link.icon}"></i> ${link.name}
                            </a>`;
            navLinks.appendChild(li);
            console.log(`✅ navbar.js: Link hinzugefügt -> ${link.name}`);
        });

        console.log("✅ navbar.js: Navigation erfolgreich erstellt!");

        // ✅ Logout-Button Handling
        if (!logoutBtn) {
            console.error("❌ navbar.js: Logout-Button nicht gefunden!");
            return;
        }

        console.log("✅ navbar.js: Logout-Button gefunden!");

        logoutBtn.addEventListener("click", async () => {
            console.log("🔴 Logout-Button wurde geklickt!");

            try {
                const response = await fetch("/logout", {
                    method: "POST",
                    headers: {
                        "Authorization": "Bearer " + getAccessToken()
                    },
                    credentials: "include"  // ✅ WICHTIG: Cookies mit senden!
                });
    

                if (!response.ok) {
                    throw new Error("❌ Fehler beim Logout: " + response.statusText);
                }

                console.log("✅ Logout erfolgreich!");

                // Cookies löschen
                document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                document.cookie = "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                console.log("✅ Cookies gelöscht!");

                // Weiterleitung zur Login-Seite
                window.location.href = "/login.html";

            } catch (error) {
                console.error("❌ Logout fehlgeschlagen:", error);
            }
        });

    }, 500);

    // ✅ Hilfsfunktion: Token aus Cookie lesen
function getAccessToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("access_token="))
        ?.split("=")[1] || "";
}

});


