
export function checkLoginStatus() {
    fetch("/get_current_user", { method: "POST", credentials: "include" })
    .then(response => {
        if (response.ok) return response.json();
        throw new Error("Nicht eingeloggt");
    })
    .then(() => {
        document.getElementById("navButtons").style.display = "flex";
        loadDashboard();
    })
    .catch(() => {
        showLoginForm();
    });
}

export function showLoginForm() {
    document.getElementById("content").innerHTML = `
        <div class="login-container">
            <h2>Login</h2>
            <input type="text" id="username" placeholder="Benutzername">
            <input type="password" id="password" placeholder="Passwort">
            <button id="btnLogin">Login</button>  
        </div>`;

    // Event-Listener für Login-Button setzen
    document.getElementById("btnLogin").addEventListener("click", login);
}


export function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
        credentials: "include"
    })
    .then(response => {
        if (response.ok) {
            checkLoginStatus();
        } else {
            alert("Login fehlgeschlagen");
        }
    })
    .catch(error => console.error("Fehler beim Login:", error));
}

export function logout() {
    fetch("/api/logout", { method: "POST", credentials: "include" })
    .then(() => {
        showLoginForm();
    })
    .catch(error => console.error("Fehler beim Logout:", error));
}
