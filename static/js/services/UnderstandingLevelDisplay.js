/**
 * UnderstandingLevelDisplay.js
 * 
 * This component is responsible for displaying the profile understanding level
 * with visual indicators, tooltips, and progress visualization. It connects to
 * the /api/v2/profiles/{id}/understanding endpoint to fetch data.
 */

class UnderstandingLevelDisplay {
  constructor() {
    this.baseUrl = '/api/v2';
    this.currentProfileId = null;
    this.currentLevel = null;
    this.levelData = null;
    this.loading = false;
    this.refreshTimer = null;
    this.containerSelector = '.understanding-level-container';
    
    // Integration with ApiService
    this.apiService = window.ApiService;
    
    // Integration with LoadingStateManager if available
    this.loadingStateManager = window.LoadingStateManager || null;
    
    // Integration with ErrorHandlingService if available
    this.errorHandlingService = window.ErrorHandlingService || null;
    
    // Integration with dataEventBus if available
    this.dataEventBus = window.dataEventBus || null;
  }
  
  /**
   * Initialize the UnderstandingLevelDisplay
   * @param {Object} options - Configuration options
   * @param {string} options.profileId - ID of the current profile
   * @param {string} options.containerSelector - CSS selector for the container
   * @param {boolean} options.autoRefresh - Whether to automatically refresh data
   * @param {number} options.refreshInterval - Refresh interval in milliseconds
   * @returns {UnderstandingLevelDisplay} The instance for chaining
   */
  initialize(options = {}) {
    this.currentProfileId = options.profileId || this._extractProfileIdFromUrl();
    this.containerSelector = options.containerSelector || '.understanding-level-container';
    this.autoRefresh = options.autoRefresh || false;
    this.refreshInterval = options.refreshInterval || 60000; // Default: 1 minute
    
    // If API integration is available, fetch level data
    if (this.currentProfileId) {
      this.fetchUnderstandingLevel();
    } else {
      // If no profile ID, try to extract level from the DOM
      this.extractLevelFromDOM();
    }
    
    // Set up automatic refresh if requested
    if (this.autoRefresh) {
      this.startAutoRefresh();
    }
    
    // Subscribe to dataEventBus events if available
    if (this.dataEventBus) {
      this.dataEventBus.subscribe('question:answered', this.handleQuestionAnswered.bind(this));
    }
    
    // Return this for chaining
    return this;
  }
  
  /**
   * Fetch understanding level data from the API
   * @returns {Promise<Object>} The understanding level data
   */
  async fetchUnderstandingLevel() {
    if (!this.currentProfileId) {
      throw new Error('No profile ID provided');
    }
    
    this._setLoading(true);
    
    try {
      // Use ApiService if available, otherwise use fetch directly
      let levelData;
      
      if (this.apiService) {
        levelData = await this.apiService.get(`/profiles/${this.currentProfileId}/understanding`, {
          loadingId: 'understanding-level',
          cacheKey: `understanding-level-${this.currentProfileId}`,
          useCache: true,
          cacheTTL: 300000 // 5 minutes
        });
      } else {
        const response = await fetch(`${this.baseUrl}/profiles/${this.currentProfileId}/understanding`);
        if (!response.ok) {
          throw new Error(`Error fetching understanding level: ${response.statusText}`);
        }
        levelData = await response.json();
      }
      
      if (!levelData) {
        throw new Error('No understanding level data received from API');
      }
      
      // Store the data
      this.levelData = levelData;
      this.currentLevel = levelData.id;
      
      // Update the display
      this.updateDisplay(levelData);
      
      // Emit event
      this._emit('levelFetched', { levelData });
      
      // Return the data
      return levelData;
    } catch (error) {
      this._handleError(error, 'fetching understanding level');
      return null;
    } finally {
      this._setLoading(false);
    }
  }
  
  /**
   * Extract understanding level from the DOM
   * @returns {Object|null} The extracted level data or null
   */
  extractLevelFromDOM() {
    const container = document.querySelector(this.containerSelector);
    if (!container) return null;
    
    // Get level ID from active indicator
    const activeIndicator = container.querySelector('.level-indicator.active');
    if (!activeIndicator) return null;
    
    // Extract level ID from class
    const levelClassMatch = Array.from(activeIndicator.classList)
      .find(cls => cls.startsWith('level-'))
      ?.replace('level-', '')
      ?.toUpperCase();
    
    if (!levelClassMatch) return null;
    
    // Map level class to level ID
    const levelIdMap = {
      'RED': 'RED',
      'AMBER': 'AMBER',
      'YELLOW': 'YELLOW',
      'GREEN': 'GREEN',
      'DARK-GREEN': 'DARK_GREEN',
      'DARK_GREEN': 'DARK_GREEN'
    };
    
    const levelId = levelIdMap[levelClassMatch] || levelClassMatch;
    
    // Extract level label
    const levelLabel = activeIndicator.querySelector('.level-label')?.textContent;
    
    // Extract level description
    const levelDescription = container.querySelector('.understanding-level-description')?.textContent;
    
    // Extract next level info if available
    let nextLevel = null;
    const nextLevelInfo = container.querySelector('.next-level-info');
    if (nextLevelInfo) {
      const nextLevelLabel = nextLevelInfo.querySelector('h5')?.textContent?.replace('Next Level:', '')?.trim();
      
      // Extract requirements
      const requirementItems = nextLevelInfo.querySelectorAll('.next-level-requirements li');
      const requirements = Array.from(requirementItems).map(item => item.textContent);
      
      nextLevel = {
        label: nextLevelLabel,
        requirements: requirements
      };
    }
    
    // Create level data object
    const levelData = {
      id: levelId,
      label: levelLabel,
      description: levelDescription,
      next_level: nextLevel,
      css_class: levelClassMatch.toLowerCase()
    };
    
    // Store the data
    this.levelData = levelData;
    this.currentLevel = levelId;
    
    // Emit event
    this._emit('levelExtracted', { levelData });
    
    return levelData;
  }
  
  /**
   * Update the understanding level display with new data
   * @param {Object} levelData - The understanding level data
   */
  updateDisplay(levelData) {
    if (!levelData) return;
    
    const container = document.querySelector(this.containerSelector);
    if (!container) return;
    
    // Update level badge
    const levelBadge = container.querySelector('.understanding-level-badge');
    if (levelBadge) {
      // Update class
      levelBadge.className = 'understanding-level-badge';
      if (levelData.css_class) {
        levelBadge.classList.add(levelData.css_class);
      }
      
      // Update text
      levelBadge.textContent = levelData.label;
    }
    
    // Update level indicators
    const levelIndicators = container.querySelectorAll('.level-indicator');
    levelIndicators.forEach(indicator => {
      indicator.classList.remove('active');
      
      // Get the level class
      const levelClass = Array.from(indicator.classList)
        .find(cls => cls.startsWith('level-'));
      
      if (!levelClass) return;
      
      // Extract level ID from class
      const levelId = levelClass.replace('level-', '').toUpperCase()
        .replace('-', '_'); // Handle dash vs underscore
      
      // Check if this is the current level
      if (levelId === levelData.id) {
        indicator.classList.add('active');
      }
    });
    
    // Update description
    const descriptionElement = container.querySelector('.understanding-level-description');
    if (descriptionElement && levelData.description) {
      descriptionElement.textContent = levelData.description;
    }
    
    // Update next level info
    const nextLevelInfo = container.querySelector('.next-level-info');
    if (nextLevelInfo) {
      if (levelData.next_level) {
        // Update next level header
        const nextLevelHeader = nextLevelInfo.querySelector('h5');
        if (nextLevelHeader) {
          nextLevelHeader.textContent = `Next Level: ${levelData.next_level.label}`;
        }
        
        // Update requirements
        const requirementsList = nextLevelInfo.querySelector('.next-level-requirements');
        if (requirementsList && levelData.next_level.requirements) {
          requirementsList.innerHTML = levelData.next_level.requirements
            .map(req => `<li>${req}</li>`)
            .join('');
        }
        
        // Make sure it's visible
        nextLevelInfo.style.display = '';
      } else {
        // No next level, hide the container
        nextLevelInfo.style.display = 'none';
      }
    }
    
    // Emit update event
    this._emit('displayUpdated', { levelData });
  }
  
  /**
   * Handle question answered event
   * @param {Object} data - Event data
   */
  handleQuestionAnswered(data) {
    // When a question is answered, refresh the understanding level
    // But use a debounce to avoid too many requests
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    
    this.refreshTimer = setTimeout(() => {
      this.fetchUnderstandingLevel();
    }, 1000);
  }
  
  /**
   * Start auto-refresh for understanding level data
   */
  startAutoRefresh() {
    // Clear any existing timer
    this.stopAutoRefresh();
    
    // Set up new timer
    this.refreshInterval = setInterval(() => {
      this.fetchUnderstandingLevel();
    }, this.refreshInterval);
  }
  
  /**
   * Stop auto-refresh for understanding level data
   */
  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }
  
  /**
   * Extract profile ID from the URL or DOM
   * @private
   * @returns {string|null} Extracted profile ID or null
   */
  _extractProfileIdFromUrl() {
    // Extract from URL path /profile/:id/questions
    const profileMatch = window.location.pathname.match(/\/profile\/([^\/]+)\/questions/);
    if (profileMatch && profileMatch[1]) {
      return profileMatch[1];
    }
    
    // Extract from query string ?profile_id=...
    const urlParams = new URLSearchParams(window.location.search);
    const profileId = urlParams.get('profile_id');
    
    if (profileId) return profileId;
    
    // Try to find it in the DOM
    const profileIdElement = document.querySelector('[data-profile-id]');
    if (profileIdElement) {
      return profileIdElement.dataset.profileId;
    }
    
    // Extract from questions container
    const questionsContainer = document.querySelector('.questions-container');
    if (questionsContainer && questionsContainer.dataset.profileId) {
      return questionsContainer.dataset.profileId;
    }
    
    console.warn('Could not extract profile ID from URL or DOM');
    return null;
  }
  
  /**
   * Set loading state
   * @private
   * @param {boolean} isLoading - Whether loading is active
   */
  _setLoading(isLoading) {
    this.loading = isLoading;
    
    // Use LoadingStateManager if available
    if (this.loadingStateManager) {
      this.loadingStateManager.setLoading('understanding-level', isLoading, {
        text: 'Updating understanding level...'
      });
      return;
    }
    
    // Otherwise, add loading class to container
    const container = document.querySelector(this.containerSelector);
    if (!container) return;
    
    if (isLoading) {
      container.classList.add('loading');
    } else {
      container.classList.remove('loading');
    }
  }
  
  /**
   * Handle errors
   * @private
   * @param {Error} error - The error that occurred
   * @param {string} context - Context in which the error occurred
   */
  _handleError(error, context) {
    console.error(`Error ${context}:`, error);
    
    // Use ErrorHandlingService if available
    if (this.errorHandlingService) {
      this.errorHandlingService.handleError(error, 'understanding_level_display', {
        showToast: false, // Don't show toast for understanding level errors
        metadata: { context, profileId: this.currentProfileId }
      });
      return;
    }
    
    // Otherwise, just log to console
    console.error(`UnderstandingLevelDisplay error ${context}:`, error.message || error);
  }
  
  /**
   * Emit an event
   * @private
   * @param {string} eventName - Name of the event
   * @param {Object} data - Event data
   */
  _emit(eventName, data) {
    // Emit via dataEventBus if available
    if (this.dataEventBus) {
      this.dataEventBus.publish(`understandingLevel:${eventName}`, data);
    }
    
    // Dispatch DOM event
    const customEvent = new CustomEvent(`understandingLevel:${eventName}`, {
      detail: data,
      bubbles: true
    });
    document.dispatchEvent(customEvent);
  }
}

// Create singleton instance
const understandingLevelDisplay = new UnderstandingLevelDisplay();

// Export as both module and global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = understandingLevelDisplay;
} else {
  window.UnderstandingLevelDisplay = understandingLevelDisplay;
}