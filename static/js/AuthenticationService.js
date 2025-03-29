/**
 * Authentication Service
 * 
 * Handles all client-side authentication operations including:
 * - Login/logout functionality
 * - Token storage and retrieval
 * - Session management
 * - Authentication state detection
 * - Comprehensive error handling with specific error codes
 */

class AuthenticationService {
  constructor() {
    this.TOKEN_KEY = 'auth_token';
    this.USER_KEY = 'auth_user';
    this.TOKEN_EXPIRY_KEY = 'auth_token_expiry';
    this.REFRESH_INTERVAL = 60000; // Check token expiry every minute
    this.SESSION_TIMEOUT_WARNING = 300000; // 5 minutes before expiry to warn user
    
    this.authListeners = [];
    this.initializeRefreshChecker();
    this.errorMessages = {
      'invalid_credentials': 'Invalid username or password. Please check your credentials and try again.',
      'account_locked': 'Your account has been locked due to too many failed attempts. Please contact an administrator.',
      'account_disabled': 'Your account has been disabled. Please contact an administrator.',
      'session_expired': 'Your session has expired. Please log in again to continue.',
      'server_error': 'A server error occurred. Please try again later or contact support if the issue persists.',
      'network_error': 'Could not connect to the server. Please check your internet connection and try again.',
      'permission_denied': 'You do not have permission to access this resource.',
      'invalid_token': 'Your authentication token is invalid. Please log in again.',
      'missing_token': 'No authentication token found. Please log in to continue.'
    };
  }

  /**
   * Initialize the token refresh checker
   * Periodically checks if the token is about to expire and warns the user
   */
  initializeRefreshChecker() {
    // Clear any existing interval
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    // Set up a new interval
    this.refreshInterval = setInterval(() => {
      if (this.isAuthenticated()) {
        const expiry = this.getTokenExpiry();
        const now = Date.now();
        const timeToExpiry = expiry - now;

        // If token is about to expire in the next 5 minutes
        if (timeToExpiry > 0 && timeToExpiry < this.SESSION_TIMEOUT_WARNING) {
          // Show warning to user
          this.showSessionExpiryWarning(Math.floor(timeToExpiry / 60000));
        }

        // If token has expired, log the user out
        if (timeToExpiry <= 0) {
          this.handleSessionExpired();
        }
      }
    }, this.REFRESH_INTERVAL);
  }

  /**
   * Attempt to log in the user
   * 
   * @param {string} username - The username
   * @param {string} password - The user password
   * @param {boolean} rememberMe - Whether to keep the session after browser close
   * @returns {Promise<Object>} Login result with success status and potential error
   */
  async login(username, password, rememberMe = false) {
    try {
      const response = await fetch('/api/v2/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password, remember_me: rememberMe }),
      });

      const data = await response.json();

      if (response.ok && data.token) {
        // Save authentication data
        this.saveAuthData(data.token, data.user, data.expires_at, rememberMe);
        
        // Notify listeners
        this.notifyAuthChange(true);
        
        return { success: true };
      } else {
        // Handle specific error codes with descriptive messages
        const errorCode = data.error_code || 'server_error';
        const errorMessage = this.errorMessages[errorCode] || data.error || 'Authentication failed';
        
        // Log the error for debugging
        console.error('Login error:', errorCode, errorMessage);
        
        return { 
          success: false, 
          error: errorMessage,
          errorCode: errorCode
        };
      }
    } catch (error) {
      // Handle network errors
      console.error('Login request failed:', error);
      
      return { 
        success: false, 
        error: this.errorMessages.network_error,
        errorCode: 'network_error'
      };
    }
  }

  /**
   * Log the user out
   * 
   * @param {boolean} showSessionExpiredMessage - Whether to show session expired message
   * @returns {Promise<Object>} Logout result with success status
   */
  async logout(showSessionExpiredMessage = false) {
    try {
      // Attempt to call logout endpoint if we have a token
      if (this.getAuthToken()) {
        try {
          await fetch('/api/v2/auth/logout', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${this.getAuthToken()}`,
              'Content-Type': 'application/json',
            },
          });
        } catch (e) {
          // If logout request fails, still proceed with local logout
          console.warn('Logout request failed, but proceeding with client-side logout');
        }
      }
      
      // Clear auth data regardless of server response
      this.clearAuthData();
      
      // Notify listeners
      this.notifyAuthChange(false);
      
      // Show session expired message if requested
      if (showSessionExpiredMessage) {
        this.showCustomMessage('Your session has expired. Please log in again to continue.', 'warning');
      }
      
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      
      // Still consider logout successful even if the API call fails
      // because we've cleared the local tokens
      this.clearAuthData();
      this.notifyAuthChange(false);
      
      return { success: true };
    }
  }

  /**
   * Save authentication data to storage
   * 
   * @param {string} token - The authentication token
   * @param {Object} user - The user data
   * @param {number} expiresAt - Token expiration timestamp
   * @param {boolean} persistent - Whether to use localStorage (true) or sessionStorage (false)
   */
  saveAuthData(token, user, expiresAt, persistent = false) {
    const storage = persistent ? localStorage : sessionStorage;
    
    storage.setItem(this.TOKEN_KEY, token);
    
    if (user) {
      storage.setItem(this.USER_KEY, JSON.stringify(user));
    }
    
    if (expiresAt) {
      storage.setItem(this.TOKEN_EXPIRY_KEY, expiresAt);
    } else {
      // Default to 24 hours from now if no expiry provided
      const defaultExpiry = Date.now() + (24 * 60 * 60 * 1000);
      storage.setItem(this.TOKEN_EXPIRY_KEY, defaultExpiry.toString());
    }
  }

  /**
   * Clear all authentication data from storage
   */
  clearAuthData() {
    // Clear from both storage types to ensure complete logout
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
    
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.USER_KEY);
    sessionStorage.removeItem(this.TOKEN_EXPIRY_KEY);
  }

  /**
   * Check if the user is authenticated
   * 
   * @returns {boolean} True if authenticated, false otherwise
   */
  isAuthenticated() {
    const token = this.getAuthToken();
    const expiry = this.getTokenExpiry();
    
    return !!token && expiry > Date.now();
  }

  /**
   * Get the authentication token
   * 
   * @returns {string|null} The auth token or null if not found
   */
  getAuthToken() {
    return localStorage.getItem(this.TOKEN_KEY) || 
           sessionStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Get token expiration timestamp
   * 
   * @returns {number} Expiration timestamp in milliseconds or 0 if not found
   */
  getTokenExpiry() {
    const expiry = localStorage.getItem(this.TOKEN_EXPIRY_KEY) || 
                   sessionStorage.getItem(this.TOKEN_EXPIRY_KEY);
    
    return expiry ? parseInt(expiry, 10) : 0;
  }

  /**
   * Get the authenticated user data
   * 
   * @returns {Object|null} User data or null if not authenticated
   */
  getUser() {
    const userJson = localStorage.getItem(this.USER_KEY) || 
                     sessionStorage.getItem(this.USER_KEY);
    
    try {
      return userJson ? JSON.parse(userJson) : null;
    } catch (e) {
      console.error('Error parsing user data:', e);
      return null;
    }
  }

  /**
   * Check if user has a specific role
   * 
   * @param {string} role - The role to check for
   * @returns {boolean} True if user has the role, false otherwise
   */
  hasRole(role) {
    const user = this.getUser();
    return user && user.roles && user.roles.includes(role);
  }

  /**
   * Check if user has admin permission
   * 
   * @returns {boolean} True if user is admin, false otherwise
   */
  isAdmin() {
    return this.hasRole('admin');
  }

  /**
   * Add a listener for authentication state changes
   * 
   * @param {Function} listener - Function to call on auth state change
   */
  addAuthChangeListener(listener) {
    if (typeof listener === 'function' && !this.authListeners.includes(listener)) {
      this.authListeners.push(listener);
    }
  }

  /**
   * Remove an authentication state change listener
   * 
   * @param {Function} listener - The listener to remove
   */
  removeAuthChangeListener(listener) {
    const index = this.authListeners.indexOf(listener);
    if (index !== -1) {
      this.authListeners.splice(index, 1);
    }
  }

  /**
   * Notify all listeners about authentication state change
   * 
   * @param {boolean} isAuthenticated - Current authentication state
   */
  notifyAuthChange(isAuthenticated) {
    this.authListeners.forEach(listener => {
      try {
        listener(isAuthenticated);
      } catch (e) {
        console.error('Error in auth change listener:', e);
      }
    });
  }

  /**
   * Handle session expired scenario
   */
  handleSessionExpired() {
    // Only perform the logout if currently authenticated
    if (this.isAuthenticated()) {
      this.logout(true).then(() => {
        // Redirect to login page with return URL
        const currentPath = window.location.pathname;
        window.location.href = `/login?return_to=${encodeURIComponent(currentPath)}&expired=1`;
      });
    }
  }

  /**
   * Show a session expiry warning
   * 
   * @param {number} minutesRemaining - Minutes until session expires
   */
  showSessionExpiryWarning(minutesRemaining) {
    // Create or update the warning banner
    let warningBanner = document.getElementById('session-expiry-warning');
    
    if (!warningBanner) {
      warningBanner = document.createElement('div');
      warningBanner.id = 'session-expiry-warning';
      warningBanner.className = 'session-warning-banner';
      
      // Create banner styles if not already in document
      if (!document.getElementById('session-warning-styles')) {
        const style = document.createElement('style');
        style.id = 'session-warning-styles';
        style.textContent = `
          .session-warning-banner {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .session-warning-banner button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
          }
          .session-warning-banner button:hover {
            background-color: #0069d9;
          }
        `;
        document.head.appendChild(style);
      }
      
      document.body.prepend(warningBanner);
    }
    
    // Update the warning text
    warningBanner.innerHTML = `
      <span>Your session will expire in ${minutesRemaining} minute${minutesRemaining !== 1 ? 's' : ''}. Any unsaved changes may be lost.</span>
      <button id="refresh-session-btn">Stay Logged In</button>
    `;
    
    // Add click handler to the refresh button
    document.getElementById('refresh-session-btn').addEventListener('click', () => {
      this.refreshToken();
      warningBanner.remove();
    });
  }

  /**
   * Attempt to refresh the authentication token
   * 
   * @returns {Promise<boolean>} Success status of token refresh
   */
  async refreshToken() {
    try {
      const currentToken = this.getAuthToken();
      
      if (!currentToken) {
        return false;
      }
      
      const response = await fetch('/api/v2/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (response.ok && data.token) {
        // Update token and expiry with refreshed values
        const isPersistent = !!localStorage.getItem(this.TOKEN_KEY);
        this.saveAuthData(data.token, data.user, data.expires_at, isPersistent);
        return true;
      } else {
        // If refresh fails, handle as expired session
        this.handleSessionExpired();
        return false;
      }
    } catch (error) {
      console.error('Token refresh error:', error);
      return false;
    }
  }

  /**
   * Handle authentication errors from API responses
   * 
   * @param {Response} response - The fetch API response object
   * @param {Object} options - Additional options for error handling
   * @returns {Promise<boolean>} False if authentication error was handled, true otherwise
   */
  async handleAuthenticationError(response, options = {}) {
    // Default options
    const { redirectToLogin = true, showMessage = true } = options;
    
    if (response.status === 401) {
      const data = await response.json().catch(() => ({}));
      const errorCode = data.error_code || 'invalid_token';
      
      if (errorCode === 'session_expired' || errorCode === 'invalid_token') {
        // Handle as session expired
        if (redirectToLogin) {
          this.handleSessionExpired();
        } else {
          this.clearAuthData();
          this.notifyAuthChange(false);
        }
        
        return false;
      }
    }
    
    if (response.status === 403) {
      // Handle permission denied
      if (showMessage) {
        this.showCustomMessage(this.errorMessages.permission_denied, 'error');
      }
      
      return false;
    }
    
    // Not an authentication error or was not handled
    return true;
  }

  /**
   * Show a custom message to the user
   * 
   * @param {string} message - The message to display
   * @param {string} type - Message type (info, warning, error, success)
   */
  showCustomMessage(message, type = 'info') {
    // First check if there's a toast system available
    if (window.ToastService) {
      window.ToastService.show(message, { type });
      return;
    }
    
    // Use alert as fallback
    if (type === 'error') {
      alert(`Error: ${message}`);
    } else {
      alert(message);
    }
  }
}

// Create and export a singleton instance
window.AuthenticationService = new AuthenticationService();