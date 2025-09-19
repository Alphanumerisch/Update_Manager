document.addEventListener("DOMContentLoaded", async function () {
    console.log("📌 navbar.js wurde geladen!");

    setTimeout(async () => {
        console.log("⏳ Wartezeit vorbei, starte Abruf der Benutzerrolle...");

        try {
            // **API-Call für get_current_user**
            const response = await fetch("/api", {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ action: "get_current_user" }),
                credentials: "include"  // ✅ Sendet Cookies automatisch mit
            });

            if (!response.ok) {
                throw new Error("Nicht authentifiziert");
            }

            const userData = await response.json();
            console.log("✅ Benutzer erfolgreich abgerufen:", userData);

            const role = userData.role;
            console.log("👤 Benutzerrolle:", role);

            const navLinks = document.getElementById("nav-links");
            const logoutBtn = document.getElementById("logout-btn");

            if (!navLinks) {
                console.error("❌ navbar.js: #nav-links nicht gefunden!");
                return;
            }
            console.log("✅ navbar.js: #nav-links gefunden!", navLinks);

            // Definierte Navigationspunkte basierend auf der Rolle
            const routes = {
                "admin": [
                    { name: "Dashboard", url: "/modules/dashboard.html", icon: "fas fa-home" },
                    { name: "Kunden", url: "/modules/customers.html", icon: "fas fa-users" },
                    { name: "Updates", url: "/modules/updates.html", icon: "fas fa-edit" },
                    { name: "Einstellungen", url: "/modules/settings.html", icon: "fas fa-cogs" }
                ],
                "user": [
                    { name: "Dashboard", url: "/modules/dashboard.html", icon: "fas fa-home" },
                    { name: "Kunden", url: "/modules/customers.html", icon: "fas fa-users" },
                    { name: "Updates", url: "/modules/updates.html", icon: "fas fa-edit" }
                ],
                "viewer": [
                    { name: "Dashboard", url: "/modules/dashboard.html", icon: "fas fa-home" }
                ]
            };

            console.log("🔍 navbar.js: Starte Navigationserstellung für Rolle:", role);

            // Bestehende Navigation leeren
            navLinks.innerHTML = "";

            // Links basierend auf der Rolle generieren
            routes[role]?.forEach(link => {
                const li = document.createElement("li");
                li.classList.add("nav-item");
                li.innerHTML = `<a class="nav-link" href="${link.url}">
                                    <i class="${link.icon}"></i> ${link.name}
                                </a>`;
                navLinks.appendChild(li);
                console.log(`✅ navbar.js: Link hinzugefügt -> ${link.name}`);
            });

            console.log("✅ navbar.js: Navigation erfolgreich erstellt!");

            // ✅ Logout-Button aktivieren
            if (logoutBtn) {
                logoutBtn.addEventListener("click", async () => {
                    try {
                        const response = await fetch("/logout", {
                            method: "POST",
                            credentials: "include"
                        });

                        if (!response.ok) {
                            throw new Error("Fehler beim Logout");
                        }

                        console.log("✅ Logout erfolgreich!");
                        window.location.href = "/login.html"; // Zurück zur Login-Seite
                    } catch (error) {
                        console.error("❌ Logout fehlgeschlagen:", error);
                    }
                });
                console.log("✅ navbar.js: Logout-Button aktiviert!");
            } else {
                console.error("❌ navbar.js: Logout-Button nicht gefunden!");
            }

        } catch (error) {
            console.error("❌ navbar.js: Fehler beim Laden der Navigation:", error);
            window.location.href = "/login.html"; // Umleitung zur Login-Seite
        }
    }, 1);
});
