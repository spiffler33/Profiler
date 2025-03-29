/**
 * Performance Optimizer Service
 *
 * This service provides performance optimization utilities for the application including:
 * - Request batching for related API calls
 * - Efficient caching with size limits, TTL, and prioritization
 * - Component rendering optimization with throttling and debouncing
 * - Performance metrics collection and analysis
 */

const PerformanceOptimizer = (function() {
  // Configuration
  const config = {
    // Cache settings
    maxCacheSize: 50, // Maximum number of cached items
    maxCacheSizeBytes: 5 * 1024 * 1024, // 5MB max cache size
    cachePruneThreshold: 0.8, // When to start pruning cache (80% full)
    
    // Request batching
    enableRequestBatching: true,
    maxBatchDelay: 50, // Maximum delay for batching in ms
    maxBatchSize: 5, // Maximum number of requests in a batch
    
    // Throttling/Debouncing settings
    eventThrottleDelay: 100, // ms to throttle rapid events
    standardDebounceTimes: {
      keyup: 300,       // 300ms for keyboard input
      scroll: 100,      // 100ms for scroll events
      resize: 200,      // 200ms for window resize
      probabilityCalc: 500  // 500ms for probability calculations
    },
    
    // Performance metrics
    collectMetrics: true,
    reportMetricsInterval: 60000, // Report metrics every minute
    slowThreshold: 500, // Operations taking longer than this are considered slow (ms)
    
    // DOM optimization
    batchDomUpdates: true,
    useRequestAnimationFrame: true,
    
    // Feature flags
    enableMemoization: true,
    enableLazyLoading: true,
    
    // Debug settings
    logPerformanceIssues: true,
    verboseLogging: false
  };
  
  // Performance metrics storage
  const metrics = {
    apiCalls: {},
    renderTimes: {},
    cacheStats: {
      hits: 0,
      misses: 0,
      size: 0,
      pruneCount: 0
    },
    lastCalculation: Date.now()
  };
  
  // Request batching state
  const requestBatchingState = {
    pendingRequests: {},
    batchTimers: {},
    batchPromises: {}
  };
  
  // Memoization cache
  const memoCache = new Map();
  
  /**
   * Throttles a function to prevent excessive calls
   * @param {Function} fn - Function to throttle
   * @param {number} delay - Throttle delay in ms
   * @returns {Function} Throttled function
   */
  function throttle(fn, delay = config.eventThrottleDelay) {
    let lastCall = 0;
    let throttleTimeout = null;
    
    return function throttled(...args) {
      const now = Date.now();
      const context = this;
      
      // If enough time has passed since last call, execute immediately
      if (now - lastCall >= delay) {
        lastCall = now;
        return fn.apply(context, args);
      }
      
      // Otherwise, schedule for later and cancel any existing timeout
      clearTimeout(throttleTimeout);
      return new Promise(resolve => {
        throttleTimeout = setTimeout(() => {
          lastCall = Date.now();
          resolve(fn.apply(context, args));
        }, delay - (now - lastCall));
      });
    };
  }
  
  /**
   * Debounces a function to delay execution until after a quiet period
   * @param {Function} fn - Function to debounce
   * @param {number} delay - Debounce delay in ms
   * @param {Object} options - Options for debouncing
   * @returns {Function} Debounced function
   */
  function debounce(fn, delay, options = {}) {
    const { leading = false, maxWait = 0 } = options;
    let timeout = null;
    let lastArgs = null;
    let lastContext = null;
    let lastCallTime = 0;
    let result;
    
    function invokeFunction() {
      result = fn.apply(lastContext, lastArgs);
      lastArgs = null;
      lastContext = null;
      return result;
    }
    
    function trailingEdge() {
      timeout = null;
      if (lastArgs) {
        return invokeFunction();
      }
    }
    
    function debounced(...args) {
      lastArgs = args;
      lastContext = this;
      lastCallTime = Date.now();
      
      // If no timeout is active and leading edge execution is enabled
      if (!timeout && leading) {
        result = invokeFunction();
        return result;
      }
      
      // Clear the existing timeout
      if (timeout) {
        clearTimeout(timeout);
      }
      
      // Set a new timeout to execute the function
      timeout = setTimeout(trailingEdge, delay);
      
      // If maxWait is set and we've waited too long, invoke now
      if (maxWait > 0 && Date.now() - lastCallTime >= maxWait) {
        result = invokeFunction();
        timeout = null;
        return result;
      }
      
      return result;
    }
    
    // Add a flush method to execute immediately
    debounced.flush = function() {
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
        return invokeFunction();
      }
    };
    
    // Add a cancel method to cancel the debounce
    debounced.cancel = function() {
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
        lastArgs = null;
        lastContext = null;
      }
    };
    
    return debounced;
  }
  
  /**
   * Memoizes a function to cache results for repeated calls with same arguments
   * @param {Function} fn - Function to memoize
   * @param {Function} keyGenerator - Optional function to generate cache key
   * @param {number} maxSize - Maximum size of memoization cache
   * @returns {Function} Memoized function
   */
  function memoize(fn, keyGenerator = JSON.stringify, maxSize = 100) {
    if (!config.enableMemoization) {
      return fn;
    }
    
    const cache = new Map();
    
    function memoized(...args) {
      const key = keyGenerator(args);
      
      if (cache.has(key)) {
        metrics.cacheStats.hits++;
        return cache.get(key);
      }
      
      const result = fn.apply(this, args);
      metrics.cacheStats.misses++;
      
      // Manage cache size
      if (cache.size >= maxSize) {
        // Delete oldest entry (first inserted)
        const oldestKey = cache.keys().next().value;
        cache.delete(oldestKey);
      }
      
      cache.set(key, result);
      return result;
    }
    
    // Add a method to clear the cache
    memoized.clearCache = () => cache.clear();
    
    // Add method to get cache size
    memoized.getCacheSize = () => cache.size;
    
    return memoized;
  }
  
  /**
   * Batches related API requests together to reduce network overhead
   * @param {string} batchKey - Key to group related requests
   * @param {Function} requestFn - Function that makes the actual request
   * @param {Object} requestData - Data for this specific request
   * @param {Function} processBatchFn - Function to process the batch of requests
   * @returns {Promise} Promise resolving to the request result
   */
  function batchRequest(batchKey, requestFn, requestData, processBatchFn) {
    if (!config.enableRequestBatching) {
      // If batching is disabled, just execute the request directly
      return requestFn(requestData);
    }
    
    return new Promise((resolve, reject) => {
      // Create the batch if it doesn't exist
      if (!requestBatchingState.pendingRequests[batchKey]) {
        requestBatchingState.pendingRequests[batchKey] = [];
      }
      
      // Add this request to the batch with its resolver and rejector
      requestBatchingState.pendingRequests[batchKey].push({
        data: requestData,
        resolve,
        reject
      });
      
      // If we already have a timer for this batch, clear it
      if (requestBatchingState.batchTimers[batchKey]) {
        clearTimeout(requestBatchingState.batchTimers[batchKey]);
      }
      
      // Process the batch immediately if it reaches max size
      if (requestBatchingState.pendingRequests[batchKey].length >= config.maxBatchSize) {
        processBatch(batchKey, requestFn, processBatchFn);
        return;
      }
      
      // Otherwise, set a timer to process the batch after a delay
      requestBatchingState.batchTimers[batchKey] = setTimeout(() => {
        processBatch(batchKey, requestFn, processBatchFn);
      }, config.maxBatchDelay);
    });
  }
  
  /**
   * Processes a batch of requests
   * @param {string} batchKey - Key for the batch to process
   * @param {Function} requestFn - Function to execute the request
   * @param {Function} processBatchFn - Function to process the batch results
   */
  function processBatch(batchKey, requestFn, processBatchFn) {
    // Get the batch requests
    const batch = requestBatchingState.pendingRequests[batchKey] || [];
    
    // Clear the batch and timer
    requestBatchingState.pendingRequests[batchKey] = [];
    if (requestBatchingState.batchTimers[batchKey]) {
      clearTimeout(requestBatchingState.batchTimers[batchKey]);
      delete requestBatchingState.batchTimers[batchKey];
    }
    
    // If batch is empty, nothing to do
    if (batch.length === 0) return;
    
    // Extract all request data
    const batchData = batch.map(request => request.data);
    
    // Execute the batch request
    requestFn(batchData)
      .then(results => {
        // Process the results
        const processedResults = processBatchFn ? processBatchFn(results, batchData) : results;
        
        // Resolve each individual request
        batch.forEach((request, index) => {
          const result = Array.isArray(processedResults) ? 
            processedResults[index] : processedResults;
          request.resolve(result);
        });
      })
      .catch(error => {
        // Reject all requests in the batch with the same error
        batch.forEach(request => {
          request.reject(error);
        });
      });
  }
  
  /**
   * Optimizes cache storage and retrieval with dynamic TTL and priority
   */
  const OptimizedCache = (function() {
    // Internal cache storage
    const cacheStore = new Map();
    const cachePriorities = new Map();
    const cacheExpiry = new Map();
    const cacheSize = new Map();
    let totalCacheSize = 0;
    
    /**
     * Calculates the size of data in bytes (approximate)
     * @param {any} data - Data to measure
     * @returns {number} Size in bytes
     */
    function getDataSize(data) {
      if (data === null || data === undefined) return 0;
      
      // For strings, use length * 2 (approximation for UTF-16)
      if (typeof data === 'string') return data.length * 2;
      
      // For objects and arrays, use JSON stringification
      if (typeof data === 'object') {
        try {
          const json = JSON.stringify(data);
          return json.length * 2;
        } catch (e) {
          // Fallback if JSON stringification fails
          return 1024; // Assume 1KB 
        }
      }
      
      // For numbers and booleans, use small fixed sizes
      if (typeof data === 'number') return 8;
      if (typeof data === 'boolean') return 4;
      
      // Default fallback
      return 512; // Assume 512 bytes
    }
    
    /**
     * Prunes the cache when it exceeds size limits
     */
    function pruneCache() {
      // Sort by priority and then by expiry
      const entries = Array.from(cacheStore.entries())
        .map(([key, value]) => ({
          key,
          value,
          priority: cachePriorities.get(key) || 0,
          expiry: cacheExpiry.get(key) || 0,
          size: cacheSize.get(key) || 0
        }))
        .sort((a, b) => {
          // Expired items first
          const now = Date.now();
          const aExpired = a.expiry > 0 && a.expiry < now;
          const bExpired = b.expiry > 0 && b.expiry < now;
          
          if (aExpired && !bExpired) return -1;
          if (!aExpired && bExpired) return 1;
          
          // Then by priority (lower priority first)
          if (a.priority !== b.priority) {
            return a.priority - b.priority;
          }
          
          // Then by expiry time (sooner first)
          return a.expiry - b.expiry;
        });
    
      // Start removing items until we're below the threshold
      let removedCount = 0;
      const targetSize = config.maxCacheSizeBytes * config.cachePruneThreshold;
      
      for (const entry of entries) {
        if (totalCacheSize <= targetSize) break;
        
        // Remove the item
        cacheStore.delete(entry.key);
        cachePriorities.delete(entry.key);
        cacheExpiry.delete(entry.key);
        totalCacheSize -= entry.size;
        cacheSize.delete(entry.key);
        removedCount++;
        
        if (config.verboseLogging) {
          console.log(`Pruned cache item: ${entry.key}, size: ${entry.size}, priority: ${entry.priority}`);
        }
      }
      
      metrics.cacheStats.pruneCount++;
      
      if (config.logPerformanceIssues && removedCount > 0) {
        console.log(`Cache pruned: removed ${removedCount} items, new size: ${totalCacheSize} bytes`);
      }
    }
    
    /**
     * Sets a value in the cache with TTL and priority
     * @param {string} key - Cache key
     * @param {any} value - Value to cache
     * @param {Object} options - Cache options
     */
    function set(key, value, options = {}) {
      const {
        ttl = 0,           // Time to live in ms (0 = no expiry)
        priority = 1,      // Priority (1-10, higher = more important)
        updateAccessTime = true  // Update last access time on set
      } = options;
      
      // Check if we should prune before adding
      if (cacheStore.size >= config.maxCacheSize || 
          totalCacheSize >= config.maxCacheSizeBytes * config.cachePruneThreshold) {
        pruneCache();
      }
      
      // Calculate data size
      const size = getDataSize(value);
      
      // If single item is too large, log warning and don't cache
      if (size > config.maxCacheSizeBytes * 0.5) {
        if (config.logPerformanceIssues) {
          console.warn(`Cache item too large (${size} bytes): ${key}`);
        }
        return false;
      }
      
      // If already exists, update existing entry and adjust size
      if (cacheStore.has(key)) {
        const oldSize = cacheSize.get(key) || 0;
        totalCacheSize = totalCacheSize - oldSize + size;
      } else {
        totalCacheSize += size;
      }
      
      // Set the value and metadata
      cacheStore.set(key, value);
      cacheSize.set(key, size);
      cachePriorities.set(key, priority);
      
      // Set expiry time if TTL provided
      if (ttl > 0) {
        cacheExpiry.set(key, Date.now() + ttl);
      } else {
        cacheExpiry.set(key, 0); // No expiry
      }
      
      metrics.cacheStats.size = totalCacheSize;
      return true;
    }
    
    /**
     * Gets a value from the cache
     * @param {string} key - Cache key
     * @param {Object} options - Get options
     * @returns {any} Cached value or undefined
     */
    function get(key, options = {}) {
      const {
        updateAccessTime = true,   // Update last access time on get
        checkExpiry = true         // Check if entry has expired
      } = options;
      
      // Check if key exists
      if (!cacheStore.has(key)) {
        metrics.cacheStats.misses++;
        return undefined;
      }
      
      // Check expiry if needed
      if (checkExpiry) {
        const expiry = cacheExpiry.get(key) || 0;
        if (expiry > 0 && expiry < Date.now()) {
          // Entry has expired, remove it
          remove(key);
          metrics.cacheStats.misses++;
          return undefined;
        }
      }
      
      // Increase priority slightly on access to implement LRU-like behavior
      if (updateAccessTime) {
        const currentPriority = cachePriorities.get(key) || 1;
        // Small increase to priority, max of 10
        cachePriorities.set(key, Math.min(10, currentPriority + 0.1));
      }
      
      metrics.cacheStats.hits++;
      return cacheStore.get(key);
    }
    
    /**
     * Removes an item from the cache
     * @param {string} key - Cache key
     * @returns {boolean} True if item was removed
     */
    function remove(key) {
      if (!cacheStore.has(key)) return false;
      
      // Reduce total size
      const size = cacheSize.get(key) || 0;
      totalCacheSize -= size;
      
      // Remove all metadata
      cacheStore.delete(key);
      cachePriorities.delete(key);
      cacheExpiry.delete(key);
      cacheSize.delete(key);
      
      metrics.cacheStats.size = totalCacheSize;
      return true;
    }
    
    /**
     * Clears the entire cache
     */
    function clear() {
      cacheStore.clear();
      cachePriorities.clear();
      cacheExpiry.clear();
      cacheSize.clear();
      totalCacheSize = 0;
      
      metrics.cacheStats.size = 0;
      if (config.verboseLogging) {
        console.log('Cache cleared');
      }
    }
    
    /**
     * Gets cache stats
     * @returns {Object} Cache statistics
     */
    function getStats() {
      return {
        itemCount: cacheStore.size,
        totalSize: totalCacheSize,
        maxSize: config.maxCacheSizeBytes,
        utilization: totalCacheSize / config.maxCacheSizeBytes,
        hits: metrics.cacheStats.hits,
        misses: metrics.cacheStats.misses,
        hitRatio: metrics.cacheStats.hits / (metrics.cacheStats.hits + metrics.cacheStats.misses || 1),
        pruneCount: metrics.cacheStats.pruneCount
      };
    }
    
    return {
      set,
      get,
      remove,
      clear,
      getStats,
      pruneCache
    };
  })();
  
  /**
   * Manages DOM updates efficiently using requestAnimationFrame and batching
   */
  const DomOptimizer = (function() {
    const updateQueue = new Map();
    let updateScheduled = false;
    
    /**
     * Schedules an update to a DOM element
     * @param {string|Element} elementId - Element ID or element
     * @param {Function} updateFn - Function to call for the update
     */
    function scheduleUpdate(elementId, updateFn) {
      if (!config.batchDomUpdates) {
        // If batching is disabled, just do the update immediately
        const element = typeof elementId === 'string' ? 
          document.getElementById(elementId) : elementId;
        if (element) updateFn(element);
        return;
      }
      
      // Add to queue
      updateQueue.set(elementId, updateFn);
      
      // Schedule batch update if not already scheduled
      if (!updateScheduled) {
        updateScheduled = true;
        
        if (config.useRequestAnimationFrame && window.requestAnimationFrame) {
          requestAnimationFrame(processDomUpdates);
        } else {
          setTimeout(processDomUpdates, 0);
        }
      }
    }
    
    /**
     * Processes all queued DOM updates
     */
    function processDomUpdates() {
      updateScheduled = false;
      
      // Process all queued updates
      updateQueue.forEach((updateFn, elementId) => {
        const element = typeof elementId === 'string' ? 
          document.getElementById(elementId) : elementId;
        
        if (element) {
          try {
            updateFn(element);
          } catch (error) {
            console.error('Error updating DOM element:', error);
          }
        }
      });
      
      // Clear the queue
      updateQueue.clear();
    }
    
    /**
     * Measures rendering performance for an element
     * @param {string|Element} elementId - Element ID or element
     * @param {Function} renderFn - Function that performs rendering
     * @returns {Promise} Promise that resolves when rendering is complete
     */
    function measureRenderPerformance(elementId, renderFn) {
      return new Promise((resolve) => {
        const id = typeof elementId === 'string' ? elementId : elementId.id;
        const element = typeof elementId === 'string' ? 
          document.getElementById(elementId) : elementId;
        
        if (!element) {
          resolve({ duration: 0, error: 'Element not found' });
          return;
        }
        
        // Use Performance API if available
        if (window.performance && window.performance.mark) {
          const startMark = `render-start-${id}`;
          const endMark = `render-end-${id}`;
          const measureName = `render-duration-${id}`;
          
          // Start timing
          performance.mark(startMark);
          
          try {
            // Perform the rendering
            const result = renderFn(element);
            
            // End timing
            performance.mark(endMark);
            performance.measure(measureName, startMark, endMark);
            
            // Get the measurement
            const entries = performance.getEntriesByName(measureName);
            const duration = entries.length > 0 ? entries[0].duration : 0;
            
            // Store in metrics
            if (!metrics.renderTimes[id]) {
              metrics.renderTimes[id] = {
                count: 0,
                totalDuration: 0,
                min: Infinity,
                max: 0,
                average: 0,
                slow: 0
              };
            }
            
            const stats = metrics.renderTimes[id];
            stats.count++;
            stats.totalDuration += duration;
            stats.min = Math.min(stats.min, duration);
            stats.max = Math.max(stats.max, duration);
            stats.average = stats.totalDuration / stats.count;
            
            if (duration > config.slowThreshold) {
              stats.slow++;
              
              if (config.logPerformanceIssues) {
                console.warn(`Slow render detected for ${id}: ${duration.toFixed(2)}ms`);
              }
            }
            
            // Clean up performance entries
            performance.clearMarks(startMark);
            performance.clearMarks(endMark);
            performance.clearMeasures(measureName);
            
            resolve({ duration, result });
          } catch (error) {
            console.error('Error during rendering:', error);
            resolve({ duration: 0, error });
          }
        } else {
          // Fallback for browsers without Performance API
          const startTime = Date.now();
          
          try {
            const result = renderFn(element);
            const duration = Date.now() - startTime;
            resolve({ duration, result });
          } catch (error) {
            console.error('Error during rendering:', error);
            resolve({ duration: 0, error });
          }
        }
      });
    }
    
    return {
      scheduleUpdate,
      processDomUpdates,
      measureRenderPerformance
    };
  })();
  
  /**
   * Collects and reports performance metrics
   */
  function collectPerformanceMetrics() {
    if (!config.collectMetrics) return null;
    
    // Get various performance metrics
    const performanceData = {
      timing: window.performance && window.performance.timing ? 
        {
          domComplete: window.performance.timing.domComplete - window.performance.timing.navigationStart,
          domInteractive: window.performance.timing.domInteractive - window.performance.timing.navigationStart,
          domContentLoaded: window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart,
          loadEvent: window.performance.timing.loadEventEnd - window.performance.timing.navigationStart
        } : null,
      
      memory: window.performance && window.performance.memory ? 
        {
          jsHeapSizeLimit: window.performance.memory.jsHeapSizeLimit,
          totalJSHeapSize: window.performance.memory.totalJSHeapSize,
          usedJSHeapSize: window.performance.memory.usedJSHeapSize
        } : null,
        
      navigation: window.performance && window.performance.navigation ? 
        {
          redirectCount: window.performance.navigation.redirectCount,
          type: window.performance.navigation.type
        } : null,
        
      // Custom metrics
      apiCalls: { ...metrics.apiCalls },
      renderTimes: { ...metrics.renderTimes },
      cacheStats: OptimizedCache.getStats(),
      
      // Time since last calculation
      elapsed: Date.now() - metrics.lastCalculation
    };
    
    metrics.lastCalculation = Date.now();
    
    // Reset counters for next collection period
    Object.keys(metrics.apiCalls).forEach(key => {
      metrics.apiCalls[key].count = 0;
      metrics.apiCalls[key].totalDuration = 0;
    });
    
    return performanceData;
  }
  
  /**
   * Tracks API call performance
   * @param {string} endpoint - API endpoint
   * @param {number} duration - Call duration in ms
   * @param {boolean} success - Whether the call was successful
   * @param {boolean} fromCache - Whether the response came from cache
   */
  function trackApiCall(endpoint, duration, success, fromCache = false) {
    if (!config.collectMetrics) return;
    
    if (!metrics.apiCalls[endpoint]) {
      metrics.apiCalls[endpoint] = {
        count: 0,
        totalDuration: 0,
        min: Infinity,
        max: 0,
        average: 0,
        errors: 0,
        cacheHits: 0
      };
    }
    
    const stats = metrics.apiCalls[endpoint];
    stats.count++;
    stats.totalDuration += duration;
    stats.min = Math.min(stats.min, duration);
    stats.max = Math.max(stats.max, duration);
    stats.average = stats.totalDuration / stats.count;
    
    if (fromCache) {
      stats.cacheHits++;
    }
    
    if (!success) {
      stats.errors++;
    }
    
    // Log slow API calls
    if (duration > config.slowThreshold && config.logPerformanceIssues) {
      console.warn(`Slow API call to ${endpoint}: ${duration.toFixed(2)}ms`);
    }
  }
  
  /**
   * Setup periodic performance reporting
   */
  function setupPerformanceReporting() {
    if (!config.collectMetrics || !config.reportMetricsInterval) return;
    
    // Report metrics at configured interval
    setInterval(() => {
      const performanceData = collectPerformanceMetrics();
      
      // Log to console in development
      if (config.logPerformanceIssues && window.location.hostname === 'localhost') {
        console.log('Performance metrics:', performanceData);
      }
      
      // Here you could send metrics to your analytics service
      // Example:
      // sendMetricsToAnalytics(performanceData);
    }, config.reportMetricsInterval);
  }
  
  /**
   * Updates the service configuration
   * @param {Object} newConfig - New configuration options
   */
  function configure(newConfig = {}) {
    Object.assign(config, newConfig);
  }
  
  // Initialize on load
  setupPerformanceReporting();
  
  // Public API
  return {
    // Utilities
    throttle,
    debounce,
    memoize,
    
    // Request optimization
    batchRequest,
    
    // Cache optimization
    cache: OptimizedCache,
    
    // DOM optimization
    dom: DomOptimizer,
    
    // Performance metrics
    trackApiCall,
    collectPerformanceMetrics,
    
    // Configuration
    configure,
    
    // For testing and debugging
    getConfig: () => ({ ...config })
  };
})();

// Make available globally
window.PerformanceOptimizer = PerformanceOptimizer;