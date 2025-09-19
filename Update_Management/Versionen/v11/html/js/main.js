// main.js - Hauptsteuerung

import {logout, checkLoginStatus } from "./auth.js"; 
import { loadDashboard } from "./dashboard.js";
import { loadCustomers } from "./customers.js";
import { loadUpdates } from "./updates.js";

// Prüft Login-Status beim Laden der Seite
document.addEventListener("DOMContentLoaded", checkLoginStatus);

// Buttons verknüpfen (Navigation wird nur für eingeloggte User angezeigt)
document.getElementById("btnDashboard").addEventListener("click", loadDashboard);
document.getElementById("btnCustomers").addEventListener("click", loadCustomers);
document.getElementById("btnUpdates").addEventListener("click", loadUpdates);
document.getElementById("btnLogout").addEventListener("click", logout);
