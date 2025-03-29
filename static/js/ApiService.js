/**
 * API Service
 * 
 * Central API service for making authenticated requests to the backend
 * - Handles authentication token management
 * - Implements comprehensive error handling
 * - Provides automatic retries for recoverable errors
 * - Manages loading states for UI components
 * - Implements request caching with configurable TTL
 */

class ApiService {
  constructor() {
    this.baseUrl = '/api/v2';
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    this.pendingRequests = new Map();
    this.cache = new Map();
    this.TOKEN_KEY = 'auth_token';
    this.maxRetries = 2;
    this.retryDelay = 1000;
    
    // Error messages for different scenarios
    this.errorMessages = {
      network: "Network error: Unable to connect to the server. Please check your internet connection and try again.",
      timeout: "Request timed out. Please try again later.",
      server: "Server error: The server encountered an issue processing your request.",
      auth: "Authentication error: Your session may have expired. Please log in again.",
      validation: "Validation error: Please check your input and try again.",
      forbidden: "Access denied: You don't have permission to access this resource.",
      notFound: "Resource not found: The requested data doesn't exist or has been moved.",
      rateLimit: "Rate limit exceeded: Please wait before making more requests.",
      unknown: "An unexpected error occurred. Please try again later."
    };
  }

  /**
   * Get authentication token from storage
   * @returns {string|null} Auth token or null if not found
   */
  getAuthToken() {
    // Use AuthenticationService if available, otherwise fall back to direct storage access
    if (window.AuthenticationService) {
      return window.AuthenticationService.getAuthToken();
    }
    
    return localStorage.getItem(this.TOKEN_KEY) || sessionStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Make an API request with comprehensive error handling
   * 
   * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
   * @param {string} endpoint - API endpoint path
   * @param {Object} data - Request data (for POST/PUT)
   * @param {Object} options - Additional request options
   * @returns {Promise<any>} Response data
   */
  async request(method, endpoint, data = null, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    const cacheKey = options.cacheKey || `${method}:${url}:${JSON.stringify(data || {})}`;
    
    // Check cache for GET requests if not explicitly disabled
    if (method === 'GET' && options.useCache !== false) {
      const cachedData = this.getFromCache(cacheKey);
      if (cachedData) {
        return cachedData;
      }
    }

    // Cancel previous request with same key if requested
    if (options.cancelPrevious && this.pendingRequests.has(cacheKey)) {
      this.pendingRequests.get(cacheKey).abort();
    }
    
    // Show loading state if ID provided
    if (options.loadingId) {
      this.setLoading(options.loadingId, true, options.loadingText || 'Loading...');
    }

    // Request configuration
    const config = {
      method,
      headers: { ...this.defaultHeaders },
    };
    
    // Add auth token if available
    const authToken = this.getAuthToken();
    if (authToken) {
      config.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    // Add custom headers
    if (options.headers) {
      config.headers = { ...config.headers, ...options.headers };
    }
    
    // Add timeout if specified
    if (options.timeout) {
      config.timeout = options.timeout;
    }
    
    // Add request body for non-GET methods
    if (method !== 'GET' && data) {
      config.body = JSON.stringify(data);
    }
    
    // Create AbortController for request cancellation
    const controller = new AbortController();
    config.signal = controller.signal;
    this.pendingRequests.set(cacheKey, controller);
    
    // Initialize retry counter
    let retries = 0;
    
    // Retry loop
    while (true) {
      try {
        const response = await fetch(url, config);
        this.pendingRequests.delete(cacheKey);
        
        // Handle loading state
        if (options.loadingId) {
          this.setLoading(options.loadingId, false);
        }
        
        // Parse response
        let result;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          result = await response.json();
        } else {
          result = await response.text();
        }
        
        // Handle unsuccessful responses
        if (!response.ok) {
          // Handle specific error types
          const error = this.createError(response, result);
          
          // Handle authentication errors
          if (response.status === 401) {
            // Handle with AuthenticationService if available
            if (window.AuthenticationService) {
              const authContinue = await window.AuthenticationService.handleAuthenticationError(response, {
                redirectToLogin: options.redirectOnAuthError !== false,
                showMessage: options.showAuthErrorMessage !== false
              });
              
              // If auth error was handled and we shouldn't redirect yet, throw the error
              if (!authContinue) {
                throw error;
              }
            } else {
              // Without AuthenticationService, clear token directly
              localStorage.removeItem(this.TOKEN_KEY);
              sessionStorage.removeItem(this.TOKEN_KEY);
              
              // Redirect to login if not explicitly disabled
              if (options.redirectOnAuthError !== false) {
                window.location.href = `/login?return_to=${encodeURIComponent(window.location.pathname)}`;
              }
              
              throw error;
            }
          }
          
          // If it's a server error and we haven't reached max retries, retry
          if (response.status >= 500 && retries < this.maxRetries && options.retry !== false) {
            retries++;
            
            // Exponential backoff delay
            const delay = this.retryDelay * Math.pow(2, retries - 1);
            await new Promise(resolve => setTimeout(resolve, delay));
            
            // Continue to next iteration (retry)
            continue;
          }
          
          // If it's a rate limit error, wait and retry
          if (response.status === 429 && retries < this.maxRetries && options.retry !== false) {
            retries++;
            
            // Get retry-after header or use default delay
            const retryAfter = response.headers.get('retry-after');
            const delay = retryAfter ? parseInt(retryAfter, 10) * 1000 : this.retryDelay * 2;
            
            await new Promise(resolve => setTimeout(resolve, delay));
            
            // Continue to next iteration (retry)
            continue;
          }
          
          // Use ErrorHandlingService if available and not disabled
          if (window.ErrorHandlingService && options.useErrorService !== false) {
            window.ErrorHandlingService.handleError(error, options.context || 'api_request', {
              showToast: options.showErrorToast !== false,
              metadata: { endpoint, method, requestData: data }
            });
          } else if (options.showErrorToast !== false) {
            // Simple error toast fallback
            this.showErrorMessage(error.message);
          }
          
          throw error;
        }
        
        // Cache successful GET responses
        if (method === 'GET' && options.useCache !== false) {
          this.addToCache(cacheKey, result, options.cacheTTL);
        }
        
        return result;
      } catch (error) {
        // Handle loading state
        if (options.loadingId) {
          this.setLoading(options.loadingId, false);
        }
        
        // Handle aborted requests
        if (error.name === 'AbortError') {
          console.log('Request cancelled:', cacheKey);
          return { cancelled: true };
        }
        
        // Handle network errors with retry
        if (error.name === 'TypeError' && error.message.includes('NetworkError') && 
            retries < this.maxRetries && options.retry !== false) {
          retries++;
          
          // Linear backoff for network errors
          await new Promise(resolve => setTimeout(resolve, this.retryDelay));
          
          // Continue to next iteration (retry)
          continue;
        }
        
        // Handle timeout errors
        if (error.name === 'TimeoutError' && retries < this.maxRetries && options.retry !== false) {
          retries++;
          
          // Exponential backoff for timeouts
          const delay = this.retryDelay * Math.pow(1.5, retries - 1);
          await new Promise(resolve => setTimeout(resolve, delay));
          
          // Continue to next iteration (retry)
          continue;
        }
        
        // Use ErrorHandlingService if available and not disabled
        if (window.ErrorHandlingService && options.useErrorService !== false) {
          window.ErrorHandlingService.handleError(error, options.context || 'api_request', {
            showToast: options.showErrorToast !== false,
            metadata: { endpoint, method, requestData: data }
          });
        } else if (options.showErrorToast !== false) {
          // Simple error toast fallback
          this.showErrorMessage(error.message || this.errorMessages.unknown);
        }
        
        throw error;
      }
    }
  }

  /**
   * Create a normalized error object with additional metadata
   * 
   * @param {Response} response - Fetch Response object
   * @param {Object|string} data - Response data
   * @returns {Error} Enhanced error object
   */
  createError(response, data) {
    const error = new Error(
      (data && data.message) || 
      (data && data.error) || 
      this.getErrorMessageByStatus(response.status)
    );
    
    error.status = response.status;
    error.statusText = response.statusText;
    error.data = data;
    
    // Add error code if available
    if (data && data.error_code) {
      error.code = data.error_code;
    } else {
      error.code = this.getErrorCodeByStatus(response.status);
    }
    
    // Add validation errors if available
    if (data && data.errors) {
      error.validationErrors = data.errors;
    }
    
    return error;
  }

  /**
   * Get error message based on HTTP status code
   * 
   * @param {number} status - HTTP status code
   * @returns {string} Error message
   */
  getErrorMessageByStatus(status) {
    switch (true) {
      case status === 400:
        return this.errorMessages.validation;
      case status === 401:
        return this.errorMessages.auth;
      case status === 403:
        return this.errorMessages.forbidden;
      case status === 404:
        return this.errorMessages.notFound;
      case status === 429:
        return this.errorMessages.rateLimit;
      case status >= 500:
        return this.errorMessages.server;
      default:
        return this.errorMessages.unknown;
    }
  }

  /**
   * Get error code based on HTTP status code
   * 
   * @param {number} status - HTTP status code
   * @returns {string} Error code
   */
  getErrorCodeByStatus(status) {
    switch (true) {
      case status === 400:
        return 'validation_error';
      case status === 401:
        return 'authentication_error';
      case status === 403:
        return 'forbidden';
      case status === 404:
        return 'not_found';
      case status === 429:
        return 'rate_limit_exceeded';
      case status >= 500:
        return 'server_error';
      default:
        return 'unknown_error';
    }
  }

  /**
   * Show an error message
   * 
   * @param {string} message - Error message to display
   */
  showErrorMessage(message) {
    // Check if we have a toast system
    if (window.ToastService) {
      window.ToastService.show(message, { type: 'error' });
      return;
    }
    
    // Use alert as fallback
    console.error('API Error:', message);
    // Don't show alert as it can be disruptive
    // alert('Error: ' + message);
  }

  /**
   * Set loading state for a UI element
   * 
   * @param {string|Element} elementId - Element ID or element to show loading state on
   * @param {boolean} isLoading - Whether to show or hide loading state
   * @param {string} text - Optional loading text to display
   * @returns {boolean} Success indicator
   */
  setLoading(elementId, isLoading, text) {
    // Use LoadingStateManager if available
    if (window.LoadingStateManager) {
      return window.LoadingStateManager.setLoading(elementId, isLoading, { text });
    }
    
    // Simple fallback implementation
    const element = typeof elementId === 'string' ? document.getElementById(elementId) : elementId;
    if (!element) return false;
    
    if (isLoading) {
      element.classList.add('is-loading');
      element.setAttribute('aria-busy', 'true');
      
      // If element has a data-loading-text attribute, store original text
      if (element.innerText && !element.dataset.originalText && text) {
        element.dataset.originalText = element.innerText;
        element.innerText = text;
      }
    } else {
      element.classList.remove('is-loading');
      element.setAttribute('aria-busy', 'false');
      
      // Restore original text if it was stored
      if (element.dataset.originalText) {
        element.innerText = element.dataset.originalText;
        delete element.dataset.originalText;
      }
    }
    
    return true;
  }
  
  /**
   * Get data from cache
   * 
   * @param {string} key - Cache key
   * @returns {any|null} Cached data or null if not found/expired
   */
  getFromCache(key) {
    if (!this.cache.has(key)) return null;
    
    const cacheEntry = this.cache.get(key);
    if (cacheEntry.expires && cacheEntry.expires < Date.now()) {
      this.cache.delete(key);
      return null;
    }
    
    return cacheEntry.data;
  }
  
  /**
   * Add data to cache
   * 
   * @param {string} key - Cache key
   * @param {any} data - Data to cache
   * @param {number} ttl - Time to live in milliseconds
   */
  addToCache(key, data, ttl = 300000) { // Default 5 minutes
    this.cache.set(key, {
      data,
      expires: ttl ? Date.now() + ttl : null,
      added: Date.now()
    });
  }
  
  /**
   * Clear all cache or by pattern
   * 
   * @param {string|null} pattern - Optional regex pattern to match keys
   */
  clearCache(pattern = null) {
    if (!pattern) {
      this.cache.clear();
      return;
    }
    
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }
  
  /**
   * Convenience method for GET requests
   * 
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async get(endpoint, options = {}) {
    return this.request('GET', endpoint, null, options);
  }
  
  /**
   * Convenience method for POST requests
   * 
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async post(endpoint, data, options = {}) {
    return this.request('POST', endpoint, data, options);
  }
  
  /**
   * Convenience method for PUT requests
   * 
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async put(endpoint, data, options = {}) {
    return this.request('PUT', endpoint, data, options);
  }
  
  /**
   * Convenience method for DELETE requests
   * 
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data
   */
  async delete(endpoint, options = {}) {
    return this.request('DELETE', endpoint, null, options);
  }
  
  /**
   * Create a new user profile
   * 
   * @param {Object} profileData - Profile data to create
   * @param {Object} options - Request options
   * @returns {Promise<any>} Response data with created profile
   */
  async createProfile(profileData, options = {}) {
    return this.post('/profiles', profileData, options);
  }

  /**
   * Execute multiple requests in a batch
   * 
   * @param {Array<Object>} requests - Array of request configs
   * @param {Object} options - Batch options
   * @returns {Promise<Array>} Array of response data
   */
  async batch(requests, options = {}) {
    const results = [];
    const loadingId = options.loadingId;
    
    if (loadingId) {
      this.setLoading(loadingId, true, options.loadingText || 'Processing batch request...');
    }
    
    try {
      if (options.parallel) {
        // Execute requests in parallel
        const promises = requests.map(req => {
          const method = req.method || 'GET';
          return this.request(
            method,
            req.endpoint,
            req.data,
            { ...req.options, loadingId: null } // Don't show individual loading indicators
          ).catch(err => ({ error: err }));
        });
        
        const responses = await Promise.all(promises);
        results.push(...responses);
      } else {
        // Execute requests sequentially
        for (const req of requests) {
          const method = req.method || 'GET';
          try {
            const result = await this.request(
              method,
              req.endpoint,
              req.data,
              { ...req.options, loadingId: null }
            );
            results.push(result);
          } catch (err) {
            results.push({ error: err });
            if (options.stopOnError) break;
          }
        }
      }
    } finally {
      if (loadingId) {
        this.setLoading(loadingId, false);
      }
    }
    
    return results;
  }
}

// Create and export a singleton instance
window.ApiService = new ApiService();