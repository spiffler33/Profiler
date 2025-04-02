/**
 * QuestionResponseSubmitter.js
 *
 * This service handles the submission of question responses to the API.
 * It provides validation, optimistic updates, and integration with the
 * existing question flow system.
 */

class QuestionResponseSubmitter {
  constructor() {
    this.baseUrl = '/api/v2';
    this.currentProfileId = null;
    this.pendingSubmissions = new Map();
    this.submissionHistory = [];

    // Integration with ApiService
    this.apiService = window.ApiService;

    // Integration with LoadingStateManager if available
    this.loadingStateManager = window.LoadingStateManager || null;

    // Integration with ErrorHandlingService if available
    this.errorHandlingService = window.ErrorHandlingService || null;

    // Integration with QuestionFlowManager
    this.questionFlowManager = window.QuestionFlowManager || null;

    // Integration with dataEventBus if available
    this.dataEventBus = window.dataEventBus || null;
  }

  /**
   * Initialize the QuestionResponseSubmitter
   * @param {Object} options - Configuration options
   * @param {string} options.profileId - ID of the current profile
   * @returns {QuestionResponseSubmitter} The submitter instance for chaining
   */
  initialize(options = {}) {
    this.currentProfileId = options.profileId || this._extractProfileIdFromUrl();

    // Setup form submission handlers
    this._setupFormListeners();

    // Listen for QuestionFlowManager events if available
    if (this.questionFlowManager) {
      // We don't want to duplicate submission handling
      // The manager will call our submit method
    }

    // Subscribe to dataEventBus if available
    if (this.dataEventBus) {
      this.dataEventBus.subscribe('question:submit', this.handleSubmitEvent.bind(this));
    }

    return this;
  }

  /**
   * Submit a question answer to the API
   * @param {Object} answerData - The answer data to submit
   * @param {string} answerData.questionId - ID of the question
   * @param {any} answerData.answer - The answer value
   * @param {Object} options - Submission options
   * @param {boolean} options.optimistic - Whether to apply optimistic updates
   * @param {boolean} options.validate - Whether to validate the answer before submission
   * @returns {Promise<Object>} The API response
   */
  async submitAnswer(answerData, options = {}) {
    const { questionId, answer } = answerData;

    if (!questionId) {
      throw new Error('Question ID is required for submission');
    }

    if (!this.currentProfileId) {
      this.currentProfileId = this._extractProfileIdFromUrl();
      if (!this.currentProfileId) {
        throw new Error('Profile ID is required for submission');
      }
    }

    // Validate if requested
    if (options.validate !== false) {
      this._validateAnswer(answerData);
    }

    // Start loading indicator
    this._setLoading(questionId, true, 'Submitting your answer...');

    // Apply optimistic update if requested
    if (options.optimistic !== false) {
      this._applyOptimisticUpdate(answerData);
    }

    // Create submission payload
    const payload = {
      profile_id: this.currentProfileId,
      question_id: questionId,
      answer: answer
    };

    // Keep track of this submission
    const submissionId = `${questionId}-${Date.now()}`;
    this.pendingSubmissions.set(submissionId, {
      data: answerData,
      timestamp: Date.now(),
      status: 'pending'
    });

    try {
      // Use ApiService if available, otherwise use fetch directly
      let response;

      if (this.apiService) {
        response = await this.apiService.post('/questions/submit', payload, {
          loadingId: `question-submit-${questionId}`,
          cacheKey: `question-submit-${this.currentProfileId}-${questionId}`,
          context: 'question_submission',
          cancelPrevious: true
        });
      } else {
        const fetchResponse = await fetch(`${this.baseUrl}/questions/submit`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!fetchResponse.ok) {
          throw new Error(`Error submitting answer: ${fetchResponse.statusText}`);
        }

        response = await fetchResponse.json();
      }

      // Update submission status
      this.pendingSubmissions.set(submissionId, {
        ...this.pendingSubmissions.get(submissionId),
        status: 'success',
        response
      });

      // Add to submission history
      this.submissionHistory.push({
        ...answerData,
        timestamp: Date.now(),
        status: 'success'
      });

      // Emit success event
      this._emit('submissionSuccess', {
        questionId,
        answer,
        response
      });

      // Return the response
      return response;
    } catch (error) {
      // Update submission status
      this.pendingSubmissions.set(submissionId, {
        ...this.pendingSubmissions.get(submissionId),
        status: 'error',
        error
      });

      // Add to submission history
      this.submissionHistory.push({
        ...answerData,
        timestamp: Date.now(),
        status: 'error',
        error: error.message
      });

      // Handle error
      this._handleError(error, 'submitting answer');

      // Emit error event
      this._emit('submissionError', {
        questionId,
        answer,
        error
      });

      throw error;
    } finally {
      // End loading indicator
      this._setLoading(questionId, false);
    }
  }

  /**
   * Check if an answer submission is pending
   * @param {string} questionId - ID of the question
   * @returns {boolean} Whether a submission is pending
   */
  isSubmissionPending(questionId) {
    // Check if we have any pending submissions for this question
    for (const [, submission] of this.pendingSubmissions.entries()) {
      if (submission.data.questionId === questionId && submission.status === 'pending') {
        return true;
      }
    }

    return false;
  }

  /**
   * Get submission history
   * @returns {Array} Array of submission history entries
   */
  getSubmissionHistory() {
    return [...this.submissionHistory];
  }

  /**
   * Handle a form submission event
   * @param {Event|Object} event - The submission event or data
   */
  handleFormSubmission(event) {
    // Check if this is an event or direct data
    const isEvent = event instanceof Event;

    if (isEvent) {
      // Prevent default form submission
      event.preventDefault();

      // Extract form data
      const form = event.target;
      const formData = new FormData(form);

      const questionId = formData.get('question_id');
      const inputType = formData.get('input_type');

      // Process answer based on input type
      let answer = this._extractAnswerFromForm(form, formData);

      // Submit the answer
      this.submitAnswer({
        questionId,
        answer,
        inputType
      }).then(response => {
        // If submission was successful and we have QuestionFlowManager,
        // let it handle the next steps
        if (this.questionFlowManager) {
          // The manager will load the next question
        } else {
          // Without QuestionFlowManager, we need to handle form submission manually
          // Reload the page instead of submitting the form directly
          window.location.reload();
        }
      }).catch(error => {
        console.error('Error submitting answer:', error);
        // On error, reload the page instead of submitting the form
        if (isEvent) {
          window.location.reload();
        }
      });
    } else {
      // Direct data submission (non-event)
      const { questionId, answer, inputType } = event;

      if (!questionId) {
        console.error('Question ID is required for submission');
        return;
      }

      // Submit the answer
      this.submitAnswer({
        questionId,
        answer,
        inputType
      }).catch(error => {
        console.error('Error submitting answer:', error);
      });
    }
  }

  /**
   * Handle submission event from dataEventBus
   * @param {Object} data - Event data
   */
  handleSubmitEvent(data) {
    this.handleFormSubmission(data);
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
   * Set up form submission listeners
   * @private
   */
  _setupFormListeners() {
    // Find answer form
    const answerForm = document.getElementById('answer-form');
    if (!answerForm) return;

    // Create a wrapped event handler that preserves the default behavior
    // but also processes the submission via API
    const originalSubmitHandler = answerForm.onsubmit;

    answerForm.addEventListener('submit', e => {
      // Check if the form has already been processed by this handler
      if (e.defaultPrevented || e._submitterHandled) return;

      // Mark this event as handled to prevent loops
      e._submitterHandled = true;

      // Let the original handler run if it exists
      if (typeof originalSubmitHandler === 'function') {
        const result = originalSubmitHandler.call(answerForm, e);
        if (result === false) return; // If original handler returns false, stop propagation
      }

      // Process the submission
      this.handleFormSubmission(e);
    });
  }

  /**
   * Extract answer from a form based on input type
   * @private
   * @param {HTMLFormElement} form - The form element
   * @param {FormData} formData - Form data object
   * @returns {any} The extracted answer
   */
  _extractAnswerFromForm(form, formData) {
    const inputType = formData.get('input_type');
    let answer = formData.get('answer');

    // Handle multiselect type
    if (inputType === 'multiselect') {
      const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked');
      if (checkboxes.length > 0) {
        answer = Array.from(checkboxes).map(cb => cb.value);
      }
    }

    // Handle slider type to ensure numeric value
    if (inputType === 'slider' && answer !== null && answer !== undefined) {
      answer = parseFloat(answer);
    }

    // Handle number type
    if (inputType === 'number' && answer !== null && answer !== undefined) {
      answer = parseFloat(answer);
    }

    return answer;
  }

  /**
   * Validate an answer before submission
   * @private
   * @param {Object} answerData - The answer data to validate
   * @throws {Error} If validation fails
   */
  _validateAnswer(answerData) {
    const { questionId, answer, inputType } = answerData;

    // Basic validation - ensure we have an answer
    if (answer === null || answer === undefined || answer === '') {
      throw new Error('Answer cannot be empty');
    }

    // For multiselect, ensure we have at least one selection
    if (inputType === 'multiselect' && Array.isArray(answer) && answer.length === 0) {
      throw new Error('Please select at least one option');
    }

    // For number inputs, validate min/max if we can find them in the DOM
    if (inputType === 'number') {
      const numberInput = document.querySelector(`input[name="answer"][type="number"]`);
      if (numberInput) {
        const min = parseFloat(numberInput.getAttribute('min'));
        const max = parseFloat(numberInput.getAttribute('max'));

        if (!isNaN(min) && parseFloat(answer) < min) {
          throw new Error(`Value must be at least ${min}`);
        }

        if (!isNaN(max) && parseFloat(answer) > max) {
          throw new Error(`Value cannot exceed ${max}`);
        }
      }
    }
  }

  /**
   * Apply optimistic update for an answer
   * @private
   * @param {Object} answerData - The answer data
   */
  _applyOptimisticUpdate(answerData) {
    // If we have QuestionFlowManager, update its answer history
    if (this.questionFlowManager) {
      this.questionFlowManager.answerHistory.push({
        questionId: answerData.questionId,
        answer: answerData.answer,
        timestamp: new Date().toISOString(),
        optimistic: true
      });

      // Save the updated state
      if (typeof this.questionFlowManager._saveCurrentState === 'function') {
        this.questionFlowManager._saveCurrentState();
      }
    }

    // If we have dataEventBus, publish the update
    if (this.dataEventBus) {
      this.dataEventBus.publish('question:answered', {
        ...answerData,
        timestamp: new Date().toISOString(),
        optimistic: true
      });
    }

    // Add to previous answers UI if possible
    this._addToPreviousAnswers(answerData);
  }

  /**
   * Add an answer to the previous answers section in the UI
   * @private
   * @param {Object} answerData - The answer data
   */
  _addToPreviousAnswers(answerData) {
    // Find the previous answers section
    const previousAnswersSection = document.querySelector('.previous-answers-section .answers-list');
    if (!previousAnswersSection) return;

    // Find the current question to get its text
    const currentQuestionCard = document.querySelector('.current-question-card');
    if (!currentQuestionCard) return;

    const questionText = currentQuestionCard.querySelector('.question-text')?.textContent;
    if (!questionText) return;

    // Extract category from question card
    const categoryBadge = currentQuestionCard.querySelector('.cat-badge');
    const category = categoryBadge?.className?.match(/cat-badge\s+([^\s]+)/)?.[1] || '';

    // Create new answer item
    const answerItem = document.createElement('div');
    answerItem.className = 'answer-item optimistic';
    answerItem.dataset.questionId = answerData.questionId;

    // Format answer for display
    let formattedAnswer = '';
    if (Array.isArray(answerData.answer)) {
      formattedAnswer = `
        <ul class="multiselect-answer-list">
          ${answerData.answer.map(item => `<li>${item}</li>`).join('')}
        </ul>
      `;
    } else if (answerData.inputType === 'educational') {
      formattedAnswer = '<em>Educational content - acknowledged</em>';
    } else {
      formattedAnswer = String(answerData.answer);
    }

    // Set HTML content
    answerItem.innerHTML = `
      <div class="answer-header">
        <span class="cat-badge ${category}">${category.replace('_', ' ')}</span>
        ${answerData.isDynamic ? `
        <span class="dynamic-mini-badge" title="This was a personalized question based on your financial profile">
          <i class="fa fa-brain"></i>
        </span>
        ` : ''}
        <span class="optimistic-badge" title="This answer is being processed">Sending...</span>
      </div>
      <div class="question-text">${questionText}</div>
      <div class="answer-text">
        <strong>Your answer:</strong> ${formattedAnswer}
      </div>
    `;

    // Add to the beginning of the list
    previousAnswersSection.insertBefore(answerItem, previousAnswersSection.firstChild);

    // If there was a "no answers" message, remove it
    const noAnswers = document.querySelector('.no-answers');
    if (noAnswers) {
      noAnswers.remove();
    }
  }

  /**
   * Set loading state during submission
   * @private
   * @param {string} questionId - ID of the question
   * @param {boolean} isLoading - Whether loading is active
   * @param {string} message - Loading message to display
   */
  _setLoading(questionId, isLoading, message = 'Submitting...') {
    // Use LoadingStateManager if available
    if (this.loadingStateManager) {
      this.loadingStateManager.setLoading(`question-submit-${questionId}`, isLoading, { text: message });
      return;
    }

    // Otherwise, find the submit button and set loading state manually
    const submitButton = document.querySelector('#answer-form button[type="submit"]');
    if (!submitButton) return;

    if (isLoading) {
      submitButton.classList.add('loading');
      submitButton.dataset.originalText = submitButton.textContent;
      submitButton.textContent = message;
      submitButton.disabled = true;
    } else {
      submitButton.classList.remove('loading');
      if (submitButton.dataset.originalText) {
        submitButton.textContent = submitButton.dataset.originalText;
      }
      submitButton.disabled = false;
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
      this.errorHandlingService.handleError(error, 'question_response_submitter', {
        showToast: true,
        metadata: { context, profileId: this.currentProfileId }
      });
      return;
    }

    // Otherwise show a simple alert
    alert(`Error ${context}: ${error.message || error}`);
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
      this.dataEventBus.publish(`questionResponse:${eventName}`, data);
    }

    // Dispatch DOM event
    const customEvent = new CustomEvent(`questionResponse:${eventName}`, {
      detail: data,
      bubbles: true
    });
    document.dispatchEvent(customEvent);
  }
}

// Create singleton instance
const questionResponseSubmitter = new QuestionResponseSubmitter();

// Export as both module and global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = questionResponseSubmitter;
} else {
  window.QuestionResponseSubmitter = questionResponseSubmitter;
}

// Add static method references to constructor
['initialize', 'submitAnswer', 'handleFormSubmission'].forEach(method => {
  QuestionResponseSubmitter[method] = function(...args) {
    return questionResponseSubmitter[method](...args);
  };
});
