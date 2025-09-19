document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("login-form");
    const errorMessage = document.getElementById("error-message");

    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
                credentials: "include" // ✅ Wichtig: Cookies werden automatisch gesetzt!
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Fehler beim Login");
            }

            // ✅ Kein `document.cookie` nötig – das Token wird als HttpOnly-Cookie gesetzt!
            console.log("✅ Login erfolgreich, Token wurde als Cookie gesetzt!");

            // Weiterleitung nach erfolgreichem Login
            window.location.href = "/modules/dashboard.html";
        } catch (error) {
            errorMessage.textContent = error.message;
            errorMessage.classList.remove("d-none");
        }
    });
});
