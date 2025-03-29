/**
 * ProfileSummaryView - Component to display profile summary data
 * 
 * This component connects to the /api/v2/profiles/{id} endpoint to fetch and display
 * profile summary information. Features include:
 * - Data-driven visualization of profile details
 * - Automatic error handling and recovery mechanisms
 * - Refresh/reload capability for updated data
 * - Loading states and UI feedback
 * - Responsive design for all device sizes
 */

class ProfileSummaryView {
  /**
   * Constructor for the ProfileSummaryView component
   * @param {string} containerId - ID of the container element
   * @param {Object} options - Configuration options
   */
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Container element with ID "${containerId}" not found`);
      return;
    }

    // Default options
    this.options = {
      showAnalytics: true,
      showInsights: true,
      showRecommendations: true,
      loadingId: `profile-summary-${containerId}`,
      profileId: null,
      refreshInterval: 0, // 0 means no auto-refresh
      ...options
    };

    // State
    this.state = {
      profile: null,
      analytics: null,
      isLoading: true,
      error: null,
      lastUpdated: null
    };

    // Bind methods
    this.fetchProfileData = this.fetchProfileData.bind(this);
    this.render = this.render.bind(this);
    this.handleRefreshClick = this.handleRefreshClick.bind(this);
    this.setupAutoRefresh = this.setupAutoRefresh.bind(this);
    this.clearAutoRefresh = this.clearAutoRefresh.bind(this);
    this.renderDimension = this.renderDimension.bind(this);
    this.renderInsight = this.renderInsight.bind(this);
    this.renderRecommendation = this.renderRecommendation.bind(this);

    // Set up API connection with error handling
    this.apiConnection = null;

    // Initialize
    this.init();
  }

  /**
   * Initialize the component
   */
  init() {
    // Get profile ID from options or URL
    const profileId = this.options.profileId || this.getProfileIdFromUrl();
    
    if (!profileId) {
      this.state.error = new Error('No profile ID provided');
      this.render();
      return;
    }

    this.options.profileId = profileId;
    
    // Create initial loading state
    this.container.innerHTML = '<div class="profile-summary-loader">Loading profile data...</div>';
    window.LoadingStateManager.setLoading(this.options.loadingId, true, {
      text: 'Loading profile data...'
    });

    // Connect to API and fetch data
    this.connectToApi();
    
    // Set up auto-refresh if configured
    this.setupAutoRefresh();
  }

  /**
   * Connect to the API using the ApiConnectionAdapter
   */
  connectToApi() {
    if (this.apiConnection) {
      this.apiConnection.disconnect();
    }

    const endpoint = `/profiles/${this.options.profileId}`;
    
    // Use the ApiConnectionAdapter for non-React components
    this.apiConnection = window.ApiHooks.ApiConnectionAdapter.connect(
      this,
      endpoint,
      {
        loadingCallback: (isLoading) => {
          this.state.isLoading = isLoading;
          window.LoadingStateManager.setLoading(this.options.loadingId, isLoading);
          this.render();
        },
        dataCallback: (data) => {
          this.state.profile = data;
          this.state.lastUpdated = new Date();
          this.state.error = null;
          
          // Fetch analytics data if applicable
          if (this.options.showAnalytics) {
            this.fetchAnalyticsData();
          } else {
            this.render();
          }
        },
        errorCallback: (error) => {
          this.state.error = error;
          this.state.isLoading = false;
          this.render();
          
          // Handle error with ErrorHandlingService
          window.ErrorHandlingService.handleError(error, 'profile_summary_fetch', {
            showToast: true,
            retryAction: this.fetchProfileData,
            metadata: { profileId: this.options.profileId }
          });
        }
      }
    );
  }

  /**
   * Fetch profile data from the API
   */
  fetchProfileData() {
    if (!this.options.profileId) return;

    this.state.isLoading = true;
    window.LoadingStateManager.setLoading(this.options.loadingId, true, {
      text: 'Loading profile data...'
    });
    
    this.render();
    
    if (this.apiConnection) {
      this.apiConnection.load();
    } else {
      this.connectToApi();
    }
  }

  /**
   * Fetch analytics data if available
   */
  fetchAnalyticsData() {
    if (!this.options.profileId) return;
    
    const endpoint = `/profiles/${this.options.profileId}/analytics`;
    
    window.ApiService.get(endpoint, {
      loadingId: `${this.options.loadingId}-analytics`,
      useCache: true,
      cacheTTL: 300000 // 5 minutes
    })
      .then(data => {
        this.state.analytics = data;
        this.render();
      })
      .catch(error => {
        // Just log the error but don't show it to the user
        // We still want to display the profile even if analytics fails
        console.warn('Failed to load profile analytics:', error);
        
        // Try to use cached data if available
        if (window.ErrorHandlingService.shouldUseFallback('profile-analytics', 'data')) {
          // Record that we're using fallback data
          window.ErrorHandlingService.recordFallbackUsage('profile-analytics', 'data');
          
          // The error handling service will show a toast about using cached data
        }
        
        this.render();
      });
  }

  /**
   * Extract profile ID from URL if present
   * @returns {string|null} Profile ID from URL
   */
  getProfileIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('profile_id') || urlParams.get('id');
  }

  /**
   * Set up auto-refresh if configured
   */
  setupAutoRefresh() {
    this.clearAutoRefresh();
    
    if (this.options.refreshInterval > 0) {
      this.refreshTimer = setInterval(() => {
        this.fetchProfileData();
      }, this.options.refreshInterval);
    }
  }

  /**
   * Clear any existing auto-refresh timer
   */
  clearAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Handle refresh button click
   */
  handleRefreshClick() {
    this.fetchProfileData();
  }

  /**
   * Main render method
   */
  render() {
    const { profile, analytics, isLoading, error, lastUpdated } = this.state;
    
    // Clear container
    this.container.innerHTML = '';
    
    // Handle error state
    if (error && !profile) {
      const errorTemplate = `
        <div class="profile-summary-error">
          <div class="alert alert-danger" role="alert">
            <h5 class="alert-heading">Error Loading Profile</h5>
            <p>${error.message || 'Unable to load profile data'}</p>
            <hr>
            <button class="btn btn-outline-danger btn-sm retry-btn">
              <i class="bi bi-arrow-repeat me-1"></i> Retry
            </button>
          </div>
        </div>
      `;
      
      this.container.innerHTML = errorTemplate;
      
      // Add retry button handler
      this.container.querySelector('.retry-btn').addEventListener('click', this.handleRefreshClick);
      return;
    }
    
    // Handle loading state with no existing data
    if (isLoading && !profile) {
      const loadingTemplate = `
        <div class="profile-summary-loading">
          <div class="d-flex align-items-center justify-content-center p-4">
            <div class="spinner-border text-primary me-2" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <span>Loading profile data...</span>
          </div>
        </div>
      `;
      
      this.container.innerHTML = loadingTemplate;
      return;
    }
    
    // If we have no profile data at all
    if (!profile) {
      const emptyTemplate = `
        <div class="profile-summary-empty">
          <div class="alert alert-info" role="alert">
            <h5 class="alert-heading">No Profile Data</h5>
            <p>No profile data available for the specified ID.</p>
            <hr>
            <button class="btn btn-outline-primary btn-sm retry-btn">
              <i class="bi bi-arrow-repeat me-1"></i> Retry
            </button>
          </div>
        </div>
      `;
      
      this.container.innerHTML = emptyTemplate;
      
      // Add retry button handler
      this.container.querySelector('.retry-btn').addEventListener('click', this.handleRefreshClick);
      return;
    }
    
    // Build profile display
    const profileTemplate = `
      <div class="profile-summary ${isLoading ? 'is-loading' : ''}">
        <div class="profile-summary-header d-flex justify-content-between align-items-center mb-3">
          <h3 class="profile-name">
            ${profile.name || 'Unnamed Profile'}
          </h3>
          <div class="profile-actions">
            <button class="btn btn-sm btn-outline-primary refresh-btn">
              <i class="bi bi-arrow-repeat me-1"></i> Refresh
            </button>
          </div>
        </div>
        
        ${lastUpdated ? `
          <div class="profile-last-updated text-muted small mb-3">
            Last updated: ${lastUpdated.toLocaleString()}
          </div>
        ` : ''}
        
        <div class="row">
          <div class="col-md-4">
            <div class="card card-profile mb-3">
              <div class="card-header">
                <i class="bi bi-person-badge me-2"></i> Profile Information
              </div>
              <div class="card-body">
                <div class="mb-2">
                  <strong>Name:</strong> ${profile.name || 'Not specified'}
                </div>
                <div class="mb-2">
                  <strong>Email:</strong> ${profile.email || 'Not specified'}
                </div>
                <div class="mb-2">
                  <strong>Profile ID:</strong> 
                  <small class="text-muted">${profile.id}</small>
                </div>
                <div class="mb-2">
                  <strong>Created:</strong> 
                  <span>${this.formatDate(profile.created_at)}</span>
                </div>
                <div class="mb-2">
                  <strong>Last Updated:</strong> 
                  <span>${this.formatDate(profile.updated_at)}</span>
                </div>
                <div class="mb-2">
                  <strong>Total Answers:</strong> 
                  <span class="badge bg-primary">${profile.answers ? profile.answers.length : 0}</span>
                </div>
              </div>
            </div>
            
            ${analytics && this.options.showAnalytics ? this.renderAnalyticsSummary(analytics) : ''}
          </div>
          
          <div class="col-md-8">
            ${analytics && this.options.showInsights && analytics.key_insights ? this.renderKeyInsights(analytics.key_insights) : ''}
            
            ${analytics && this.options.showRecommendations && analytics.recommendations ? this.renderRecommendations(analytics.recommendations) : ''}
            
            ${profile.answers && profile.answers.length > 0 ? this.renderAnswersSummary(profile.answers) : ''}
          </div>
        </div>
      </div>
    `;
    
    this.container.innerHTML = profileTemplate;
    
    // Add refresh button handler
    this.container.querySelector('.refresh-btn').addEventListener('click', this.handleRefreshClick);
    
    // Setup dimension charts if analytics are available
    if (analytics && analytics.dimensions) {
      Object.keys(analytics.dimensions).forEach(dimension => {
        const dimensionElement = this.container.querySelector(`#dimension-${dimension}`);
        if (dimensionElement) {
          this.setupDimensionChart(dimensionElement, dimension, analytics.dimensions[dimension]);
        }
      });
    }
  }

  /**
   * Format a date string for display
   * @param {string} dateString - ISO date string
   * @returns {string} Formatted date string
   */
  formatDate(dateString) {
    if (!dateString) return 'Unknown';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch (e) {
      return dateString;
    }
  }

  /**
   * Render analytics summary section
   * @param {Object} analytics - Analytics data
   * @returns {string} HTML for analytics summary
   */
  renderAnalyticsSummary(analytics) {
    if (!analytics) return '';
    
    let dimensionsHtml = '';
    if (analytics.dimensions) {
      dimensionsHtml = Object.keys(analytics.dimensions)
        .map(dimension => this.renderDimension(dimension, analytics.dimensions[dimension]))
        .join('');
    }
    
    return `
      <div class="card card-profile mb-3">
        <div class="card-header">
          <i class="bi bi-graph-up me-2"></i> Analytics Summary
        </div>
        <div class="card-body">
          ${analytics.investment_profile ? `
            <div class="mb-3">
              <strong>Investment Profile:</strong> 
              <span class="badge bg-primary">${analytics.investment_profile.type}</span>
            </div>
          ` : ''}
          
          ${analytics.financial_health_score ? `
            <div class="mb-3">
              <strong>Financial Health:</strong> 
              <div class="progress mt-2">
                <div class="progress-bar 
                  ${this.getHealthScoreClass(analytics.financial_health_score.score)}" 
                  role="progressbar" 
                  style="width: ${analytics.financial_health_score.score}%"
                  aria-valuenow="${analytics.financial_health_score.score}" 
                  aria-valuemin="0" 
                  aria-valuemax="100">
                  ${analytics.financial_health_score.score}%
                </div>
              </div>
              <small class="text-muted d-block mt-1">
                ${analytics.financial_health_score.status || ''}
              </small>
            </div>
          ` : ''}
          
          ${dimensionsHtml ? `
            <div class="mb-0">
              <strong>Key Dimensions:</strong>
              <div class="dimensions-container mt-2">
                ${dimensionsHtml}
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Get CSS class for health score based on value
   * @param {number} score - Health score
   * @returns {string} CSS class
   */
  getHealthScoreClass(score) {
    if (score >= 80) return 'bg-success';
    if (score >= 60) return 'bg-info';
    if (score >= 40) return 'bg-warning';
    return 'bg-danger';
  }

  /**
   * Render a single dimension
   * @param {string} dimension - Dimension name
   * @param {number} value - Dimension value
   * @returns {string} HTML for dimension
   */
  renderDimension(dimension, value) {
    const formattedName = dimension
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
    
    return `
      <div class="dimension-item mb-2">
        <div class="d-flex justify-content-between align-items-center">
          <span>${formattedName}</span>
          <span class="badge bg-primary rounded-pill">${value}/10</span>
        </div>
        <div class="progress mt-1" id="dimension-${dimension}" data-value="${value}">
          <div class="progress-bar bg-primary" role="progressbar" 
            style="width: ${value * 10}%" 
            aria-valuenow="${value}" 
            aria-valuemin="0" 
            aria-valuemax="10">
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Set up dimension chart (can be extended to use more advanced visualizations)
   * @param {HTMLElement} element - Container element
   * @param {string} dimension - Dimension name
   * @param {number} value - Dimension value
   */
  setupDimensionChart(element, dimension, value) {
    // This is a placeholder for more advanced chart setup
    // In a real implementation, this could integrate with libraries like Chart.js
    // For now, we're just using the built-in progress bar
  }

  /**
   * Render key insights section
   * @param {Array} insights - Key insights
   * @returns {string} HTML for insights section
   */
  renderKeyInsights(insights) {
    if (!insights || insights.length === 0) return '';
    
    const insightsHtml = insights
      .map(insight => this.renderInsight(insight))
      .join('');
    
    return `
      <div class="card card-profile mb-3">
        <div class="card-header">
          <i class="bi bi-lightbulb me-2"></i> Key Insights
        </div>
        <div class="card-body">
          <ul class="list-group insights-list">
            ${insightsHtml}
          </ul>
        </div>
      </div>
    `;
  }

  /**
   * Render a single insight
   * @param {string} insight - Insight text
   * @returns {string} HTML for insight
   */
  renderInsight(insight) {
    return `<li class="list-group-item">${insight}</li>`;
  }

  /**
   * Render recommendations section
   * @param {Array} recommendations - Recommendations
   * @returns {string} HTML for recommendations section
   */
  renderRecommendations(recommendations) {
    if (!recommendations || recommendations.length === 0) return '';
    
    const recommendationsHtml = recommendations
      .map(recommendation => this.renderRecommendation(recommendation))
      .join('');
    
    return `
      <div class="card card-profile mb-3">
        <div class="card-header">
          <i class="bi bi-check2-square me-2"></i> Recommendations
        </div>
        <div class="card-body">
          <ul class="list-group recommendations-list">
            ${recommendationsHtml}
          </ul>
        </div>
      </div>
    `;
  }

  /**
   * Render a single recommendation
   * @param {string} recommendation - Recommendation text
   * @returns {string} HTML for recommendation
   */
  renderRecommendation(recommendation) {
    return `<li class="list-group-item">${recommendation}</li>`;
  }

  /**
   * Render answers summary section
   * @param {Array} answers - Profile answers
   * @returns {string} HTML for answers summary
   */
  renderAnswersSummary(answers) {
    if (!answers || answers.length === 0) return '';
    
    // Limit to the most recent 5 answers for the summary view
    const recentAnswers = [...answers]
      .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
      .slice(0, 5);
    
    const answersHtml = recentAnswers.map((answer, index) => `
      <tr>
        <td>
          <span class="text-monospace">${answer.question_id || 'Unknown'}</span>
          ${this.getQuestionTypeBadge(answer.question_id || '')}
        </td>
        <td>
          ${this.formatAnswerValue(answer.answer, index)}
        </td>
        <td>${this.formatDate(answer.timestamp)}</td>
      </tr>
    `).join('');
    
    return `
      <div class="card card-profile mb-3">
        <div class="card-header d-flex justify-content-between align-items-center">
          <div>
            <i class="bi bi-card-list me-2"></i> Recent Answers
          </div>
          <div>
            <span class="badge bg-primary rounded-pill">${answers.length} total</span>
          </div>
        </div>
        <div class="card-body">
          <div class="table-responsive">
            <table class="table table-sm table-striped">
              <thead>
                <tr>
                  <th>Question ID</th>
                  <th>Answer</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                ${answersHtml}
              </tbody>
            </table>
          </div>
          ${answers.length > 5 ? `
            <div class="text-center mt-2">
              <button class="btn btn-sm btn-outline-primary view-all-answers-btn">
                View All ${answers.length} Answers
              </button>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  /**
   * Get badge for question type
   * @param {string} questionId - Question ID
   * @returns {string} HTML for badge
   */
  getQuestionTypeBadge(questionId) {
    if (questionId.endsWith('_insights')) {
      return '<span class="badge bg-info ms-1">LLM Insight</span>';
    } else if (questionId.includes('_next_level_') || questionId.includes('next_level_')) {
      return '<span class="badge bg-success ms-1">Next-Level</span>';
    } else {
      return '<span class="badge bg-primary ms-1">Core</span>';
    }
  }

  /**
   * Format answer value for display
   * @param {*} answer - Answer value
   * @param {number} index - Answer index
   * @returns {string} Formatted answer HTML
   */
  formatAnswerValue(answer, index) {
    if (!answer) return 'No answer';
    
    if (typeof answer === 'object') {
      return `
        <button class="btn btn-sm btn-outline-info" type="button" data-bs-toggle="collapse" data-bs-target="#insight-${index}">
          View Details
        </button>
        <div class="collapse mt-2" id="insight-${index}">
          <div class="card card-body">
            <pre class="small">${JSON.stringify(answer, null, 2)}</pre>
          </div>
        </div>
      `;
    }
    
    return answer.toString();
  }

  /**
   * Update the component's options
   * @param {Object} newOptions - New options to set
   */
  updateOptions(newOptions) {
    this.options = {
      ...this.options,
      ...newOptions
    };
    
    // If profile ID changed, refetch data
    if (newOptions.profileId && newOptions.profileId !== this.options.profileId) {
      this.fetchProfileData();
    }
    
    // Update auto-refresh if interval changed
    if (newOptions.refreshInterval !== undefined) {
      this.setupAutoRefresh();
    }
    
    // Re-render if display options changed
    this.render();
  }
}

// Export the component globally
window.ProfileSummaryView = ProfileSummaryView;