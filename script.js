// Exemple de graphique avec Chart.js
const salesChartCtx = document.getElementById('salesChart').getContext('2d');
const activityChartCtx = document.getElementById('activityChart').getContext('2d');

const salesChart = new Chart(salesChartCtx, {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Ventes',
            data: [65, 59, 80, 81, 56, 55],
            backgroundColor: 'rgba(26, 188, 156, 0.2)',
            borderColor: 'rgba(26, 188, 156, 1)',
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

const activityChart = new Chart(activityChartCtx, {
    type: 'bar',
    data: {
        labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
        datasets: [{
            label: 'Activité',
            data: [12, 19, 3, 5, 2, 3, 9],
            backgroundColor: 'rgba(52, 152, 219, 0.2)',
            borderColor: 'rgba(52, 152, 219, 1)',
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});