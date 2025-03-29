/**
 * ProfileEditForm - Component for editing existing user profiles
 * 
 * This component connects to the /api/v2/profiles/{id} PUT endpoint to update
 * existing profile information. Features include:
 * - Form validation and error handling
 * - Unsaved changes detection and warning
 * - Optimistic updates for responsive UI feedback
 * - API integration with ErrorHandlingService
 * - Loading states via LoadingStateManager
 */

class ProfileEditForm {
  /**
   * Constructor for the ProfileEditForm component
   * @param {string} containerId - ID of the container element
   * @param {Object} options - Configuration options
   */
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Container element with ID "${containerId}" not found`);
      return;
    }

    // Default options
    this.options = {
      profileId: null,
      loadingId: `profile-edit-${containerId}`,
      redirectOnUpdate: false,
      redirectUrl: '',
      saveButtonText: 'Save Changes',
      cancelButtonText: 'Cancel',
      promptOnUnsavedChanges: true,
      autoLoadProfile: true,
      ...options
    };

    // State
    this.state = {
      originalData: null,
      formData: {
        name: '',
        email: '',
        age: '',
        occupation: '',
        household_size: '1',
        currency: 'INR',
      },
      hasChanges: false,
      isLoading: false,
      errors: {},
      isSubmitting: false,
      submitSuccess: false,
      apiError: null
    };

    // Bind methods
    this.fetchProfileData = this.fetchProfileData.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.updateProfile = this.updateProfile.bind(this);
    this.checkForChanges = this.checkForChanges.bind(this);
    this.resetForm = this.resetForm.bind(this);
    this.validateForm = this.validateForm.bind(this);
    this.render = this.render.bind(this);
    this.warnOnUnsavedChanges = this.warnOnUnsavedChanges.bind(this);
    this.handleCancel = this.handleCancel.bind(this);

    // Initialize
    this.init();
  }

  /**
   * Initialize the component
   */
  init() {
    // Get profile ID from options or URL
    const profileId = this.options.profileId || this.getProfileIdFromUrl();
    
    if (!profileId) {
      this.state.apiError = new Error('No profile ID provided');
      this.render();
      return;
    }

    this.options.profileId = profileId;
    
    // Create initial loading state
    this.container.innerHTML = '<div class="profile-edit-loader">Loading profile data...</div>';
    window.LoadingStateManager.setLoading(this.options.loadingId, true, {
      text: 'Loading profile data...'
    });

    // Set up unsaved changes warning
    if (this.options.promptOnUnsavedChanges) {
      window.addEventListener('beforeunload', this.warnOnUnsavedChanges);
    }

    // Load profile data if autoLoadProfile is true
    if (this.options.autoLoadProfile) {
      this.fetchProfileData();
    }
  }

  /**
   * Extract profile ID from URL if present
   * @returns {string|null} Profile ID from URL
   */
  getProfileIdFromUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('profile_id') || urlParams.get('id');
  }

  /**
   * Fetch profile data from the API
   */
  async fetchProfileData() {
    if (!this.options.profileId) return;

    this.state.isLoading = true;
    window.LoadingStateManager.setLoading(this.options.loadingId, true, {
      text: 'Loading profile data...'
    });
    
    this.render();
    
    try {
      const profile = await window.ApiService.getProfile(this.options.profileId, {
        loadingId: this.options.loadingId
      });
      
      // Convert applicable fields to strings for form inputs
      const formData = {
        name: profile.name || '',
        email: profile.email || '',
        age: profile.age ? profile.age.toString() : '',
        occupation: profile.occupation || '',
        household_size: profile.household_size ? profile.household_size.toString() : '1',
        currency: profile.currency || 'INR',
      };
      
      this.state.originalData = { ...formData };
      this.state.formData = { ...formData };
      this.state.apiError = null;
      this.state.hasChanges = false;
    } catch (error) {
      this.state.apiError = error;
      
      // Handle error with ErrorHandlingService
      window.ErrorHandlingService.handleError(error, 'profile_edit_fetch', {
        showToast: true,
        retryAction: this.fetchProfileData,
        metadata: { profileId: this.options.profileId }
      });
    } finally {
      this.state.isLoading = false;
      window.LoadingStateManager.setLoading(this.options.loadingId, false);
      this.render();
    }
  }

  /**
   * Handle form input changes
   * @param {Event} event - Input change event
   */
  handleInputChange(event) {
    const { name, value, type } = event.target;
    const inputValue = type === 'checkbox' ? event.target.checked : value;
    
    // Update form data
    this.state.formData = {
      ...this.state.formData,
      [name]: inputValue
    };
    
    // Clear error for this field if any
    if (this.state.errors[name]) {
      this.state.errors = {
        ...this.state.errors,
        [name]: null
      };
    }
    
    // Check for changes between original and current data
    this.checkForChanges();
    
    // Re-render
    this.render();
  }

  /**
   * Check for changes between original and current form data
   */
  checkForChanges() {
    if (!this.state.originalData) return;
    
    const { originalData, formData } = this.state;
    let hasChanges = false;
    
    // Compare each field
    for (const key in originalData) {
      if (originalData[key] !== formData[key]) {
        hasChanges = true;
        break;
      }
    }
    
    this.state.hasChanges = hasChanges;
  }

  /**
   * Reset form to original data
   */
  resetForm() {
    if (this.state.originalData) {
      this.state.formData = { ...this.state.originalData };
      this.state.hasChanges = false;
      this.state.errors = {};
      this.render();
    }
  }

  /**
   * Validate the form
   * @returns {Object} Validation errors
   */
  validateForm() {
    const { formData } = this.state;
    const errors = {};
    
    // Validate name
    if (!formData.name || formData.name.trim() === '') {
      errors.name = 'Name is required';
    } else if (formData.name.length < 2) {
      errors.name = 'Name must be at least 2 characters';
    }
    
    // Validate email
    if (!formData.email || formData.email.trim() === '') {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    // Validate age if provided
    if (formData.age) {
      const age = parseInt(formData.age, 10);
      if (isNaN(age) || age < 18 || age > 120) {
        errors.age = 'Please enter a valid age between 18 and 120';
      }
    }
    
    // Validate household size
    if (!formData.household_size) {
      errors.household_size = 'Please select a household size';
    }
    
    // Validate currency
    if (!formData.currency) {
      errors.currency = 'Please select a preferred currency';
    }
    
    return errors;
  }

  /**
   * Handle form submission
   * @param {Event} event - Form submission event
   */
  async handleSubmit(event) {
    event.preventDefault();
    
    // Validate form
    const errors = this.validateForm();
    this.state.errors = errors;
    
    if (Object.keys(errors).length > 0) {
      this.render();
      
      // Scroll to first error
      const firstErrorField = document.querySelector('.has-error');
      if (firstErrorField) {
        firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      
      return;
    }
    
    // If no changes, don't submit
    if (!this.state.hasChanges) {
      window.ErrorHandlingService.showErrorToast(
        'No changes to save', 
        { level: 'info', duration: 3000 }
      );
      return;
    }
    
    // Submit form
    this.updateProfile();
  }

  /**
   * Update profile via API
   */
  async updateProfile() {
    if (!this.options.profileId) return;
    
    this.state.isSubmitting = true;
    this.render();
    
    window.LoadingStateManager.setLoading(this.options.loadingId, true, {
      text: 'Saving changes...'
    });
    
    try {
      // Prepare data for API - convert string values to appropriate types
      const profileData = {
        ...this.state.formData,
        // Convert household_size to number if it's a number string
        household_size: isNaN(parseInt(this.state.formData.household_size, 10)) 
          ? this.state.formData.household_size 
          : parseInt(this.state.formData.household_size, 10),
        // Convert age to number if provided
        age: this.state.formData.age ? parseInt(this.state.formData.age, 10) : null
      };
      
      // Optimistic update - assume update will succeed
      this.state.originalData = { ...this.state.formData };
      this.state.hasChanges = false;
      this.state.submitSuccess = true;
      
      // Call API
      const result = await window.ApiService.updateProfile(this.options.profileId, profileData, {
        loadingId: this.options.loadingId,
        loadingText: 'Updating profile...'
      });
      
      // Show success message
      window.ErrorHandlingService.showErrorToast(
        'Profile updated successfully!', 
        { level: 'success', duration: 3000 }
      );
      
      // Redirect if configured
      if (this.options.redirectOnUpdate) {
        let redirectUrl = this.options.redirectUrl;
        
        // Add profile ID to redirect URL if needed
        if (redirectUrl.includes('{profile_id}')) {
          redirectUrl = redirectUrl.replace('{profile_id}', this.options.profileId);
        } else if (redirectUrl.includes('?')) {
          redirectUrl += `&profile_id=${this.options.profileId}`;
        } else {
          redirectUrl += `?profile_id=${this.options.profileId}`;
        }
        
        window.location.href = redirectUrl;
      }
      
      return result;
    } catch (error) {
      // Revert optimistic update
      this.state.hasChanges = true;
      this.state.submitSuccess = false;
      
      // Extract API error message if available
      let errorMessage = 'An error occurred while updating your profile.';
      if (error.data && error.data.message) {
        errorMessage = error.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Add error to state
      this.state.errors = {
        ...this.state.errors,
        submit: errorMessage
      };
      
      // Log the error via ErrorHandlingService
      window.ErrorHandlingService.handleError(
        error, 
        'profile_update', 
        {
          showToast: true,
          metadata: { formData: this.state.formData }
        }
      );
      
      throw error;
    } finally {
      this.state.isSubmitting = false;
      window.LoadingStateManager.setLoading(this.options.loadingId, false);
      this.render();
    }
  }

  /**
   * Handle cancel button click
   */
  handleCancel() {
    if (this.state.hasChanges && this.options.promptOnUnsavedChanges) {
      const confirmCancel = window.confirm('You have unsaved changes. Are you sure you want to cancel?');
      if (!confirmCancel) {
        return;
      }
    }
    
    this.resetForm();
    
    // If redirectUrl is provided, navigate there on cancel
    if (this.options.redirectUrl) {
      let redirectUrl = this.options.redirectUrl;
      
      // Add profile ID to redirect URL if needed
      if (redirectUrl.includes('{profile_id}')) {
        redirectUrl = redirectUrl.replace('{profile_id}', this.options.profileId);
      } else if (redirectUrl.includes('?')) {
        redirectUrl += `&profile_id=${this.options.profileId}`;
      } else {
        redirectUrl += `?profile_id=${this.options.profileId}`;
      }
      
      window.location.href = redirectUrl;
    }
  }

  /**
   * Warn on unsaved changes
   * @param {Event} event - beforeunload event
   */
  warnOnUnsavedChanges(event) {
    if (this.state.hasChanges) {
      const message = 'You have unsaved changes. Are you sure you want to leave this page?';
      event.preventDefault();
      event.returnValue = message;
      return message;
    }
  }

  /**
   * Get currency label from currency code
   * @param {string} currencyCode - Currency code
   * @returns {string} Formatted currency label
   */
  getCurrencyLabel(currencyCode) {
    const currencies = {
      'INR': 'Indian Rupee (₹)',
      'USD': 'US Dollar ($)',
      'EUR': 'Euro (€)',
      'GBP': 'British Pound (£)'
    };
    
    return currencies[currencyCode] || currencyCode;
  }

  /**
   * Main render method
   */
  render() {
    // Clear container
    this.container.innerHTML = '';
    
    const { formData, errors, isLoading, apiError, hasChanges, isSubmitting, submitSuccess } = this.state;
    
    // Handle API error state
    if (apiError && !formData.name) {
      const errorTemplate = `
        <div class="profile-edit-error">
          <div class="alert alert-danger" role="alert">
            <h5 class="alert-heading">Error Loading Profile</h5>
            <p>${apiError.message || 'Unable to load profile data'}</p>
            <hr>
            <button class="btn btn-outline-danger btn-sm retry-btn">
              <i class="bi bi-arrow-repeat me-1"></i> Retry
            </button>
          </div>
        </div>
      `;
      
      this.container.innerHTML = errorTemplate;
      
      // Add retry button handler
      this.container.querySelector('.retry-btn').addEventListener('click', this.fetchProfileData);
      return;
    }
    
    // Handle loading state with no existing data
    if (isLoading && !formData.name) {
      const loadingTemplate = `
        <div class="profile-edit-loading">
          <div class="d-flex align-items-center justify-content-center p-4">
            <div class="spinner-border text-primary me-2" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <span>Loading profile data...</span>
          </div>
        </div>
      `;
      
      this.container.innerHTML = loadingTemplate;
      return;
    }
    
    // Render form
    const formTemplate = `
      <div class="profile-edit-form-container ${isSubmitting ? 'form-submitting' : ''}">
        <h3 class="mb-3">Edit Profile</h3>
        
        ${submitSuccess ? `
          <div class="alert alert-success" role="alert">
            Profile updated successfully!
          </div>
        ` : ''}
        
        ${errors.submit ? `
          <div class="alert alert-danger" role="alert">
            ${errors.submit}
          </div>
        ` : ''}
        
        ${hasChanges ? `
          <div class="unsaved-changes-alert alert alert-warning mb-3" role="alert">
            <i class="bi bi-exclamation-triangle me-2"></i>
            You have unsaved changes
          </div>
        ` : ''}
        
        <form id="profile-edit-form" class="profile-edit-form">
          <!-- Basic Information Section -->
          <div class="card mb-3">
            <div class="card-header">
              <i class="bi bi-person me-2"></i> Basic Information
            </div>
            <div class="card-body">
              <div class="form-group mb-3 ${errors.name ? 'has-error' : ''}">
                <label for="name" class="form-label">Your Name</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="name" 
                  name="name" 
                  value="${formData.name || ''}" 
                  placeholder="Enter your full name"
                  required
                >
                ${errors.name ? `<div class="error-message text-danger mt-1 small">${errors.name}</div>` : ''}
              </div>
              
              <div class="form-group mb-3 ${errors.email ? 'has-error' : ''}">
                <label for="email" class="form-label">Email Address</label>
                <input 
                  type="email" 
                  class="form-control" 
                  id="email" 
                  name="email" 
                  value="${formData.email || ''}" 
                  placeholder="Enter your email address"
                  required
                >
                ${errors.email ? `<div class="error-message text-danger mt-1 small">${errors.email}</div>` : ''}
                <div class="form-text">We'll use this to identify your profile</div>
              </div>
            </div>
          </div>
          
          <!-- Additional Information Section -->
          <div class="card mb-3">
            <div class="card-header">
              <i class="bi bi-info-circle me-2"></i> Additional Information
            </div>
            <div class="card-body">
              <div class="form-group mb-3 ${errors.age ? 'has-error' : ''}">
                <label for="age" class="form-label">Your Age</label>
                <input 
                  type="number" 
                  class="form-control" 
                  id="age" 
                  name="age" 
                  value="${formData.age || ''}" 
                  placeholder="Enter your age"
                  min="18"
                  max="120"
                >
                ${errors.age ? `<div class="error-message text-danger mt-1 small">${errors.age}</div>` : ''}
              </div>
              
              <div class="form-group mb-3 ${errors.occupation ? 'has-error' : ''}">
                <label for="occupation" class="form-label">Occupation</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="occupation" 
                  name="occupation" 
                  value="${formData.occupation || ''}" 
                  placeholder="Enter your occupation"
                >
                ${errors.occupation ? `<div class="error-message text-danger mt-1 small">${errors.occupation}</div>` : ''}
              </div>
              
              <div class="row">
                <div class="col-md-6">
                  <div class="form-group mb-3 ${errors.household_size ? 'has-error' : ''}">
                    <label for="household_size" class="form-label">Household Size</label>
                    <select class="form-select" id="household_size" name="household_size">
                      <option value="1" ${formData.household_size === '1' ? 'selected' : ''}>1 (Just me)</option>
                      <option value="2" ${formData.household_size === '2' ? 'selected' : ''}>2</option>
                      <option value="3" ${formData.household_size === '3' ? 'selected' : ''}>3</option>
                      <option value="4" ${formData.household_size === '4' ? 'selected' : ''}>4</option>
                      <option value="5+" ${formData.household_size === '5+' ? 'selected' : ''}>5 or more</option>
                    </select>
                    ${errors.household_size ? `<div class="error-message text-danger mt-1 small">${errors.household_size}</div>` : ''}
                  </div>
                </div>
                
                <div class="col-md-6">
                  <div class="form-group mb-3 ${errors.currency ? 'has-error' : ''}">
                    <label for="currency" class="form-label">Preferred Currency</label>
                    <select class="form-select" id="currency" name="currency">
                      <option value="INR" ${formData.currency === 'INR' ? 'selected' : ''}>Indian Rupee (₹)</option>
                      <option value="USD" ${formData.currency === 'USD' ? 'selected' : ''}>US Dollar ($)</option>
                      <option value="EUR" ${formData.currency === 'EUR' ? 'selected' : ''}>Euro (€)</option>
                      <option value="GBP" ${formData.currency === 'GBP' ? 'selected' : ''}>British Pound (£)</option>
                    </select>
                    ${errors.currency ? `<div class="error-message text-danger mt-1 small">${errors.currency}</div>` : ''}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Form Actions -->
          <div class="form-actions d-flex justify-content-between">
            <button type="button" class="btn btn-outline-secondary cancel-btn" id="cancel-btn">
              ${this.options.cancelButtonText}
            </button>
            <button 
              type="submit" 
              class="btn btn-primary save-btn" 
              id="save-btn"
              ${!hasChanges ? 'disabled' : ''}
              ${isSubmitting ? 'disabled' : ''}
            >
              ${isSubmitting ? '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>' : ''}
              ${this.options.saveButtonText}
            </button>
          </div>
        </form>
      </div>
    `;
    
    this.container.innerHTML = formTemplate;
    
    // Add event listeners to form elements
    const form = this.container.querySelector('#profile-edit-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    const saveButton = form.querySelector('#save-btn');
    const cancelButton = form.querySelector('#cancel-btn');
    
    inputs.forEach(input => {
      input.addEventListener('input', this.handleInputChange);
      input.addEventListener('change', this.handleInputChange);
    });
    
    form.addEventListener('submit', this.handleSubmit);
    cancelButton.addEventListener('click', this.handleCancel);
    
    // Set focus on save button if there are changes
    if (hasChanges && saveButton) {
      saveButton.focus();
    }
  }

  /**
   * Clean up resources
   */
  destroy() {
    // Remove event listeners
    window.removeEventListener('beforeunload', this.warnOnUnsavedChanges);
    
    // Clear container
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}

// Export the component globally
window.ProfileEditForm = ProfileEditForm;