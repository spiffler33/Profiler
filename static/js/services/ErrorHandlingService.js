/**
 * ErrorHandlingService - Centralized error handling for the application
 * 
 * This service provides consistent error handling, reporting, and recovery mechanisms
 * across the application. It includes features for:
 * - User-friendly error messages
 * - Error classification and categorization
 * - Recovery strategies for different types of errors
 * - Error logging and reporting
 * - Retry mechanisms with backoff
 * - Fallback UI and graceful degradation
 */

const ErrorHandlingService = (function() {
  // Configuration
  const config = {
    // Error display settings
    errorDisplayDuration: 5000, // 5 seconds
    showErrorDetails: false, // Show technical details to users (false for production)
    maxErrorsDisplayed: 3, // Maximum number of errors to show at once
    
    // Error handling behavior
    automaticRetry: true, // Automatically retry failed operations
    maxRetries: 3, // Maximum retry attempts
    retryBackoffFactor: 1.5, // Exponential backoff factor for retries
    initialRetryDelay: 1000, // Initial retry delay in ms
    
    // Recovery options
    enableFallbacks: true, // Use fallback data/UI when errors occur
    offlineMode: true, // Support offline mode for critical features
    
    // Reporting options
    logErrors: true, // Log errors to console
    reportErrors: false, // Report errors to server
    errorReportingEndpoint: '/api/v2/error-reporting',
    
    // Error categorization thresholds
    warningThreshold: 1, // Number of similar warnings before escalation
    criticalThreshold: 3, // Number of similar errors before marking critical
    
    // UI options
    showFallbackNotification: true, // Show notification when using fallback data
    errorToastPosition: 'bottom-right' // Position of error toast
  };
  
  // Error state tracking
  const errorState = {
    activeErrors: [], // Currently active/displayed errors
    errorHistory: {}, // History of errors by type/code
    retryHistory: {}, // History of retry attempts
    fallbacksUsed: {}, // Tracking of fallback usage
    lastNetworkError: null, // Last network-related error
    offlineDetected: false // Whether offline mode has been detected
  };
  
  // DOM elements for error display
  let errorToastContainer = null;
  let globalErrorBanner = null;
  let errorModalElement = null;
  
  /**
   * Creates necessary DOM elements for error displays
   */
  function createErrorDisplayElements() {
    const body = document.body;
    
    // Create error toast container if it doesn't exist
    if (!errorToastContainer) {
      errorToastContainer = document.getElementById('error-toast-container');
      if (!errorToastContainer) {
        errorToastContainer = document.createElement('div');
        errorToastContainer.id = 'error-toast-container';
        errorToastContainer.className = `fixed ${getToastPosition()} z-50 flex flex-col gap-2`;
        body.appendChild(errorToastContainer);
      }
    }
    
    // Create global error banner if it doesn't exist
    if (!globalErrorBanner) {
      globalErrorBanner = document.getElementById('global-error-banner');
      if (!globalErrorBanner) {
        globalErrorBanner = document.createElement('div');
        globalErrorBanner.id = 'global-error-banner';
        globalErrorBanner.className = 'hidden fixed top-0 left-0 w-full bg-red-600 text-white py-2 px-4 text-center z-50';
        
        const bannerMessage = document.createElement('p');
        bannerMessage.id = 'global-error-message';
        bannerMessage.className = 'font-medium';
        
        const bannerCloseBtn = document.createElement('button');
        bannerCloseBtn.className = 'absolute right-2 top-2 text-white hover:text-gray-200';
        bannerCloseBtn.innerHTML = '&times;';
        bannerCloseBtn.setAttribute('aria-label', 'Close');
        bannerCloseBtn.addEventListener('click', () => {
          globalErrorBanner.classList.add('hidden');
        });
        
        globalErrorBanner.appendChild(bannerMessage);
        globalErrorBanner.appendChild(bannerCloseBtn);
        body.appendChild(globalErrorBanner);
      }
    }
    
    // Create error modal if it doesn't exist
    if (!errorModalElement) {
      errorModalElement = document.getElementById('error-modal');
      if (!errorModalElement) {
        errorModalElement = document.createElement('div');
        errorModalElement.id = 'error-modal';
        errorModalElement.className = 'hidden fixed inset-0 flex items-center justify-center z-50';
        errorModalElement.innerHTML = `
          <div class="fixed inset-0 bg-black opacity-50 modal-backdrop"></div>
          <div class="bg-white rounded-lg shadow-lg p-6 max-w-md w-full z-10 relative">
            <button class="absolute right-3 top-3 text-gray-500 hover:text-gray-700" id="error-modal-close" aria-label="Close">
              &times;
            </button>
            <div class="text-red-600 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2" id="error-modal-title">Error</h3>
            <p class="text-gray-700 mb-6" id="error-modal-message">An error has occurred.</p>
            <div class="text-sm text-gray-500 mb-4 hidden" id="error-modal-details"></div>
            <div class="flex justify-end gap-3">
              <button class="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-md" id="error-modal-secondary">
                Cancel
              </button>
              <button class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md" id="error-modal-primary">
                Retry
              </button>
            </div>
          </div>
        `;
        
        body.appendChild(errorModalElement);
        
        // Add event listeners to modal buttons
        document.getElementById('error-modal-close').addEventListener('click', hideErrorModal);
        document.getElementById('error-modal-secondary').addEventListener('click', hideErrorModal);
      }
    }
  }
  
  /**
   * Get CSS classes for toast position based on config
   * @returns {string} CSS classes for positioning
   */
  function getToastPosition() {
    switch (config.errorToastPosition) {
      case 'top-right':
        return 'top-4 right-4';
      case 'top-left':
        return 'top-4 left-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'top-center':
        return 'top-4 left-1/2 transform -translate-x-1/2';
      case 'bottom-center':
        return 'bottom-4 left-1/2 transform -translate-x-1/2';
      default: // bottom-right
        return 'bottom-4 right-4';
    }
  }
  
  /**
   * Classifies an error into predefined categories
   * @param {Error|string} error - The error to classify
   * @param {string} context - The context in which the error occurred
   * @returns {Object} Classification information
   */
  function classifyError(error, context = '') {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorName = error instanceof Error ? error.name : 'Error';
    
    // Common error types by classification
    const classifications = {
      network: {
        patterns: ['network', 'offline', 'internet', 'failed to fetch', 'cors', 'aborted'],
        level: 'warning',
        category: 'connectivity',
        recoverable: true
      },
      authentication: {
        patterns: ['auth', 'unauthorized', 'forbidden', 'login', 'session', '401', '403'],
        level: 'error',
        category: 'session',
        recoverable: false
      },
      validation: {
        patterns: ['validation', 'invalid', 'required', 'constraint', 'parameter', 'input'],
        level: 'warning',
        category: 'input',
        recoverable: true
      },
      server: {
        patterns: ['server', 'internal', '500', '502', '503', '504'],
        level: 'error',
        category: 'backend',
        recoverable: true
      },
      client: {
        patterns: ['typeerror', 'referenceerror', 'syntaxerror', 'undefined'],
        level: 'error',
        category: 'frontend',
        recoverable: false
      },
      timeout: {
        patterns: ['timeout', 'too long', 'slow', 'time exceeded'],
        level: 'warning',
        category: 'performance',
        recoverable: true
      },
      data: {
        patterns: ['parse', 'json', 'syntax', 'formatting', 'unexpected token'],
        level: 'error',
        category: 'data',
        recoverable: false
      },
      calculation: {
        patterns: ['monte carlo', 'simulation', 'calculation', 'compute', 'algorithm'],
        level: 'warning',
        category: 'processing',
        recoverable: true
      }
    };
    
    // Get navigator.onLine status
    const isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;
    
    // Specific error handling for network issues
    if (!isOnline) {
      return {
        level: 'warning',
        category: 'connectivity',
        recoverable: true,
        type: 'offline',
        context
      };
    }
    
    // Check for matches against classifications
    const lowerCaseError = errorMessage.toLowerCase();
    
    for (const [type, classification] of Object.entries(classifications)) {
      if (classification.patterns.some(pattern => lowerCaseError.includes(pattern.toLowerCase()))) {
        return {
          level: classification.level,
          category: classification.category,
          recoverable: classification.recoverable,
          type,
          context
        };
      }
    }
    
    // Status code based classification (for errors with status property)
    if (error.status) {
      const status = error.status;
      
      if (status >= 400 && status < 500) {
        if (status === 401 || status === 403) {
          return {
            level: 'error', 
            category: 'session',
            recoverable: false,
            type: 'authentication',
            context
          };
        }
        return {
          level: 'warning',
          category: 'input',
          recoverable: true,
          type: 'client-error',
          context
        };
      }
      
      if (status >= 500) {
        return {
          level: 'error',
          category: 'backend',
          recoverable: true,
          type: 'server-error',
          context
        };
      }
    }
    
    // Default classification
    return {
      level: 'error', 
      category: 'unknown',
      recoverable: false,
      type: 'generic',
      context
    };
  }
  
  /**
   * Creates a user-friendly error message based on error type
   * @param {Error|string} error - The error to create a message for
   * @param {string} context - The context in which the error occurred
   * @returns {string} User-friendly error message
   */
  function createUserFriendlyMessage(error, context = '') {
    if (!error) return 'An unknown error occurred';
    
    const errorMessage = error instanceof Error ? error.message : String(error);
    const classification = classifyError(error, context);
    
    // Return the original error if it's already user-friendly
    if (errorMessage.startsWith('Unable to') || 
        errorMessage.includes('Please') ||
        errorMessage.includes('try again')) {
      return errorMessage;
    }
    
    // Context-specific messages
    if (context) {
      return `Unable to ${context}. ${getRecoveryInstructions(classification)}`;
    }
    
    // Classification-based messages
    switch (classification.type) {
      case 'offline':
        return 'You are currently offline. Please check your internet connection and try again.';
      case 'network':
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      case 'authentication':
        return 'Your session may have expired. Please refresh the page and try again.';
      case 'validation':
        return 'Some information provided is invalid. Please check your inputs and try again.';
      case 'server':
        return 'The server encountered an error. Our team has been notified and we\'re working to fix it.';
      case 'client':
        return 'An error occurred in the application. Please refresh the page and try again.';
      case 'timeout':
        return 'The request took too long to complete. This might be due to a slow connection or the server is busy.';
      case 'data':
        return 'There was a problem processing the data. Please try again later.';
      case 'calculation':
        return 'There was a problem calculating the results. The system may be experiencing high load.';
      default:
        return 'Something went wrong. Please try again later.';
    }
  }
  
  /**
   * Gets recovery instructions based on error classification
   * @param {Object} classification - Error classification
   * @returns {string} Recovery instructions
   */
  function getRecoveryInstructions(classification) {
    if (!classification.recoverable) {
      return 'Please try again later or contact support if the problem persists.';
    }
    
    switch (classification.category) {
      case 'connectivity':
        return 'Please check your internet connection and try again.';
      case 'session':
        return 'Please refresh the page to renew your session.';
      case 'input':
        return 'Please check your inputs and try again.';
      case 'backend':
        return 'Please try again in a few minutes.';
      case 'performance':
        return 'Please try again. Consider using smaller data sets if the problem persists.';
      default:
        return 'Please try again later.';
    }
  }
  
  /**
   * Displays an error toast notification
   * @param {string} message - The message to display
   * @param {Object} options - Display options
   */
  function showErrorToast(message, options = {}) {
    createErrorDisplayElements();
    
    const {
      duration = config.errorDisplayDuration,
      level = 'error',
      onAction = null,
      actionText = 'Retry',
      id = `error-${Date.now()}`,
      technical = null
    } = options;
    
    // Create toast element
    const toast = document.createElement('div');
    toast.id = id;
    toast.className = `error-toast flex items-center p-4 mb-3 rounded-md shadow-lg border-l-4 transition-all transform translate-x-full animate-slide-in ${getToastColorClasses(level)}`;
    toast.setAttribute('role', 'alert');
    
    // Create toast content
    toast.innerHTML = `
      <div class="flex-1 mr-2">
        <p class="font-medium">${message}</p>
        ${technical && config.showErrorDetails ? `<p class="text-xs mt-1 opacity-75">${technical}</p>` : ''}
      </div>
      <div class="flex items-center gap-2">
        ${onAction ? `<button class="text-sm underline error-toast-action">${actionText}</button>` : ''}
        <button class="error-toast-close ml-1" aria-label="Close">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    `;
    
    // Add to container
    errorToastContainer.appendChild(toast);
    
    // Track in active errors
    errorState.activeErrors.push({
      id,
      message,
      level,
      timestamp: Date.now()
    });
    
    // Limit the number of visible errors
    if (errorState.activeErrors.length > config.maxErrorsDisplayed) {
      const oldestError = errorState.activeErrors.shift();
      const oldToast = document.getElementById(oldestError.id);
      if (oldToast) {
        removeToast(oldToast);
      }
    }
    
    // Add event listeners
    const closeBtn = toast.querySelector('.error-toast-close');
    closeBtn.addEventListener('click', () => removeToast(toast));
    
    const actionBtn = toast.querySelector('.error-toast-action');
    if (actionBtn && onAction) {
      actionBtn.addEventListener('click', () => {
        onAction();
        removeToast(toast);
      });
    }
    
    // Auto-remove after duration (if duration > 0)
    if (duration > 0) {
      setTimeout(() => {
        if (document.getElementById(id)) {
          removeToast(toast);
        }
      }, duration);
    }
    
    return id;
  }
  
  /**
   * Removes a toast from the DOM with animation
   * @param {HTMLElement} toast - The toast element to remove
   */
  function removeToast(toast) {
    // Add exit animation class
    toast.classList.remove('animate-slide-in');
    toast.classList.add('animate-slide-out');
    
    // Remove from DOM after animation
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      
      // Update active errors
      errorState.activeErrors = errorState.activeErrors.filter(e => e.id !== toast.id);
    }, 300); // Animation duration
  }
  
  /**
   * Get color classes for toast based on error level
   * @param {string} level - Error level (error, warning, info)
   * @returns {string} CSS classes
   */
  function getToastColorClasses(level) {
    switch (level.toLowerCase()) {
      case 'error':
        return 'bg-red-50 border-red-500 text-red-800';
      case 'warning':
        return 'bg-amber-50 border-amber-500 text-amber-800';
      case 'info':
        return 'bg-blue-50 border-blue-500 text-blue-800';
      case 'success':
        return 'bg-green-50 border-green-500 text-green-800';
      default:
        return 'bg-gray-50 border-gray-500 text-gray-800';
    }
  }
  
  /**
   * Shows the global error banner for critical errors
   * @param {string} message - Error message to display
   */
  function showGlobalErrorBanner(message) {
    createErrorDisplayElements();
    
    const bannerMessage = document.getElementById('global-error-message');
    if (bannerMessage) {
      bannerMessage.textContent = message;
    }
    
    globalErrorBanner.classList.remove('hidden');
  }
  
  /**
   * Hides the global error banner
   */
  function hideGlobalErrorBanner() {
    if (globalErrorBanner) {
      globalErrorBanner.classList.add('hidden');
    }
  }
  
  /**
   * Shows the error modal for serious errors
   * @param {string} title - Modal title
   * @param {string} message - Error message
   * @param {Object} options - Modal options
   */
  function showErrorModal(title, message, options = {}) {
    createErrorDisplayElements();
    
    const {
      details = null,
      primaryButtonText = 'Retry',
      secondaryButtonText = 'Cancel',
      onPrimaryAction = hideErrorModal,
      onSecondaryAction = hideErrorModal,
      showDetails = config.showErrorDetails
    } = options;
    
    // Set modal content
    document.getElementById('error-modal-title').textContent = title;
    document.getElementById('error-modal-message').textContent = message;
    
    const detailsElement = document.getElementById('error-modal-details');
    if (details && showDetails) {
      detailsElement.textContent = details;
      detailsElement.classList.remove('hidden');
    } else {
      detailsElement.classList.add('hidden');
    }
    
    // Set button text
    const primaryButton = document.getElementById('error-modal-primary');
    primaryButton.textContent = primaryButtonText;
    
    const secondaryButton = document.getElementById('error-modal-secondary');
    secondaryButton.textContent = secondaryButtonText;
    
    // Set button handlers
    primaryButton.onclick = () => {
      onPrimaryAction();
      hideErrorModal();
    };
    
    secondaryButton.onclick = () => {
      onSecondaryAction();
      hideErrorModal();
    };
    
    // Show modal
    errorModalElement.classList.remove('hidden');
  }
  
  /**
   * Hides the error modal
   */
  function hideErrorModal() {
    if (errorModalElement) {
      errorModalElement.classList.add('hidden');
    }
  }
  
  /**
   * Logs the error for analytics and debugging
   * @param {Error} error - The error to log
   * @param {string} context - The context in which the error occurred
   * @param {Object} metadata - Additional metadata about the error
   */
  function logError(error, context, metadata = {}) {
    if (!config.logErrors) return;
    
    // Prepare error data for logging
    const errorData = {
      message: error instanceof Error ? error.message : String(error),
      name: error instanceof Error ? error.name : 'Error',
      stack: error instanceof Error ? error.stack : null,
      context,
      metadata,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      classification: classifyError(error, context)
    };
    
    // Log to console
    console.error(`Error in ${context}:`, errorData);
    
    // Track in error history
    const errorKey = `${errorData.classification.type}_${context}`;
    if (!errorState.errorHistory[errorKey]) {
      errorState.errorHistory[errorKey] = {
        count: 1,
        firstOccurrence: Date.now(),
        lastOccurrence: Date.now(),
        errors: [errorData]
      };
    } else {
      errorState.errorHistory[errorKey].count++;
      errorState.errorHistory[errorKey].lastOccurrence = Date.now();
      
      // Keep only the last 5 errors in history
      if (errorState.errorHistory[errorKey].errors.length >= 5) {
        errorState.errorHistory[errorKey].errors.shift();
      }
      errorState.errorHistory[errorKey].errors.push(errorData);
      
      // Check for escalation based on count
      if (errorState.errorHistory[errorKey].count === config.criticalThreshold) {
        // This error has occurred enough times to be considered critical
        const userMessage = 'We\'re experiencing some technical difficulties. Our team has been notified.';
        showGlobalErrorBanner(userMessage);
        
        // Report as critical if reporting is enabled
        if (config.reportErrors) {
          reportError({
            ...errorData,
            critical: true,
            occurrences: errorState.errorHistory[errorKey].count
          });
        }
      }
    }
    
    // Report to server if enabled
    if (config.reportErrors) {
      reportError(errorData);
    }
  }
  
  /**
   * Reports an error to the server
   * @param {Object} errorData - Error data to report
   */
  function reportError(errorData) {
    if (!config.reportErrors) return;
    
    // Use fetch API to report error
    fetch(config.errorReportingEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(errorData),
      // Don't wait for the response, fire and forget
      keepalive: true
    }).catch(reportingError => {
      // Don't try to report errors that occur during error reporting
      console.error('Error reporting failed:', reportingError);
    });
  }
  
  /**
   * Handles an error with appropriate user feedback and logging
   * @param {Error|string} error - The error to handle
   * @param {string} context - The context in which the error occurred
   * @param {Object} options - Error handling options
   * @returns {Object} Handling result
   */
  function handleError(error, context = '', options = {}) {
    const {
      showToast = true,
      showBanner = false,
      showModal = false,
      retryAction = null,
      metadata = {},
      level = null, // Auto-detect if not specified
      silent = false, // Don't show any UI if true
      allowRetry = true,
      modalOptions = {}
    } = options;
    
    // Classify the error
    const classification = classifyError(error, context);
    const errorLevel = level || classification.level;
    
    // Create user-friendly message
    const userMessage = createUserFriendlyMessage(error, context);
    const technicalMessage = error instanceof Error ? error.message : String(error);
    
    // Log the error
    logError(error, context, {
      ...metadata,
      classification,
      userMessage
    });
    
    // Skip UI updates if silent
    if (silent) {
      return {
        handled: true,
        classification,
        userMessage,
        technicalMessage,
        recovery: classification.recoverable
      };
    }
    
    // Based on classification and options, show appropriate UI
    if (showModal || errorLevel === 'critical') {
      showErrorModal('Error', userMessage, {
        details: technicalMessage,
        primaryButtonText: allowRetry && classification.recoverable ? 'Retry' : 'OK',
        onPrimaryAction: allowRetry && classification.recoverable && retryAction ? retryAction : hideErrorModal,
        ...modalOptions
      });
    } else if (showBanner || errorLevel === 'error') {
      if (errorState.activeErrors.length >= config.criticalThreshold) {
        // Too many errors, show banner instead
        showGlobalErrorBanner(userMessage);
      } else if (showToast) {
        // Show as toast
        showErrorToast(userMessage, {
          level: errorLevel,
          technical: technicalMessage,
          onAction: allowRetry && classification.recoverable && retryAction ? retryAction : null
        });
      }
    } else if (showToast) {
      // Show as toast for warnings and info
      showErrorToast(userMessage, {
        level: errorLevel,
        technical: technicalMessage,
        onAction: allowRetry && classification.recoverable && retryAction ? retryAction : null
      });
    }
    
    return {
      handled: true,
      classification,
      userMessage,
      technicalMessage,
      recovery: classification.recoverable
    };
  }
  
  /**
   * Creates a retry function with exponential backoff
   * @param {Function} actionFn - Function to retry
   * @param {Object} options - Retry options
   * @returns {Function} Function that will retry the action
   */
  function createRetryFunction(actionFn, options = {}) {
    const {
      maxRetries = config.maxRetries,
      initialDelay = config.initialRetryDelay,
      backoffFactor = config.retryBackoffFactor,
      onRetry = null, // Called before each retry attempt
      onSuccess = null, // Called on success
      onFailure = null, // Called after all retries fail
      context = 'operation'
    } = options;
    
    let attemptCount = 0;
    
    // Return a function that will execute the action with retries
    return async function retryWrapper(...args) {
      while (attemptCount <= maxRetries) {
        try {
          // If this isn't the first attempt, trigger onRetry
          if (attemptCount > 0 && onRetry) {
            onRetry(attemptCount, maxRetries);
          }
          
          // Execute the action
          const result = await actionFn(...args);
          
          // Success! Call onSuccess and return the result
          if (onSuccess) {
            onSuccess(result);
          }
          
          return result;
        } catch (error) {
          attemptCount++;
          
          // Log the retry attempt
          console.warn(`Retry attempt ${attemptCount}/${maxRetries} for ${context}:`, error.message);
          
          // Handle the case where we've exhausted all retries
          if (attemptCount > maxRetries) {
            if (onFailure) {
              onFailure(error);
            }
            
            // Handle the final error
            handleError(error, `${context} after ${maxRetries} retry attempts`, {
              showToast: true,
              allowRetry: false,
              metadata: {
                retryAttempts: attemptCount,
                args
              }
            });
            
            throw error;
          }
          
          // Calculate delay with exponential backoff
          const delay = initialDelay * Math.pow(backoffFactor, attemptCount - 1);
          
          // Show toast for retry
          showErrorToast(`${createUserFriendlyMessage(error, context)} Retrying in ${Math.round(delay/1000)}s...`, {
            level: 'warning',
            duration: delay
          });
          
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    };
  }
  
  /**
   * Wraps a function with error handling
   * @param {Function} fn - Function to wrap
   * @param {Object} options - Error handling options
   * @returns {Function} Wrapped function
   */
  function withErrorHandling(fn, options = {}) {
    const {
      context = 'function',
      retryPolicy = null,
      errorOptions = {}
    } = options;
    
    // Return wrapped function
    return async function errorHandlingWrapper(...args) {
      try {
        // Execute original function
        return await fn(...args);
      } catch (error) {
        // Apply retry policy if specified
        if (retryPolicy && config.automaticRetry) {
          const retryFn = createRetryFunction(fn, {
            ...retryPolicy,
            context
          });
          
          try {
            return await retryFn(...args);
          } catch (retryError) {
            // If retries also failed, handle the error
            handleError(retryError, context, {
              ...errorOptions,
              metadata: {
                ...errorOptions.metadata,
                args
              }
            });
            throw retryError;
          }
        } else {
          // No retry policy, just handle the error
          handleError(error, context, {
            ...errorOptions,
            metadata: {
              ...errorOptions.metadata,
              args
            }
          });
          throw error;
        }
      }
    };
  }
  
  /**
   * Checks if a component should use fallback data/UI due to errors
   * @param {string} componentId - ID of the component
   * @param {string} errorType - Type of error
   * @returns {boolean} True if should use fallback
   */
  function shouldUseFallback(componentId, errorType) {
    if (!config.enableFallbacks) return false;
    
    const fallbackKey = `${componentId}_${errorType}`;
    
    // Check if this specific error/component has exceeded threshold
    if (errorState.fallbacksUsed[fallbackKey]) {
      return errorState.fallbacksUsed[fallbackKey].count >= config.fallbackThreshold;
    }
    
    // Check general error history for this type
    const errorHistory = Object.keys(errorState.errorHistory)
      .filter(key => key.startsWith(`${errorType}_`))
      .map(key => errorState.errorHistory[key]);
    
    if (errorHistory.length === 0) return false;
    
    // Calculate total error count for this type
    const totalOccurrences = errorHistory.reduce((sum, entry) => sum + entry.count, 0);
    return totalOccurrences >= config.fallbackThreshold;
  }
  
  /**
   * Records a fallback usage
   * @param {string} componentId - ID of the component
   * @param {string} errorType - Type of error
   * @param {Object} fallbackData - Data about the fallback
   */
  function recordFallbackUsage(componentId, errorType, fallbackData = {}) {
    if (!config.enableFallbacks) return;
    
    const fallbackKey = `${componentId}_${errorType}`;
    
    if (!errorState.fallbacksUsed[fallbackKey]) {
      errorState.fallbacksUsed[fallbackKey] = {
        count: 1,
        firstOccurrence: Date.now(),
        lastOccurrence: Date.now(),
        data: [fallbackData]
      };
    } else {
      errorState.fallbacksUsed[fallbackKey].count++;
      errorState.fallbacksUsed[fallbackKey].lastOccurrence = Date.now();
      
      // Keep only the last 5 entries
      if (errorState.fallbacksUsed[fallbackKey].data.length >= 5) {
        errorState.fallbacksUsed[fallbackKey].data.shift();
      }
      errorState.fallbacksUsed[fallbackKey].data.push(fallbackData);
    }
    
    // Show notification if configured
    if (config.showFallbackNotification) {
      showErrorToast(`Using cached data due to repeated errors. Some information may be outdated.`, {
        level: 'warning',
        duration: 5000
      });
    }
  }
  
  /**
   * Gets error stats for reporting and analysis
   * @returns {Object} Error statistics
   */
  function getErrorStats() {
    return {
      totalTrackedErrors: Object.keys(errorState.errorHistory).reduce(
        (sum, key) => sum + errorState.errorHistory[key].count, 0
      ),
      activeErrors: errorState.activeErrors.length,
      errorsByType: Object.keys(errorState.errorHistory).reduce((acc, key) => {
        const [type] = key.split('_');
        acc[type] = (acc[type] || 0) + errorState.errorHistory[key].count;
        return acc;
      }, {}),
      fallbacksUsed: Object.keys(errorState.fallbacksUsed).length,
      mostFrequentError: Object.entries(errorState.errorHistory)
        .sort((a, b) => b[1].count - a[1].count)?.[0]?.[0] || null
    };
  }
  
  /**
   * Updates the service configuration
   * @param {Object} options - New configuration options
   */
  function configure(options = {}) {
    Object.assign(config, options);
    
    // Update any UI elements based on new config
    if (errorToastContainer) {
      errorToastContainer.className = `fixed ${getToastPosition()} z-50 flex flex-col gap-2`;
    }
  }
  
  /**
   * Clears all error history and state
   */
  function clearErrorHistory() {
    errorState.errorHistory = {};
    errorState.retryHistory = {};
    errorState.fallbacksUsed = {};
    
    // Hide any active UI elements
    hideGlobalErrorBanner();
    hideErrorModal();
    
    // Remove all active toasts
    errorState.activeErrors.forEach(error => {
      const toast = document.getElementById(error.id);
      if (toast) {
        removeToast(toast);
      }
    });
    
    errorState.activeErrors = [];
  }
  
  // Initialize the service
  createErrorDisplayElements();
  
  // Listen for online/offline events
  window.addEventListener('online', () => {
    errorState.offlineDetected = false;
    showErrorToast('Your internet connection has been restored.', {
      level: 'success',
      duration: 3000
    });
  });
  
  window.addEventListener('offline', () => {
    errorState.offlineDetected = true;
    showErrorToast('You are currently offline. Some features may be unavailable.', {
      level: 'warning',
      duration: 0 // Don't auto-hide
    });
  });
  
  // Expose public API
  return {
    handleError,
    showErrorToast,
    showErrorModal,
    showGlobalErrorBanner,
    hideGlobalErrorBanner,
    hideErrorModal,
    withErrorHandling,
    createRetryFunction,
    shouldUseFallback,
    recordFallbackUsage,
    getErrorStats,
    configure,
    clearErrorHistory
  };
})();

// Make service available globally
window.ErrorHandlingService = ErrorHandlingService;