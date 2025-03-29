/**
 * ParameterAdminService.js
 * 
 * This service handles the integration with the parameter management API endpoints.
 * It provides functionality for retrieving, creating, updating, and deleting parameters,
 * as well as managing user parameter overrides and the audit log.
 */

class ParameterAdminService {
  constructor() {
    this.baseUrl = '/api/v2';
    this.cachedParameters = null;
    this.cachedAuditLog = null;
    this.lastParameterRefresh = null;
    this.lastAuditRefresh = null;
    
    // Integration with ApiService
    this.apiService = window.ApiService;
    
    // Integration with LoadingStateManager if available
    this.loadingStateManager = window.LoadingStateManager || null;
    
    // Integration with ErrorHandlingService if available
    this.errorHandlingService = window.ErrorHandlingService || null;
    
    // Default cache timeout (10 minutes)
    this.cacheTTL = 10 * 60 * 1000;
  }
  
  /**
   * Initialize the service
   * @param {Object} options - Initialization options
   * @param {number} options.cacheTTL - Cache TTL in milliseconds
   * @returns {ParameterAdminService} - Service instance
   */
  initialize(options = {}) {
    if (options.cacheTTL) {
      this.cacheTTL = options.cacheTTL;
    }
    
    // Initialize event listeners and subscription hooks
    this._setupEventHandlers();
    
    return this;
  }
  
  /**
   * Get all parameters
   * @param {Object} options - Request options
   * @param {boolean} options.forceRefresh - Whether to force a refresh
   * @param {string} options.search - Search term to filter parameters
   * @param {string} options.category - Category to filter parameters
   * @returns {Promise<Object>} - Parameters and parameter tree
   */
  async getParameters(options = {}) {
    const forceRefresh = options.forceRefresh || false;
    const search = options.search || '';
    const category = options.category || '';
    
    // Check if we have cached parameters and they're not expired
    if (!forceRefresh && 
        this.cachedParameters && 
        this.lastParameterRefresh && 
        (Date.now() - this.lastParameterRefresh) < this.cacheTTL) {
      
      // Filter cached parameters if needed
      if (search || category) {
        return this._filterParameters(this.cachedParameters, search, category);
      }
      
      return this.cachedParameters;
    }
    
    // Set loading state
    this._setLoading('parameters', true);
    
    try {
      // Build query string
      let queryParams = '';
      if (search) {
        queryParams += `search=${encodeURIComponent(search)}`;
      }
      if (category) {
        queryParams += queryParams ? '&' : '';
        queryParams += `category=${encodeURIComponent(category)}`;
      }
      
      let endpoint = '/admin/parameters';
      if (queryParams) {
        endpoint += `?${queryParams}`;
      }
      
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(endpoint, {
          loadingId: 'parameters-admin',
          cacheKey: `parameters-admin${queryParams ? '-filtered' : ''}`,
          useCache: !forceRefresh
        });
      } else {
        const response = await fetch(`${this.baseUrl}${endpoint}`);
        if (!response.ok) {
          throw new Error(`Error fetching parameters: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      // Cache the result
      this.cachedParameters = result;
      this.lastParameterRefresh = Date.now();
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching parameters');
      throw error;
    } finally {
      this._setLoading('parameters', false);
    }
  }
  
  /**
   * Get parameter details
   * @param {string} path - Parameter path
   * @returns {Promise<Object>} - Parameter details
   */
  async getParameterDetails(path) {
    if (!path) {
      throw new Error('Parameter path is required');
    }
    
    this._setLoading(`parameter-${path}`, true);
    
    try {
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(`/admin/parameters/${encodeURIComponent(path)}`, {
          loadingId: `parameter-details-${path}`,
          cacheKey: `parameter-details-${path}`,
          useCache: true,
          cacheTTL: this.cacheTTL
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/${encodeURIComponent(path)}`);
        if (!response.ok) {
          throw new Error(`Error fetching parameter details: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching parameter details');
      throw error;
    } finally {
      this._setLoading(`parameter-${path}`, false);
    }
  }
  
  /**
   * Get parameter history
   * @param {string} path - Parameter path
   * @returns {Promise<Array>} - Parameter history
   */
  async getParameterHistory(path) {
    if (!path) {
      throw new Error('Parameter path is required');
    }
    
    this._setLoading(`parameter-history-${path}`, true);
    
    try {
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(`/admin/parameters/history/${encodeURIComponent(path)}`, {
          loadingId: `parameter-history-${path}`,
          cacheKey: `parameter-history-${path}`,
          useCache: true,
          cacheTTL: this.cacheTTL
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/history/${encodeURIComponent(path)}`);
        if (!response.ok) {
          throw new Error(`Error fetching parameter history: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching parameter history');
      throw error;
    } finally {
      this._setLoading(`parameter-history-${path}`, false);
    }
  }
  
  /**
   * Get parameter impact and relationships
   * @param {string} path - Parameter path
   * @returns {Promise<Object>} - Parameter impact information
   */
  async getParameterImpact(path) {
    if (!path) {
      throw new Error('Parameter path is required');
    }
    
    this._setLoading(`parameter-impact-${path}`, true);
    
    try {
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(`/admin/parameters/impact/${encodeURIComponent(path)}`, {
          loadingId: `parameter-impact-${path}`,
          cacheKey: `parameter-impact-${path}`,
          useCache: true,
          cacheTTL: this.cacheTTL
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/impact/${encodeURIComponent(path)}`);
        if (!response.ok) {
          throw new Error(`Error fetching parameter impact: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching parameter impact');
      throw error;
    } finally {
      this._setLoading(`parameter-impact-${path}`, false);
    }
  }
  
  /**
   * Get related parameters
   * @param {string} path - Parameter path
   * @returns {Promise<Array>} - Related parameters
   */
  async getRelatedParameters(path) {
    if (!path) {
      throw new Error('Parameter path is required');
    }
    
    this._setLoading(`parameter-related-${path}`, true);
    
    try {
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(`/admin/parameters/related/${encodeURIComponent(path)}`, {
          loadingId: `parameter-related-${path}`,
          cacheKey: `parameter-related-${path}`,
          useCache: true,
          cacheTTL: this.cacheTTL
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/related/${encodeURIComponent(path)}`);
        if (!response.ok) {
          throw new Error(`Error fetching related parameters: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching related parameters');
      throw error;
    } finally {
      this._setLoading(`parameter-related-${path}`, false);
    }
  }
  
  /**
   * Get audit log
   * @param {Object} options - Filtering options
   * @param {boolean} options.forceRefresh - Whether to force a refresh
   * @param {string} options.search - Search term to filter log entries
   * @param {string} options.action - Action type to filter (access, change)
   * @returns {Promise<Array>} - Audit log entries
   */
  async getAuditLog(options = {}) {
    const forceRefresh = options.forceRefresh || false;
    const search = options.search || '';
    const action = options.action || '';
    
    // Check if we have cached audit log and it's not expired
    if (!forceRefresh && 
        this.cachedAuditLog && 
        this.lastAuditRefresh && 
        (Date.now() - this.lastAuditRefresh) < this.cacheTTL && 
        !search && !action) {
      
      return this.cachedAuditLog;
    }
    
    // Set loading state
    this._setLoading('audit-log', true);
    
    try {
      // Build query string
      let queryParams = '';
      if (search) {
        queryParams += `search=${encodeURIComponent(search)}`;
      }
      if (action) {
        queryParams += queryParams ? '&' : '';
        queryParams += `action=${encodeURIComponent(action)}`;
      }
      
      let endpoint = '/admin/parameters/audit';
      if (queryParams) {
        endpoint += `?${queryParams}`;
      }
      
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(endpoint, {
          loadingId: 'audit-log-admin',
          cacheKey: `audit-log-admin${queryParams ? '-filtered' : ''}`,
          useCache: !forceRefresh
        });
      } else {
        const response = await fetch(`${this.baseUrl}${endpoint}`);
        if (!response.ok) {
          throw new Error(`Error fetching audit log: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      // Only cache unfiltered results
      if (!search && !action) {
        this.cachedAuditLog = result;
        this.lastAuditRefresh = Date.now();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching audit log');
      throw error;
    } finally {
      this._setLoading('audit-log', false);
    }
  }
  
  /**
   * Get profiles for user parameter management
   * @returns {Promise<Array>} - Profiles
   */
  async getProfiles() {
    this._setLoading('profiles', true);
    
    try {
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get('/admin/profiles', {
          loadingId: 'profiles-admin',
          cacheKey: 'profiles-admin',
          useCache: true,
          cacheTTL: this.cacheTTL
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/profiles`);
        if (!response.ok) {
          throw new Error(`Error fetching profiles: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching profiles');
      throw error;
    } finally {
      this._setLoading('profiles', false);
    }
  }
  
  /**
   * Get user parameter overrides
   * @param {string} profileId - Profile ID
   * @returns {Promise<Object>} - User parameter overrides
   */
  async getUserParameters(profileId) {
    if (!profileId) {
      throw new Error('Profile ID is required');
    }
    
    this._setLoading(`user-parameters-${profileId}`, true);
    
    try {
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.get(`/admin/parameters/user/${profileId}`, {
          loadingId: `user-parameters-${profileId}`,
          cacheKey: `user-parameters-${profileId}`,
          useCache: true,
          cacheTTL: this.cacheTTL
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/user/${profileId}`);
        if (!response.ok) {
          throw new Error(`Error fetching user parameters: ${response.statusText}`);
        }
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'fetching user parameters');
      throw error;
    } finally {
      this._setLoading(`user-parameters-${profileId}`, false);
    }
  }
  
  /**
   * Create a new parameter
   * @param {Object} parameter - Parameter data
   * @param {string} parameter.path - Parameter path
   * @param {*} parameter.value - Parameter value
   * @param {string} parameter.description - Parameter description
   * @param {string} parameter.source - Parameter source
   * @param {boolean} parameter.is_editable - Whether the parameter is user-editable
   * @returns {Promise<Object>} - API response
   */
  async createParameter(parameter) {
    if (!parameter || !parameter.path || parameter.value === undefined) {
      throw new Error('Parameter path and value are required');
    }
    
    this._setLoading('create-parameter', true);
    
    try {
      // Parse the parameter value if it's a string
      const paramData = {
        ...parameter,
        value: this._parseParameterValue(parameter.value)
      };
      
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.post('/admin/parameters', paramData, {
          loadingId: 'create-parameter',
          context: 'parameter_admin'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(paramData)
        });
        
        if (!response.ok) {
          throw new Error(`Error creating parameter: ${response.statusText}`);
        }
        
        result = await response.json();
      }
      
      // Clear cached parameters
      this.cachedParameters = null;
      
      return result;
    } catch (error) {
      this._handleError(error, 'creating parameter');
      throw error;
    } finally {
      this._setLoading('create-parameter', false);
    }
  }
  
  /**
   * Update an existing parameter
   * @param {string} path - Parameter path
   * @param {Object} parameter - Updated parameter data
   * @param {*} parameter.value - Parameter value
   * @param {string} parameter.description - Parameter description
   * @param {string} parameter.source - Parameter source
   * @param {boolean} parameter.is_editable - Whether the parameter is user-editable
   * @returns {Promise<Object>} - API response
   */
  async updateParameter(path, parameter) {
    if (!path || !parameter || parameter.value === undefined) {
      throw new Error('Parameter path and value are required');
    }
    
    this._setLoading(`update-parameter-${path}`, true);
    
    try {
      // Parse the parameter value if it's a string
      const paramData = {
        ...parameter,
        value: this._parseParameterValue(parameter.value)
      };
      
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.put(`/admin/parameters/${encodeURIComponent(path)}`, paramData, {
          loadingId: `update-parameter-${path}`,
          context: 'parameter_admin'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/${encodeURIComponent(path)}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(paramData)
        });
        
        if (!response.ok) {
          throw new Error(`Error updating parameter: ${response.statusText}`);
        }
        
        result = await response.json();
      }
      
      // Clear cached parameters
      this.cachedParameters = null;
      
      return result;
    } catch (error) {
      this._handleError(error, 'updating parameter');
      throw error;
    } finally {
      this._setLoading(`update-parameter-${path}`, false);
    }
  }
  
  /**
   * Delete a parameter
   * @param {string} path - Parameter path
   * @returns {Promise<Object>} - API response
   */
  async deleteParameter(path) {
    if (!path) {
      throw new Error('Parameter path is required');
    }
    
    this._setLoading(`delete-parameter-${path}`, true);
    
    try {
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.delete(`/admin/parameters/${encodeURIComponent(path)}`, {
          loadingId: `delete-parameter-${path}`,
          context: 'parameter_admin'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/${encodeURIComponent(path)}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`Error deleting parameter: ${response.statusText}`);
        }
        
        result = await response.json();
      }
      
      // Clear cached parameters
      this.cachedParameters = null;
      
      return result;
    } catch (error) {
      this._handleError(error, 'deleting parameter');
      throw error;
    } finally {
      this._setLoading(`delete-parameter-${path}`, false);
    }
  }
  
  /**
   * Update a user parameter override
   * @param {string} profileId - Profile ID
   * @param {string} path - Parameter path
   * @param {*} value - Parameter value
   * @returns {Promise<Object>} - API response
   */
  async updateUserParameter(profileId, path, value) {
    if (!profileId || !path || value === undefined) {
      throw new Error('Profile ID, parameter path, and value are required');
    }
    
    this._setLoading(`update-user-parameter-${profileId}-${path}`, true);
    
    try {
      const paramData = {
        path,
        value: this._parseParameterValue(value)
      };
      
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.post(`/admin/parameters/user/${profileId}`, paramData, {
          loadingId: `update-user-parameter-${profileId}-${path}`,
          context: 'parameter_admin'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/user/${profileId}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(paramData)
        });
        
        if (!response.ok) {
          throw new Error(`Error updating user parameter: ${response.statusText}`);
        }
        
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'updating user parameter');
      throw error;
    } finally {
      this._setLoading(`update-user-parameter-${profileId}-${path}`, false);
    }
  }
  
  /**
   * Reset a user parameter override
   * @param {string} profileId - Profile ID
   * @param {string} path - Parameter path
   * @returns {Promise<Object>} - API response
   */
  async resetUserParameter(profileId, path) {
    if (!profileId || !path) {
      throw new Error('Profile ID and parameter path are required');
    }
    
    this._setLoading(`reset-user-parameter-${profileId}-${path}`, true);
    
    try {
      const paramData = { path };
      
      // Use ApiService if available, otherwise use fetch
      let result;
      
      if (this.apiService) {
        result = await this.apiService.post(`/admin/parameters/user/${profileId}/reset`, paramData, {
          loadingId: `reset-user-parameter-${profileId}-${path}`,
          context: 'parameter_admin'
        });
      } else {
        const response = await fetch(`${this.baseUrl}/admin/parameters/user/${profileId}/reset`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(paramData)
        });
        
        if (!response.ok) {
          throw new Error(`Error resetting user parameter: ${response.statusText}`);
        }
        
        result = await response.json();
      }
      
      return result;
    } catch (error) {
      this._handleError(error, 'resetting user parameter');
      throw error;
    } finally {
      this._setLoading(`reset-user-parameter-${profileId}-${path}`, false);
    }
  }
  
  /**
   * Clear parameter cache
   */
  clearCache() {
    this.cachedParameters = null;
    this.cachedAuditLog = null;
    this.lastParameterRefresh = null;
    this.lastAuditRefresh = null;
    
    // Also clear ApiService cache if available
    if (this.apiService && typeof this.apiService.clearCache === 'function') {
      this.apiService.clearCache(/^parameters-admin|^audit-log-admin|^parameter-/);
    }
  }
  
  /**
   * Filter parameters based on search and category
   * @private
   * @param {Object} parametersData - Parameters data
   * @param {string} search - Search term
   * @param {string} category - Category filter
   * @returns {Object} - Filtered parameters data
   */
  _filterParameters(parametersData, search, category) {
    if (!parametersData || !parametersData.parameters) {
      return parametersData;
    }
    
    const searchLower = search.toLowerCase();
    const categoryLower = category.toLowerCase();
    
    // Filter parameters
    const filteredParams = parametersData.parameters.filter(param => {
      // Search term filter
      const matchesSearch = !searchLower || 
        param.path.toLowerCase().includes(searchLower) || 
        (param.description && param.description.toLowerCase().includes(searchLower));
      
      // Category filter
      const matchesCategory = !categoryLower || param.path.toLowerCase().startsWith(categoryLower);
      
      return matchesSearch && matchesCategory;
    });
    
    // Return filtered data
    return {
      parameters: filteredParams,
      tree: parametersData.tree // Keep the original tree for now
    };
  }
  
  /**
   * Parse parameter value from string
   * @private
   * @param {*} value - Value to parse
   * @returns {*} - Parsed value
   */
  _parseParameterValue(value) {
    // If value is not a string, return as is
    if (typeof value !== 'string') {
      return value;
    }
    
    // Try to detect the value type
    const valueStr = value.trim();
    
    if (valueStr === 'null' || valueStr === '') {
      return null;
    }
    
    if (valueStr === 'true') {
      return true;
    }
    
    if (valueStr === 'false') {
      return false;
    }
    
    // Check if it's a number
    if (!isNaN(valueStr) && valueStr !== '') {
      return parseFloat(valueStr);
    }
    
    // Check if it's JSON
    try {
      if ((valueStr.startsWith('{') && valueStr.endsWith('}')) || 
          (valueStr.startsWith('[') && valueStr.endsWith(']'))) {
        return JSON.parse(valueStr);
      }
    } catch (e) {
      // Not valid JSON, continue as string
    }
    
    // Default to string
    return valueStr;
  }
  
  /**
   * Set up event handlers for communication with other services
   * @private
   */
  _setupEventHandlers() {
    // Set up event bus subscriptions if available
    if (window.dataEventBus) {
      window.dataEventBus.subscribe('parameters:refresh', () => this.clearCache());
    }
    
    // Add window-level event handlers for legacy components
    window.addEventListener('refreshParameters', () => this.clearCache());
  }
  
  /**
   * Set loading state for a specific operation
   * @private
   * @param {string} id - Loading state ID
   * @param {boolean} isLoading - Whether loading is active
   */
  _setLoading(id, isLoading) {
    // Use LoadingStateManager if available
    if (this.loadingStateManager) {
      this.loadingStateManager.setLoading(`parameter-admin-${id}`, isLoading, {
        text: `${isLoading ? 'Loading' : 'Loaded'} ${id}...`
      });
    }
    
    // Emit loading event for legacy components
    const event = new CustomEvent('parameterAdminLoading', {
      detail: { id, isLoading }
    });
    window.dispatchEvent(event);
  }
  
  /**
   * Handle errors
   * @private
   * @param {Error} error - Error object
   * @param {string} context - Error context
   */
  _handleError(error, context) {
    console.error(`Error ${context}:`, error);
    
    // Use ErrorHandlingService if available
    if (this.errorHandlingService) {
      this.errorHandlingService.handleError(error, 'parameter_admin', {
        showToast: true,
        metadata: { context }
      });
      return;
    }
    
    // Emit error event for legacy components
    const event = new CustomEvent('parameterAdminError', {
      detail: { error, context }
    });
    window.dispatchEvent(event);
  }
}

// Create singleton instance
const parameterAdminService = new ParameterAdminService();

// Export as both module and global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = parameterAdminService;
} else {
  window.ParameterAdminService = parameterAdminService;
}