// auth.js - Login-Management

import { loadDashboard } from "./dashboard.js";

export function checkLoginStatus() {
    fetch("/get_current_user", { 
        method: "POST",
        credentials: "include"  // WICHTIG: Cookies mit senden
    })
    .then(response => {
        console.log("Login-Status Response:", response);
        if (response.ok) {
            return response.json();
        } else {
            throw new Error("Nicht authentifiziert");
        }
    })
    .then(data => {
        console.log("User-Data:", data); // Prüfen, ob der User erfolgreich geladen wurde
        loadDashboard();  // Falls authentifiziert -> Dashboard laden
        document.getElementById("navButtons").style.display = "flex";
    })
    .catch(error => {
        console.error("Fehler in checkLoginStatus:", error);
        showLoginForm();  // Falls nicht eingeloggt -> Login anzeigen
    });
}



export function showLoginForm() {
    document.getElementById("content").innerHTML = `
        <div class="login-container">
            <h2>Login</h2>
            <input type="text" id="username" placeholder="Benutzername">
            <input type="password" id="password" placeholder="Passwort">
            <button id="btnLogin">Login</button>
        </div>
    `;

    document.getElementById("btnLogin").addEventListener("click", login);
}

export function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "include"  // WICHTIG: Damit das Cookie mitgesendet wird
    })
    .then(response => {
        if (response.ok) {
            checkLoginStatus(); // Login erfolgreich -> Status neu prüfen
        } else {
            alert("Login fehlgeschlagen!");
        }
    })
    .catch(error => console.error("Fehler beim Login:", error));
}


export function logout() {
    localStorage.removeItem("access_token");
    checkLoginStatus();
}
