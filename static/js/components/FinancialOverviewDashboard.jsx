/**
 * FinancialOverviewDashboard Component
 * 
 * This component renders a comprehensive financial overview dashboard
 * for a user's profile, showing key metrics, asset allocation,
 * goal progress summaries, and recommended actions.
 * 
 * It connects to the /api/v2/profiles/{id}/overview endpoint
 * and supports various data visualization components.
 */

class FinancialOverviewDashboard {
  constructor(container, profileId, options = {}) {
    this.container = typeof container === 'string' 
      ? document.getElementById(container) 
      : container;
    
    if (!this.container) {
      console.error('Dashboard container not found');
      return;
    }
    
    this.profileId = profileId;
    this.options = {
      refreshInterval: 0, // Auto-refresh interval in ms (0 for no auto-refresh)
      showAssetAllocation: true,
      showIncomeBreakdown: true,
      showGoalProgress: true,
      showRecommendations: true,
      ...options
    };
    
    this.state = {
      loading: true,
      error: null,
      data: null,
      lastUpdated: null
    };
    
    this.refreshTimer = null;
    
    // Initialize the dashboard
    this.init();
  }
  
  /**
   * Initialize the dashboard
   */
  init() {
    // Create loading state
    this.renderLoadingState();
    
    // Load initial data
    this.loadDashboardData();
    
    // Set up refresh timer if enabled
    if (this.options.refreshInterval > 0) {
      this.setupRefreshTimer();
    }
  }
  
  /**
   * Set up auto-refresh timer
   */
  setupRefreshTimer() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
    
    this.refreshTimer = setInterval(() => {
      this.loadDashboardData(true); // Silent refresh
    }, this.options.refreshInterval);
  }
  
  /**
   * Load dashboard data from API
   * @param {boolean} silent - Whether to show loading indicators
   */
  loadDashboardData(silent = false) {
    if (!silent) {
      this.setState({ loading: true });
    }
    
    const loadingId = `overview-dashboard-${this.profileId}`;
    
    // Call the API service
    const apiService = window.ApiService;
    const endpoint = apiService.apiResources && apiService.apiResources.profiles
      ? apiService.apiResources.profiles.overview(this.profileId)
      : `/profiles/${this.profileId}/overview`;
    
    apiService.get(
      endpoint,
      {
        loadingId: silent ? null : loadingId,
        cacheTTL: 300000, // 5 minute cache
        useCache: true
      }
    )
    .then(data => {
      this.setState({
        loading: false,
        data,
        error: null,
        lastUpdated: new Date()
      });
      this.renderDashboard();
    })
    .catch(error => {
      // Log the error
      console.error('Error loading financial overview:', error);
      
      // Use error handling service if available
      if (window.ErrorHandlingService) {
        window.ErrorHandlingService.handleError(error, 'loading financial overview', {
          showToast: !silent,
          retryAction: () => this.loadDashboardData()
        });
        
        // Check if we should use fallback
        if (typeof window.ErrorHandlingService.shouldUseFallback === 'function' &&
            window.ErrorHandlingService.shouldUseFallback('financial-overview', 'network')) {
          // Use existing data if available
          if (this.state.data) {
            window.ErrorHandlingService.recordFallbackUsage('financial-overview', 'network', {
              profileId: this.profileId
            });
            
            this.setState({
              loading: false,
              error: error
            });
            return;
          }
        }
      }
      
      this.setState({
        loading: false,
        error: error,
        data: null
      });
      this.renderErrorState();
    });
  }
  
  /**
   * Update component state
   * @param {Object} newState - New state to merge
   */
  setState(newState) {
    this.state = {
      ...this.state,
      ...newState
    };
  }
  
  /**
   * Render loading state
   */
  renderLoadingState() {
    if (!this.container) return;
    
    // Create skeleton loaders
    this.container.innerHTML = `
      <div class="financial-overview-dashboard p-4 rounded-lg border border-gray-200 bg-white shadow-sm">
        <div class="mb-4 flex justify-between items-center">
          <h2 class="text-2xl font-bold text-gray-800 skeleton-loader skeleton-text width-50"></h2>
          <div class="skeleton-loader skeleton-text width-25"></div>
        </div>
        
        <div class="summary-metrics grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          ${Array(3).fill().map(() => `
            <div class="metric-card p-4 rounded-md border border-gray-100 bg-gray-50">
              <div class="skeleton-loader skeleton-text width-50"></div>
              <div class="skeleton-loader skeleton-text width-75 mt-2"></div>
            </div>
          `).join('')}
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="dashboard-panel p-4 rounded-md border border-gray-200">
            <div class="skeleton-loader skeleton-text width-50 mb-3"></div>
            <div class="h-48 skeleton-loader skeleton-box"></div>
          </div>
          
          <div class="dashboard-panel p-4 rounded-md border border-gray-200">
            <div class="skeleton-loader skeleton-text width-50 mb-3"></div>
            <div class="h-48 skeleton-loader skeleton-box"></div>
          </div>
        </div>
        
        <div class="dashboard-panel p-4 rounded-md border border-gray-200 mt-6">
          <div class="skeleton-loader skeleton-text width-50 mb-3"></div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${Array(4).fill().map(() => `
              <div class="flex items-center p-2 rounded border border-gray-100">
                <div class="skeleton-loader skeleton-circle mr-3" style="width: 2rem; height: 2rem;"></div>
                <div class="flex-1">
                  <div class="skeleton-loader skeleton-text width-75"></div>
                  <div class="skeleton-loader skeleton-text width-50 mt-1"></div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }
  
  /**
   * Render error state
   */
  renderErrorState() {
    if (!this.container) return;
    
    this.container.innerHTML = `
      <div class="financial-overview-dashboard-error p-8 rounded-lg border border-red-100 bg-red-50 text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-red-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 class="text-lg font-semibold text-red-800 mb-2">Unable to load financial overview</h3>
        <p class="text-red-700 mb-4">${this.state.error ? this.state.error.message : 'An unknown error occurred'}</p>
        <button id="retry-dashboard-load" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md">
          Retry
        </button>
      </div>
    `;
    
    // Add click handler for retry button
    const retryButton = document.getElementById('retry-dashboard-load');
    if (retryButton) {
      retryButton.addEventListener('click', () => this.loadDashboardData());
    }
  }
  
  /**
   * Format currency amounts
   * @param {number} amount - Amount to format
   * @param {string} currency - Currency code (default: INR)
   * @returns {string} Formatted currency
   */
  formatCurrency(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: 0
    }).format(amount);
  }
  
  /**
   * Format percentage values
   * @param {number} value - Value to format
   * @param {number} decimals - Number of decimal places
   * @returns {string} Formatted percentage
   */
  formatPercentage(value, decimals = 1) {
    return `${value.toFixed(decimals)}%`;
  }
  
  /**
   * Format date values
   * @param {Date|string} date - Date to format
   * @returns {string} Formatted date
   */
  formatDate(date) {
    const dateObj = date instanceof Date ? date : new Date(date);
    return dateObj.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
  
  /**
   * Get color scale for asset allocation chart
   * @returns {string[]} Array of colors
   */
  getColorScale() {
    return [
      '#4F46E5', // Indigo
      '#2563EB', // Blue
      '#0EA5E9', // Light Blue
      '#10B981', // Emerald
      '#84CC16', // Lime
      '#EAB308', // Yellow
      '#F59E0B', // Amber
      '#EC4899', // Pink
      '#8B5CF6', // Purple
      '#6366F1'  // Indigo (lighter)
    ];
  }
  
  /**
   * Get icon for a goal type
   * @param {string} goalType - Type of goal
   * @returns {string} SVG icon markup
   */
  getGoalIcon(goalType) {
    const iconMap = {
      retirement: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
      </svg>`,
      education: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path d="M12 14l9-5-9-5-9 5 9 5z" />
        <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
      </svg>`,
      home: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>`,
      emergency: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>`,
      wedding: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>`,
      debt: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>`,
      custom: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11" />
      </svg>`,
      default: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>`
    };
    
    return iconMap[goalType] || iconMap.default;
  }
  
  /**
   * Get icon for a recommendation type
   * @param {string} type - Type of recommendation
   * @returns {string} SVG icon markup
   */
  getRecommendationIcon(type) {
    const iconMap = {
      contribution: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>`,
      allocation: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>`,
      expense: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>`,
      income: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>`,
      timeline: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>`,
      default: `<svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>`
    };
    
    return iconMap[type] || iconMap.default;
  }
  
  /**
   * Render the dashboard with data
   */
  renderDashboard() {
    if (!this.container || !this.state.data) return;
    
    const { data } = this.state;
    const { profile, summary, assets, goals, recommendations } = data;
    
    // Create the dashboard structure
    this.container.innerHTML = `
      <div class="financial-overview-dashboard p-4 rounded-lg border border-gray-200 bg-white shadow-sm">
        <div class="mb-4 flex justify-between items-center">
          <h2 class="text-2xl font-bold text-gray-800">Financial Overview</h2>
          <div class="text-sm text-gray-500">
            Last updated: ${this.formatDate(this.state.lastUpdated)}
            <button id="refresh-dashboard" class="ml-2 text-blue-600 hover:text-blue-800">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
        </div>
        
        <div class="summary-metrics grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div class="metric-card p-4 rounded-md border border-gray-100 bg-gray-50">
            <div class="text-sm font-medium text-gray-500">Net Worth</div>
            <div class="text-2xl font-bold text-blue-700 mt-1">${this.formatCurrency(summary.netWorth)}</div>
          </div>
          
          <div class="metric-card p-4 rounded-md border border-gray-100 bg-gray-50">
            <div class="text-sm font-medium text-gray-500">Monthly Savings</div>
            <div class="text-2xl font-bold text-green-700 mt-1">${this.formatCurrency(summary.monthlySavings)}</div>
          </div>
          
          <div class="metric-card p-4 rounded-md border border-gray-100 bg-gray-50">
            <div class="text-sm font-medium text-gray-500">Goals Success Rate</div>
            <div class="text-2xl font-bold text-indigo-700 mt-1">
              ${this.formatPercentage(summary.goalSuccessRate)}
              <span class="text-sm font-normal text-gray-500">(${goals.length} goals)</span>
            </div>
          </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          ${this.options.showAssetAllocation ? `
          <div class="dashboard-panel p-4 rounded-md border border-gray-200">
            <h3 class="text-lg font-medium text-gray-800 mb-3">Asset Allocation</h3>
            <div id="asset-allocation-chart" class="h-48"></div>
            <div class="grid grid-cols-2 gap-2 mt-3">
              ${assets.allocation.map(item => `
                <div class="flex items-center">
                  <div class="w-3 h-3 rounded-full mr-2" style="background-color: ${item.color || '#888'}"></div>
                  <div class="text-sm">
                    <span class="font-medium">${item.name}</span>
                    <span class="text-gray-500 ml-1">${this.formatPercentage(item.percentage)}</span>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
          ` : ''}
          
          ${this.options.showIncomeBreakdown ? `
          <div class="dashboard-panel p-4 rounded-md border border-gray-200">
            <h3 class="text-lg font-medium text-gray-800 mb-3">Income vs. Expenses</h3>
            <div id="income-expense-chart" class="h-48"></div>
            <div class="grid grid-cols-2 gap-4 mt-3">
              <div>
                <div class="text-sm font-medium text-gray-500">Monthly Income</div>
                <div class="text-lg font-medium text-green-700">${this.formatCurrency(summary.monthlyIncome)}</div>
              </div>
              <div>
                <div class="text-sm font-medium text-gray-500">Monthly Expenses</div>
                <div class="text-lg font-medium text-red-700">${this.formatCurrency(summary.monthlyExpenses)}</div>
              </div>
            </div>
          </div>
          ` : ''}
        </div>
        
        ${this.options.showGoalProgress ? `
        <div class="dashboard-panel p-4 rounded-md border border-gray-200 mt-6">
          <h3 class="text-lg font-medium text-gray-800 mb-3">Goal Progress</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${goals.map(goal => `
              <div class="flex items-start p-3 rounded border border-gray-100 hover:bg-gray-50 transition-colors">
                <div class="text-blue-600 mr-3">
                  ${this.getGoalIcon(goal.type)}
                </div>
                <div class="flex-1">
                  <div class="flex justify-between">
                    <h4 class="font-medium text-gray-800">${goal.name}</h4>
                    <span class="text-sm font-medium ${goal.probability >= 70 ? 'text-green-600' : goal.probability >= 40 ? 'text-amber-600' : 'text-red-600'}">
                      ${this.formatPercentage(goal.probability)}
                    </span>
                  </div>
                  <div class="text-sm text-gray-500">${goal.targetDate ? `Target: ${this.formatDate(goal.targetDate)}` : ''}</div>
                  <div class="mt-2 w-full bg-gray-200 rounded-full h-2.5">
                    <div class="h-2.5 rounded-full ${goal.progress >= 70 ? 'bg-green-600' : goal.progress >= 40 ? 'bg-amber-500' : 'bg-red-600'}" 
                         style="width: ${goal.progress}%"></div>
                  </div>
                  <div class="flex justify-between mt-1 text-xs text-gray-500">
                    <span>Current: ${this.formatCurrency(goal.currentAmount)}</span>
                    <span>Target: ${this.formatCurrency(goal.targetAmount)}</span>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
        ` : ''}
        
        ${this.options.showRecommendations && recommendations.length > 0 ? `
        <div class="dashboard-panel p-4 rounded-md border border-gray-200 mt-6">
          <h3 class="text-lg font-medium text-gray-800 mb-3">Recommendations</h3>
          <div class="grid grid-cols-1 gap-3">
            ${recommendations.map(rec => `
              <div class="flex items-start p-3 rounded border border-blue-100 bg-blue-50">
                <div class="text-blue-600 mr-3">
                  ${this.getRecommendationIcon(rec.type)}
                </div>
                <div class="flex-1">
                  <h4 class="font-medium text-gray-800">${rec.title}</h4>
                  <p class="text-gray-600 text-sm">${rec.description}</p>
                  ${rec.impact ? `
                    <div class="mt-2 text-sm">
                      <span class="font-medium text-blue-600">Impact:</span> 
                      <span>${rec.impact}</span>
                    </div>
                  ` : ''}
                </div>
                <div>
                  <button class="recommendation-action text-sm bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded" 
                          data-action="${rec.actionType || ''}" 
                          data-id="${rec.id}">
                    ${rec.actionText || 'Apply'}
                  </button>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
        ` : ''}
      </div>
    `;
    
    // Set up event listeners
    const refreshButton = document.getElementById('refresh-dashboard');
    if (refreshButton) {
      refreshButton.addEventListener('click', () => this.loadDashboardData());
    }
    
    // Set up action buttons
    const actionButtons = this.container.querySelectorAll('.recommendation-action');
    actionButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        const actionType = button.getAttribute('data-action');
        const id = button.getAttribute('data-id');
        this.handleRecommendationAction(actionType, id);
      });
    });
    
    // Initialize charts if they exist
    this.initializeCharts();
  }
  
  /**
   * Initialize charts for the dashboard
   */
  initializeCharts() {
    if (!this.state.data) return;
    
    const { assets, summary } = this.state.data;
    
    // Asset allocation chart
    if (this.options.showAssetAllocation && assets && assets.allocation && 
        assets.allocation.length > 0 && typeof window.ApexCharts === 'function') {
      const assetChartElement = document.getElementById('asset-allocation-chart');
      if (assetChartElement) {
        const chartColors = this.getColorScale();
        
        // Prepare data for the chart
        const allocationData = assets.allocation.map(item => item.percentage);
        const allocationLabels = assets.allocation.map(item => item.name);
        
        const assetAllocationChart = new ApexCharts(assetChartElement, {
          series: allocationData,
          labels: allocationLabels,
          chart: {
            type: 'donut',
            height: 250
          },
          colors: chartColors,
          legend: {
            show: false
          },
          dataLabels: {
            enabled: false
          },
          plotOptions: {
            pie: {
              donut: {
                size: '65%'
              }
            }
          },
          responsive: [{
            breakpoint: 480,
            options: {
              chart: {
                height: 200
              }
            }
          }]
        });
        
        assetAllocationChart.render();
      }
    }
    
    // Income vs Expenses chart
    if (this.options.showIncomeBreakdown && summary && 
        summary.monthlyIncome !== undefined && summary.monthlyExpenses !== undefined && 
        typeof window.ApexCharts === 'function') {
      const incomeExpenseElement = document.getElementById('income-expense-chart');
      if (incomeExpenseElement) {
        const incomeExpenseChart = new ApexCharts(incomeExpenseElement, {
          series: [{
            name: 'Income',
            data: [summary.monthlyIncome]
          }, {
            name: 'Expenses',
            data: [summary.monthlyExpenses]
          }, {
            name: 'Savings',
            data: [summary.monthlySavings]
          }],
          chart: {
            type: 'bar',
            height: 250,
            stacked: true,
            toolbar: {
              show: false
            }
          },
          colors: ['#10B981', '#EF4444', '#3B82F6'],
          plotOptions: {
            bar: {
              horizontal: false,
              columnWidth: '40%'
            },
          },
          dataLabels: {
            enabled: false
          },
          xaxis: {
            categories: ['Monthly Breakdown'],
            labels: {
              show: false
            }
          },
          yaxis: {
            labels: {
              formatter: (value) => this.formatCurrency(value, 'INR')
            }
          },
          legend: {
            position: 'bottom',
            horizontalAlign: 'center'
          },
          tooltip: {
            y: {
              formatter: (value) => this.formatCurrency(value, 'INR')
            }
          }
        });
        
        incomeExpenseChart.render();
      }
    }
  }
  
  /**
   * Handle recommendation action clicks
   * @param {string} actionType - Type of action
   * @param {string} id - ID of the recommendation
   */
  handleRecommendationAction(actionType, id) {
    // Implement action handling based on the action type
    console.log(`Action: ${actionType}, ID: ${id}`);
    
    // Validate input
    if (!id) {
      console.error('Missing recommendation ID');
      if (window.ErrorHandlingService) {
        window.ErrorHandlingService.showErrorToast('Cannot apply recommendation: Missing ID', {
          level: 'error', 
          duration: 5000
        });
      }
      return;
    }
    
    // Show loading indicator
    if (window.LoadingStateManager) {
      window.LoadingStateManager.setLoading('recommendation-action', true, {
        text: 'Applying recommendation...'
      });
    }
    
    // Call appropriate API endpoint based on action type
    let apiEndpoint;
    let apiMethod = 'POST';
    let apiData = { recommendationId: id };
    
    switch (actionType) {
      case 'adjust_contribution':
        apiEndpoint = `/api/v2/profiles/${this.profileId}/recommendations/contribution`;
        break;
      case 'adjust_allocation':
        apiEndpoint = `/api/v2/profiles/${this.profileId}/recommendations/allocation`;
        break;
      case 'adjust_timeline':
        apiEndpoint = `/api/v2/profiles/${this.profileId}/recommendations/timeline`;
        break;
      default:
        apiEndpoint = `/api/v2/profiles/${this.profileId}/recommendations/apply`;
    }
    
    // Make API call
    const apiService = window.ApiService;
    apiService.request(apiMethod, apiEndpoint, apiData, {
      loadingId: 'recommendation-action',
      allowFailure: false // Ensure errors are handled properly
    })
    .then(response => {
      // Show success message
      window.ErrorHandlingService.showErrorToast(`Recommendation applied successfully.`, {
        level: 'success',
        duration: 3000
      });
      
      // Refresh dashboard
      this.loadDashboardData();
    })
    .catch(error => {
      // Handle error
      window.ErrorHandlingService.handleError(error, 'applying recommendation', {
        showToast: true,
        retryAction: () => this.handleRecommendationAction(actionType, id)
      });
    })
    .finally(() => {
      // Hide loading indicator
      window.LoadingStateManager.setLoading('recommendation-action', false);
    });
  }
  
  /**
   * Update dashboard options
   * @param {Object} newOptions - New options to set
   */
  updateOptions(newOptions) {
    this.options = {
      ...this.options,
      ...newOptions
    };
    
    // Update refresh timer if interval changed
    if (newOptions.refreshInterval !== undefined) {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer);
        this.refreshTimer = null;
      }
      
      if (this.options.refreshInterval > 0) {
        this.setupRefreshTimer();
      }
    }
    
    // Re-render dashboard with current data
    if (this.state.data) {
      this.renderDashboard();
    }
  }
  
  /**
   * Clean up resources used by the dashboard
   */
  destroy() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
    
    // Clear the container
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}

// Export the component
window.FinancialOverviewDashboard = FinancialOverviewDashboard;