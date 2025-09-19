async function loadModule(moduleName) {
    console.log(`🔄 content-loader.js: Lade Modul: ${moduleName}`);

    try {
        console.log(`📡 content-loader.js: Sende Anfrage an: /modules/${moduleName}`);

        const response = await fetch(`/modules/${moduleName}`, {
            method: "GET",
            credentials: "include",
        });

        console.log(`📡 content-loader.js: Antwort-Status für ${moduleName}: ${response.status}`);

        if (!response.ok) {
            console.error(`❌ content-loader.js: Fehler beim Laden des Moduls ${moduleName}, Status: ${response.status}`);
            throw new Error("Modul konnte nicht geladen werden");
        }

        const htmlContent = await response.text();
        const contentContainer = document.getElementById("content-container");

        if (!contentContainer) {
            console.error("❌ content-loader.js: Fehler - #content-container nicht gefunden!");
            return;
        }

        // **HTML einfügen**
        contentContainer.innerHTML = htmlContent;
        console.log(`✅ content-loader.js: Modul erfolgreich geladen: ${moduleName}`);

        // **Falls das Dashboard geladen wurde, lade das Dashboard-Skript**
        if (moduleName === "dashboard.html") {
            loadDashboardScript();
        }

        // **Falls das Customer geladen wurde, lade das Dashboard-Skript**
        if (moduleName === "customers.html") {
            loadCustomersScript();
        }

        // **Falls das Update geladen wurde, lade das Dashboard-Skript**
        if (moduleName === "updates.html") {
            loadUpdateScript();
        }

    } catch (error) {
        console.error(`❌ content-loader.js: Fehler beim Laden der Seite: ${error}`);
        window.location.href = "/login.html";  // Falls Token abgelaufen, umleiten
    }
}

/**
 * 🟢 Lädt `dashboard_content.js` und ruft initDashboard() nach dem Laden auf.
 */
function loadDashboardScript() {
    console.log("📡 content-loader.js: Lade dashboard_content.js...");

    const script = document.createElement("script");
    script.src = "/js/dashboard_content.js";
    script.defer = true;
    script.onload = function() {
        console.log("✅ content-loader.js: dashboard_content.js wurde erfolgreich geladen!");
        if (typeof initDashboard === "function") {
            console.log("📡 content-loader.js: Starte initDashboard()...");
            initDashboard();  // **Dashboard-Daten laden**
        } else {
            console.error("❌ content-loader.js: Funktion initDashboard() nicht gefunden!");
        }
    };

    document.body.appendChild(script);
}

function loadCustomersScript() {
    console.log("📡 content-loader.js: Lade customer_content.js...");

    const script = document.createElement("script");
    script.src = "/js/customer_content.js";
    script.defer = true;
    script.onload = function() {
        console.log("✅ content-loader.js: customer_content.js wurde erfolgreich geladen!");
        if (typeof initCustomers === "function") {
            console.log("📡 content-loader.js: Starte initCustomers()...");
            initCustomers();  // **Customer-Daten laden**
        } else {
            console.error("❌ content-loader.js: Funktion initDashboard() nicht gefunden!");
        }
    };

    document.body.appendChild(script);
}

function loadUpdateScript() {
    console.log("📡 update-loader.js: Lade update_content.js...");

    const script = document.createElement("script");
    script.src = "/js/update_content.js";
    script.defer = true;
    script.onload = function() {
        console.log("✅ update-loader.js: update_content.js wurde erfolgreich geladen!");
        if (typeof initUpdates === "function") {
            console.log("📡 content-loader.js: Starte initUpdate()...");
            initUpdates();  // **Customer-Daten laden**
        } else {
            console.error("❌ content-loader.js: Funktion initUpdate() nicht gefunden!");
        }
    };

    document.body.appendChild(script);
}
