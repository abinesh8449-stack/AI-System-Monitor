/**
 * Chart.js Real-Time Stream Initializer and Rolling Buffer Manager
 */

const MAX_CHART_POINTS = 15;

const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 400,
        easing: 'linear'
    },
    plugins: {
        legend: {
            display: false
        },
        tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(15, 23, 42, 0.9)',
            titleColor: '#e2e8f0',
            bodyColor: '#e2e8f0',
            borderColor: '#334155',
            borderWidth: 1
        }
    },
    scales: {
        x: {
            grid: {
                color: 'rgba(255, 255, 255, 0.04)',
                drawBorder: false
            },
            ticks: {
                color: '#64748b',
                font: { size: 10, family: 'JetBrains Mono' },
                maxTicksLimit: 6
            }
        },
        y: {
            min: 0,
            max: 100,
            grid: {
                color: 'rgba(255, 255, 255, 0.04)',
                drawBorder: false
            },
            ticks: {
                color: '#64748b',
                font: { size: 10, family: 'JetBrains Mono' },
                callback: function(value) { return value + '%'; }
            }
        }
    }
};

let cpuChart = null;
let ramChart = null;
let diskChart = null;
let networkChart = null;

function initCharts() {
    // 1. CPU Chart
    const cpuCtx = document.getElementById('cpuLiveChart')?.getContext('2d');
    if (cpuCtx) {
        cpuChart = new Chart(cpuCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage (%)',
                    data: [],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.12)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: commonChartOptions
        });
    }

    // 2. RAM Chart
    const ramCtx = document.getElementById('ramLiveChart')?.getContext('2d');
    if (ramCtx) {
        ramChart = new Chart(ramCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'RAM Usage (%)',
                    data: [],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.12)',
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: commonChartOptions
        });
    }

    // 3. Disk Chart (Line or Bar)
    const diskCtx = document.getElementById('diskLiveChart')?.getContext('2d');
    if (diskCtx) {
        diskChart = new Chart(diskCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Disk Usage (%)',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.12)',
                    fill: true,
                    tension: 0.2,
                    borderWidth: 2,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: commonChartOptions
        });
    }

    // 4. Network Chart
    const netCtx = document.getElementById('networkLiveChart')?.getContext('2d');
    if (netCtx) {
        const netOptions = JSON.parse(JSON.stringify(commonChartOptions));
        delete netOptions.scales.y.max; // Dynamic upper bound for KB/s
        netOptions.plugins.legend.display = true;
        netOptions.plugins.legend.labels = { color: '#94a3b8', boxWidth: 12, font: { size: 11 } };
        netOptions.scales.y.ticks.callback = function(value) { return value + ' KB/s'; };

        networkChart = new Chart(netCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Upload (KB/s)',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.08)',
                        fill: false,
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 1
                    },
                    {
                        label: 'Download (KB/s)',
                        data: [],
                        borderColor: '#818cf8',
                        backgroundColor: 'rgba(129, 140, 248, 0.08)',
                        fill: false,
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 1
                    }
                ]
            },
            options: netOptions
        });
    }
}

function updateChartSeries(chart, label, value) {
    if (!chart) return;
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);

    if (chart.data.labels.length > MAX_CHART_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update('none');
}

function updateNetworkChartSeries(label, uploadKb, downloadKb) {
    if (!networkChart) return;
    networkChart.data.labels.push(label);
    networkChart.data.datasets[0].data.push(uploadKb);
    networkChart.data.datasets[1].data.push(downloadKb);

    if (networkChart.data.labels.length > MAX_CHART_POINTS) {
        networkChart.data.labels.shift();
        networkChart.data.datasets[0].data.shift();
        networkChart.data.datasets[1].data.shift();
    }
    networkChart.update('none');
}
