/**
 * Central API Service
 * 
 * Provides a unified interface for all API communication in the application.
 * This service extends the patterns established in VisualizationDataService
 * but generalizes them for all component types and API endpoints.
 * 
 * Features:
 * - Authentication token management (integrated with AuthenticationService)
 * - Unified error handling via ErrorHandlingService
 * - Loading state management via LoadingStateManager
 * - Request batching for related operations
 * - Caching with TTL, size limits, and prioritization
 * - Intelligent request deduplication
 * - Network status detection and offline mode
 * - Request timeout and retry mechanisms
 */

const ApiService = (function() {
  // Import AuthenticationService if available
  const AuthService = window.AuthenticationService || null;
  
  // Configuration
  const config = {
    // API settings
    apiBasePath: '/api/v2',
    defaultHeaders: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    
    // Request settings
    requestTimeout: 15000, // 15 seconds
    retryAttempts: 2,
    retryDelay: 1000, // 1 second
    
    // Authentication settings
    tokenKey: 'auth_token',
    refreshTokenKey: 'refresh_token',
    tokenType: 'Basic', // Changed to Basic for HTTP Basic Auth
    persistentAuth: true, // Use localStorage instead of sessionStorage
    
    // Cache settings
    useCache: true,
    defaultCacheTTL: 300000, // 5 minutes
    resourceSpecificTTL: {
      profiles: 600000,       // 10 minutes for profiles
      parameters: 900000,     // 15 minutes for parameters
      goals: 300000,          // 5 minutes for goals
      questions: 180000       // 3 minutes for questions
    },
    
    // Cache priorities (higher is more important)
    cachePriorities: {
      profiles: 8,
      goals: 7,
      parameters: 6,
      questions: 5
    },
    
    // Batching settings
    enableBatching: true,
    batchDelay: 50, // ms
    maxBatchSize: 5,
    
    // Monitoring and debugging
    logRequests: false,
    enableNetworkDetection: true,
    debugMode: false
  };
  
  // Request tracking
  const pendingRequests = new Map();
  const requestStates = {};
  
  // Authentication state
  let authState = {
    isAuthenticated: false,
    token: null,
    refreshToken: null,
    tokenExpiry: null
  };
  
  // API resource definitions (for endpoint construction)
  const apiResources = {
    profiles: {
      base: '/profiles',
      detail: id => `/profiles/${id}`,
      overview: id => `/profiles/${id}/overview`,
      understanding: id => `/profiles/${id}/understanding`
    },
    goals: {
      base: '/goals',
      detail: id => `/goals/${id}`,
      visualizationData: id => `/goals/${id}/visualization-data`,
      probability: id => `/goals/${id}/calculate-probability`,
      batchProbability: id => `/goals/${id}/calculate-probability/batch`,
      adjustments: id => `/goals/${id}/adjustments`,
      scenarios: id => `/goals/${id}/scenarios`
    },
    parameters: {
      base: '/parameters',
      detail: id => `/parameters/${id}`,
      categories: '/parameters/categories'
    },
    questions: {
      flow: '/questions/flow',
      dynamic: '/questions/dynamic',
      submit: '/questions/submit'
    },
    admin: {
      parameters: '/admin/parameters',
      cache: '/admin/cache',
      health: '/admin/health'
    },
    auth: {
      login: '/auth/login',
      logout: '/auth/logout',
      refresh: '/auth/refresh'
    }
  };

  /**
   * Initialize the service
   */
  function initialize() {
    // Load authentication token if available
    loadAuthToken();
    
    // Set up network status listeners
    if (config.enableNetworkDetection) {
      window.addEventListener('online', handleNetworkStatusChange);
      window.addEventListener('offline', handleNetworkStatusChange);
    }
    
    // Subscribe to authentication events from AuthenticationService if available
    if (AuthService && typeof AuthService.subscribe === 'function') {
      AuthService.subscribe(handleAuthEvent);
    }
    
    // Log initialization
    if (config.debugMode) {
      console.log('ApiService initialized', {
        authenticated: authState.isAuthenticated,
        cacheEnabled: config.useCache,
        batchingEnabled: config.enableBatching,
        authServiceIntegrated: !!AuthService
      });
    }
  }
  
  /**
   * Handle authentication events from AuthenticationService
   * @param {Object} event - Auth event object
   */
  function handleAuthEvent(event) {
    if (config.debugMode) {
      console.log('Auth event received:', event);
    }
    
    // Update our internal auth state based on the event
    if (event.type === 'login') {
      // Get token from AuthService
      const token = AuthService.getToken();
      if (token) {
        authState.token = token;
        authState.isAuthenticated = true;
      }
    } else if (event.type === 'logout') {
      // Clear our auth state
      authState.token = null;
      authState.refreshToken = null;
      authState.isAuthenticated = false;
      authState.tokenExpiry = null;
      
      // Clear any cached data
      clearCache();
    }
  }
  
  /**
   * Handle network status changes
   */
  function handleNetworkStatusChange() {
    const isOnline = navigator.onLine;
    
    if (config.debugMode) {
      console.log(`Network status changed: ${isOnline ? 'online' : 'offline'}`);
    }
    
    if (isOnline) {
      // Could retry failed requests here if desired
    }
  }
  
  /**
   * Check if the browser is online
   * @returns {boolean} Online status
   */
  function isOnline() {
    if (!config.enableNetworkDetection) return true;
    return navigator.onLine !== false; // Consider online unless explicitly false
  }
  
  /**
   * Generate a cache key for a request
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {string} Cache key
   */
  function generateCacheKey(method, endpoint, data) {
    if (method !== 'GET' && method !== 'POST') return null; // Only cache GET and some POST
    
    // For POST requests, only cache specific endpoints like probability calculations
    if (method === 'POST' && !endpoint.includes('calculate-probability')) {
      return null;
    }
    
    return `${method}:${endpoint}:${data ? JSON.stringify(data) : ''}`;
  }
  
  /**
   * Authentication Functions
   */
  
  /**
   * Get the authentication token
   * @returns {string|null} The auth token or null if not authenticated
   */
  function getAuthToken() {
    // Try to get token from AuthenticationService first
    if (AuthService && typeof AuthService.getToken === 'function') {
      const token = AuthService.getToken();
      if (token) {
        // Update our internal state
        authState.token = token;
        authState.isAuthenticated = true;
        return token;
      }
    }
    
    // Fall back to internal state/storage
    if (authState.token) return authState.token;
    return loadAuthToken();
  }
  
  /**
   * Load authentication token from storage
   * @returns {string|null} The auth token or null if not found
   */
  function loadAuthToken() {
    // Try to get token from AuthenticationService first
    if (AuthService && typeof AuthService.getToken === 'function') {
      const token = AuthService.getToken();
      if (token) {
        authState.token = token;
        authState.isAuthenticated = true;
        return token;
      }
    }
    
    // Fall back to our own storage mechanism
    const storage = config.persistentAuth ? localStorage : sessionStorage;
    const token = storage.getItem(config.tokenKey);
    const refreshToken = storage.getItem(config.refreshTokenKey);
    
    if (token) {
      authState.token = token;
      authState.refreshToken = refreshToken;
      authState.isAuthenticated = true;
      
      // Try to get expiry from token if it's a JWT
      try {
        const tokenData = parseJwt(token);
        if (tokenData && tokenData.exp) {
          authState.tokenExpiry = tokenData.exp * 1000; // Convert to milliseconds
        }
      } catch (e) {
        // Not a JWT or invalid format, ignore
      }
      
      return token;
    }
    
    return null;
  }
  
  /**
   * Parse a JWT token
   * @param {string} token - JWT token
   * @returns {Object} Decoded token data
   */
  function parseJwt(token) {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(window.atob(base64));
    } catch (e) {
      return null;
    }
  }
  
  /**
   * Set the authentication token
   * @param {Object} tokenData - Token data from authentication
   * @param {boolean} persistent - Whether to persist in localStorage
   */
  function setAuthToken(tokenData, persistent = config.persistentAuth) {
    if (!tokenData || !tokenData.token) {
      console.error('Invalid token data provided');
      return false;
    }
    
    const storage = persistent ? localStorage : sessionStorage;
    const { token, refreshToken, expiresIn } = tokenData;
    
    // Store tokens
    storage.setItem(config.tokenKey, token);
    if (refreshToken) {
      storage.setItem(config.refreshTokenKey, refreshToken);
    }
    
    // Update auth state
    authState.token = token;
    authState.refreshToken = refreshToken || null;
    authState.isAuthenticated = true;
    
    // Set expiry if provided
    if (expiresIn) {
      const expiryTime = Date.now() + (expiresIn * 1000);
      authState.tokenExpiry = expiryTime;
    } else {
      // Try to get expiry from token if it's a JWT
      try {
        const tokenData = parseJwt(token);
        if (tokenData && tokenData.exp) {
          authState.tokenExpiry = tokenData.exp * 1000;
        }
      } catch (e) {
        // Not a JWT or invalid format, ignore
        authState.tokenExpiry = null;
      }
    }
    
    if (config.debugMode) {
      console.log('Auth token set', { 
        persistent, 
        hasRefreshToken: !!refreshToken,
        expiry: authState.tokenExpiry ? new Date(authState.tokenExpiry) : 'unknown'
      });
    }
    
    return true;
  }
  
  /**
   * Clear authentication token and state
   */
  function clearAuthToken() {
    const storage = config.persistentAuth ? localStorage : sessionStorage;
    
    storage.removeItem(config.tokenKey);
    storage.removeItem(config.refreshTokenKey);
    
    authState.token = null;
    authState.refreshToken = null;
    authState.isAuthenticated = false;
    authState.tokenExpiry = null;
    
    if (config.debugMode) {
      console.log('Auth tokens cleared');
    }
  }
  
  /**
   * Check if token needs refresh and refresh if needed
   * @returns {Promise<boolean>} True if token is valid, false otherwise
   */
  async function checkAndRefreshToken() {
    // If no token or no expiry, can't refresh
    if (!authState.token || !authState.tokenExpiry) {
      return false;
    }
    
    // If token is not expired, it's valid
    if (authState.tokenExpiry > Date.now() + 30000) { // 30 second buffer
      return true;
    }
    
    // If we have a refresh token, try to refresh
    if (authState.refreshToken) {
      try {
        const response = await fetch(`${config.apiBasePath}${apiResources.auth.refresh}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ refreshToken: authState.refreshToken })
        });
        
        if (response.ok) {
          const tokenData = await response.json();
          setAuthToken(tokenData, config.persistentAuth);
          return true;
        }
      } catch (error) {
        if (config.debugMode) {
          console.error('Token refresh failed', error);
        }
      }
    }
    
    // If we get here, token refresh failed
    clearAuthToken();
    return false;
  }
  
  /**
   * Login with username and password
   * @param {string} username - Username
   * @param {string} password - Password
   * @param {boolean} remember - Whether to persist the session
   * @returns {Promise<Object>} Auth result
   */
  async function login(username, password, remember = false) {
    try {
      // Use AuthenticationService if available
      if (AuthService && typeof AuthService.login === 'function') {
        const result = await AuthService.login(username, password, remember);
        
        if (result.success) {
          // AuthenticationService handled the token storage, but update our internal state too
          loadAuthToken();
        }
        
        return result;
      }
      
      // Legacy implementation
      const response = await request('POST', apiResources.auth.login, {
        username,
        password,
        remember
      }, {
        requiresAuth: false,
        useCache: false
      });
      
      if (response && response.token) {
        setAuthToken(response, remember);
        return {
          success: true,
          user: response.user
        };
      }
      
      return { success: false, error: 'Invalid login response' };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Login failed'
      };
    }
  }
  
  /**
   * Logout the current user
   * @returns {Promise<Object>} Logout result
   */
  async function logout() {
    try {
      // Use AuthenticationService if available
      if (AuthService && typeof AuthService.logout === 'function') {
        AuthService.logout();
        // AuthenticationService will trigger an event that we'll catch to clear our state
        return { success: true };
      }
      
      // Legacy implementation
      // Call logout endpoint if authenticated
      if (authState.isAuthenticated) {
        await request('POST', apiResources.auth.logout, null, {
          requiresAuth: true,
          useCache: false,
          allowFailure: true // Continue even if server logout fails
        });
      }
      
      // Always clear local auth state
      clearAuthToken();
      
      // Clear any cached data
      if (window.PerformanceOptimizer && window.PerformanceOptimizer.cache) {
        window.PerformanceOptimizer.cache.clear();
      }
      
      return { success: true };
    } catch (error) {
      // Still clear token even if request fails
      clearAuthToken();
      
      return { 
        success: true, // Still consider logout successful even if API call fails
        warning: error.message || 'Server logout failed, but local session was cleared'
      };
    }
  }
  
  /**
   * Core API Request Function
   */
  
  /**
   * Make an API request
   * @param {string} method - HTTP method (GET, POST, etc.)
   * @param {string} endpoint - API endpoint (without base path)
   * @param {Object} data - Request data (for POST, PUT, etc.)
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Response data
   */
  async function request(method, endpoint, data = null, options = {}) {
    // Default options
    const {
      headers = {},
      timeout = config.requestTimeout,
      retryAttempts = config.retryAttempts,
      retryDelay = config.retryDelay,
      requiresAuth = true,
      useCache = config.useCache,
      cacheTTL = null,
      cachePriority = null,
      loadingId = null,
      loadingText = 'Loading...',
      cancelPrevious = false,
      context = 'api_request',
      showErrorToast = true,
      allowFailure = false,
      onAuthError = null
    } = options;
    
    // Create full URL
    const url = `${config.apiBasePath}${endpoint}`;
    
    // Generate cache key for GET requests if cache is enabled
    const cacheKey = useCache ? generateCacheKey(method, endpoint, data) : null;
    
    // Check if response is in cache
    if (method === 'GET' && useCache && cacheKey) {
      const cachedResponse = getCachedResponse(cacheKey);
      if (cachedResponse) {
        return cachedResponse;
      }
    }
    
    // Check if we're offline
    if (!isOnline()) {
      const error = new Error('You are currently offline. Please check your internet connection and try again.');
      error.isOffline = true;
      
      // Update request state
      updateRequestState(endpoint, 'error', error.message);
      
      // Try to get a cached version if offline
      if (useCache && cacheKey) {
        const cachedResponse = getCachedResponse(cacheKey, true); // Ignore TTL when offline
        if (cachedResponse) {
          return {
            ...cachedResponse,
            _metadata: {
              fromCache: true,
              offlineMode: true,
              timestamp: getCachedResponseTimestamp(cacheKey)
            }
          };
        }
      }
      
      throw error;
    }
    
    // If authentication is required, ensure token is valid
    if (requiresAuth) {
      const tokenValid = await checkAndRefreshToken();
      if (!tokenValid) {
        // Token is invalid or refresh failed
        const error = new Error('Authentication required. Please log in again.');
        error.status = 401;
        
        // Handle auth error callback if provided
        if (onAuthError) {
          onAuthError();
        }
        
        throw error;
      }
    }
    
    // Cancel previous request with same endpoint if requested
    if (cancelPrevious && pendingRequests.has(endpoint)) {
      pendingRequests.get(endpoint).abort();
      pendingRequests.delete(endpoint);
    }
    
    // Start loading state if ID provided
    if (loadingId) {
      window.LoadingStateManager.setLoading(loadingId, true, {
        text: loadingText
      });
    }
    
    // Update request state to loading
    updateRequestState(endpoint, 'loading');
    
    // Create AbortController for timeout
    const controller = new AbortController();
    const signal = controller.signal;
    
    // Add this controller to pending requests
    pendingRequests.set(endpoint, controller);
    
    // Set timeout if specified
    let timeoutId = null;
    if (timeout > 0) {
      timeoutId = setTimeout(() => {
        controller.abort();
        if (config.debugMode) {
          console.log(`Request to ${endpoint} timed out after ${timeout}ms`);
        }
      }, timeout);
    }
    
    // Create request config
    const requestConfig = {
      method,
      headers: { ...config.defaultHeaders, ...headers },
      signal
    };
    
    // Add auth token if available and required
    if (requiresAuth && authState.token) {
      requestConfig.headers['Authorization'] = `${config.tokenType} ${authState.token}`;
    }
    
    // Add body for non-GET requests
    if (method !== 'GET' && data !== null) {
      requestConfig.body = JSON.stringify(data);
    }
    
    // Implement retry logic
    let attemptCount = 0;
    let lastError = null;
    
    while (attemptCount <= retryAttempts) {
      try {
        // Log retry attempts in debug mode
        if (attemptCount > 0 && config.debugMode) {
          console.log(`Retry attempt ${attemptCount} for ${endpoint}`);
        }
        
        // Execute request
        const startTime = Date.now();
        const response = await fetch(url, requestConfig);
        const duration = Date.now() - startTime;
        
        // Clean up timeout and pending request
        clearTimeout(timeoutId);
        pendingRequests.delete(endpoint);
        
        // Stop loading indicator
        if (loadingId) {
          window.LoadingStateManager.setLoading(loadingId, false);
        }
        
        // Log request in debug mode
        if (config.debugMode || config.logRequests) {
          console.log(`API ${method} ${endpoint} completed in ${duration}ms with status ${response.status}`);
        }
        
        // Track API performance if PerformanceOptimizer is available
        if (window.PerformanceOptimizer) {
          window.PerformanceOptimizer.trackApiCall(
            `${method}_${endpoint}`, 
            duration, 
            response.ok, 
            false
          );
        }
        
        // Parse response
        let result;
        const contentType = response.headers.get('content-type');
        
        // Handle null responses or empty content
        if (response.status === 204 || response.headers.get('content-length') === '0') {
          result = { success: true, status: response.status };
        } else if (contentType && contentType.includes('application/json')) {
          try {
            result = await response.json();
          } catch (parseError) {
            console.error('Error parsing JSON response:', parseError);
            result = { error: 'Failed to parse JSON response', originalError: parseError.message };
          }
        } else {
          result = await response.text();
        }
        
        // Handle unsuccessful responses
        if (!response.ok) {
          // Handle auth errors
          if (response.status === 401) {
            clearAuthToken();
            
            if (onAuthError) {
              onAuthError();
            }
            
            const authError = new Error(result.message || 'Authentication required');
            authError.status = 401;
            throw authError;
          }
          
          // Create error with details
          const error = new Error(result.message || `API request failed with status ${response.status}`);
          error.status = response.status;
          error.data = result;
          
          // Handle error with ErrorHandlingService
          if (window.ErrorHandlingService && !allowFailure) {
            window.ErrorHandlingService.handleError(error, context, {
              showToast,
              metadata: { endpoint, method, requestData: data }
            });
          }
          
          throw error;
        }
        
        // Update request state to success
        updateRequestState(endpoint, 'success');
        
        // Cache successful GET responses if caching is enabled
        if (method === 'GET' && useCache && cacheKey) {
          cacheResponse(cacheKey, result, endpoint, cacheTTL, cachePriority);
        }
        
        return result;
      } catch (error) {
        // Stop loading indicator
        if (loadingId) {
          window.LoadingStateManager.setLoading(loadingId, false);
        }
        
        // Clean up pending request reference
        pendingRequests.delete(endpoint);
        
        // Handle abort/timeout specifically
        if (error.name === 'AbortError') {
          updateRequestState(endpoint, 'error', 'Request timed out');
          
          const timeoutError = new Error('Request timed out. Please try again.');
          timeoutError.isTimeout = true;
          
          // Track failed API call
          if (window.PerformanceOptimizer) {
            window.PerformanceOptimizer.trackApiCall(
              `${method}_${endpoint}`, 
              timeout, 
              false, 
              false
            );
          }
          
          throw timeoutError;
        }
        
        // Store the error
        lastError = error;
        
        // Update request state
        updateRequestState(endpoint, 'error', error.message);
        
        // Log error in debug mode
        if (config.debugMode) {
          console.error(`Error in ${method} ${endpoint} (attempt ${attemptCount + 1}/${retryAttempts + 1}):`, error);
        }
        
        // Check if we should retry
        if (attemptCount >= retryAttempts) {
          break;
        }
        
        // Don't retry certain errors
        if (error.status === 401 || error.status === 403 || error.status === 404) {
          break;
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attemptCount)));
        attemptCount++;
      }
    }
    
    // If we get here, all retry attempts failed
    if (window.ErrorHandlingService && !allowFailure) {
      window.ErrorHandlingService.handleError(
        lastError, 
        `${context} after ${retryAttempts} retry attempts`, 
        {
          showToast,
          metadata: { endpoint, method, requestData: data }
        }
      );
    }
    
    throw lastError;
  }
  
  /**
   * Update the state of a request
   * @param {string} endpoint - API endpoint
   * @param {string} state - State ('loading', 'success', 'error')
   * @param {string} error - Error message if state is 'error'
   */
  function updateRequestState(endpoint, state, error = null) {
    requestStates[endpoint] = {
      state,
      error,
      timestamp: Date.now()
    };
  }
  
  /**
   * Get the current state of a request
   * @param {string} endpoint - API endpoint
   * @returns {Object} Request state
   */
  function getRequestState(endpoint) {
    return requestStates[endpoint] || {
      state: 'idle',
      error: null,
      timestamp: null
    };
  }
  
  /**
   * Cache Management Functions
   */
  
  /**
   * Cache a response
   * @param {string} cacheKey - Cache key
   * @param {Object} data - Response data
   * @param {string} endpoint - API endpoint (for TTL determination)
   * @param {number} customTTL - Custom TTL in ms
   * @param {number} customPriority - Custom priority (1-10)
   */
  function cacheResponse(cacheKey, data, endpoint, customTTL, customPriority) {
    // Skip caching if disabled
    if (!config.useCache) return;
    
    // Determine TTL based on resource type or custom value
    let ttl = customTTL || config.defaultCacheTTL;
    
    // Check for resource-specific TTL
    for (const [resource, resourceTTL] of Object.entries(config.resourceSpecificTTL)) {
      if (endpoint.includes(resource)) {
        ttl = resourceTTL;
        break;
      }
    }
    
    // Determine priority based on resource type or custom value
    let priority = customPriority || 5; // Default priority
    
    // Check for resource-specific priority
    for (const [resource, resourcePriority] of Object.entries(config.cachePriorities)) {
      if (endpoint.includes(resource)) {
        priority = resourcePriority;
        break;
      }
    }
    
    // Use optimized cache if available
    if (window.PerformanceOptimizer && window.PerformanceOptimizer.cache) {
      window.PerformanceOptimizer.cache.set(
        cacheKey,
        data,
        {
          ttl,
          priority
        }
      );
      
      if (config.debugMode) {
        console.log(`Cached response for ${cacheKey} with TTL ${ttl}ms and priority ${priority}`);
      }
    } else {
      // Fallback to simple in-memory cache
      const timestamp = Date.now();
      const expiresAt = timestamp + ttl;
      
      // Simple in-memory cache implementation
      if (!window._apiCache) window._apiCache = {};
      if (!window._apiCacheMetadata) window._apiCacheMetadata = {};
      
      window._apiCache[cacheKey] = data;
      window._apiCacheMetadata[cacheKey] = {
        timestamp,
        expiresAt,
        priority
      };
      
      if (config.debugMode) {
        console.log(`Cached response for ${cacheKey} with TTL ${ttl}ms and priority ${priority} (using fallback cache)`);
      }
    }
  }
  
  /**
   * Get a cached response
   * @param {string} cacheKey - Cache key
   * @param {boolean} ignoreExpiry - Whether to ignore expiry (for offline mode)
   * @returns {Object|null} Cached response or null if not found/expired
   */
  function getCachedResponse(cacheKey, ignoreExpiry = false) {
    // Skip cache lookup if disabled
    if (!config.useCache) return null;
    
    // Try optimized cache first
    if (window.PerformanceOptimizer && window.PerformanceOptimizer.cache) {
      return window.PerformanceOptimizer.cache.get(cacheKey, {
        checkExpiry: !ignoreExpiry
      });
    }
    
    // Fallback to simple in-memory cache
    if (!window._apiCache || !window._apiCacheMetadata) return null;
    
    const data = window._apiCache[cacheKey];
    const metadata = window._apiCacheMetadata[cacheKey];
    
    if (!data || !metadata) return null;
    
    // Check expiry if needed
    if (!ignoreExpiry && metadata.expiresAt < Date.now()) {
      delete window._apiCache[cacheKey];
      delete window._apiCacheMetadata[cacheKey];
      return null;
    }
    
    return data;
  }
  
  /**
   * Get the timestamp for a cached response
   * @param {string} cacheKey - Cache key
   * @returns {number|null} Timestamp or null if not found
   */
  function getCachedResponseTimestamp(cacheKey) {
    // Try optimized cache metadata
    if (window.PerformanceOptimizer && window.PerformanceOptimizer.cache) {
      const data = window.PerformanceOptimizer.cache.get(cacheKey, {
        checkExpiry: false
      });
      
      if (data && data._metadata && data._metadata.timestamp) {
        return data._metadata.timestamp;
      }
    }
    
    // Fallback to simple in-memory cache
    if (window._apiCacheMetadata && window._apiCacheMetadata[cacheKey]) {
      return window._apiCacheMetadata[cacheKey].timestamp;
    }
    
    return null;
  }
  
  /**
   * Clear the cache for a specific resource or pattern
   * @param {string} pattern - Resource or pattern to clear (e.g., 'profiles', 'goals')
   */
  function clearCache(pattern = null) {
    if (!pattern) {
      // Clear all cache
      if (window.PerformanceOptimizer && window.PerformanceOptimizer.cache) {
        window.PerformanceOptimizer.cache.clear();
      }
      
      // Clear fallback cache
      window._apiCache = {};
      window._apiCacheMetadata = {};
      
      if (config.debugMode) {
        console.log('Cleared entire API cache');
      }
      
      return;
    }
    
    // Clear by pattern
    if (window.PerformanceOptimizer && window.PerformanceOptimizer.cache) {
      // The optimized cache implementation doesn't expose a clear by pattern method
      // For now, we have to clear all or implement our own pattern matching
      window.PerformanceOptimizer.cache.clear();
    }
    
    // Clear fallback cache by pattern
    if (window._apiCache && window._apiCacheMetadata) {
      const regex = new RegExp(pattern);
      
      Object.keys(window._apiCache).forEach(key => {
        if (regex.test(key)) {
          delete window._apiCache[key];
          delete window._apiCacheMetadata[key];
          
          if (config.debugMode) {
            console.log(`Cleared cache for key matching ${pattern}: ${key}`);
          }
        }
      });
    }
  }
  
  /**
   * Batch request handling
   */
  
  /**
   * Execute a batch of requests
   * @param {Array} requests - Array of request configs
   * @param {Object} options - Batch options
   * @returns {Promise<Array>} Array of results
   */
  async function batch(requests, options = {}) {
    if (!requests || !Array.isArray(requests) || requests.length === 0) {
      throw new Error('Invalid batch request: empty or not an array');
    }
    
    const {
      parallel = true,
      loadingId = null,
      loadingText = 'Processing batch request...',
      stopOnError = false
    } = options;
    
    // Start loading indicator if provided
    if (loadingId) {
      window.LoadingStateManager.setLoading(loadingId, true, {
        text: loadingText
      });
    }
    
    try {
      let results = [];
      
      if (parallel) {
        // Execute all requests in parallel
        const promises = requests.map(req => {
          const { method = 'GET', endpoint, data = null, options = {} } = req;
          
          // Don't show loading indicators for individual requests in batch
          const requestOptions = { 
            ...options, 
            loadingId: null,
            allowFailure: true // Don't throw from individual requests in batch
          };
          
          return request(method, endpoint, data, requestOptions)
            .catch(error => ({ error }));
        });
        
        results = await Promise.all(promises);
      } else {
        // Execute requests sequentially
        for (const req of requests) {
          const { method = 'GET', endpoint, data = null, options = {} } = req;
          
          // Don't show loading indicators for individual requests in batch
          const requestOptions = { 
            ...options, 
            loadingId: null,
            allowFailure: true // Don't throw from individual requests
          };
          
          try {
            const result = await request(method, endpoint, data, requestOptions);
            results.push(result);
          } catch (error) {
            results.push({ error });
            
            if (stopOnError) {
              break;
            }
          }
        }
      }
      
      return results;
    } finally {
      // Always hide loading indicator
      if (loadingId) {
        window.LoadingStateManager.setLoading(loadingId, false);
      }
    }
  }
  
  /**
   * Convenience Methods for Common API Endpoints
   */
  
  /**
   * Convenience method for GET requests
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Response data
   */
  async function get(endpoint, options = {}) {
    return request('GET', endpoint, null, options);
  }
  
  /**
   * Convenience method for POST requests
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Response data
   */
  async function post(endpoint, data, options = {}) {
    return request('POST', endpoint, data, options);
  }
  
  /**
   * Convenience method for PUT requests
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Response data
   */
  async function put(endpoint, data, options = {}) {
    return request('PUT', endpoint, data, options);
  }
  
  /**
   * Convenience method for DELETE requests
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Response data
   */
  async function del(endpoint, options = {}) {
    return request('DELETE', endpoint, null, options);
  }
  
  /**
   * Get profiles list
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Profiles data
   */
  async function getProfiles(options = {}) {
    return get(apiResources.profiles.base, {
      loadingId: 'profiles-list',
      ...options
    });
  }
  
  /**
   * Get a specific profile
   * @param {string} profileId - Profile ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Profile data
   */
  async function getProfile(profileId, options = {}) {
    return get(apiResources.profiles.detail(profileId), {
      loadingId: `profile-${profileId}`,
      ...options
    });
  }
  
  /**
   * Create a new profile
   * @param {Object} profileData - Profile data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Created profile
   */
  async function createProfile(profileData, options = {}) {
    return post(apiResources.profiles.base, profileData, {
      loadingId: 'create-profile',
      loadingText: 'Creating profile...',
      useCache: false,
      ...options
    });
  }
  
  /**
   * Update a profile
   * @param {string} profileId - Profile ID
   * @param {Object} profileData - Updated profile data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated profile
   */
  async function updateProfile(profileId, profileData, options = {}) {
    return put(apiResources.profiles.detail(profileId), profileData, {
      loadingId: `update-profile-${profileId}`,
      loadingText: 'Updating profile...',
      useCache: false,
      ...options
    });
  }
  
  /**
   * Get goals for a profile
   * @param {string} profileId - Profile ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Goals data
   */
  async function getGoals(profileId, options = {}) {
    return get(`${apiResources.profiles.detail(profileId)}/goals`, {
      loadingId: `goals-${profileId}`,
      ...options
    });
  }
  
  /**
   * Get a specific goal
   * @param {string} goalId - Goal ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Goal data
   */
  async function getGoal(goalId, options = {}) {
    return get(apiResources.goals.detail(goalId), {
      loadingId: `goal-${goalId}`,
      ...options
    });
  }
  
  /**
   * Create a new goal
   * @param {string} profileId - Profile ID
   * @param {Object} goalData - Goal data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Created goal
   */
  async function createGoal(profileId, goalData, options = {}) {
    return post(`${apiResources.profiles.detail(profileId)}/goals`, goalData, {
      loadingId: 'create-goal',
      loadingText: 'Creating goal...',
      useCache: false,
      ...options
    });
  }
  
  /**
   * Update a goal
   * @param {string} goalId - Goal ID
   * @param {Object} goalData - Updated goal data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Updated goal
   */
  async function updateGoal(goalId, goalData, options = {}) {
    return put(apiResources.goals.detail(goalId), goalData, {
      loadingId: `update-goal-${goalId}`,
      loadingText: 'Updating goal...',
      useCache: false,
      ...options
    });
  }
  
  /**
   * Delete a goal
   * @param {string} goalId - Goal ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Delete result
   */
  async function deleteGoal(goalId, options = {}) {
    return del(apiResources.goals.detail(goalId), {
      loadingId: `delete-goal-${goalId}`,
      loadingText: 'Deleting goal...',
      useCache: false,
      ...options
    });
  }
  
  /**
   * Get visualization data for a goal
   * @param {string} goalId - Goal ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Visualization data
   */
  async function getVisualizationData(goalId, options = {}) {
    return get(apiResources.goals.visualizationData(goalId), {
      loadingId: `visualization-${goalId}`,
      ...options
    });
  }
  
  /**
   * Calculate probability for a goal
   * @param {string} goalId - Goal ID
   * @param {Object} parameters - Goal parameters
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Probability result
   */
  async function calculateProbability(goalId, parameters, options = {}) {
    return post(apiResources.goals.probability(goalId), parameters, {
      loadingId: `probability-${goalId}`,
      ...options
    });
  }
  
  /**
   * Get question flow
   * @param {string} profileId - Profile ID
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Question flow data
   */
  async function getQuestionFlow(profileId, options = {}) {
    return get(`${apiResources.questions.flow}?profile_id=${profileId}`, {
      loadingId: `questions-${profileId}`,
      ...options
    });
  }
  
  /**
   * Submit a question response
   * @param {Object} responseData - Question response data
   * @param {Object} options - Request options
   * @returns {Promise<Object>} Submission result
   */
  async function submitQuestionResponse(responseData, options = {}) {
    return post(apiResources.questions.submit, responseData, {
      loadingId: 'submit-question',
      loadingText: 'Submitting response...',
      useCache: false,
      ...options
    });
  }
  
  /**
   * Update service configuration
   * @param {Object} newConfig - New configuration options
   */
  function configure(newConfig = {}) {
    // Deep merge for nested objects like cachePriorities
    Object.keys(newConfig).forEach(key => {
      if (
        typeof newConfig[key] === 'object' && 
        newConfig[key] !== null && 
        typeof config[key] === 'object' && 
        config[key] !== null
      ) {
        config[key] = { ...config[key], ...newConfig[key] };
      } else {
        config[key] = newConfig[key];
      }
    });
    
    if (config.debugMode) {
      console.log('ApiService configuration updated', newConfig);
    }
  }
  
  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  function getCacheStats() {
    if (window.PerformanceOptimizer && window.PerformanceOptimizer.cache) {
      return window.PerformanceOptimizer.cache.getStats();
    }
    
    // Basic stats for fallback cache
    if (window._apiCache && window._apiCacheMetadata) {
      const keys = Object.keys(window._apiCache);
      return {
        size: keys.length,
        keys
      };
    }
    
    return { size: 0 };
  }
  
  // Initialize the service when loaded
  initialize();
  
  // Public API
  return {
    // Core methods
    request,
    batch,
    get,
    post,
    put,
    delete: del,
    
    // Authentication
    login,
    logout,
    getAuthToken,
    setAuthToken,
    clearAuthToken,
    isAuthenticated: () => authState.isAuthenticated,
    
    // Cache management
    clearCache,
    getCacheStats,
    
    // Convenience methods
    getProfiles,
    getProfile,
    createProfile,
    updateProfile,
    getGoals,
    getGoal,
    createGoal,
    updateGoal,
    deleteGoal,
    getVisualizationData,
    calculateProbability,
    getQuestionFlow,
    submitQuestionResponse,
    
    // Request state
    getRequestState,
    isOnline,
    
    // Configuration
    configure,
    
    // Exposed for testing and extension
    apiResources
  };
})();

// Make service available globally
window.ApiService = ApiService;