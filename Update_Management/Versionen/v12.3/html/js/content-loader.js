document.addEventListener("DOMContentLoaded", function () {
    console.log("📌 content-loader.js wurde geladen!");

    window.loadContent = async function (page) {
        console.log(`🔄 Lade Seite: ${page}.html`);
        
        const contentContainer = document.getElementById("content-container");
        if (!contentContainer) {
            console.error("❌ Fehler: #content-container nicht gefunden!");
            return;
        }

        try {
            const response = await fetch(`/modules/${page}.html`);
            if (!response.ok) throw new Error("Seite nicht gefunden");

            const data = await response.text();
            contentContainer.innerHTML = data;
            console.log(`✅ ${page}.html erfolgreich geladen.`);

        } catch (error) {
            console.error("❌ Fehler beim Laden der Seite:", error);
        }
    };
});
