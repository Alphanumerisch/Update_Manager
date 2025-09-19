import { loadDashboard } from './dashboard.js';
import { loadCustomers } from './customers.js';
import { loadUpdates } from './update.js';

document.addEventListener("DOMContentLoaded", function() {
    loadDashboard(); // Standardansicht nach dem Laden der Seite

    document.getElementById("btnDashboard").addEventListener("click", loadDashboard);
    document.getElementById("btnCustomers").addEventListener("click", loadCustomers);
    document.getElementById("btnUpdates").addEventListener("click", loadUpdates);
});
