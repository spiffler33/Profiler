/**
 * JavaScript service for fetching and formatting visualization data from the API.
 * 
 * This service handles data fetching, transformation, caching, and error management
 * for the React visualization components. It provides a clean interface for the 
 * visualization initializer to interact with the API.
 *
 * Features:
 * - Optimized caching with size limits, TTL, and prioritization
 * - Request batching for related API calls
 * - Performance metrics and monitoring
 * - Request state tracking
 * - Error handling with detailed messages
 * - Automatic retry for failed requests
 * - Loading state callbacks
 * - Request timeouts
 * - Advanced recovery strategies for failed requests
 * - Fallback to alternative data sources
 * - Network status detection
 * - Proper Indian Rupee (₹) currency formatting with lakh/crore support
 */

const VisualizationDataService = (function() {
  // Configuration
  const config = {
    apiBasePath: '/api/v2',
    defaultCurrency: 'INR',
    defaultLocale: 'en-IN',
    requestTimeout: 15000, // 15 seconds
    retryAttempts: 2,
    retryDelay: 1000, // 1 second
    logApiCalls: true,
    enableNetworkDetection: true,
    enableFallbackData: true,
    networkRetryDelay: 5000, // 5 seconds
    userFriendlyErrors: true, // Show more user-friendly error messages
    fallbackThreshold: 2, // How many attempts with same error before falling back
    
    // Performance optimization settings
    enableBatchedRequests: true, // Enable request batching for probability calculations
    maxBatchDelay: 50, // Maximum delay for batching in ms
    useOptimizedCache: true, // Use the new optimized cache
    debugPerformance: false, // Log performance data
    
    // Cache settings
    cachePriorities: {
      visualizationData: 10,  // Highest priority
      adjustments: 7,
      scenarios: 7,
      probability: 5         // Lower priority for probability calculations
    },
    
    // TTL settings (in milliseconds)
    cacheTTL: {
      visualizationData: 60000, // 1 minute
      adjustments: 120000,      // 2 minutes
      scenarios: 120000,        // 2 minutes
      probability: 30000        // 30 seconds
    }
  };
  
  // Legacy cache system (for backward compatibility)
  const cache = {
    data: {},
    timestamps: {},
    expirationTime: 60000, // Cache expiration time in milliseconds (1 minute)
    errorCache: {} // Cache error types for fallback strategies
  };
  
  // Utility functions for formatting and data manipulation
  const utils = {
    // Format currency with proper Indian Rupee support
    formatCurrency: (amount, currency = config.defaultCurrency, locale = config.defaultLocale) => {
      if (amount === undefined || amount === null) return '';
      
      // Convert to number if it's a string
      const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
      
      // Use Indian formatting system for lakhs and crores if INR
      if (currency === 'INR') {
        if (numAmount >= 10000000) { // 1 crore (10 million)
          return `₹${(numAmount / 10000000).toFixed(2)} Cr`;
        } else if (numAmount >= 100000) { // 1 lakh (100 thousand)
          return `₹${(numAmount / 100000).toFixed(2)} L`;
        } else {
          // Use standard formatting for smaller amounts
          return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            maximumFractionDigits: 0
          }).format(numAmount);
        }
      }
      
      // Default currency formatting
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency
      }).format(numAmount);
    },
    
    // Deep clone an object
    deepClone: (obj) => {
      try {
        return JSON.parse(JSON.stringify(obj));
      } catch (e) {
        console.warn('Failed to deep clone object', e);
        return Object.assign({}, obj);
      }
    }
  };
  
  // Request states for each goal
  const requestStates = {};
  
  // Active request abort controllers (for cancellation)
  const abortControllers = {};
  
  // Network status tracking
  let lastNetworkStatus = true; // Assume online at start
  
  // Batch state for probability calculations
  let probabilityBatchTimer = null;
  const probabilityBatchQueue = [];

  /**
   * Check if the browser is online
   * @returns {boolean} True if browser is online, false otherwise
   */
  function isOnline() {
    if (!config.enableNetworkDetection) return true;
    
    // Check using the navigator.onLine property
    return navigator.onLine === undefined ? true : navigator.onLine;
  }
  
  /**
   * Create a user-friendly error message from a technical error
   * @param {Error|string} error - The error object or message
   * @param {string} context - The context in which the error occurred
   * @returns {string} A user-friendly error message
   */
  function createUserFriendlyErrorMessage(error, context = '') {
    if (!config.userFriendlyErrors) {
      return error.message || error.toString();
    }

    const errorMsg = error.message || error.toString();
    
    // Network-related errors
    if (
      !isOnline() || 
      errorMsg.includes('network') || 
      errorMsg.includes('failed to fetch') || 
      error.name === 'TypeError'
    ) {
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    }
    
    // Timeout errors
    if (
      errorMsg.includes('timeout') || 
      errorMsg.includes('aborted') || 
      error.name === 'AbortError'
    ) {
      return 'The request took too long to complete. This might be due to a slow connection or the server is busy.';
    }
    
    // Authentication errors
    if (
      errorMsg.includes('401') || 
      errorMsg.includes('403') || 
      errorMsg.includes('authentication') || 
      errorMsg.includes('unauthorized')
    ) {
      return 'Your session may have expired. Please refresh the page and try again.';
    }
    
    // Server errors
    if (
      errorMsg.includes('500') || 
      errorMsg.includes('502') || 
      errorMsg.includes('503') || 
      errorMsg.includes('504')
    ) {
      return 'The server encountered an error. Our team has been notified and we\'re working to fix it.';
    }
    
    // Data errors
    if (
      errorMsg.includes('parse') || 
      errorMsg.includes('json') || 
      errorMsg.includes('unexpected token')
    ) {
      return 'There was a problem processing the data received from the server.';
    }
    
    // API-specific errors that we know about
    if (errorMsg.includes('Monte Carlo simulation')) {
      return 'There was a problem calculating the probability. The system may be experiencing high load.';
    }
    
    if (errorMsg.includes('parameters')) {
      return 'Some parameters are missing or invalid. Please review your inputs and try again.';
    }
    
    // Validation errors
    if (
      errorMsg.includes('validation') || 
      errorMsg.includes('valid') || 
      errorMsg.includes('required')
    ) {
      return 'Some of the information provided is invalid. Please check your inputs and try again.';
    }
    
    // Default error message with context
    if (context) {
      return `Unable to ${context}. Please try again later.`;
    }
    
    return 'Something went wrong. Please try again later.';
  }
  
  /**
   * Check if we should fall back to cached data for a specific error
   * @param {Error} error - The error that occurred
   * @param {string} goalId - The goal ID for tracking error frequency
   * @returns {boolean} True if we should fall back to cached data
   */
  function shouldFallbackToCachedData(error, goalId) {
    if (!config.enableFallbackData) return false;
    
    // Always fallback for network issues
    if (!isOnline()) return true;

    // Create an error identifier to track frequency of specific errors
    const errorId = error.message || error.toString();
    const cacheKey = `${goalId}_error_${errorId}`;
    
    // Increment error counter for this specific error
    if (!cache.errorCache[cacheKey]) {
      cache.errorCache[cacheKey] = {
        count: 1,
        timestamp: Date.now()
      };
    } else {
      cache.errorCache[cacheKey].count++;
      cache.errorCache[cacheKey].timestamp = Date.now();
    }
    
    // Check if we've seen this error too many times
    return cache.errorCache[cacheKey].count >= config.fallbackThreshold;
  }
  
  /**
   * Log error information for analytics and debugging
   * @param {Error} error - The error that occurred
   * @param {string} context - The context in which the error occurred
   * @param {Object} metadata - Additional metadata about the request
   */
  function logErrorAnalytics(error, context, metadata = {}) {
    if (!config.logApiCalls) return;

    console.error(`API Error in ${context}:`, {
      message: error.message || error.toString(),
      name: error.name,
      stack: error.stack,
      metadata,
      timestamp: new Date().toISOString(),
      online: isOnline()
    });
    
    // In a production environment, you might want to log this to your server
    // For now, we'll just console.error it
  }
  
  /**
   * Network status event handler
   * @param {boolean} online - Whether the browser is online
   */
  function handleNetworkStatusChange(online) {
    // Only handle actual changes
    if (online === lastNetworkStatus) return;
    
    lastNetworkStatus = online;
    
    if (online) {
      if (config.logApiCalls) console.log('Network connection restored');
      
      // We could automatically retry failed requests here if desired
      // For now we'll leave it to manual user retry
    } else {
      if (config.logApiCalls) console.log('Network connection lost');
    }
  }
  
  /**
   * Fetches visualization data for a specific goal
   * 
   * @param {string} goalId - The ID of the goal to fetch data for
   * @param {Object} options - Optional configuration
   * @param {boolean} options.forceRefresh - Force refresh data from API ignoring cache
   * @param {number} options.cacheExpiration - Override default cache expiration time (ms)
   * @param {function} options.onLoadingChange - Callback for loading state changes
   * @param {number} options.timeout - Request timeout in milliseconds
   * @param {number} options.retryAttempts - Number of retry attempts for failed requests
   * @param {boolean} options.allowFallback - Allow fallback to cached data on error
   * @returns {Promise<Object>} Promise resolving to visualization data
   */
  async function fetchVisualizationData(goalId, options = {}) {
    if (!goalId) {
      throw new Error('Goal ID is required');
    }
    
    const {
      forceRefresh = false,
      cacheExpiration = config.cacheTTL.visualizationData,
      onLoadingChange = null,
      timeout = config.requestTimeout,
      retryAttempts = config.retryAttempts,
      allowFallback = config.enableFallbackData
    } = options;
    
    // Performance tracking
    const startTime = performance.now();
    let fromCache = false;
    
    // Cache key for this request
    const cacheKey = `visualization_${goalId}`;
    
    // Check network status before starting
    const networkAvailable = isOnline();
    if (!networkAvailable) {
      // If offline and we have cached data, return it with a warning
      const cachedData = config.useOptimizedCache ?
        window.PerformanceOptimizer?.cache.get(cacheKey, { checkExpiry: false }) :
        getCachedData(goalId, Infinity); // Ignore expiration when offline
      
      if (cachedData) {
        fromCache = true;
        if (config.logApiCalls) console.log(`Using cached data for goal ${goalId} (offline mode)`);
        setRequestState(goalId, 'success', null, true); // Mark as from cache
        if (onLoadingChange) onLoadingChange(false);
        
        // Track performance metrics
        if (config.debugPerformance && window.PerformanceOptimizer) {
          const duration = performance.now() - startTime;
          window.PerformanceOptimizer.trackApiCall(
            `visualization_${goalId}`, duration, true, true
          );
        }
        
        return {
          ...cachedData,
          _metadata: {
            fromCache: true,
            offlineMode: true,
            timestamp: config.useOptimizedCache ? 
              (cachedData._metadata?.timestamp || Date.now()) : 
              cache.timestamps[goalId]
          }
        };
      } else {
        // No cached data and we're offline - fail request with appropriate message
        const error = new Error('You are currently offline. Please check your internet connection and try again.');
        error.isOffline = true;
        
        setRequestState(goalId, 'error', error.message);
        if (onLoadingChange) onLoadingChange(false);
        throw error;
      }
    }
    
    // Set loading state
    setRequestState(goalId, 'loading');
    if (onLoadingChange) onLoadingChange(true);
    
    // Create an abort controller for this request
    const abortController = new AbortController();
    abortControllers[goalId] = abortController;
    
    // Set up timeout if specified
    let timeoutId = null;
    if (timeout > 0) {
      timeoutId = setTimeout(() => {
        abortController.abort();
        if (config.logApiCalls) console.log(`Request for goal ${goalId} timed out after ${timeout}ms`);
      }, timeout);
    }
    
    try {
      // Check cache first if we're not forcing a refresh
      if (!forceRefresh) {
        // Try optimized cache first if available
        if (config.useOptimizedCache && window.PerformanceOptimizer?.cache) {
          const cachedData = window.PerformanceOptimizer.cache.get(
            cacheKey, 
            { checkExpiry: true }
          );
          
          if (cachedData) {
            fromCache = true;
            if (config.logApiCalls) console.log(`Using optimized cached data for goal ${goalId}`);
            setRequestState(goalId, 'success');
            if (onLoadingChange) onLoadingChange(false);
            clearTimeout(timeoutId);
            delete abortControllers[goalId];
            
            // Track performance metrics
            if (config.debugPerformance && window.PerformanceOptimizer) {
              const duration = performance.now() - startTime;
              window.PerformanceOptimizer.trackApiCall(
                `visualization_${goalId}`, duration, true, true
              );
            }
            
            return {
              ...cachedData,
              _metadata: {
                fromCache: true,
                offlineMode: false,
                timestamp: cachedData._metadata?.timestamp || Date.now(),
                optimizedCache: true
              }
            };
          }
        }
        
        // Fall back to legacy cache if optimized cache is not available or empty
        const cachedData = getCachedData(goalId, cacheExpiration);
        if (cachedData) {
          fromCache = true;
          if (config.logApiCalls) console.log(`Using legacy cached data for goal ${goalId}`);
          setRequestState(goalId, 'success');
          if (onLoadingChange) onLoadingChange(false);
          clearTimeout(timeoutId);
          delete abortControllers[goalId];
          
          // If we have data in legacy cache but not optimized cache,
          // copy it to the optimized cache for future use
          if (config.useOptimizedCache && window.PerformanceOptimizer?.cache) {
            window.PerformanceOptimizer.cache.set(
              cacheKey, 
              cachedData,
              {
                ttl: config.cacheTTL.visualizationData,
                priority: config.cachePriorities.visualizationData
              }
            );
          }
          
          // Track performance metrics
          if (config.debugPerformance && window.PerformanceOptimizer) {
            const duration = performance.now() - startTime;
            window.PerformanceOptimizer.trackApiCall(
              `visualization_${goalId}`, duration, true, true
            );
          }
          
          return {
            ...cachedData,
            _metadata: {
              fromCache: true,
              offlineMode: false,
              timestamp: cache.timestamps[goalId]
            }
          };
        }
      }
      
      // Implement retry logic
      let attemptCount = 0;
      let lastError = null;
      
      while (attemptCount <= retryAttempts) {
        try {
          if (attemptCount > 0 && config.logApiCalls) {
            console.log(`Retry attempt ${attemptCount} for goal ${goalId}`);
          }
          
          // Check network status again before each attempt
          if (!isOnline() && attemptCount > 0) {
            // Wait for network to recover if we're retrying
            await new Promise(resolve => setTimeout(resolve, config.networkRetryDelay));
            
            // Skip this attempt if still offline
            if (!isOnline()) {
              attemptCount++;
              continue;
            }
          }
          
          // Use a memoized fetch if available
          const fetchFn = window.PerformanceOptimizer?.memoize ? 
            window.PerformanceOptimizer.memoize(fetch, undefined, 10) : fetch;
          
          // Fetch data from API with abort signal
          const response = await fetchFn(
            `${config.apiBasePath}/goals/${goalId}/visualization-data`, 
            { 
              method: 'GET',
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              },
              signal: abortController.signal 
            }
          );
          
          // Handle HTTP errors
          if (!response.ok) {
            let errorMessage;
            try {
              const errorData = await response.json();
              errorMessage = errorData.message || `API request failed with status ${response.status}`;
              
              // Check for specific API error codes and add context
              if (errorData.code) {
                switch (errorData.code) {
                  case 'RATE_LIMIT_EXCEEDED':
                    errorMessage = 'Rate limit exceeded. Please try again in a few minutes.';
                    break;
                  case 'CALCULATION_ERROR':
                    errorMessage = 'Error calculating probabilities. Some parameters may be invalid.';
                    break;
                  case 'GOAL_NOT_FOUND':
                    errorMessage = 'The requested goal could not be found.';
                    break;
                  // Add more specific API error codes as needed
                }
              }
            } catch (e) {
              errorMessage = `API request failed with status ${response.status}`;
            }
            
            const error = new Error(errorMessage);
            error.status = response.status;
            throw error;
          }
          
          // Parse and process data
          const data = await response.json();
          const processedData = processApiResponse(data);
          
          // Cache the processed data in both systems
          cacheData(goalId, processedData);
          
          // Also cache in optimized cache if available
          if (config.useOptimizedCache && window.PerformanceOptimizer?.cache) {
            window.PerformanceOptimizer.cache.set(
              cacheKey, 
              processedData,
              {
                ttl: config.cacheTTL.visualizationData,
                priority: config.cachePriorities.visualizationData
              }
            );
          }
          
          // Reset error counter for this goal
          Object.keys(cache.errorCache).forEach(key => {
            if (key.startsWith(`${goalId}_error_`)) {
              delete cache.errorCache[key];
            }
          });
          
          // Update request state
          setRequestState(goalId, 'success');
          if (onLoadingChange) onLoadingChange(false);
          
          // Clean up timeout and abort controller
          clearTimeout(timeoutId);
          delete abortControllers[goalId];
          
          if (config.logApiCalls) console.log(`Successfully fetched data for goal ${goalId}`);
          
          // Track performance metrics
          if (config.debugPerformance && window.PerformanceOptimizer) {
            const duration = performance.now() - startTime;
            window.PerformanceOptimizer.trackApiCall(
              `visualization_${goalId}`, duration, true, false
            );
          }
          
          return {
            ...processedData,
            _metadata: {
              fromCache: false,
              offlineMode: false,
              timestamp: Date.now()
            }
          };
        } catch (error) {
          // If this is an abort error, don't retry
          if (error.name === 'AbortError') {
            throw new Error('Request was aborted or timed out');
          }
          
          // Store the error
          lastError = error;
          
          // Log error for analytics
          logErrorAnalytics(error, 'fetchVisualizationData', {
            goalId,
            attemptCount,
            timestamp: Date.now()
          });
          
          // Check if we should retry
          if (attemptCount >= retryAttempts) {
            break;
          }
          
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, config.retryDelay));
          attemptCount++;
        }
      }
      
      // Check if we should fall back to cached data
      if (allowFallback && shouldFallbackToCachedData(lastError, goalId)) {
        // Try optimized cache first
        let cachedData = null;
        if (config.useOptimizedCache && window.PerformanceOptimizer?.cache) {
          cachedData = window.PerformanceOptimizer.cache.get(
            cacheKey, 
            { checkExpiry: false } // Ignore expiry for fallback
          );
        }
        
        // Fall back to legacy cache if needed
        if (!cachedData) {
          cachedData = getCachedData(goalId, Infinity); // Ignore expiration for fallback
        }
        
        if (cachedData) {
          fromCache = true;
          if (config.logApiCalls) console.log(`Falling back to cached data for goal ${goalId} after failed requests`);
          
          // Set warning state (success, but with warning flag)
          setRequestState(goalId, 'success', null, true);
          if (onLoadingChange) onLoadingChange(false);
          
          // Clean up
          clearTimeout(timeoutId);
          delete abortControllers[goalId];
          
          // Track performance metrics with error flag
          if (config.debugPerformance && window.PerformanceOptimizer) {
            const duration = performance.now() - startTime;
            window.PerformanceOptimizer.trackApiCall(
              `visualization_${goalId}`, duration, false, true
            );
          }
          
          return {
            ...cachedData,
            _metadata: {
              fromCache: true,
              fallback: true,
              error: lastError.message,
              timestamp: config.useOptimizedCache && cachedData._metadata ? 
                cachedData._metadata.timestamp : cache.timestamps[goalId]
            }
          };
        }
      }
      
      // If we get here, all retries failed
      const userFriendlyMessage = createUserFriendlyErrorMessage(
        lastError || new Error('Failed to fetch data after multiple attempts'),
        'load visualization data'
      );
      
      // Track performance metrics for failed request
      if (config.debugPerformance && window.PerformanceOptimizer) {
        const duration = performance.now() - startTime;
        window.PerformanceOptimizer.trackApiCall(
          `visualization_${goalId}`, duration, false, false
        );
      }
      
      throw new Error(userFriendlyMessage);
    } catch (error) {
      // Update request state with error
      setRequestState(goalId, 'error', error.message);
      if (onLoadingChange) onLoadingChange(false);
      
      // Clean up timeout and abort controller
      clearTimeout(timeoutId);
      delete abortControllers[goalId];
      
      // Log the error
      console.error('Error fetching visualization data:', error);
      
      // Track performance metrics for failed request
      if (config.debugPerformance && window.PerformanceOptimizer) {
        const duration = performance.now() - startTime;
        window.PerformanceOptimizer.trackApiCall(
          `visualization_${goalId}`, duration, false, false
        );
      }
      
      // Re-throw with user-friendly message if needed
      if (!config.userFriendlyErrors) {
        throw error;
      }
      
      throw new Error(
        createUserFriendlyErrorMessage(error, 'load visualization data')
      );
    }
  }
  
  /**
   * Process the API response to ensure it matches the expected format for components
   * 
   * @param {Object} apiResponse - The raw API response
   * @returns {Object} Processed data ready for visualization components
   */
  function processApiResponse(apiResponse) {
    // Create a deep copy to avoid modifying the original data
    const processed = JSON.parse(JSON.stringify(apiResponse));
    
    // Extract the goal ID
    const goalId = processed.goal_id || '';
    
    // Process probabilistic goal data if available
    if (processed.probabilisticGoalData) {
      const probabilisticData = processed.probabilisticGoalData;
      
      // Add goalId if missing
      if (!probabilisticData.goalId && goalId) {
        probabilisticData.goalId = goalId;
      }
      
      // Ensure simulationOutcomes exists
      if (!probabilisticData.simulationOutcomes) {
        probabilisticData.simulationOutcomes = {
          median: probabilisticData.targetAmount || 0,
          percentiles: {
            '10': 0, '25': 0, '50': 0, '75': 0, '90': 0
          }
        };
      }
      
      // Ensure timeBasedMetrics exists
      if (!probabilisticData.timeBasedMetrics) {
        probabilisticData.timeBasedMetrics = {
          probabilityOverTime: {
            labels: ['Start', 'End'],
            values: [0, probabilisticData.successProbability || 0]
          }
        };
      }
    } else if (goalId) {
      // Create basic structure if missing
      processed.probabilisticGoalData = {
        goalId: goalId,
        targetAmount: 0,
        timeframe: '',
        successProbability: 0,
        simulationOutcomes: {
          median: 0,
          percentiles: {
            '10': 0, '25': 0, '50': 0, '75': 0, '90': 0
          }
        },
        timeBasedMetrics: {
          probabilityOverTime: {
            labels: ['Start', 'End'],
            values: [0, 0]
          }
        }
      };
    }
    
    // Process adjustment impact data if available
    if (processed.adjustmentImpactData) {
      const adjustmentData = processed.adjustmentImpactData;
      
      // Add goalId if missing
      if (!adjustmentData.goalId && goalId) {
        adjustmentData.goalId = goalId;
      }
      
      // Ensure adjustments array exists
      if (!adjustmentData.adjustments || !Array.isArray(adjustmentData.adjustments)) {
        adjustmentData.adjustments = [];
      }
      
      // Ensure each adjustment has all required fields
      adjustmentData.adjustments.forEach((adjustment, index) => {
        // Add unique ID if missing
        if (!adjustment.id) {
          adjustment.id = `${goalId}_adj_${index}`;
        }
        
        // Ensure impactMetrics exists
        if (!adjustment.impactMetrics) {
          adjustment.impactMetrics = {
            probabilityIncrease: 0,
            newProbability: adjustmentData.currentProbability || 0
          };
        }
        
        // Ensure description exists
        if (!adjustment.description) {
          adjustment.description = `Adjustment ${index + 1}`;
        }
      });
    } else if (goalId) {
      // Create basic structure if missing
      processed.adjustmentImpactData = {
        goalId: goalId,
        currentProbability: 0,
        adjustments: []
      };
    }
    
    // Process scenario comparison data if available
    if (processed.scenarioComparisonData) {
      const scenarioData = processed.scenarioComparisonData;
      
      // Add goalId if missing
      if (!scenarioData.goalId && goalId) {
        scenarioData.goalId = goalId;
      }
      
      // Ensure scenarios array exists
      if (!scenarioData.scenarios || !Array.isArray(scenarioData.scenarios)) {
        scenarioData.scenarios = [];
      }
      
      // If no scenarios, add a default baseline scenario
      if (scenarioData.scenarios.length === 0) {
        scenarioData.scenarios.push({
          id: `${processed.goal_id || 'goal'}_baseline`,
          name: 'Current Plan',
          description: 'Your current financial plan with no changes',
          probability: processed.probabilisticGoalData?.successProbability || 0,
          isBaseline: true
        });
      }
      
      // Ensure at least one scenario is marked as baseline
      const hasBaseline = scenarioData.scenarios.some(s => s.isBaseline);
      if (!hasBaseline && scenarioData.scenarios.length > 0) {
        scenarioData.scenarios[0].isBaseline = true;
      }
      
      // Ensure each scenario has required fields
      scenarioData.scenarios.forEach((scenario, index) => {
        // Add ID if missing
        if (!scenario.id) {
          scenario.id = `${goalId}_scenario_${index}`;
        }
        
        // Ensure probability exists
        if (typeof scenario.probability !== 'number') {
          scenario.probability = 0;
        }
        
        // Ensure name exists
        if (!scenario.name) {
          scenario.name = `Scenario ${index + 1}`;
        }
      });
    } else if (goalId) {
      // Create basic structure if missing
      processed.scenarioComparisonData = {
        goalId: goalId,
        scenarios: [{
          id: `${goalId}_baseline`,
          name: 'Current Plan',
          description: 'Your current financial plan with no changes',
          probability: processed.probabilisticGoalData?.successProbability || 0,
          isBaseline: true
        }]
      };
    }
    
    return processed;
  }
  
  /**
   * Cache visualization data with timestamp
   * 
   * @param {string} goalId - Goal ID to use as cache key
   * @param {Object} data - Data to cache
   */
  function cacheData(goalId, data) {
    cache.data[goalId] = data;
    cache.timestamps[goalId] = Date.now();
  }
  
  /**
   * Get cached data if available and not expired
   * 
   * @param {string} goalId - Goal ID to retrieve from cache
   * @param {number} expirationTime - Time in ms after which cache is invalid
   * @returns {Object|null} Cached data or null if expired/not found
   */
  function getCachedData(goalId, expirationTime) {
    const timestamp = cache.timestamps[goalId];
    const data = cache.data[goalId];
    
    if (!timestamp || !data) return null;
    
    const now = Date.now();
    if (now - timestamp > expirationTime) {
      // Cache expired
      return null;
    }
    
    return data;
  }
  
  /**
   * Clear cache for a specific goal or all goals
   * 
   * @param {string} [goalId] - Optional Goal ID to clear, if not provided all cache is cleared
   */
  function clearCache(goalId) {
    if (goalId) {
      delete cache.data[goalId];
      delete cache.timestamps[goalId];
      
      // Clear error cache for this goal
      Object.keys(cache.errorCache).forEach(key => {
        if (key.startsWith(`${goalId}_`)) {
          delete cache.errorCache[key];
        }
      });
    } else {
      cache.data = {};
      cache.timestamps = {};
      cache.errorCache = {};
    }
  }
  
  /**
   * Set request state for a goal
   * 
   * @param {string} goalId - Goal ID
   * @param {string} state - State ('loading', 'success', 'error')
   * @param {string} [error] - Error message if state is 'error'
   * @param {boolean} [warning] - Warning flag for success with warning
   */
  function setRequestState(goalId, state, error = null, warning = false) {
    requestStates[goalId] = { 
      state, 
      error, 
      warning, 
      timestamp: Date.now() 
    };
  }
  
  /**
   * Get request state for a goal
   * 
   * @param {string} goalId - Goal ID
   * @returns {Object} Request state object
   */
  function getRequestState(goalId) {
    return requestStates[goalId] || { 
      state: 'idle', 
      error: null, 
      warning: false, 
      timestamp: null 
    };
  }
  
  /**
   * Get processed data for a specific visualization component
   * 
   * @param {Object} data - Complete visualization data from API/cache
   * @param {string} componentType - Component type ('probabilistic', 'adjustment', 'scenario')
   * @returns {Object} Component-specific data
   */
  function getComponentData(data, componentType) {
    if (!data) return null;
    
    switch (componentType) {
      case 'probabilistic':
        return data.probabilisticGoalData || null;
      case 'adjustment':
        return data.adjustmentImpactData || null;
      case 'scenario':
        return data.scenarioComparisonData || null;
      default:
        return null;
    }
  }
  
  /**
   * Check if visualization data is available for a goal
   * 
   * @param {string} goalId - Goal ID to check
   * @returns {boolean} True if data is cached for this goal
   */
  function hasData(goalId) {
    return !!cache.data[goalId];
  }
  
  /**
   * Checks if a goal has valid data structure
   * 
   * @param {string} goalId - Goal ID to check
   * @returns {Object} Validation result
   */
  function validateCachedData(goalId) {
    const data = cache.data[goalId];
    if (!data) {
      return { 
        valid: false, 
        reason: 'No cached data found'
      };
    }
    
    // Check if data has required structures
    const hasProb = !!data.probabilisticGoalData;
    const hasAdj = !!data.adjustmentImpactData;
    const hasScen = !!data.scenarioComparisonData;
    
    return {
      valid: hasProb || hasAdj || hasScen,
      completeness: {
        probabilistic: hasProb,
        adjustment: hasAdj,
        scenario: hasScen
      },
      age: Date.now() - (cache.timestamps[goalId] || 0)
    };
  }
  
  /**
   * Calculates probability for a goal with custom parameters
   * This is used for real-time probability updates in the goal form
   *
   * @param {string} goalId - The ID of the goal
   * @param {Object} parameters - Custom goal parameters to calculate probability with
   * @param {Object} options - Optional configuration
   * @returns {Promise<Object>} Probability result with success probability and metrics
   */
  async function calculateProbability(goalId, parameters, options = {}) {
    if (!goalId) {
      throw new Error('Goal ID is required');
    }
    
    if (!parameters || typeof parameters !== 'object') {
      throw new Error('Parameters object is required');
    }
    
    const {
      onLoadingChange = null,
      timeout = config.requestTimeout,
      validateParameters = true,
      allowFallback = config.enableFallbackData,
      useBatching = config.enableBatchedRequests, // Enable/disable batching
      batchDelay = config.maxBatchDelay
    } = options;
    
    // Performance tracking
    const startTime = performance.now();
    
    // Cache key for probability calculations
    const parameterHash = JSON.stringify(parameters);
    const cacheKey = `probability_${goalId}_${parameterHash}`;
    
    // Validate critical parameters
    if (validateParameters) {
      // Check for any obviously invalid parameters - this helps avoid unnecessary API calls
      const validationResult = validateProbabilityParameters(parameters);
      if (!validationResult.valid) {
        // Return default probability data for invalid parameters
        return {
          probability: 0,
          valid: false,
          message: validationResult.reason,
          metadata: {
            validationError: true,
            message: validationResult.reason
          }
        };
      }
    }
    
    // Check in optimized cache first
    if (config.useOptimizedCache && window.PerformanceOptimizer?.cache) {
      const cachedResult = window.PerformanceOptimizer.cache.get(
        cacheKey, 
        { checkExpiry: true }
      );
      
      if (cachedResult) {
        // Track performance metrics
        if (config.debugPerformance && window.PerformanceOptimizer) {
          const duration = performance.now() - startTime;
          window.PerformanceOptimizer.trackApiCall(
            `probability_calculation`, duration, true, true
          );
        }
        
        return {
          ...cachedResult,
          valid: true,
          metadata: {
            fromCache: true,
            optimizedCache: true,
            timestamp: cachedResult.metadata?.timestamp || Date.now()
          }
        };
      }
    }
    
    // Request key for this specific operation
    const requestKey = `${goalId}_probability`;
    
    // Check if we're offline
    if (!isOnline()) {
      const error = new Error('You are currently offline. Please check your internet connection and try again.');
      error.isOffline = true;
      
      setRequestState(requestKey, 'error', error.message);
      if (onLoadingChange) onLoadingChange(false);
      
      throw error;
    }
    
    // Set loading state
    setRequestState(requestKey, 'loading');
    if (onLoadingChange) onLoadingChange(true);
    
    try {
      let result;
      
      // If batching is enabled and PerformanceOptimizer is available, use batched requests
      if (useBatching && window.PerformanceOptimizer && window.PerformanceOptimizer.batchRequest) {
        // Execute batched request
        result = await executeBatchedProbabilityRequest(goalId, parameters, timeout);
      } else {
        // Execute single request
        result = await executeSingleProbabilityRequest(goalId, parameters, timeout);
      }
      
      // Clean up
      setRequestState(requestKey, 'success');
      if (onLoadingChange) onLoadingChange(false);
      
      // Cache the result in optimized cache if available
      if (config.useOptimizedCache && window.PerformanceOptimizer?.cache) {
        window.PerformanceOptimizer.cache.set(
          cacheKey, 
          result,
          {
            ttl: config.cacheTTL.probability,
            priority: config.cachePriorities.probability
          }
        );
      }
      
      // Track performance metrics
      if (config.debugPerformance && window.PerformanceOptimizer) {
        const duration = performance.now() - startTime;
        window.PerformanceOptimizer.trackApiCall(
          `probability_calculation`, duration, true, false
        );
      }
      
      return {
        ...result,
        valid: true,
        metadata: {
          fromCache: false,
          timestamp: Date.now()
        }
      };
    } catch (error) {
      // Update request state with error
      setRequestState(requestKey, 'error', error.message);
      if (onLoadingChange) onLoadingChange(false);
      
      // Log error for analytics
      logErrorAnalytics(error, 'calculateProbability', {
        goalId,
        parameterCount: Object.keys(parameters).length
      });
      
      // Track performance metrics for failed request
      if (config.debugPerformance && window.PerformanceOptimizer) {
        const duration = performance.now() - startTime;
        window.PerformanceOptimizer.trackApiCall(
          `probability_calculation`, duration, false, false
        );
      }
      
      // Check if we should return a fallback result
      if (allowFallback) {
        // For probability calculations, we can fall back to a simple result
        // with a warning flag rather than failing completely
        return {
          probability: null, // Null indicates failed calculation
          valid: false,
          message: createUserFriendlyErrorMessage(error, 'calculate probability'),
          metadata: {
            error: error.message,
            fallback: true,
            timestamp: Date.now()
          }
        };
      }
      
      console.error('Error calculating probability:', error);
      
      // Re-throw with user-friendly message
      if (!config.userFriendlyErrors) {
        throw error;
      }
      
      throw new Error(
        createUserFriendlyErrorMessage(error, 'calculate probability')
      );
    }
  }
  
  /**
   * Execute a batched probability calculation request
   * @param {string} goalId - The goal ID
   * @param {Object} parameters - Parameters for the calculation
   * @param {number} timeout - Request timeout
   * @returns {Promise<Object>} Probability result
   */
  async function executeBatchedProbabilityRequest(goalId, parameters, timeout) {
    return window.PerformanceOptimizer.batchRequest(
      'probability_calculation',
      async (batchedRequests) => {
        if (config.logApiCalls && config.debugPerformance) {
          console.log(`Executing batched probability calculation with ${batchedRequests.length} requests`);
        }
        
        // Group requests by goalId for efficient batching
        const requestsByGoal = {};
        batchedRequests.forEach(request => {
          const { goalId, parameters } = request;
          if (!requestsByGoal[goalId]) {
            requestsByGoal[goalId] = [];
          }
          requestsByGoal[goalId].push(parameters);
        });
        
        // Execute batched requests for each goal
        const results = [];
        const batchPromises = Object.entries(requestsByGoal).map(async ([goalId, parametersList]) => {
          // Create abort controller for this batch
          const abortController = new AbortController();
          
          // Set timeout if specified
          let timeoutId = null;
          if (timeout > 0) {
            timeoutId = setTimeout(() => {
              abortController.abort();
            }, timeout);
          }
          
          try {
            // Call the batch probability calculation endpoint
            const response = await fetch(
              `${config.apiBasePath}/goals/${goalId}/calculate-probability/batch`, 
              {
                method: 'POST',
                headers: {
                  'Accept': 'application/json',
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ parametersList }),
                signal: abortController.signal
              }
            );
            
            // Clean up timeout
            if (timeoutId) clearTimeout(timeoutId);
            
            // Handle HTTP errors
            if (!response.ok) {
              let errorMessage;
              try {
                const errorData = await response.json();
                errorMessage = errorData.message || `API request failed with status ${response.status}`;
              } catch (e) {
                errorMessage = `API request failed with status ${response.status}`;
              }
              
              throw new Error(errorMessage);
            }
            
            // Return batch results
            const batchResults = await response.json();
            return { goalId, results: batchResults };
          } catch (error) {
            // Clean up timeout
            if (timeoutId) clearTimeout(timeoutId);
            throw error;
          }
        });
        
        // Wait for all batch requests to complete
        const batchResponses = await Promise.all(batchPromises);
        
        // Map back to original request order
        return batchedRequests.map(request => {
          const { goalId, parameters } = request;
          const batchResponse = batchResponses.find(r => r.goalId === goalId);
          
          if (!batchResponse) {
            throw new Error(`No response found for goal ${goalId}`);
          }
          
          // Find matching result in batch by parameters
          const parameterHash = JSON.stringify(parameters);
          const result = batchResponse.results.find(r => {
            return JSON.stringify(r.parameters) === parameterHash;
          });
          
          return result || { probability: 0, error: 'No matching result in batch' };
        });
      },
      { goalId, parameters },
      null // No batch processing function needed
    );
  }
  
  /**
   * Execute a single probability calculation request (non-batched)
   * @param {string} goalId - The goal ID
   * @param {Object} parameters - Parameters for the calculation
   * @param {number} timeout - Request timeout
   * @returns {Promise<Object>} Probability result
   */
  async function executeSingleProbabilityRequest(goalId, parameters, timeout) {
    // Create an abort controller for this request
    const abortController = new AbortController();
    const requestKey = `${goalId}_probability`;
    abortControllers[requestKey] = abortController;
    
    // Set up timeout if specified
    let timeoutId = null;
    if (timeout > 0) {
      timeoutId = setTimeout(() => {
        abortController.abort();
      }, timeout);
    }
    
    try {
      // Call the probability calculation endpoint
      const response = await fetch(
        `${config.apiBasePath}/goals/${goalId}/calculate-probability`, 
        {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(parameters),
          signal: abortController.signal
        }
      );
      
      // Handle HTTP errors
      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || `API request failed with status ${response.status}`;
          
          // Check for specific API error codes
          if (errorData.code) {
            switch (errorData.code) {
              case 'RATE_LIMIT_EXCEEDED':
                errorMessage = 'Rate limit exceeded. Please try again in a few minutes.';
                break;
              case 'INVALID_PARAMETERS':
                errorMessage = 'Some parameters are invalid. Please check your inputs.';
                break;
              // Add more as needed
            }
          }
        } catch (e) {
          errorMessage = `API request failed with status ${response.status}`;
        }
        
        const error = new Error(errorMessage);
        error.status = response.status;
        throw error;
      }
      
      // Parse response
      const data = await response.json();
      
      // Clean up
      clearTimeout(timeoutId);
      delete abortControllers[requestKey];
      
      if (config.logApiCalls) console.log(`Successfully calculated probability for goal ${goalId}`);
      
      return data;
    } catch (error) {
      // Clean up
      clearTimeout(timeoutId);
      delete abortControllers[requestKey];
      
      // Re-throw error for handling by the main function
      throw error;
    }
  }
  
  /**
   * Validates probability calculation parameters to avoid unnecessary API calls
   * @param {Object} parameters - Parameters to validate
   * @returns {Object} Validation result
   */
  function validateProbabilityParameters(parameters) {
    // This is a simple validation - actual validation should be more comprehensive
    // and specific to your parameter requirements
    
    if (!parameters) {
      return { valid: false, reason: 'No parameters provided' };
    }
    
    // Check for required numeric fields (example)
    const requiredNumericFields = ['targetAmount', 'currentSavings', 'monthlyContribution'];
    
    for (const field of requiredNumericFields) {
      if (parameters[field] !== undefined) {
        const value = parseFloat(parameters[field]);
        if (isNaN(value) || value < 0) {
          return { 
            valid: false, 
            reason: `Invalid value for ${field}. Must be a positive number.`
          };
        }
      }
    }
    
    return { valid: true };
  }
  
  /**
   * Fetches goal adjustment recommendations
   *
   * @param {string} goalId - The ID of the goal 
   * @param {Object} options - Optional configuration
   * @returns {Promise<Object>} Adjustment recommendations data
   */
  async function fetchAdjustments(goalId, options = {}) {
    if (!goalId) {
      throw new Error('Goal ID is required');
    }
    
    const {
      onLoadingChange = null,
      timeout = config.requestTimeout,
      forceRefresh = false,
      cacheExpiration = cache.expirationTime,
      allowFallback = config.enableFallbackData
    } = options;
    
    // Cache key for this request
    const cacheKey = `${goalId}_adjustments`;
    
    // Check if we're offline
    if (!isOnline()) {
      // If offline and we have cached data, return it with warning
      const cachedData = getCachedData(cacheKey, Infinity); // No expiration when offline
      if (cachedData && allowFallback) {
        if (config.logApiCalls) console.log(`Using cached adjustments for goal ${goalId} (offline mode)`);
        
        setRequestState(cacheKey, 'success', null, true); // success with warning
        if (onLoadingChange) onLoadingChange(false);
        
        return {
          ...cachedData,
          _metadata: {
            fromCache: true,
            offlineMode: true,
            timestamp: cache.timestamps[cacheKey]
          }
        };
      } else {
        const error = new Error('You are currently offline. Please check your internet connection and try again.');
        error.isOffline = true;
        
        setRequestState(cacheKey, 'error', error.message);
        if (onLoadingChange) onLoadingChange(false);
        
        throw error;
      }
    }
    
    // Set loading state
    setRequestState(cacheKey, 'loading');
    if (onLoadingChange) onLoadingChange(true);
    
    try {
      // Check cache first if we're not forcing a refresh
      if (!forceRefresh) {
        const cachedData = getCachedData(cacheKey, cacheExpiration);
        if (cachedData) {
          setRequestState(cacheKey, 'success');
          if (onLoadingChange) onLoadingChange(false);
          return {
            ...cachedData,
            _metadata: {
              fromCache: true,
              timestamp: cache.timestamps[cacheKey]
            }
          };
        }
      }
      
      // Create abort controller
      const abortController = new AbortController();
      abortControllers[cacheKey] = abortController;
      
      // Set timeout
      let timeoutId = null;
      if (timeout > 0) {
        timeoutId = setTimeout(() => {
          abortController.abort();
        }, timeout);
      }
      
      // Fetch adjustments
      const response = await fetch(
        `${config.apiBasePath}/goals/${goalId}/adjustments`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          signal: abortController.signal
        }
      );
      
      // Handle HTTP errors
      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || `API request failed with status ${response.status}`;
          
          // Check for specific API error codes
          if (errorData.code) {
            switch (errorData.code) {
              case 'GOAL_NOT_FOUND':
                errorMessage = 'The requested goal could not be found.';
                break;
              // Add more specific error codes as needed
            }
          }
        } catch (e) {
          errorMessage = `API request failed with status ${response.status}`;
        }
        
        const error = new Error(errorMessage);
        error.status = response.status;
        throw error;
      }
      
      // Parse response
      const data = await response.json();
      
      // Process the data to ensure it has required structure
      const processedData = processAdjustmentData(data, goalId);
      
      // Cache the result
      cacheData(cacheKey, processedData);
      
      // Clean up
      setRequestState(cacheKey, 'success');
      if (onLoadingChange) onLoadingChange(false);
      clearTimeout(timeoutId);
      delete abortControllers[cacheKey];
      
      return {
        ...processedData,
        _metadata: {
          fromCache: false,
          timestamp: Date.now()
        }
      };
    } catch (error) {
      // Update request state with error
      setRequestState(cacheKey, 'error', error.message);
      if (onLoadingChange) onLoadingChange(false);
      
      // Log error for analytics
      logErrorAnalytics(error, 'fetchAdjustments', { goalId });
      
      // Check if we should fall back to cached data
      if (allowFallback && shouldFallbackToCachedData(error, goalId)) {
        const cachedData = getCachedData(cacheKey, Infinity); // No expiration for fallback
        if (cachedData) {
          if (config.logApiCalls) console.log(`Falling back to cached adjustments for goal ${goalId}`);
          
          // Set warning state
          setRequestState(cacheKey, 'success', null, true);
          if (onLoadingChange) onLoadingChange(false);
          
          return {
            ...cachedData,
            _metadata: {
              fromCache: true,
              fallback: true,
              error: error.message,
              timestamp: cache.timestamps[cacheKey]
            }
          };
        }
      }
      
      console.error('Error fetching adjustments:', error);
      
      // Return a user-friendly error
      if (!config.userFriendlyErrors) {
        throw error;
      }
      
      throw new Error(
        createUserFriendlyErrorMessage(error, 'load adjustment recommendations')
      );
    }
  }
  
  /**
   * Process adjustment data to ensure it has required fields
   * @param {Object} data - Raw adjustment data
   * @param {string} goalId - Goal ID for filling in missing data
   * @returns {Object} Processed adjustment data
   */
  function processAdjustmentData(data, goalId) {
    // Create a deep copy to avoid modifying the original
    const processed = JSON.parse(JSON.stringify(data));
    
    // Ensure adjustments array exists
    if (!processed.adjustments || !Array.isArray(processed.adjustments)) {
      processed.adjustments = [];
    }
    
    // Set default current probability if missing
    if (processed.currentProbability === undefined) {
      processed.currentProbability = 0;
    }
    
    // Add goalId if missing
    if (!processed.goalId && goalId) {
      processed.goalId = goalId;
    }
    
    // Process each adjustment
    processed.adjustments.forEach((adjustment, index) => {
      // Generate ID if missing
      if (!adjustment.id) {
        adjustment.id = `${goalId}_adj_${index}`;
      }
      
      // Ensure impact metrics exist
      if (!adjustment.impactMetrics) {
        adjustment.impactMetrics = {
          probabilityIncrease: 0,
          newProbability: processed.currentProbability
        };
      }
      
      // Add default description if missing
      if (!adjustment.description) {
        adjustment.description = `Adjustment ${index + 1}`;
      }
      
      // Ensure category exists
      if (!adjustment.category) {
        adjustment.category = 'other';
      }
    });
    
    return processed;
  }
  
  /**
   * Fetches goal scenarios comparison data
   *
   * @param {string} goalId - The ID of the goal
   * @param {Object} options - Optional configuration
   * @returns {Promise<Object>} Scenario comparison data
   */
  async function fetchScenarios(goalId, options = {}) {
    if (!goalId) {
      throw new Error('Goal ID is required');
    }
    
    const {
      onLoadingChange = null,
      timeout = config.requestTimeout,
      forceRefresh = false,
      cacheExpiration = cache.expirationTime,
      allowFallback = config.enableFallbackData
    } = options;
    
    // Cache key for this request
    const cacheKey = `${goalId}_scenarios`;
    
    // Check if we're offline
    if (!isOnline()) {
      // If offline and we have cached data, return it with warning
      const cachedData = getCachedData(cacheKey, Infinity); // No expiration when offline
      if (cachedData && allowFallback) {
        if (config.logApiCalls) console.log(`Using cached scenarios for goal ${goalId} (offline mode)`);
        
        setRequestState(cacheKey, 'success', null, true); // success with warning
        if (onLoadingChange) onLoadingChange(false);
        
        return {
          ...cachedData,
          _metadata: {
            fromCache: true,
            offlineMode: true,
            timestamp: cache.timestamps[cacheKey]
          }
        };
      } else {
        const error = new Error('You are currently offline. Please check your internet connection and try again.');
        error.isOffline = true;
        
        setRequestState(cacheKey, 'error', error.message);
        if (onLoadingChange) onLoadingChange(false);
        
        throw error;
      }
    }
    
    // Set loading state
    setRequestState(cacheKey, 'loading');
    if (onLoadingChange) onLoadingChange(true);
    
    try {
      // Check cache first if we're not forcing a refresh
      if (!forceRefresh) {
        const cachedData = getCachedData(cacheKey, cacheExpiration);
        if (cachedData) {
          setRequestState(cacheKey, 'success');
          if (onLoadingChange) onLoadingChange(false);
          return {
            ...cachedData,
            _metadata: {
              fromCache: true,
              timestamp: cache.timestamps[cacheKey]
            }
          };
        }
      }
      
      // Create abort controller
      const abortController = new AbortController();
      abortControllers[cacheKey] = abortController;
      
      // Set timeout
      let timeoutId = null;
      if (timeout > 0) {
        timeoutId = setTimeout(() => {
          abortController.abort();
        }, timeout);
      }
      
      // Fetch scenarios
      const response = await fetch(
        `${config.apiBasePath}/goals/${goalId}/scenarios`,
        {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          signal: abortController.signal
        }
      );
      
      // Handle HTTP errors
      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || `API request failed with status ${response.status}`;
        } catch (e) {
          errorMessage = `API request failed with status ${response.status}`;
        }
        
        const error = new Error(errorMessage);
        error.status = response.status;
        throw error;
      }
      
      // Parse response
      const data = await response.json();
      
      // Process the data to ensure it has required structure
      const processedData = processScenarioData(data, goalId);
      
      // Cache the result
      cacheData(cacheKey, processedData);
      
      // Clean up
      setRequestState(cacheKey, 'success');
      if (onLoadingChange) onLoadingChange(false);
      clearTimeout(timeoutId);
      delete abortControllers[cacheKey];
      
      return {
        ...processedData,
        _metadata: {
          fromCache: false,
          timestamp: Date.now()
        }
      };
    } catch (error) {
      // Update request state with error
      setRequestState(cacheKey, 'error', error.message);
      if (onLoadingChange) onLoadingChange(false);
      
      // Log error for analytics
      logErrorAnalytics(error, 'fetchScenarios', { goalId });
      
      // Check if we should fall back to cached data
      if (allowFallback && shouldFallbackToCachedData(error, goalId)) {
        const cachedData = getCachedData(cacheKey, Infinity); // No expiration for fallback
        if (cachedData) {
          if (config.logApiCalls) console.log(`Falling back to cached scenarios for goal ${goalId}`);
          
          // Set warning state
          setRequestState(cacheKey, 'success', null, true);
          if (onLoadingChange) onLoadingChange(false);
          
          return {
            ...cachedData,
            _metadata: {
              fromCache: true,
              fallback: true,
              error: error.message,
              timestamp: cache.timestamps[cacheKey]
            }
          };
        }
      }
      
      console.error('Error fetching scenarios:', error);
      
      // Return a user-friendly error
      if (!config.userFriendlyErrors) {
        throw error;
      }
      
      throw new Error(
        createUserFriendlyErrorMessage(error, 'load scenario comparisons')
      );
    }
  }
  
  /**
   * Process scenario data to ensure it has required fields
   * @param {Object} data - Raw scenario data
   * @param {string} goalId - Goal ID for filling in missing data
   * @returns {Object} Processed scenario data
   */
  function processScenarioData(data, goalId) {
    // Create a deep copy to avoid modifying the original
    const processed = JSON.parse(JSON.stringify(data));
    
    // Add goalId if missing
    if (!processed.goalId && goalId) {
      processed.goalId = goalId;
    }
    
    // Ensure scenarios array exists
    if (!processed.scenarios || !Array.isArray(processed.scenarios)) {
      processed.scenarios = [];
    }
    
    // If no scenarios, add a default baseline scenario
    if (processed.scenarios.length === 0) {
      processed.scenarios.push({
        id: `${goalId}_baseline`,
        name: 'Current Plan',
        description: 'Your current financial plan with no changes',
        probability: 0,
        isBaseline: true
      });
    }
    
    // Ensure at least one scenario is marked as baseline
    const hasBaseline = processed.scenarios.some(s => s.isBaseline);
    if (!hasBaseline && processed.scenarios.length > 0) {
      processed.scenarios[0].isBaseline = true;
    }
    
    // Process each scenario
    processed.scenarios.forEach((scenario, index) => {
      // Generate ID if missing
      if (!scenario.id) {
        scenario.id = `${goalId}_scenario_${index}`;
      }
      
      // Add default name if missing
      if (!scenario.name) {
        scenario.name = `Scenario ${index + 1}`;
      }
      
      // Add default description if missing
      if (!scenario.description) {
        if (scenario.isBaseline) {
          scenario.description = 'Your current financial plan with no changes';
        } else {
          scenario.description = `Alternative scenario ${index + 1}`;
        }
      }
      
      // Ensure probability exists and is a number
      if (scenario.probability === undefined || scenario.probability === null) {
        scenario.probability = 0;
      } else if (typeof scenario.probability !== 'number') {
        scenario.probability = parseFloat(scenario.probability) || 0;
      }
    });
    
    return processed;
  }
  
  /**
   * Cancel all pending requests
   */
  function cancelAllRequests() {
    Object.keys(abortControllers).forEach(key => {
      try {
        abortControllers[key].abort();
        delete abortControllers[key];
      } catch (e) {
        console.error(`Error cancelling request ${key}:`, e);
      }
    });
  }
  
  /**
   * Updates the service configuration
   *
   * @param {Object} newConfig - New configuration options
   */
  function configure(newConfig = {}) {
    Object.assign(config, newConfig);
  }
  
  /**
   * Gets the current caching statistics
   * @returns {Object} Cache statistics
   */
  function getCacheStats() {
    return {
      cacheSize: Object.keys(cache.data).length,
      oldestEntry: Object.keys(cache.timestamps).reduce((oldest, key) => {
        return cache.timestamps[key] < oldest.timestamp ? 
          { key, timestamp: cache.timestamps[key] } : oldest;
      }, { key: null, timestamp: Infinity }),
      newestEntry: Object.keys(cache.timestamps).reduce((newest, key) => {
        return cache.timestamps[key] > newest.timestamp ? 
          { key, timestamp: cache.timestamps[key] } : newest;
      }, { key: null, timestamp: 0 }),
      errorCacheEntries: Object.keys(cache.errorCache).length
    };
  }
  
  // Initialize event listeners for network status
  if (typeof window !== 'undefined' && config.enableNetworkDetection) {
    window.addEventListener('online', () => handleNetworkStatusChange(true));
    window.addEventListener('offline', () => handleNetworkStatusChange(false));
  }
  
  // Handle clean up on page unload
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => {
      cancelAllRequests();
    });
  }
  
  // Public API
  return {
    // Data fetching
    fetchVisualizationData,
    calculateProbability,
    fetchAdjustments,
    fetchScenarios,
    
    // Data management
    getComponentData,
    clearCache,
    validateCachedData,
    getCacheStats,
    
    // State management
    hasData,
    getRequestState,
    cancelAllRequests,
    isOnline,
    
    // Configuration
    configure
  };
})();

// Make service available globally
window.VisualizationDataService = VisualizationDataService;