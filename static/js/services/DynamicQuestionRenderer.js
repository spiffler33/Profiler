/**
 * DynamicQuestionRenderer.js
 *
 * This component is responsible for rendering dynamic questions based on API data.
 * It connects to the /api/v2/questions/dynamic endpoint to fetch and manage dynamic
 * question data, handling different question types and loading states.
 */

class DynamicQuestionRenderer {
  constructor() {
    this.baseUrl = '/api/v2';
    this.currentProfileId = null;
    this.questionTypes = new Set(['text', 'number', 'select', 'radio', 'slider', 'multiselect', 'educational']);
    this.loadingStates = {};
    this.currentQuestion = null;
    this.renderCount = 0;

    // Integration with ApiService
    this.apiService = window.ApiService;

    // Integration with LoadingStateManager if available
    this.loadingStateManager = window.LoadingStateManager || null;

    // Integration with ErrorHandlingService if available
    this.errorHandlingService = window.ErrorHandlingService || null;

    // Integration with QuestionFlowManager
    this.questionFlowManager = window.QuestionFlowManager || null;
  }

  /**
   * Initialize the DynamicQuestionRenderer
   * @param {Object} options - Configuration options
   * @param {string} options.profileId - ID of the current profile
   * @param {string} options.containerSelector - DOM selector for the question container
   * @param {Function} options.onQuestionRendered - Callback when a question is rendered
   */
  initialize(options = {}) {
    this.currentProfileId = options.profileId || this._extractProfileIdFromUrl();
    this.containerSelector = options.containerSelector || '.question-answer-section';
    this.onQuestionRendered = options.onQuestionRendered || null;

    // Listen for QuestionFlowManager events if available
    if (this.questionFlowManager) {
      this.questionFlowManager.on('questionLoaded', this.handleQuestionLoaded.bind(this));
    }

    // Subscribe to dataEventBus if available
    if (window.dataEventBus) {
      window.dataEventBus.subscribe('question:loaded', this.handleQuestionLoaded.bind(this));
    }

    // Return this for chaining
    return this;
  }

  /**
   * Handle a question loaded from QuestionFlowManager
   * @param {Object} data - Question data
   */
  handleQuestionLoaded(data) {
    const question = data.question || data;

    // Check if this is a dynamic question that needs special handling
    if (question && question.is_dynamic) {
      // Enhance with dynamic data from API
      this.enhanceDynamicQuestion(question);
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
   * Enhance a dynamic question with additional data from the API
   * @param {Object} question - Question data
   * @returns {Promise<Object>} Enhanced question data
   */
  async enhanceDynamicQuestion(question) {
    if (!question || !question.id || !question.is_dynamic) {
      return question;
    }

    this._setLoading(question.id, true, 'Fetching dynamic question details...');

    try {
      // Use ApiService if available, otherwise use fetch directly
      let dynamicData;

      if (this.apiService) {
        dynamicData = await this.apiService.get(`/questions/dynamic`, {
          params: {
            profile_id: this.currentProfileId,
            question_id: question.id
          },
          loadingId: `dynamic-question-${question.id}`,
          cacheKey: `dynamic-question-${this.currentProfileId}-${question.id}`,
          useCache: true,
          cacheTTL: 300000 // 5 minutes
        });
      } else {
        const response = await fetch(`${this.baseUrl}/questions/dynamic?profile_id=${this.currentProfileId}&question_id=${question.id}`);
        if (!response.ok) {
          throw new Error(`Error fetching dynamic question details: ${response.statusText}`);
        }
        dynamicData = await response.json();
      }

      if (!dynamicData) {
        throw new Error('No dynamic question data received from API');
      }

      // Merge the dynamic data with the original question
      const enhancedQuestion = {
        ...question,
        ...dynamicData,
        is_dynamic: true // Ensure this flag is set
      };

      // Update the DOM with enhanced data
      this.updateDynamicQuestionElements(enhancedQuestion);

      // Return the enhanced question
      return enhancedQuestion;

    } catch (error) {
      this._handleError(error, 'enhancing dynamic question');
      return question;
    } finally {
      this._setLoading(question.id, false);
    }
  }

  /**
   * Update DOM elements for a dynamic question
   * @param {Object} question - Enhanced question data
   */
  updateDynamicQuestionElements(question) {
    // Find the question card
    const container = document.querySelector(this.containerSelector);
    if (!container) return;

    const questionCard = container.querySelector('.current-question-card');
    if (!questionCard) return;

    // Check if this is the correct question
    const questionIdInput = questionCard.querySelector('input[name="question_id"]');
    if (!questionIdInput || questionIdInput.value !== question.id) return;

    // Update dynamic indicator if needed
    const dynamicIndicator = questionCard.querySelector('.dynamic-question-indicator');
    if (dynamicIndicator) {
      this.updateDynamicIndicator(dynamicIndicator, question);
    } else {
      // Create dynamic indicator if it doesn't exist
      this.createDynamicIndicator(questionCard, question);
    }

    // Update help text if available
    if (question.help_text) {
      let helpText = questionCard.querySelector('.help-text');
      if (!helpText) {
        helpText = document.createElement('div');
        helpText.className = 'help-text';

        // Insert after question text
        const questionText = questionCard.querySelector('.question-text');
        if (questionText) {
          questionText.insertAdjacentElement('afterend', helpText);
        } else {
          questionCard.appendChild(helpText);
        }
      }

      helpText.innerHTML = `<p>${question.help_text}</p>`;
    }

    // Update educational content if applicable
    if (question.input_type === 'educational' && question.educational_content) {
      const educationalContent = questionCard.querySelector('.educational-content');
      if (educationalContent) {
        educationalContent.innerHTML = question.educational_content;
      }
    }

    // Update calculation details if applicable
    if (question.calculation_details) {
      const calculationDetails = questionCard.querySelector('.calculation-details');
      if (calculationDetails) {
        calculationDetails.innerHTML = question.calculation_details;
      }
    }

    // Call onQuestionRendered callback if provided
    if (typeof this.onQuestionRendered === 'function') {
      this.onQuestionRendered(question);
    }

    // Emit event for external listeners
    this._emit('dynamicQuestionRendered', { question });
  }

  /**
   * Update an existing dynamic indicator with new data
   * @param {HTMLElement} indicator - The indicator element
   * @param {Object} question - Question data
   */
  updateDynamicIndicator(indicator, question) {
    // Update tooltip content
    const tooltipContent = indicator.querySelector('.tooltip-content');
    if (tooltipContent) {
      // Update data sources
      const dataSourcesList = tooltipContent.querySelector('.data-source-list');
      if (dataSourcesList && question.data_sources) {
        dataSourcesList.innerHTML = question.data_sources.map(source => `
          <li>
            <span class="data-source-name">${source.name}</span>
            ${source.value ? `<span class="data-source-value">${source.value}</span>` : ''}
          </li>
        `).join('');
      }

      // Update reasoning
      const reasoningContent = tooltipContent.querySelector('.generation-reasoning p');
      if (reasoningContent && question.reasoning) {
        reasoningContent.textContent = question.reasoning;
      }
    }

    // Update context panel
    if (question.context_panel) {
      let contextPanel = indicator.querySelector('.context-panel');

      if (!contextPanel) {
        // Create context panel if it doesn't exist
        const toggleButton = document.createElement('button');
        toggleButton.className = 'context-panel-toggle';
        toggleButton.dataset.target = `context-panel-${question.id}`;
        toggleButton.innerHTML = '<i class="fa fa-info-circle"></i> Why this question?';

        indicator.appendChild(toggleButton);

        contextPanel = document.createElement('div');
        contextPanel.id = `context-panel-${question.id}`;
        contextPanel.className = 'context-panel hidden';
        contextPanel.innerHTML = `
          <div class="context-panel-header">
            <h4>Why we're asking this question</h4>
            <button class="context-panel-close">&times;</button>
          </div>
          <div class="context-panel-content"></div>
        `;

        indicator.appendChild(contextPanel);

        // Add event listeners
        toggleButton.addEventListener('click', function() {
          contextPanel.classList.toggle('hidden');
        });

        contextPanel.querySelector('.context-panel-close').addEventListener('click', function() {
          contextPanel.classList.add('hidden');
        });
      }

      // Update content
      const contentContainer = contextPanel.querySelector('.context-panel-content');
      if (contentContainer) {
        contentContainer.innerHTML = question.context_panel;

        // Add related goals if available
        if (question.related_goals && question.related_goals.length > 0) {
          contentContainer.innerHTML += `
            <div class="related-goals">
              <h5>Related to your goals:</h5>
              <ul class="related-goals-list">
                ${question.related_goals.map(goal => `
                  <li>
                    <span class="goal-title">${goal.title}</span>
                    ${goal.relevance ? `<span class="goal-relevance">${goal.relevance}</span>` : ''}
                  </li>
                `).join('')}
              </ul>
            </div>
          `;
        }

        // Add parameters if available
        if (question.parameters && question.parameters.length > 0) {
          contentContainer.innerHTML += `
            <div class="related-parameters">
              <h5>Financial parameters used:</h5>
              <ul class="parameter-list">
                ${question.parameters.map(param => `
                  <li>
                    <span class="parameter-name">${param.name}</span>
                    ${param.influence ? `<span class="parameter-influence">${param.influence}</span>` : ''}
                  </li>
                `).join('')}
              </ul>
            </div>
          `;
        }
      }
    }
  }

  /**
   * Create a new dynamic indicator for a question
   * @param {HTMLElement} questionCard - The question card element
   * @param {Object} question - Question data
   */
  createDynamicIndicator(questionCard, question) {
    // Find question header
    const questionHeader = questionCard.querySelector('.question-header');
    if (!questionHeader) return;

    // Create dynamic indicator
    const indicator = document.createElement('div');
    indicator.className = 'dynamic-question-indicator';

    // Add badge
    indicator.innerHTML = `
      <span class="dynamic-badge">
        <i class="fa fa-brain"></i> Adaptive Question
      </span>

      <div class="tooltip-container">
        <span class="tooltip-icon">?</span>
        <div class="tooltip-content tooltip-top">
          <div class="tooltip-title">
            <i class="tooltip-icon-info fa fa-lightbulb"></i> Personalized Question
          </div>
          <p>This question was dynamically generated based on your profile data.</p>

          ${question.data_sources ? `
          <div class="data-sources">
            <strong>Based on:</strong>
            <ul class="data-source-list">
              ${question.data_sources.map(source => `
                <li>
                  <span class="data-source-name">${source.name}</span>
                  ${source.value ? `<span class="data-source-value">${source.value}</span>` : ''}
                </li>
              `).join('')}
            </ul>
          </div>
          ` : ''}

          ${question.reasoning ? `
          <div class="generation-reasoning">
            <strong>Reasoning:</strong>
            <p>${question.reasoning}</p>
          </div>
          ` : ''}
        </div>
      </div>
    `;

    // Add context panel if available
    if (question.context_panel) {
      indicator.innerHTML += `
        <button class="context-panel-toggle" data-target="context-panel-${question.id}">
          <i class="fa fa-info-circle"></i> Why this question?
        </button>

        <div id="context-panel-${question.id}" class="context-panel hidden">
          <div class="context-panel-header">
            <h4>Why we're asking this question</h4>
            <button class="context-panel-close">&times;</button>
          </div>
          <div class="context-panel-content">
            ${question.context_panel}

            ${question.related_goals ? `
            <div class="related-goals">
              <h5>Related to your goals:</h5>
              <ul class="related-goals-list">
                ${question.related_goals.map(goal => `
                  <li>
                    <span class="goal-title">${goal.title}</span>
                    ${goal.relevance ? `<span class="goal-relevance">${goal.relevance}</span>` : ''}
                  </li>
                `).join('')}
              </ul>
            </div>
            ` : ''}

            ${question.parameters ? `
            <div class="related-parameters">
              <h5>Financial parameters used:</h5>
              <ul class="parameter-list">
                ${question.parameters.map(param => `
                  <li>
                    <span class="parameter-name">${param.name}</span>
                    ${param.influence ? `<span class="parameter-influence">${param.influence}</span>` : ''}
                  </li>
                `).join('')}
              </ul>
            </div>
            ` : ''}
          </div>
        </div>
      `;
    }

    // Add to question header
    questionHeader.appendChild(indicator);

    // Add event listeners
    const toggleButton = indicator.querySelector('.context-panel-toggle');
    if (toggleButton) {
      toggleButton.addEventListener('click', function() {
        const targetId = this.dataset.target;
        const panel = document.getElementById(targetId);

        if (panel.classList.contains('hidden')) {
          // Close any open panels first
          document.querySelectorAll('.context-panel:not(.hidden)').forEach(p => {
            p.classList.add('hidden');
          });

          // Open this panel
          panel.classList.remove('hidden');
        } else {
          panel.classList.add('hidden');
        }
      });
    }

    const closeButton = indicator.querySelector('.context-panel-close');
    if (closeButton) {
      closeButton.addEventListener('click', function() {
        const panel = this.closest('.context-panel');
        panel.classList.add('hidden');
      });
    }

    // Initialize tooltips if tooltips.js is loaded
    if (window.initializeTooltips) {
      window.initializeTooltips();
    }
  }

  /**
   * Set loading state for a specific question
   * @private
   * @param {string} questionId - ID of the question
   * @param {boolean} isLoading - Whether loading is active
   * @param {string} message - Loading message to display
   */
  _setLoading(questionId, isLoading, message = 'Loading...') {
    // Store loading state
    this.loadingStates[questionId] = isLoading;

    // Use LoadingStateManager if available
    if (this.loadingStateManager) {
      this.loadingStateManager.setLoading(`dynamic-question-${questionId}`, isLoading, { text: message });
      return;
    }

    // Find the question card
    const container = document.querySelector(this.containerSelector);
    if (!container) return;

    const questionCard = container.querySelector('.current-question-card');
    if (!questionCard) return;

    // Check if this is the correct question
    const questionIdInput = questionCard.querySelector('input[name="question_id"]');
    if (!questionIdInput || questionIdInput.value !== questionId) return;

    // Simple loading indicator management
    const dynamicIndicator = questionCard.querySelector('.dynamic-question-indicator');
    if (!dynamicIndicator) return;

    if (isLoading) {
      dynamicIndicator.classList.add('loading');

      // Add loading indicator if not present
      let loadingIndicator = dynamicIndicator.querySelector('.dynamic-loading-indicator');
      if (!loadingIndicator) {
        loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'dynamic-loading-indicator';
        loadingIndicator.innerHTML = `
          <div class="spinner"></div>
          <div class="loading-text">${message}</div>
        `;
        dynamicIndicator.appendChild(loadingIndicator);
      } else {
        // Update loading message
        const loadingText = loadingIndicator.querySelector('.loading-text');
        if (loadingText) {
          loadingText.textContent = message;
        }
      }
    } else {
      dynamicIndicator.classList.remove('loading');

      // Remove loading indicator
      const loadingIndicator = dynamicIndicator.querySelector('.dynamic-loading-indicator');
      if (loadingIndicator) {
        loadingIndicator.remove();
      }
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
      this.errorHandlingService.handleError(error, 'dynamic_question_renderer', {
        showToast: true,
        metadata: { context, profileId: this.currentProfileId }
      });
      return;
    }

    // Otherwise, just log to console
    console.error(`DynamicQuestionRenderer error ${context}:`, error.message || error);
  }

  /**
   * Emit an event
   * @private
   * @param {string} eventName - Name of the event
   * @param {Object} data - Event data
   */
  _emit(eventName, data) {
    // Emit via dataEventBus if available
    if (window.dataEventBus) {
      window.dataEventBus.publish(`dynamicQuestion:${eventName}`, data);
    }

    // Dispatch DOM event
    const customEvent = new CustomEvent(`dynamicQuestion:${eventName}`, {
      detail: data,
      bubbles: true
    });
    document.dispatchEvent(customEvent);
  }
}

// Create singleton instance
const dynamicQuestionRenderer = new DynamicQuestionRenderer();

// Export as both module and global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = dynamicQuestionRenderer;
} else {
  window.DynamicQuestionRenderer = dynamicQuestionRenderer;
}

// Make static methods delegate to the instance
const dynamicRendererStaticMethods = ['initialize', 'handleQuestionLoaded', 'enhanceDynamicQuestion'];
dynamicRendererStaticMethods.forEach(method => {
    DynamicQuestionRenderer[method] = function(...args) {
        return dynamicQuestionRenderer[method](...args);
    };
});

// Make static properties delegate to the instance
const dynamicRendererStaticProperties = ['currentProfileId', 'containerSelector'];
dynamicRendererStaticProperties.forEach(prop => {
    Object.defineProperty(DynamicQuestionRenderer, prop, {
        get: function() { return dynamicQuestionRenderer[prop]; },
        set: function(value) { dynamicQuestionRenderer[prop] = value; }
    });
});
