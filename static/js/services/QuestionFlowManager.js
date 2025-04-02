/**
 * QuestionFlowManager.js
 *
 * Manages the question flow state, progress tracking, and API interactions
 * for the question flow feature in the Financial Profiler application.
 */

class QuestionFlowManager {
  constructor() {
    this.baseUrl = '/api/v2';
    this.currentProfileId = null;
    this.currentQuestionData = null;
    this.progressData = null;
    this.answerHistory = [];
    this.isLoading = false;
    this.loadingTimeout = null;
    this.localStorage = window.localStorage;
    this.eventListeners = {};

    // Integration with ApiService
    this.apiService = window.ApiService;

    // Integration with LoadingStateManager if available
    this.loadingStateManager = window.LoadingStateManager || null;

    // Integration with ErrorHandlingService if available
    this.errorHandlingService = window.ErrorHandlingService || null;
  }

  /**
   * Initialize the QuestionFlowManager
   * @param {Object} options - Configuration options
   * @param {string} options.profileId - ID of the current profile
   * @param {string} options.containerSelector - DOM selector for the question container
   * @param {Function} options.onQuestionLoad - Callback when a question is loaded
   */
  initialize(options = {}) {
    this.currentProfileId = options.profileId || this._extractProfileIdFromUrl();
    this.containerSelector = options.containerSelector || '.question-answer-section';
    this.onQuestionLoad = options.onQuestionLoad || null;

    // Load any saved state from localStorage
    this._loadSavedState();

    // Attach event listeners for UI elements
    this._attachEventListeners();

    // Register with ApiService if available
    if (this.apiService && typeof this.apiService.registerStaticHandler === 'function') {
      this.apiService.registerStaticHandler('questions/flow', this);
    }

    // Return this for chaining
    return this;
  }

  /**
   * Load the next question for the current profile
   * @returns {Promise<Object>} The loaded question data
   */
  async loadNextQuestion() {
    if (!this.currentProfileId) {
      throw new Error('No profile ID provided. Call initialize() first.');
    }

    this._setLoading(true, 'Loading next question...');

    try {
      // Use ApiService if available, otherwise use fetch directly
      let questionData;

      if (this.apiService) {
        questionData = await this.apiService.get(`/questions/flow`, {
          params: { profile_id: this.currentProfileId },
          loadingId: 'question-flow',
          cacheKey: `question-flow-${this.currentProfileId}`,
          useCache: false
        });
      } else {
        const response = await fetch(`${this.baseUrl}/questions/flow?profile_id=${this.currentProfileId}`);
        if (!response.ok) {
          throw new Error(`Error fetching next question: ${response.statusText}`);
        }
        questionData = await response.json();
      }

      if (!questionData || (questionData.no_questions && !questionData.next_question)) {
        // No more questions - handle completion
        this._handleQuestionCompletion();
        return null;
      }

      // Store the current question
      this.currentQuestionData = questionData.next_question;
      this.progressData = questionData.completion;

      // Save state to localStorage
      this._saveCurrentState();

      // Render the question to the UI
      this._renderQuestion(this.currentQuestionData);

      // Update progress indicators
      this._updateProgressIndicators(this.progressData);

      // Call the onQuestionLoad callback if provided
      if (this.onQuestionLoad && typeof this.onQuestionLoad === 'function') {
        this.onQuestionLoad(this.currentQuestionData, this.progressData);
      }

      // Emit question loaded event
      this._emit('questionLoaded', {
        question: this.currentQuestionData,
        progress: this.progressData
      });

      return this.currentQuestionData;
    } catch (error) {
      this._handleError(error, 'loading question');
      return null;
    } finally {
      this._setLoading(false);
    }
  }

  /**
   * Submit an answer to the current question
   * @param {*} answer - The answer data to submit
   * @returns {Promise<Object>} The submission result
   */
  async submitAnswer(answer) {
    if (!this.currentQuestionData) {
      throw new Error('No current question. Call loadNextQuestion() first.');
    }

    this._setLoading(true, 'Submitting your answer...');

    try {
      const questionId = this.currentQuestionData.id;
      const formData = {
        profile_id: this.currentProfileId,
        question_id: questionId,
        answer: answer
      };

      // Use ApiService if available, otherwise use fetch directly
      let result;

      if (this.apiService) {
        result = await this.apiService.post(`/questions/submit`, formData, {
          loadingId: 'question-submit',
          cacheKey: `question-submit-${this.currentProfileId}-${questionId}`,
          context: 'question_answer'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/questions/submit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData)
        });

        if (!response.ok) {
          throw new Error(`Error submitting answer: ${response.statusText}`);
        }

        result = await response.json();
      }

      // Add to answer history
      this.answerHistory.push({
        questionId,
        question: this.currentQuestionData.text,
        answer,
        timestamp: new Date().toISOString()
      });

      // Save updated state
      this._saveCurrentState();

      // Emit answer submitted event
      this._emit('answerSubmitted', {
        questionId,
        answer,
        result
      });

      // Load the next question
      await this.loadNextQuestion();

      return result;
    } catch (error) {
      this._handleError(error, 'submitting answer');
      return null;
    } finally {
      this._setLoading(false);
    }
  }

  /**
   * Get current progress data
   * @returns {Object} Current progress metrics
   */
  getProgressData() {
    return this.progressData || {};
  }

  /**
   * Get answer history
   * @returns {Array} History of submitted answers
   */
  getAnswerHistory() {
    return [...this.answerHistory];
  }

  /**
   * Clear all saved state
   */
  clearState() {
    this.localStorage.removeItem(`question_flow_state_${this.currentProfileId}`);
    this.answerHistory = [];
    this.currentQuestionData = null;
    this.progressData = null;
  }

  /**
   * Add event listener
   * @param {string} event - Event name to listen for
   * @param {Function} callback - Function to call when event occurs
   */
  on(event, callback) {
    if (!this.eventListeners[event]) {
      this.eventListeners[event] = [];
    }
    this.eventListeners[event].push(callback);
    return this;
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} callback - Function to remove
   */
  off(event, callback) {
    if (!this.eventListeners[event]) return this;
    this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
    return this;
  }

  /**
   * Extract profile ID from the current URL
   * @private
   * @returns {string|null} Extracted profile ID or null
   */
  _extractProfileIdFromUrl() {
    // Extract profile ID from URL pattern /profile/:id/questions
    const profileMatch = window.location.pathname.match(/\/profile\/([^\/]+)\/questions/);
    if (profileMatch && profileMatch[1]) {
      return profileMatch[1];
    }

    // Also try to get from query string ?profile_id=...
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('profile_id');
  }

  /**
   * Save current state to localStorage
   * @private
   */
  _saveCurrentState() {
    if (!this.currentProfileId) return;

    const state = {
      currentQuestionData: this.currentQuestionData,
      progressData: this.progressData,
      answerHistory: this.answerHistory,
      lastUpdated: new Date().toISOString()
    };

    try {
      this.localStorage.setItem(
        `question_flow_state_${this.currentProfileId}`,
        JSON.stringify(state)
      );
    } catch (error) {
      console.warn('Failed to save question flow state to localStorage', error);
    }
  }

  /**
   * Load saved state from localStorage
   * @private
   */
  _loadSavedState() {
    if (!this.currentProfileId) return;

    try {
      const savedState = this.localStorage.getItem(`question_flow_state_${this.currentProfileId}`);
      if (savedState) {
        const state = JSON.parse(savedState);
        this.currentQuestionData = state.currentQuestionData;
        this.progressData = state.progressData;
        this.answerHistory = state.answerHistory || [];

        // Check if state is too old (over 24 hours)
        const lastUpdated = new Date(state.lastUpdated);
        const now = new Date();
        const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;

        if (now - lastUpdated > TWENTY_FOUR_HOURS) {
          console.log('Saved question flow state is too old, clearing it');
          this.clearState();
        }
      }
    } catch (error) {
      console.warn('Failed to load question flow state from localStorage', error);
    }
  }

  /**
   * Attach event listeners to UI elements
   * @private
   */
  _attachEventListeners() {
    // Listen for form submission
    document.addEventListener('submit', this._handleFormSubmit.bind(this));

    // Listen for reload/back events
    window.addEventListener('beforeunload', () => {
      // Save current state before unloading
      this._saveCurrentState();
    });
  }

  /**
   * Handle form submission
   * @private
   * @param {Event} event - Form submission event
   */
  _handleFormSubmit(event) {
    // Only handle answer form submissions
    const form = event.target;
    if (form.id !== 'answer-form') return;

    // Prevent default form submission
    event.preventDefault();

    // Check if this is our current question
    const questionIdInput = form.querySelector('input[name="question_id"]');
    if (!questionIdInput || questionIdInput.value !== this.currentQuestionData?.id) return;

    // Extract answer data from form
    const formData = new FormData(form);
    let answer = formData.get('answer');
    const inputType = formData.get('input_type');

    // Handle multiselect answers
    if (inputType === 'multiselect') {
      const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked');
      if (checkboxes.length > 0) {
        answer = Array.from(checkboxes).map(cb => cb.value);
      }
    }

    // Submit the answer
    this.submitAnswer(answer).catch(error => {
      console.error('Error submitting answer:', error);
    });
  }

  /**
   * Render question to the UI
   * @private
   * @param {Object} questionData - Question data to render
   */
  _renderQuestion(questionData) {
    // Find the container
    const container = document.querySelector(this.containerSelector);
    if (!container) {
      console.error(`Question container not found: ${this.containerSelector}`);
      return;
    }

    // If using a template-based approach, we'll leave rendering to the template engine
    if (this._isServerRendered()) {
      // Emit event so the server can handle the rendering
      this._emit('requestRender', { questionData });
      return;
    }

    // For client-side rendering, we would implement DOM manipulation here
    // But for the integration with the existing template-based system,
    // we'll rely on the server-side rendering for now
    console.log('Client-side rendering not implemented. Using server-side rendering.');
  }

  /**
   * Update progress indicators in the UI
   * @private
   * @param {Object} progressData - Progress data to display
   */
  _updateProgressIndicators(progressData) {
    if (!progressData) return;

    // Update overall progress
    const overallFill = document.querySelector('.overall-progress .progress-fill');
    if (overallFill) {
      overallFill.style.width = `${progressData.overall}%`;

      const overallLabel = document.querySelector('.overall-progress .progress-label');
      if (overallLabel) {
        overallLabel.textContent = `Overall: ${progressData.overall}%`;
      }
    }

    // Update category progress bars
    const categoryProgressMappings = {
      core: '.progress-tier .progress-fill.core',
      next_level: '.progress-tier .progress-fill.next-level',
      behavioral: '.progress-tier .progress-fill.behavioral'
    };

    Object.entries(categoryProgressMappings).forEach(([category, selector]) => {
      const progressBar = document.querySelector(selector);
      if (progressBar && progressData[category]) {
        let completionValue = progressData[category].overall || 0;
        if (typeof completionValue !== 'number') {
          completionValue = progressData[category].completion || 0;
        }
        progressBar.style.width = `${completionValue}%`;

        // Update stats if available
        const statsContainer = progressBar.parentElement.nextElementSibling;
        if (statsContainer && statsContainer.classList.contains('progress-stats')) {
          const answered = progressData[category].count || progressData[category].questions_answered || 0;
          const total = progressData[category].total || progressData[category].questions_count || 1;
          statsContainer.textContent = `${answered} of ${total}`;
        }
      }
    });

    // Dispatch event for external progress handling
    this._emit('progressUpdated', { progressData });
  }

  /**
   * Handle question completion (no more questions)
   * @private
   */
  _handleQuestionCompletion() {
    // Get the container
    const container = document.querySelector(this.containerSelector);
    if (!container) return;

    // Clear the container
    const completionMessageHTML = `
      <div class="current-question-card">
        <h3 class="question-text">Profile Complete!</h3>
        <div class="help-text">
          <p>You have answered all the questions for now. Your profile is being processed.</p>
        </div>
        <div class="form-actions">
          <a href="/profile_complete" class="btn primary">View Your Profile Summary</a>
        </div>
      </div>
    `;

    container.innerHTML = completionMessageHTML;

    // Emit completion event
    this._emit('questionsCompleted', {
      profileId: this.currentProfileId,
      answerCount: this.answerHistory.length
    });
  }

  /**
   * Set loading state
   * @private
   * @param {boolean} isLoading - Whether loading is active
   * @param {string} message - Loading message to display
   */
  _setLoading(isLoading, message = 'Loading...') {
    this.isLoading = isLoading;

    // Clear any existing timeout
    if (this.loadingTimeout) {
      clearTimeout(this.loadingTimeout);
      this.loadingTimeout = null;
    }

    // Use LoadingStateManager if available
    if (this.loadingStateManager) {
      this.loadingStateManager.setLoading('question-flow', isLoading, { text: message });
      return;
    }

    // Otherwise use simple loading class
    const container = document.querySelector(this.containerSelector);
    if (!container) return;

    if (isLoading) {
      container.classList.add('is-loading');

      // Add loading indicator if not present
      let loadingIndicator = container.querySelector('.loading-indicator');
      if (!loadingIndicator) {
        loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = `
          <div class="spinner"></div>
          <div class="loading-text">${message}</div>
        `;
        container.appendChild(loadingIndicator);
      } else {
        // Update loading message
        const loadingText = loadingIndicator.querySelector('.loading-text');
        if (loadingText) {
          loadingText.textContent = message;
        }
      }

      // Set a timeout to show loading state for at least 500ms
      // This prevents flickering for fast operations
      this.loadingTimeout = setTimeout(() => {
        this.loadingTimeout = null;
      }, 500);
    } else {
      // Only remove loading state if the timeout is complete
      if (!this.loadingTimeout) {
        container.classList.remove('is-loading');
        const loadingIndicator = container.querySelector('.loading-indicator');
        if (loadingIndicator) {
          loadingIndicator.remove();
        }
      } else {
        // Wait for timeout to complete
        this.loadingTimeout = setTimeout(() => {
          container.classList.remove('is-loading');
          const loadingIndicator = container.querySelector('.loading-indicator');
          if (loadingIndicator) {
            loadingIndicator.remove();
          }
          this.loadingTimeout = null;
        }, 500);
      }
    }
  }

  /**
   * Handle errors during API calls
   * @private
   * @param {Error} error - The error that occurred
   * @param {string} context - Context in which the error occurred
   */
  _handleError(error, context) {
    console.error(`Error ${context}:`, error);

    // Use ErrorHandlingService if available
    if (this.errorHandlingService) {
      this.errorHandlingService.handleError(error, 'question_flow', {
        showToast: true,
        metadata: { context, profileId: this.currentProfileId }
      });
      return;
    }

    // Fallback error handling
    const container = document.querySelector(this.containerSelector);
    if (!container) return;

    const errorHTML = `
      <div class="error-message">
        <h3>Error ${context}</h3>
        <p>${error.message || 'An unexpected error occurred'}</p>
        <button type="button" class="btn primary retry-button">Try Again</button>
      </div>
    `;

    // Add error message
    const errorElement = document.createElement('div');
    errorElement.className = 'question-error';
    errorElement.innerHTML = errorHTML;

    // Replace loading indicator or append to container
    const loadingIndicator = container.querySelector('.loading-indicator');
    if (loadingIndicator) {
      loadingIndicator.replaceWith(errorElement);
    } else {
      container.appendChild(errorElement);
    }

    // Add retry handler
    const retryButton = errorElement.querySelector('.retry-button');
    if (retryButton) {
      retryButton.addEventListener('click', () => {
        errorElement.remove();
        if (context === 'loading question') {
          this.loadNextQuestion();
        }
      });
    }

    // Emit error event
    this._emit('error', { error, context });
  }

  /**
   * Emit an event to registered listeners
   * @private
   * @param {string} event - Event name
   * @param {Object} data - Event data
   */
  _emit(event, data) {
    if (!this.eventListeners[event]) return;

    this.eventListeners[event].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });

    // Also dispatch DOM event for external listeners
    const customEvent = new CustomEvent(`questionFlow:${event}`, {
      detail: data,
      bubbles: true
    });
    document.dispatchEvent(customEvent);
  }

  /**
     * Check if application is using server-side rendering
     * @private
     * @returns {boolean} True if server-rendered
     */
    _isServerRendered() {
      // Look for signs of server-side rendering
      // 1. Jinja2 template comments
      const hasJinjaComments = document.documentElement.innerHTML.includes('{#') ||
                               document.documentElement.innerHTML.includes('#}');

      // 2. Form with server-side action
      const answerForm = document.getElementById('answer-form');
      const hasServerAction = answerForm &&
                             answerForm.getAttribute('action') &&
                             answerForm.getAttribute('action').includes('/submit_answer');

      return hasJinjaComments || hasServerAction;
    }
  }

  // Create singleton instance
  const questionFlowManager = new QuestionFlowManager();

  // Export as both module and global
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = questionFlowManager;
  } else {
    window.QuestionFlowManager = questionFlowManager;
  }

  // Make static methods delegate to the instance
  const staticMethods = ['initialize', 'on', 'off', '_emit', '_saveCurrentState'];
  staticMethods.forEach(method => {
      QuestionFlowManager[method] = function(...args) {
          return questionFlowManager[method](...args);
      };
  });

  // Make static properties delegate to the instance
  const staticProperties = ['answerHistory', 'currentProfileId', 'progressData', 'currentQuestionData'];
  staticProperties.forEach(prop => {
      Object.defineProperty(QuestionFlowManager, prop, {
          get: function() { return questionFlowManager[prop]; },
          set: function(value) { questionFlowManager[prop] = value; }
      });
  });
