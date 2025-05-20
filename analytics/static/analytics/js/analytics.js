// Analytics Dashboard JavaScript

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Chart configuration
const chartConfig = {
    // Common options for all charts
    commonOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false,
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    },

    // Line chart specific options
    lineOptions: {
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        }
    },

    // Bar chart specific options
    barOptions: {
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: function(value) {
                        return value + '%';
                    }
                }
            }
        }
    },

    // Doughnut chart specific options
    doughnutOptions: {
        cutout: '60%',
        plugins: {
            legend: {
                position: 'bottom'
            }
        }
    }
};

// Function to create a line chart
function createLineChart(ctx, labels, datasets) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            ...chartConfig.commonOptions,
            ...chartConfig.lineOptions
        }
    });
}

// Function to create a bar chart
function createBarChart(ctx, labels, datasets) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            ...chartConfig.commonOptions,
            ...chartConfig.barOptions
        }
    });
}

// Function to create a doughnut chart
function createDoughnutChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgb(75, 192, 192)',
                    'rgb(255, 205, 86)',
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)'
                ]
            }]
        },
        options: {
            ...chartConfig.commonOptions,
            ...chartConfig.doughnutOptions
        }
    });
}

// Function to update chart data
function updateChartData(chart, newData) {
    chart.data.datasets.forEach((dataset, index) => {
        dataset.data = newData[index];
    });
    chart.update();
}

// Function to handle filter form submission
function handleFilterSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const params = new URLSearchParams(formData);
    
    // Show loading state
    document.querySelector('.loading').style.display = 'block';
    
    // Fetch filtered data
    fetch(`${window.location.pathname}?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            // Update charts with new data
            updateCharts(data);
            // Hide loading state
            document.querySelector('.loading').style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching filtered data:', error);
            // Hide loading state
            document.querySelector('.loading').style.display = 'none';
        });
}

// Function to update all charts with new data
function updateCharts(data) {
    // Update each chart based on the received data
    Object.keys(data.charts).forEach(chartId => {
        const chart = Chart.getChart(chartId);
        if (chart) {
            updateChartData(chart, data.charts[chartId]);
        }
    });
}

// Function to export chart as image
function exportChartAsImage(chartId, fileName) {
    const chart = Chart.getChart(chartId);
    if (chart) {
        const link = document.createElement('a');
        link.download = `${fileName}.png`;
        link.href = chart.toBase64Image();
        link.click();
    }
}

// Function to handle date range selection
function handleDateRangeChange(startDate, endDate) {
    const params = new URLSearchParams(window.location.search);
    params.set('start_date', startDate);
    params.set('end_date', endDate);
    
    // Show loading state
    document.querySelector('.loading').style.display = 'block';
    
    // Fetch data for the selected date range
    fetch(`${window.location.pathname}?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            updateCharts(data);
            // Hide loading state
            document.querySelector('.loading').style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching date range data:', error);
            // Hide loading state
            document.querySelector('.loading').style.display = 'none';
        });
}

// Function to refresh data periodically
function startPeriodicRefresh(interval = 300000) { // Default: 5 minutes
    setInterval(() => {
        const params = new URLSearchParams(window.location.search);
        fetch(`${window.location.pathname}?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                updateCharts(data);
            })
            .catch(error => {
                console.error('Error refreshing data:', error);
            });
    }, interval);
}

// Initialize charts when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Start periodic refresh for real-time updates
    startPeriodicRefresh();
    
    // Add event listeners for filter forms
    document.querySelectorAll('form[data-filter-form]').forEach(form => {
        form.addEventListener('submit', handleFilterSubmit);
    });
    
    // Add event listeners for export buttons
    document.querySelectorAll('[data-export-chart]').forEach(button => {
        button.addEventListener('click', function() {
            const chartId = this.dataset.chartId;
            const fileName = this.dataset.fileName;
            exportChartAsImage(chartId, fileName);
        });
    });
}); 