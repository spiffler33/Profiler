/**
 * Loading State Manager - Manages loading states across the application
 * 
 * This service provides a consistent interface for showing loading states
 * across different parts of the application. It handles:
 * - Component-specific loading indicators
 * - Global loading indicators and progress bars
 * - Error messages and toast notifications
 * - Skeleton loading placeholders
 */

const LoadingStateManager = (function() {
  // Configuration
  const config = {
    defaultLoadingSize: 'default',
    defaultLoadingMessage: 'Loading...',
    progressBarTimeout: 10000, // 10 seconds
    errorMessageDuration: 5000, // 5 seconds
    autoShowProgressBar: true,
    logErrors: true
  };
  
  // State tracking
  const state = {
    loadingComponents: new Set(),
    loadingTimeouts: {},
    globalProgressBarVisible: false,
    globalLoadingOverlayVisible: false
  };
  
  /**
   * Initialize the loading state manager
   * This will be called when the module is loaded
   */
  function initialize() {
    createDefaultElements();
    monitorFetchRequests();
    
    // Expose the API globally
    window.loadingState = {
      setLoading,
      showGlobalLoading,
      hideGlobalLoading,
      showProgressBar,
      hideProgressBar,
      showError,
      createSkeletons,
      configure
    };
    
    // Return to allow direct use via import as well
    return window.loadingState;
  }
  
  /**
   * Create the default DOM elements needed for the loading system
   * if they don't already exist
   */
  function createDefaultElements() {
    const body = document.body;
    
    // Create global progress loader if it doesn't exist
    if (!document.getElementById('global-progress-loader')) {
      const progressLoader = document.createElement('div');
      progressLoader.id = 'global-progress-loader';
      progressLoader.className = 'progress-loader hidden';
      body.appendChild(progressLoader);
    }
    
    // Create global loading overlay if it doesn't exist
    if (!document.getElementById('global-loading-overlay')) {
      const loadingOverlay = document.createElement('div');
      loadingOverlay.id = 'global-loading-overlay';
      loadingOverlay.className = 'loading-overlay hidden';
      
      const overlayContent = document.createElement('div');
      overlayContent.className = 'loading-overlay-content';
      
      const spinner = document.createElement('div');
      spinner.className = 'w-12 h-12 rounded-full border-4 border-t-4 border-gray-200 border-t-green-500 animate-spin';
      
      const loadingText = document.createElement('p');
      loadingText.className = 'mt-4 loading-text';
      loadingText.textContent = 'Processing';
      
      overlayContent.appendChild(spinner);
      overlayContent.appendChild(loadingText);
      loadingOverlay.appendChild(overlayContent);
      body.appendChild(loadingOverlay);
    }
    
    // Create global error toast if it doesn't exist
    if (!document.getElementById('global-error-toast')) {
      const errorToast = document.createElement('div');
      errorToast.id = 'global-error-toast';
      errorToast.className = 'hidden fixed bottom-4 right-4 bg-red-50 border-l-4 border-red-500 p-4 rounded shadow z-50';
      
      const errorContent = document.createElement('div');
      errorContent.id = 'global-error-content';
      errorContent.className = 'text-red-800';
      
      errorToast.appendChild(errorContent);
      body.appendChild(errorToast);
    }
  }
  
  /**
   * Sets loading state for a component
   * @param {string|Element} element - Element ID or element object
   * @param {boolean} isLoading - Whether the element is loading
   * @param {Object} options - Additional options
   */
  function setLoading(element, isLoading, options = {}) {
    // Default options
    const defaults = {
      size: config.defaultLoadingSize,
      text: config.defaultLoadingMessage,
      showProgressBar: config.autoShowProgressBar,
      timeout: config.progressBarTimeout
    };
    
    const settings = {...defaults, ...options};
    
    // Get the element
    const el = typeof element === 'string' ? document.getElementById(element) : element;
    if (!el) return false;
    
    // Get component ID for tracking
    const componentId = el.id || `loading-element-${Math.random().toString(36).substring(2, 9)}`;
    
    // Toggle loading state
    if (isLoading) {
      // Add to tracking set
      state.loadingComponents.add(componentId);
      
      // Add loading class and size class if specified
      el.classList.add('is-loading');
      if (settings.size !== 'default') {
        el.classList.add(`size-${settings.size}`);
      }
      
      // Set aria attributes for accessibility
      el.setAttribute('aria-busy', 'true');
      
      // Show progress bar if requested
      if (settings.showProgressBar) {
        showProgressBar();
        
        // Set up timeout to hide progress bar if loading takes too long
        if (settings.timeout > 0) {
          clearTimeout(state.loadingTimeouts[componentId]);
          state.loadingTimeouts[componentId] = setTimeout(() => {
            // Only hide if no other components are still loading
            if (state.loadingComponents.size === 1 && state.loadingComponents.has(componentId)) {
              hideProgressBar();
            }
          }, settings.timeout);
        }
      }
      
      // Dispatch custom event
      const event = new CustomEvent('loadingStateChanged', {
        detail: { 
          element: el, 
          isLoading: true,
          options: settings
        }
      });
      document.dispatchEvent(event);
      
      return true;
    } else {
      // Remove from tracking set
      state.loadingComponents.delete(componentId);
      
      // Clear any pending timeouts
      if (state.loadingTimeouts[componentId]) {
        clearTimeout(state.loadingTimeouts[componentId]);
        delete state.loadingTimeouts[componentId];
      }
      
      // Remove loading classes
      el.classList.remove('is-loading');
      el.classList.remove('size-sm', 'size-lg');
      
      // Remove aria attributes
      el.setAttribute('aria-busy', 'false');
      
      // Hide progress bar if no other components are loading
      if (settings.showProgressBar && state.loadingComponents.size === 0) {
        hideProgressBar();
      }
      
      // Dispatch custom event
      const event = new CustomEvent('loadingStateChanged', {
        detail: { 
          element: el, 
          isLoading: false,
          options: settings
        }
      });
      document.dispatchEvent(event);
      
      return true;
    }
  }
  
  /**
   * Show the global progress bar
   * @returns {boolean} Success state
   */
  function showProgressBar() {
    const progressLoader = document.getElementById('global-progress-loader');
    if (!progressLoader) return false;
    
    progressLoader.classList.remove('hidden');
    state.globalProgressBarVisible = true;
    return true;
  }
  
  /**
   * Hide the global progress bar
   * @returns {boolean} Success state
   */
  function hideProgressBar() {
    const progressLoader = document.getElementById('global-progress-loader');
    if (!progressLoader) return false;
    
    progressLoader.classList.add('hidden');
    state.globalProgressBarVisible = false;
    return true;
  }
  
  /**
   * Show full-page loading overlay
   * @param {string} text - Loading text to display
   * @returns {boolean} Success state
   */
  function showGlobalLoading(text = 'Processing') {
    const overlay = document.getElementById('global-loading-overlay');
    if (!overlay) return false;
    
    // Set loading text
    const loadingText = overlay.querySelector('.loading-text');
    if (loadingText) {
      loadingText.textContent = text;
    }
    
    // Show overlay
    overlay.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
    state.globalLoadingOverlayVisible = true;
    
    return true;
  }
  
  /**
   * Hide full-page loading overlay
   * @returns {boolean} Success state
   */
  function hideGlobalLoading() {
    const overlay = document.getElementById('global-loading-overlay');
    if (!overlay) return false;
    
    overlay.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
    state.globalLoadingOverlayVisible = false;
    
    return true;
  }
  
  /**
   * Show global error toast
   * @param {string} message - Error message to display
   * @param {number} duration - Duration in ms to show toast (0 for no auto-hide)
   * @returns {boolean} Success state
   */
  function showError(message, duration = config.errorMessageDuration) {
    const errorToast = document.getElementById('global-error-toast');
    const errorContent = document.getElementById('global-error-content');
    if (!errorToast || !errorContent) return false;
    
    // Log the error if configured to do so
    if (config.logErrors) {
      console.error('Error:', message);
    }
    
    // Set error message
    errorContent.textContent = message;
    
    // Show toast
    errorToast.classList.remove('hidden');
    
    // Auto-hide after duration
    if (duration > 0) {
      setTimeout(() => {
        errorToast.classList.add('hidden');
      }, duration);
    }
    
    return true;
  }
  
  /**
   * Create skeleton loading placeholders
   * @param {string|Element} container - Container ID or element
   * @param {string} type - Type of skeleton ('text', 'circle', 'box', 'button')
   * @param {number} count - Number of skeletons to create
   * @param {Object} options - Additional options
   * @returns {boolean} Success state
   */
  function createSkeletons(container, type = 'text', count = 1, options = {}) {
    const containerEl = typeof container === 'string' ? document.getElementById(container) : container;
    if (!containerEl) return false;
    
    // Clear container
    containerEl.innerHTML = '';
    
    // Create skeletons
    for (let i = 0; i < count; i++) {
      const skeleton = document.createElement('div');
      skeleton.className = `skeleton-loader skeleton-${type}`;
      
      // Add width class if specified
      if (options.width && ['25', '50', '75'].includes(options.width.toString())) {
        skeleton.classList.add(`width-${options.width}`);
      }
      
      containerEl.appendChild(skeleton);
    }
    
    return true;
  }
  
  /**
   * Configure the loading state manager
   * @param {Object} options - Configuration options
   */
  function configure(options = {}) {
    Object.assign(config, options);
  }
  
  /**
   * Monitor fetch requests to automatically show loading states
   */
  function monitorFetchRequests() {
    if (!window.fetch) return;
    
    // Store original fetch
    const originalFetch = window.fetch;
    
    // Override fetch with our version that tracks loading
    window.fetch = function(resource, init) {
      // Determine if this is an API request
      const isApiRequest = typeof resource === 'string' && (
        resource.startsWith('/api/') || 
        (init && init.headers && 
         init.headers['Content-Type'] === 'application/json')
      );
      
      // Show progress bar for API requests
      if (isApiRequest && config.autoShowProgressBar) {
        showProgressBar();
      }
      
      // Start request
      const startTime = Date.now();
      
      // Call original fetch
      const promise = originalFetch.apply(this, arguments);
      
      // When request completes
      promise.then(response => {
        // Hide progress bar for API requests
        if (isApiRequest && config.autoShowProgressBar) {
          // Only hide if no components are explicitly loading
          if (state.loadingComponents.size === 0) {
            hideProgressBar();
          }
        }
        
        // Calculate request time
        const requestTime = Date.now() - startTime;
        
        // Log API timings in development
        if (isApiRequest && window.location.hostname === 'localhost') {
          console.log(`API Request to ${resource} completed in ${requestTime}ms`);
        }
        
        return response;
      }).catch(error => {
        // Hide progress bar
        if (isApiRequest && config.autoShowProgressBar) {
          // Only hide if no components are explicitly loading
          if (state.loadingComponents.size === 0) {
            hideProgressBar();
          }
        }
        
        // Show error for API requests
        if (isApiRequest) {
          showError(`API Error: ${error.message || 'Unknown error'}`);
        }
        
        throw error;
      });
      
      return promise;
    };
  }
  
  // Initialize when the script loads
  return initialize();
})();

// Export the module
window.LoadingStateManager = LoadingStateManager;