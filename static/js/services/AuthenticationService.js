/**
 * Authentication Service
 * 
 * Manages authentication for the frontend application including:
 * - Login and logout functionality
 * - Token storage and management
 * - Authentication state tracking
 * - Session expiration handling
 */

class AuthenticationService {
  constructor() {
    this.TOKEN_KEY = 'auth_token';
    this.USER_KEY = 'auth_user';
    this.EXPIRY_KEY = 'auth_expiry';
    this.AUTH_EVENT = 'auth_state_changed';
    this.isAuthenticated = this.checkAuthentication();
    
    // Check for token expiration periodically
    this.startExpiryCheck();
  }

  /**
   * Check if user is currently authenticated
   * @returns {boolean} Authentication status
   */
  checkAuthentication() {
    const token = this.getToken();
    const expiry = localStorage.getItem(this.EXPIRY_KEY);
    
    if (!token) return false;
    
    // Check if token has expired
    if (expiry && new Date(expiry) < new Date()) {
      this.logout('Session expired');
      return false;
    }
    
    return true;
  }

  /**
   * Get current authentication token
   * @returns {string|null} Current token or null if not authenticated
   */
  getToken() {
    return localStorage.getItem(this.TOKEN_KEY) || sessionStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Get current authenticated username
   * @returns {string|null} Current username or null if not authenticated
   */
  getUser() {
    return localStorage.getItem(this.USER_KEY) || sessionStorage.getItem(this.USER_KEY);
  }

  /**
   * Store authentication information
   * @param {string} token - Authentication token
   * @param {string} username - Authenticated username
   * @param {boolean} rememberMe - Whether to persist authentication
   * @param {number} expiryMinutes - Session duration in minutes
   */
  setAuthentication(token, username, rememberMe = false, expiryMinutes = 60) {
    // Calculate expiry date
    const expiryDate = new Date();
    expiryDate.setMinutes(expiryDate.getMinutes() + expiryMinutes);
    
    // Store in appropriate storage based on remember me setting
    const storage = rememberMe ? localStorage : sessionStorage;
    
    storage.setItem(this.TOKEN_KEY, token);
    storage.setItem(this.USER_KEY, username);
    localStorage.setItem(this.EXPIRY_KEY, expiryDate.toISOString());
    
    this.isAuthenticated = true;
    this.dispatchAuthEvent({ type: 'login', user: username });
  }

  /**
   * Clear authentication information
   * @param {string} reason - Optional reason for logout
   */
  logout(reason = 'user_logout') {
    const username = this.getUser();
    
    // Clear both storage locations to be safe
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.EXPIRY_KEY);
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.USER_KEY);
    
    this.isAuthenticated = false;
    this.dispatchAuthEvent({ type: 'logout', reason, user: username });
  }

  /**
   * Login with username and password
   * @param {string} username - Username to authenticate
   * @param {string} password - Password to authenticate
   * @param {boolean} rememberMe - Whether to persist authentication
   * @returns {Promise<Object>} Authentication result
   */
  async login(username, password, rememberMe = false) {
    try {
      // Create token for basic auth (username:password base64 encoded)
      const token = btoa(`${username}:${password}`);
      
      // Test authentication with admin health endpoint
      const response = await fetch('/api/v2/admin/health', {
        headers: {
          'Authorization': `Basic ${token}`
        }
      });
      
      if (response.ok) {
        // Store authentication
        this.setAuthentication(token, username, rememberMe);
        return { success: true, user: username };
      } else if (response.status === 401) {
        return { success: false, error: 'Invalid username or password' };
      } else {
        return { success: false, error: 'Authentication failed. Please try again.' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Authentication service unavailable' };
    }
  }

  /**
   * Handle authentication for API requests
   * @param {Object} headers - Request headers to modify
   * @returns {Object} Modified headers with authentication
   */
  addAuthToHeaders(headers = {}) {
    const token = this.getToken();
    if (token) {
      return {
        ...headers,
        'Authorization': `Basic ${token}`
      };
    }
    return headers;
  }

  /**
   * Dispatch authentication state change event
   * @param {Object} detail - Event details
   */
  dispatchAuthEvent(detail) {
    const event = new CustomEvent(this.AUTH_EVENT, { detail });
    window.dispatchEvent(event);
  }

  /**
   * Start periodic check for token expiration
   * Checks every minute if the token has expired
   */
  startExpiryCheck() {
    setInterval(() => {
      if (this.isAuthenticated) {
        this.checkAuthentication();
      }
    }, 60000); // Check every minute
  }

  /**
   * Subscribe to authentication state changes
   * @param {Function} callback - Function to call when auth state changes
   * @returns {Function} Unsubscribe function
   */
  subscribe(callback) {
    const handler = (event) => callback(event.detail);
    window.addEventListener(this.AUTH_EVENT, handler);
    return () => window.removeEventListener(this.AUTH_EVENT, handler);
  }

  /**
   * Extend current session
   * @param {number} expiryMinutes - Additional minutes to extend session
   */
  extendSession(expiryMinutes = 60) {
    if (!this.isAuthenticated) return;
    
    const expiryDate = new Date();
    expiryDate.setMinutes(expiryDate.getMinutes() + expiryMinutes);
    localStorage.setItem(this.EXPIRY_KEY, expiryDate.toISOString());
  }
}

// Export singleton instance
const authService = new AuthenticationService();
export default authService;