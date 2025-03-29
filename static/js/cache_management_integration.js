/**
 * cache_management_integration.js
 * 
 * This script integrates the CacheManagementService with the cache management
 * admin interface. It provides the connection between the API-based cache
 * management and the UI components.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Check if we're on the cache management page
  const cacheTypesContainer = document.getElementById('cache-types-container');
  if (!cacheTypesContainer) return;
  
  // Check if API services are loaded
  const hasApiService = typeof ApiService !== 'undefined';
  const hasCacheManagementService = typeof CacheManagementService !== 'undefined';
  
  if (!hasApiService) {
    console.warn('ApiService not found. Cache Management API integration will be limited.');
  }
  
  if (!hasCacheManagementService) {
    console.warn('CacheManagementService not found. Cache Management API integration will be limited.');
  }
  
  // Initialize the CacheManagementService if available
  if (hasCacheManagementService) {
    CacheManagementService.initialize({
      refreshInterval: 5 * 60 * 1000 // 5 minutes
    });
  }
  
  // Set up integration with LoadingStateManager if available
  if (window.LoadingStateManager) {
    window.addEventListener('cacheManagementLoading', function(event) {
      const { id, isLoading } = event.detail;
      LoadingStateManager.setLoading(`cache-management-${id}`, isLoading, {
        text: `${isLoading ? 'Loading' : 'Loaded'} ${id}...`
      });
    });
  }
  
  // Set up integration with ErrorHandlingService if available
  if (window.ErrorHandlingService) {
    window.addEventListener('cacheManagementError', function(event) {
      const { error, context } = event.detail;
      ErrorHandlingService.handleError(error, 'cache_management', {
        showToast: true,
        metadata: { context }
      });
    });
  }
  
  // Override cache stats loading function
  if (hasCacheManagementService && typeof window.loadCacheStats === 'function') {
    const originalLoadCacheStats = window.loadCacheStats;
    
    window.loadCacheStats = function() {
      CacheManagementService.getCacheStats({ forceRefresh: true })
        .then(data => {
          window.cacheStats = data;
          window.renderCacheTypes(data);
          window.updatePerformanceMetrics(data);
          console.log('Cache stats loaded via CacheManagementService');
        })
        .catch(error => {
          console.error('Error loading cache stats:', error);
          // Fall back to original implementation
          originalLoadCacheStats();
        });
    };
  }
  
  // Override cache entries loading function
  if (hasCacheManagementService && typeof window.loadCacheEntries === 'function') {
    const originalLoadCacheEntries = window.loadCacheEntries;
    
    window.loadCacheEntries = function(cacheType, filter = '') {
      const entriesContainer = document.getElementById('modal-cache-entries');
      entriesContainer.innerHTML = `
        <div class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2">Loading cache entries...</p>
        </div>
      `;
      
      CacheManagementService.getCacheEntries(cacheType, {
        forceRefresh: true,
        filter: filter
      })
        .then(data => {
          window.cacheEntries[cacheType] = data;
          window.renderCacheEntries(data);
          console.log('Cache entries loaded via CacheManagementService');
        })
        .catch(error => {
          console.error('Error loading cache entries:', error);
          // Fall back to original implementation
          originalLoadCacheEntries(cacheType, filter);
        });
    };
  }
  
  // Override cache invalidation function
  if (hasCacheManagementService && typeof window.invalidateCache === 'function') {
    const originalInvalidateCache = window.invalidateCache;
    
    window.invalidateCache = function(cacheType, pattern = '') {
      CacheManagementService.invalidateCache(cacheType, { pattern })
        .then(result => {
          if (result.success) {
            alert(`Successfully invalidated ${result.count} entries from ${window.formatCacheType(cacheType)} cache.`);
            window.loadCacheStats();
            
            // If modal is open, refresh entries
            if (window.selectedCacheType === cacheType) {
              window.loadCacheEntries(cacheType);
            }
            
            console.log('Cache invalidated via CacheManagementService');
          } else {
            alert(`Error invalidating cache: ${result.error || 'Unknown error'}`);
          }
        })
        .catch(error => {
          console.error('Error invalidating cache:', error);
          // Fall back to original implementation
          originalInvalidateCache(cacheType, pattern);
        });
    };
  }
  
  // Override refresh all caches function
  if (hasCacheManagementService && typeof window.refreshAllCaches === 'function') {
    const originalRefreshAllCaches = window.refreshAllCaches;
    
    window.refreshAllCaches = function() {
      CacheManagementService.refreshAllCaches()
        .then(result => {
          if (result.success) {
            alert(`Successfully refreshed all caches.`);
            window.loadCacheStats();
            console.log('All caches refreshed via CacheManagementService');
          } else {
            alert(`Error refreshing caches: ${result.error || 'Unknown error'}`);
          }
        })
        .catch(error => {
          console.error('Error refreshing caches:', error);
          // Fall back to original implementation
          originalRefreshAllCaches();
        });
    };
  }
  
  // Load cache configuration
  function loadCacheConfig() {
    if (!hasCacheManagementService) return;
    
    fetch('/api/v2/admin/cache/config')
      .then(response => response.json())
      .then(config => {
        // Update form fields with current configuration
        document.getElementById('monteCarloCacheSize').value = config.monte_carlo?.max_size || 100;
        document.getElementById('monteCarloCacheTTL').value = config.monte_carlo?.ttl || 3600;
        document.getElementById('apiCacheTTL').value = config.api?.ttl || 300;
        document.getElementById('enableApiCache').checked = config.api?.enabled !== false;
        document.getElementById('persistCache').checked = config.persist !== false;
        
        console.log('Cache configuration loaded');
      })
      .catch(error => {
        console.error('Error loading cache configuration:', error);
      });
  }
  
  // Load the configuration after a short delay
  setTimeout(loadCacheConfig, 500);
  
  console.log('Cache Management API integration initialized successfully');
});