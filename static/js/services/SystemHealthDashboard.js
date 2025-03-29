/**
 * SystemHealthDashboard.js
 * 
 * Provides UI components and API handling for the admin system health dashboard
 * Displays system metrics, alerts, and historical data.
 */

class SystemHealthDashboard {
  constructor() {
    this.refreshInterval = null;
    this.charts = {};
    this.lastUpdate = null;
    this.metricsElement = null;
    this.alertsElement = null;
    this.historyElement = null;
    this.healthData = null;
    
    // Chart configuration
    this.chartConfigs = {
      cpu: {
        title: 'CPU Usage',
        color: '#4e73df',
        unit: '%'
      },
      memory: {
        title: 'Memory Usage',
        color: '#1cc88a',
        unit: '%'
      },
      disk: {
        title: 'Disk Usage',
        color: '#36b9cc',
        unit: '%'
      },
      api_latency: {
        title: 'API Latency',
        color: '#f6c23e',
        unit: 'ms'
      },
      requests: {
        title: 'Requests/min',
        color: '#e74a3b',
        unit: ''
      }
    };
  }

  /**
   * Initialize the dashboard
   * @param {Object} options - Dashboard options
   */
  initialize(options = {}) {
    const {
      metricsElement = 'system-metrics',
      alertsElement = 'system-alerts',
      historyElement = 'system-history',
      autoRefresh = true,
      refreshInterval = 60000
    } = options;

    // Store element references
    this.metricsElement = document.getElementById(metricsElement);
    this.alertsElement = document.getElementById(alertsElement);
    this.historyElement = document.getElementById(historyElement);

    // Validate elements
    if (!this.metricsElement) {
      console.error('Metrics element not found:', metricsElement);
      return;
    }

    // Initial data fetch
    this.fetchHealthData();

    // Set up auto-refresh
    if (autoRefresh) {
      this.startAutoRefresh(refreshInterval);
    }

    // Set up event listeners
    this.setupEventListeners();
  }

  /**
   * Set up event listeners
   */
  setupEventListeners() {
    // Refresh button listener
    const refreshBtn = document.getElementById('refresh-health-data');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.fetchHealthData());
    }

    // Interval selector listener
    const intervalSelect = document.getElementById('refresh-interval');
    if (intervalSelect) {
      intervalSelect.addEventListener('change', (e) => {
        const interval = parseInt(e.target.value, 10);
        if (interval > 0) {
          this.startAutoRefresh(interval);
        } else {
          this.stopAutoRefresh();
        }
      });
    }

    // Time range selector for history
    const timeRangeSelect = document.getElementById('history-time-range');
    if (timeRangeSelect) {
      timeRangeSelect.addEventListener('change', (e) => {
        this.fetchHistoricalData(e.target.value);
      });
    }
  }

  /**
   * Start auto refresh
   * @param {number} interval - Refresh interval in ms
   */
  startAutoRefresh(interval) {
    this.stopAutoRefresh();
    this.refreshInterval = setInterval(() => {
      this.fetchHealthData();
    }, interval);

    console.log(`Auto refresh started with interval ${interval / 1000}s`);
  }

  /**
   * Stop auto refresh
   */
  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
      console.log('Auto refresh stopped');
    }
  }

  /**
   * Fetch system health data
   */
  async fetchHealthData() {
    try {
      // Show loading state
      this.setLoadingState(true);

      // Fetch data from API
      const data = await window.ApiService.get(window.ApiService.apiResources.admin.health, {
        loadingId: 'system-health',
        useCache: false, // Always get fresh health data
      });

      // Update last update timestamp
      this.lastUpdate = new Date();
      this.healthData = data;

      // Update UI with new data
      this.updateMetricsDisplay(data.metrics);
      this.updateAlertsDisplay(data.alerts);
      this.updateStatusIndicators(data.status);
      
      // Also fetch historical data if we have the element
      if (this.historyElement) {
        this.fetchHistoricalData();
      }

      // Update last update time display
      const lastUpdateEl = document.getElementById('last-update-time');
      if (lastUpdateEl) {
        lastUpdateEl.textContent = this.lastUpdate.toLocaleTimeString();
      }

      // Hide loading state
      this.setLoadingState(false);
    } catch (error) {
      console.error('Failed to fetch health data:', error);
      this.setLoadingState(false);
      
      // Show error state
      this.showErrorState('Failed to load system health data. ' + error.message);
    }
  }

  /**
   * Fetch historical health data
   * @param {string} timeRange - Time range to fetch
   */
  async fetchHistoricalData(timeRange = '1h') {
    if (!this.historyElement) return;
    
    try {
      // Show loading state for history
      const historyLoadingEl = document.getElementById('history-loading');
      if (historyLoadingEl) {
        historyLoadingEl.style.display = 'block';
      }

      // Fetch historical data from API
      const data = await window.ApiService.get(
        `${window.ApiService.apiResources.admin.health}/history?range=${timeRange}`, 
        {
          loadingId: 'system-history',
          useCache: false
        }
      );

      // Update charts with historical data
      this.updateHistoricalCharts(data);

      // Hide loading state
      if (historyLoadingEl) {
        historyLoadingEl.style.display = 'none';
      }
    } catch (error) {
      console.error('Failed to fetch historical health data:', error);
      
      // Show error message in history section
      if (this.historyElement) {
        this.historyElement.innerHTML = `
          <div class="alert alert-danger">
            Failed to load historical data: ${error.message}
          </div>
        `;
      }
    }
  }

  /**
   * Update metrics display
   * @param {Object} metrics - System metrics data
   */
  updateMetricsDisplay(metrics) {
    if (!this.metricsElement || !metrics) return;

    // Clear existing content
    this.metricsElement.innerHTML = '';

    // Create metrics grid
    const metricsGrid = document.createElement('div');
    metricsGrid.className = 'row';

    // Add each metric
    Object.entries(metrics).forEach(([key, value]) => {
      // Skip non-numeric values and metadata
      if (typeof value !== 'number' || key === 'timestamp') return;

      // Create metric card
      const metricCard = document.createElement('div');
      metricCard.className = 'col-xl-3 col-md-6 mb-4';
      
      // Determine status color based on thresholds
      let statusColor = 'primary';
      if (key.includes('usage') || key === 'cpu' || key === 'memory' || key === 'disk') {
        if (value > 90) statusColor = 'danger';
        else if (value > 70) statusColor = 'warning';
        else statusColor = 'success';
      } else if (key.includes('latency')) {
        if (value > 500) statusColor = 'danger';
        else if (value > 200) statusColor = 'warning';
        else statusColor = 'success';
      }

      // Format the metric value
      let formattedValue = value;
      let unit = '';
      
      // Add unit based on metric type
      if (key.includes('usage') || key === 'cpu' || key === 'memory' || key === 'disk') {
        unit = '%';
        formattedValue = value.toFixed(1);
      } else if (key.includes('latency')) {
        unit = 'ms';
        formattedValue = value.toFixed(0);
      } else if (key.includes('count')) {
        formattedValue = value.toLocaleString();
      } else if (key.includes('size')) {
        formattedValue = this.formatBytes(value);
        unit = '';
      }

      // Format the metric name for display
      const metricName = key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());

      // Create metric card HTML
      metricCard.innerHTML = `
        <div class="card border-left-${statusColor} shadow h-100 py-2">
          <div class="card-body">
            <div class="row no-gutters align-items-center">
              <div class="col mr-2">
                <div class="text-xs font-weight-bold text-${statusColor} text-uppercase mb-1">
                  ${metricName}
                </div>
                <div class="h5 mb-0 font-weight-bold text-gray-800">
                  ${formattedValue}${unit}
                </div>
              </div>
              <div class="col-auto">
                <i class="bi bi-speedometer2 fa-2x text-gray-300"></i>
              </div>
            </div>
          </div>
        </div>
      `;

      metricsGrid.appendChild(metricCard);
    });

    // Add system info section
    if (metrics.system_info) {
      const infoSection = document.createElement('div');
      infoSection.className = 'col-12 mt-4';
      infoSection.innerHTML = `
        <div class="card shadow mb-4">
          <div class="card-header py-3 d-flex flex-row align-items-center justify-content-between">
            <h6 class="m-0 font-weight-bold text-primary">System Information</h6>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6">
                <table class="table table-sm">
                  <tbody>
                    <tr>
                      <th>Hostname</th>
                      <td>${metrics.system_info.hostname || 'N/A'}</td>
                    </tr>
                    <tr>
                      <th>Platform</th>
                      <td>${metrics.system_info.platform || 'N/A'}</td>
                    </tr>
                    <tr>
                      <th>Python Version</th>
                      <td>${metrics.system_info.python_version || 'N/A'}</td>
                    </tr>
                    <tr>
                      <th>Uptime</th>
                      <td>${this.formatUptime(metrics.system_info.uptime_seconds)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="col-md-6">
                <table class="table table-sm">
                  <tbody>
                    <tr>
                      <th>Process ID</th>
                      <td>${metrics.system_info.pid || 'N/A'}</td>
                    </tr>
                    <tr>
                      <th>CPU Cores</th>
                      <td>${metrics.system_info.cpu_cores || 'N/A'}</td>
                    </tr>
                    <tr>
                      <th>Total Memory</th>
                      <td>${this.formatBytes(metrics.system_info.total_memory) || 'N/A'}</td>
                    </tr>
                    <tr>
                      <th>Flask Version</th>
                      <td>${metrics.system_info.flask_version || 'N/A'}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      `;
      metricsGrid.appendChild(infoSection);
    }

    // Append to the metrics element
    this.metricsElement.appendChild(metricsGrid);
  }

  /**
   * Update alerts display
   * @param {Array} alerts - System alerts
   */
  updateAlertsDisplay(alerts) {
    if (!this.alertsElement || !alerts) return;

    // Clear existing content
    this.alertsElement.innerHTML = '';

    // Create alerts wrapper
    const alertsWrapper = document.createElement('div');
    alertsWrapper.className = 'card shadow mb-4';
    
    // Add header
    const header = document.createElement('div');
    header.className = 'card-header py-3';
    header.innerHTML = `
      <h6 class="m-0 font-weight-bold text-primary">
        System Alerts 
        <span class="badge bg-${alerts.length > 0 ? 'danger' : 'success'} text-white ms-2">
          ${alerts.length}
        </span>
      </h6>
    `;
    alertsWrapper.appendChild(header);
    
    // Add alerts content
    const content = document.createElement('div');
    content.className = 'card-body';
    
    if (alerts.length === 0) {
      content.innerHTML = `
        <div class="text-center">
          <i class="bi bi-check-circle text-success" style="font-size: 2rem;"></i>
          <p class="mt-2">No active alerts. System is running normally.</p>
        </div>
      `;
    } else {
      const alertsList = document.createElement('div');
      alertsList.className = 'list-group';
      
      alerts.forEach(alert => {
        // Determine severity class
        let severityClass = 'info';
        if (alert.severity === 'high') severityClass = 'danger';
        else if (alert.severity === 'medium') severityClass = 'warning';
        else if (alert.severity === 'low') severityClass = 'primary';
        
        // Format timestamp
        const timestamp = new Date(alert.timestamp).toLocaleString();
        
        // Create alert item
        const alertItem = document.createElement('div');
        alertItem.className = `list-group-item list-group-item-${severityClass} d-flex justify-content-between align-items-center`;
        alertItem.innerHTML = `
          <div>
            <h6 class="mb-1">${alert.title}</h6>
            <p class="mb-1 small">${alert.message}</p>
            <small>${timestamp}</small>
          </div>
          <span class="badge bg-${severityClass} rounded-pill">${alert.severity}</span>
        `;
        
        alertsList.appendChild(alertItem);
      });
      
      content.appendChild(alertsList);
    }
    
    alertsWrapper.appendChild(content);
    this.alertsElement.appendChild(alertsWrapper);
  }

  /**
   * Update status indicators
   * @param {Object} status - System status data
   */
  updateStatusIndicators(status) {
    if (!status) return;

    // Update status indicators for each service
    Object.entries(status).forEach(([service, serviceStatus]) => {
      const indicator = document.getElementById(`status-${service}`);
      if (!indicator) return;

      // Update indicator color
      const statusClass = serviceStatus.status === 'ok' ? 'success' : 
                          serviceStatus.status === 'warning' ? 'warning' : 'danger';
      
      // Remove all status classes
      indicator.classList.remove('bg-success', 'bg-warning', 'bg-danger');
      
      // Add current status class
      indicator.classList.add(`bg-${statusClass}`);
      
      // Update tooltip text
      indicator.setAttribute('title', serviceStatus.message || service);
      
      // If using bootstrap tooltips, refresh
      if (window.bootstrap && window.bootstrap.Tooltip) {
        const tooltip = bootstrap.Tooltip.getInstance(indicator);
        if (tooltip) {
          tooltip.dispose();
        }
        new bootstrap.Tooltip(indicator);
      }
    });
  }

  /**
   * Update historical charts
   * @param {Object} historyData - Historical data
   */
  updateHistoricalCharts(historyData) {
    if (!this.historyElement || !historyData || !historyData.metrics) return;

    // Clear existing content
    this.historyElement.innerHTML = '';

    // Create a row for charts
    const chartsRow = document.createElement('div');
    chartsRow.className = 'row';

    // Create charts for each metric
    Object.entries(this.chartConfigs).forEach(([metricKey, config]) => {
      // Skip if no data for this metric
      if (!historyData.metrics[metricKey]) return;

      // Create column for this chart
      const chartCol = document.createElement('div');
      chartCol.className = 'col-xl-6 col-lg-6 mb-4';
      
      // Create card for chart
      const chartCard = document.createElement('div');
      chartCard.className = 'card shadow mb-4';
      
      // Add card header
      const header = document.createElement('div');
      header.className = 'card-header py-3 d-flex flex-row align-items-center justify-content-between';
      header.innerHTML = `<h6 class="m-0 font-weight-bold text-primary">${config.title}</h6>`;
      chartCard.appendChild(header);
      
      // Add card body with canvas
      const body = document.createElement('div');
      body.className = 'card-body';
      
      const canvas = document.createElement('canvas');
      canvas.id = `chart-${metricKey}`;
      body.appendChild(canvas);
      chartCard.appendChild(body);
      
      // Add to row
      chartCol.appendChild(chartCard);
      chartsRow.appendChild(chartCol);
      
      // Get data for this metric
      const metricData = historyData.metrics[metricKey];
      
      // Prepare data for chart
      const labels = metricData.map(point => {
        const date = new Date(point.timestamp);
        return date.toLocaleTimeString();
      });
      
      const values = metricData.map(point => point.value);
      
      // Create or update chart
      this.createChart(canvas.id, config.title, labels, values, config.color, config.unit);
    });

    // Add charts row to history element
    this.historyElement.appendChild(chartsRow);
  }

  /**
   * Create a chart
   * @param {string} canvasId - Canvas element ID
   * @param {string} title - Chart title
   * @param {Array} labels - X-axis labels
   * @param {Array} data - Y-axis data
   * @param {string} color - Chart color
   * @param {string} unit - Data unit
   */
  createChart(canvasId, title, labels, data, color, unit) {
    // Destroy existing chart if any
    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }
    
    // Get canvas context
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Create new chart
    this.charts[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: title,
          data: data,
          backgroundColor: this.hexToRgba(color, 0.1),
          borderColor: color,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: color,
          pointBorderColor: '#fff',
          pointHoverRadius: 5,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            left: 10,
            right: 25,
            top: 25,
            bottom: 0
          }
        },
        scales: {
          x: {
            grid: {
              display: false,
              drawBorder: false
            },
            ticks: {
              maxTicksLimit: 7
            }
          },
          y: {
            beginAtZero: this.shouldStartAtZero(title),
            grid: {
              color: "rgb(234, 236, 244)",
              zeroLineColor: "rgb(234, 236, 244)",
              drawBorder: false,
              borderDash: [2],
              zeroLineBorderDash: [2]
            },
            ticks: {
              callback: function(value) {
                return value + unit;
              }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: "rgb(255,255,255)",
            bodyColor: "#858796",
            titleMarginBottom: 10,
            titleColor: '#6e707e',
            titleFontSize: 14,
            borderColor: '#dddfeb',
            borderWidth: 1,
            padding: 15,
            displayColors: false,
            caretPadding: 10,
            callbacks: {
              label: function(context) {
                const value = context.parsed.y;
                return `${title}: ${value}${unit}`;
              }
            }
          }
        }
      }
    });
  }

  /**
   * Set loading state
   * @param {boolean} isLoading - Whether the dashboard is loading
   */
  setLoadingState(isLoading) {
    const loadingElement = document.getElementById('system-health-loading');
    if (loadingElement) {
      loadingElement.style.display = isLoading ? 'block' : 'none';
    }

    // Also update refresh button if it exists
    const refreshBtn = document.getElementById('refresh-health-data');
    if (refreshBtn) {
      refreshBtn.disabled = isLoading;
      
      const icon = refreshBtn.querySelector('i');
      if (icon) {
        if (isLoading) {
          icon.className = 'bi bi-arrow-clockwise spin';
        } else {
          icon.className = 'bi bi-arrow-clockwise';
        }
      }
    }
  }

  /**
   * Show error state
   * @param {string} message - Error message
   */
  showErrorState(message) {
    if (this.metricsElement) {
      this.metricsElement.innerHTML = `
        <div class="alert alert-danger" role="alert">
          <i class="bi bi-exclamation-triangle-fill me-2"></i>
          ${message}
        </div>
      `;
    }
    
    if (this.alertsElement) {
      this.alertsElement.innerHTML = '';
    }
    
    if (this.historyElement) {
      this.historyElement.innerHTML = '';
    }
  }

  /**
   * Format bytes to human readable string
   * @param {number} bytes - Bytes to format
   * @param {number} decimals - Decimal places
   * @returns {string} Formatted bytes
   */
  formatBytes(bytes, decimals = 2) {
    if (!bytes || bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }

  /**
   * Format uptime to human readable string
   * @param {number} seconds - Uptime in seconds
   * @returns {string} Formatted uptime
   */
  formatUptime(seconds) {
    if (!seconds) return 'N/A';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    
    return parts.join(' ') || '< 1m';
  }

  /**
   * Convert hex color to rgba
   * @param {string} hex - Hex color code
   * @param {number} alpha - Alpha value
   * @returns {string} RGBA color string
   */
  hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  /**
   * Determine if chart should start at zero
   * @param {string} title - Chart title
   * @returns {boolean} Whether chart should start at zero
   */
  shouldStartAtZero(title) {
    // Latency should usually not start at zero
    return !title.includes('Latency');
  }
}

// Export the dashboard
window.SystemHealthDashboard = new SystemHealthDashboard();