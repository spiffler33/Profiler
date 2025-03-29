/**
 * Authentication Error Handler
 * 
 * This script adds robust error handling for authentication issues across the application.
 * It provides visual feedback for auth errors and gracefully handles session expiration.
 */

(function() {
  // Create an error container that will be shown when authentication errors occur
  function createAuthErrorContainer() {
    // Check if container already exists
    if (document.getElementById('auth-error-container')) {
      return;
    }
    
    // Create the container
    const container = document.createElement('div');
    container.id = 'auth-error-container';
    container.className = 'auth-error-container hidden';
    container.setAttribute('role', 'alert');
    container.setAttribute('aria-live', 'assertive');
    
    // Create content
    container.innerHTML = `
      <div class="auth-error-content">
        <div class="auth-error-icon">
          <i class="fa fa-exclamation-triangle" aria-hidden="true"></i>
        </div>
        <div class="auth-error-message">
          <div class="auth-error-title">Authentication Error</div>
          <div class="auth-error-text"></div>
        </div>
        <div class="auth-error-actions">
          <button class="auth-error-login-btn">Login</button>
          <button class="auth-error-dismiss-btn">Dismiss</button>
        </div>
      </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .auth-error-container {
        position: fixed;
        top: 20px;
        right: 20px;
        max-width: 400px;
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
        padding: 0;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        z-index: 9999;
        transition: transform 0.3s ease-in-out, opacity 0.3s ease-in-out;
        transform: translateY(-20px);
        opacity: 0;
      }
      
      .auth-error-container.visible {
        transform: translateY(0);
        opacity: 1;
      }
      
      .auth-error-container.hidden {
        display: none;
      }
      
      .auth-error-content {
        display: flex;
        padding: 15px;
      }
      
      .auth-error-icon {
        margin-right: 15px;
        font-size: 24px;
        color: #721c24;
        flex-shrink: 0;
      }
      
      .auth-error-message {
        flex-grow: 1;
      }
      
      .auth-error-title {
        font-weight: bold;
        margin-bottom: 5px;
      }
      
      .auth-error-text {
        font-size: 14px;
      }
      
      .auth-error-actions {
        display: flex;
        margin-top: 10px;
      }
      
      .auth-error-login-btn, .auth-error-dismiss-btn {
        padding: 6px 12px;
        border-radius: 3px;
        font-size: 14px;
        cursor: pointer;
        margin-left: 10px;
      }
      
      .auth-error-login-btn {
        background-color: #007bff;
        color: white;
        border: none;
      }
      
      .auth-error-login-btn:hover {
        background-color: #0069d9;
      }
      
      .auth-error-dismiss-btn {
        background-color: transparent;
        color: #6c757d;
        border: 1px solid #6c757d;
      }
      
      .auth-error-dismiss-btn:hover {
        background-color: #f8f9fa;
      }
      
      /* Session expiry dialog */
      .session-expiry-dialog {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
      }
      
      .session-expiry-content {
        background-color: white;
        border-radius: 5px;
        width: 100%;
        max-width: 450px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
      }
      
      .session-expiry-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
      }
      
      .session-expiry-icon {
        font-size: 24px;
        color: #f0ad4e;
        margin-right: 15px;
      }
      
      .session-expiry-title {
        font-size: 18px;
        font-weight: bold;
        color: #333;
      }
      
      .session-expiry-message {
        margin-bottom: 20px;
        line-height: 1.5;
        color: #555;
      }
      
      .session-expiry-actions {
        display: flex;
        justify-content: flex-end;
      }
      
      .session-expiry-login-btn {
        background-color: #007bff;
        color: white;
        border: none;
        padding: 8px 15px;
        border-radius: 3px;
        cursor: pointer;
      }
      
      .session-expiry-login-btn:hover {
        background-color: #0069d9;
      }
    `;
    
    document.head.appendChild(style);
    document.body.appendChild(container);
    
    // Add event listeners
    const loginBtn = container.querySelector('.auth-error-login-btn');
    const dismissBtn = container.querySelector('.auth-error-dismiss-btn');
    
    loginBtn.addEventListener('click', () => {
      // Redirect to login page with return URL
      window.location.href = `/login?return_to=${encodeURIComponent(window.location.pathname)}`;
    });
    
    dismissBtn.addEventListener('click', () => {
      hideAuthError();
    });
    
    return container;
  }
  
  // Show authentication error
  function showAuthError(message, errorCode) {
    const container = createAuthErrorContainer();
    const errorText = container.querySelector('.auth-error-text');
    
    // Set error message
    errorText.textContent = message || 'You are not authorized to access this resource.';
    
    // Set error code as data attribute
    if (errorCode) {
      container.setAttribute('data-error-code', errorCode);
    } else {
      container.removeAttribute('data-error-code');
    }
    
    // Show container
    container.classList.remove('hidden');
    
    // Use setTimeout to ensure transition works
    setTimeout(() => {
      container.classList.add('visible');
    }, 10);
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
      hideAuthError();
    }, 10000);
  }
  
  // Hide authentication error
  function hideAuthError() {
    const container = document.getElementById('auth-error-container');
    if (!container) return;
    
    container.classList.remove('visible');
    
    // Wait for transition to complete before hiding
    setTimeout(() => {
      container.classList.add('hidden');
    }, 300);
  }
  
  // Show session expiry dialog
  function showSessionExpiryDialog() {
    // Check if dialog already exists
    if (document.getElementById('session-expiry-dialog')) {
      return;
    }
    
    // Create the dialog
    const dialog = document.createElement('div');
    dialog.id = 'session-expiry-dialog';
    dialog.className = 'session-expiry-dialog';
    
    dialog.innerHTML = `
      <div class="session-expiry-content">
        <div class="session-expiry-header">
          <div class="session-expiry-icon">
            <i class="fa fa-clock-o" aria-hidden="true"></i>
          </div>
          <div class="session-expiry-title">Session Expired</div>
        </div>
        <div class="session-expiry-message">
          Your session has expired due to inactivity. To protect your security, you have been signed out. 
          Please log in again to continue.
        </div>
        <div class="session-expiry-actions">
          <button class="session-expiry-login-btn">Log In Again</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Prevent scrolling of background content
    document.body.style.overflow = 'hidden';
    
    // Add event listener to login button
    const loginBtn = dialog.querySelector('.session-expiry-login-btn');
    loginBtn.addEventListener('click', () => {
      // Redirect to login page with return URL and expired flag
      window.location.href = `/login?return_to=${encodeURIComponent(window.location.pathname)}&expired=1`;
    });
    
    // Focus the login button for keyboard accessibility
    setTimeout(() => loginBtn.focus(), 100);
  }
  
  // Intercept all fetch requests to handle auth errors
  const originalFetch = window.fetch;
  window.fetch = async function(resource, init = {}) {
    try {
      const response = await originalFetch(resource, init);
      
      // Check for authentication errors
      if (response.status === 401) {
        // Clone the response before reading its body
        const clonedResponse = response.clone();
        
        try {
          const data = await clonedResponse.json();
          const errorCode = data.error_code || 'authentication_error';
          
          // Handle session expiry
          if (errorCode === 'session_expired') {
            // If AuthenticationService exists, let it handle
            if (window.AuthenticationService) {
              window.AuthenticationService.handleSessionExpired();
            } else {
              // Otherwise handle directly
              if (window.sessionStorage.getItem('auth_token') || window.localStorage.getItem('auth_token')) {
                window.sessionStorage.removeItem('auth_token');
                window.localStorage.removeItem('auth_token');
                showSessionExpiryDialog();
              }
            }
          } else {
            // For other auth errors, show the message
            const message = data.message || data.error || 'Authentication error';
            showAuthError(message, errorCode);
          }
        } catch (e) {
          // If parsing JSON fails, still show a generic auth error
          showAuthError('Authentication error: Your session may have expired.', 'authentication_error');
        }
      } else if (response.status === 403) {
        // Handle forbidden errors
        showAuthError('Access denied: You don\'t have permission to access this resource.', 'forbidden');
      }
      
      return response;
    } catch (error) {
      // Let original error propagate
      throw error;
    }
  };
  
  // Initialize the auth error handler
  document.addEventListener('DOMContentLoaded', function() {
    // Create the auth error container
    createAuthErrorContainer();
    
    // Listen for custom auth events
    document.addEventListener('auth:error', function(event) {
      showAuthError(event.detail.message, event.detail.errorCode);
    });
    
    document.addEventListener('auth:session-expired', function() {
      showSessionExpiryDialog();
    });
    
    // Check if we need to setup AuthenticationService integration
    if (window.AuthenticationService) {
      // Listen for auth changes
      window.AuthenticationService.addAuthChangeListener(function(isAuthenticated) {
        if (!isAuthenticated) {
          // Check if we're not already on the login page
          if (!window.location.pathname.includes('/login')) {
            // Show auth error if not redirecting
            if (!window.location.search.includes('expired=1')) {
              showAuthError('You have been logged out.', 'logged_out');
            }
          }
        }
      });
    }
  });
  
  // Expose the API globally
  window.AuthErrorHandler = {
    showError: showAuthError,
    hideError: hideAuthError,
    showSessionExpired: showSessionExpiryDialog
  };
})();