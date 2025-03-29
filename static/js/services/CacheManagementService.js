/**
 * CacheManagementService.js
 * 
 * Service for managing application caches through the API.
 * Provides functionality to view cache statistics, list cache entries,
 * and invalidate cache items selectively or entirely.
 */

class CacheManagementService {
  constructor() {
    this.baseUrl = '/api/v2';
    this.lastStatsRefresh = null;
    this.lastEntriesRefresh = null;
    this.cacheStats = null;
    this.cacheEntries = null;
    
    // Integration with ApiService
    this.apiService = window.ApiService;
    
    // Integration with LoadingStateManager if available
    this.loadingStateManager = window.LoadingStateManager || null;
    
    // Integration with ErrorHandlingService if available
    this.errorHandlingService = window.ErrorHandlingService || null;
    
    // Default cache refresh interval (5 minutes)
    this.refreshInterval = 5 * 60 * 1000;
  }
  
  /**
   * Initialize the service
   * @param {Object} options - Initialization options
   * @param {number} options.refreshInterval - Cache refresh interval in milliseconds
   */
  initialize(options = {}) {
    if (options.refreshInterval) {
      this.refreshInterval = options.refreshInterval;
    }
    
    return this;
  }
  
  /**
   * Get cache statistics for all cache systems in the application
   * @param {Object} options - Options for the request
   * @param {boolean} options.forceRefresh - Whether to force a refresh from server
   * @returns {Promise<Object>} - Cache statistics
   */
  async getCacheStats(options = {}) {
    const forceRefresh = options.forceRefresh || false;
    
    // Check if we have cached stats that aren't expired
    if (!forceRefresh && 
        this.cacheStats && 
        this.lastStatsRefresh && 
        (Date.now() - this.lastStatsRefresh) < this.refreshInterval) {
      return this.cacheStats;
    }
    
    this._setLoading('cache-stats', true);
    
    try {
      // Use ApiService if available
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get('/admin/cache/stats', {
          loadingId: 'cache-stats',
          cacheKey: 'cache-stats',
          useCache: !forceRefresh,
          cacheTTL: this.refreshInterval
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/cache/stats`);
        if (!response.ok) {
          throw new Error(`Error fetching cache stats: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      // Update cache
      this.cacheStats = result;
      this.lastStatsRefresh = Date.now();
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching cache statistics');
      throw error;
    } finally {
      this._setLoading('cache-stats', false);
    }
  }
  
  /**
   * Get cache entries for a specific cache system
   * @param {string} cacheType - Type of cache (e.g., 'monte_carlo', 'api', 'general')
   * @param {Object} options - Options for the request
   * @param {boolean} options.forceRefresh - Whether to force a refresh from server
   * @param {string} options.filter - Optional filter pattern for entries
   * @returns {Promise<Array>} - List of cache entries
   */
  async getCacheEntries(cacheType, options = {}) {
    const forceRefresh = options.forceRefresh || false;
    const filter = options.filter || '';
    
    // Build cache key
    const cacheKey = `cache-entries-${cacheType}${filter ? `-${filter}` : ''}`;
    
    // Check if we have cached entries that aren't expired
    if (!forceRefresh && 
        this.cacheEntries && 
        this.cacheEntries[cacheKey] && 
        this.lastEntriesRefresh && 
        (Date.now() - this.lastEntriesRefresh) < this.refreshInterval) {
      return this.cacheEntries[cacheKey];
    }
    
    this._setLoading(`cache-entries-${cacheType}`, true);
    
    try {
      // Build URL with query params
      let url = `/admin/cache/entries/${cacheType}`;
      if (filter) {
        url += `?filter=${encodeURIComponent(filter)}`;
      }
      
      // Use ApiService if available
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(url, {
          loadingId: `cache-entries-${cacheType}`,
          cacheKey: cacheKey,
          useCache: !forceRefresh,
          cacheTTL: this.refreshInterval
        });
      } else {
        const response = await fetch(`${this.baseUrl}${url}`);
        if (!response.ok) {
          throw new Error(`Error fetching cache entries: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      // Initialize cache entries object if needed
      if (!this.cacheEntries) {
        this.cacheEntries = {};
      }
      
      // Update cache
      this.cacheEntries[cacheKey] = result;
      this.lastEntriesRefresh = Date.now();
      
      return result;
    } catch (error) {
      this._handleError(error, `fetching cache entries for ${cacheType}`);
      throw error;
    } finally {
      this._setLoading(`cache-entries-${cacheType}`, false);
    }
  }
  
  /**
   * Invalidate cache entries
   * @param {string} cacheType - Type of cache (e.g., 'monte_carlo', 'api', 'general')
   * @param {Object} options - Options for the request
   * @param {string} options.pattern - Optional pattern to match cache keys
   * @param {string} options.key - Optional specific key to invalidate
   * @returns {Promise<Object>} - Invalidation result
   */
  async invalidateCache(cacheType, options = {}) {
    const pattern = options.pattern || '';
    const key = options.key || '';
    
    this._setLoading(`invalidate-cache-${cacheType}`, true);
    
    try {
      // Build request data
      const requestData = {
        type: cacheType
      };
      
      if (pattern) {
        requestData.pattern = pattern;
      }
      
      if (key) {
        requestData.key = key;
      }
      
      // Use ApiService if available
      let result;
      
      if (this.apiService) {
        result = await this.apiService.post('/admin/cache/invalidate', requestData, {
          loadingId: `invalidate-cache-${cacheType}`,
          context: 'cache_management'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/cache/invalidate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
          throw new Error(`Error invalidating cache: ${response.statusText}`);
        }
        
        result = await response.json();
      }
      
      // Clear cached data
      this.cacheStats = null;
      this.cacheEntries = null;
      
      return result;
    } catch (error) {
      this._handleError(error, `invalidating cache for ${cacheType}`);
      throw error;
    } finally {
      this._setLoading(`invalidate-cache-${cacheType}`, false);
    }
  }
  
  /**
   * Refresh all caches in the application
   * @returns {Promise<Object>} - Refresh result
   */
  async refreshAllCaches() {
    this._setLoading('refresh-all-caches', true);
    
    try {
      // Use ApiService if available
      let result;
      
      if (this.apiService) {
        result = await this.apiService.post('/admin/cache/refresh', {}, {
          loadingId: 'refresh-all-caches',
          context: 'cache_management'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/cache/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`Error refreshing caches: ${response.statusText}`);
        }
        
        result = await response.json();
      }
      
      // Clear cached data
      this.cacheStats = null;
      this.cacheEntries = null;
      
      return result;
    } catch (error) {
      this._handleError(error, 'refreshing all caches');
      throw error;
    } finally {
      this._setLoading('refresh-all-caches', false);
    }
  }
  
  /**
   * Set loading state for operations
   * @private
   * @param {string} id - Loading operation ID
   * @param {boolean} isLoading - Whether loading is active
   */
  _setLoading(id, isLoading) {
    // Use LoadingStateManager if available
    if (this.loadingStateManager) {
      this.loadingStateManager.setLoading(`cache-management-${id}`, isLoading, {
        text: `${isLoading ? 'Loading' : 'Loaded'} ${id}...`
      });
    }
    
    // Dispatch event for legacy components
    const event = new CustomEvent('cacheManagementLoading', {
      detail: { id, isLoading }
    });
    window.dispatchEvent(event);
  }
  
  /**
   * Handle errors from API requests
   * @private
   * @param {Error} error - Error object
   * @param {string} context - Error context
   */
  _handleError(error, context) {
    console.error(`Error ${context}:`, error);
    
    // Use ErrorHandlingService if available
    if (this.errorHandlingService) {
      this.errorHandlingService.handleError(error, 'cache_management', {
        showToast: true,
        metadata: { context }
      });
      return;
    }
    
    // Dispatch event for legacy components
    const event = new CustomEvent('cacheManagementError', {
      detail: { error, context }
    });
    window.dispatchEvent(event);
  }
}

// Create singleton instance
const cacheManagementService = new CacheManagementService();

// Export as both module and global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = cacheManagementService;
} else {
  window.CacheManagementService = cacheManagementService;
}