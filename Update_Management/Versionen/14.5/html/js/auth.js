async function refreshToken() {
    console.log("🔄 Versuche Token zu erneuern...");

    try {
        const response = await fetch("/refresh_token", {
            method: "POST",
            credentials: "include" // WICHTIG: Sendet Cookies mit!
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "❌ Fehler beim Erneuern des Tokens");
        }

        console.log("✅ Token erfolgreich erneuert!");

        return true; // Erfolgreich
    } catch (error) {
        console.error("❌ Token-Erneuerung fehlgeschlagen:", error.message);
        window.location.href = "/login.html"; // Zur Login-Seite umleiten
        return false;
    }
}

async function fetchWithAuth(url, options = {}) {
    let response = await fetch(url, {
        ...options,
        credentials: "include" // Cookies senden!
    });

    // Falls Token abgelaufen → Versuche zu erneuern & Request erneut senden
    if (response.status === 401) {
        console.warn("⚠️ Token abgelaufen. Versuche es zu erneuern...");
        const refreshed = await refreshToken();

        if (refreshed) {
            response = await fetch(url, {
                ...options,
                credentials: "include"
            });
        }
    }

    return response;
}
