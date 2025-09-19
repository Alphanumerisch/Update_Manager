// main.js - Hauptsteuerung
import { checkLoginStatus, logout } from "./auth.js";
import { loadDashboard } from "./dashboard.js";
import { loadCustomers } from "./customers.js";
import { loadUpdates } from "./update.js";

// Seite lädt und prüft Login-Status
document.addEventListener("DOMContentLoaded", checkLoginStatus);

// Buttons mit Funktionen verknüpfen (Navigation bleibt, wenn User eingeloggt ist)
document.getElementById("btnDashboard").addEventListener("click", loadDashboard);
document.getElementById("btnCustomers").addEventListener("click", loadCustomers);
document.getElementById("btnUpdates").addEventListener("click", loadUpdates);
document.getElementById("btnLogout").addEventListener("click", logout);
