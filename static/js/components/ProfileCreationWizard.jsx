/**
 * ProfileCreationWizard - Multi-step form for creating new user profiles
 * 
 * This component implements a wizard-style form for collecting 
 * profile information from users. It includes:
 * - Multi-step form with progress tracking
 * - Form validation
 * - Form persistence between steps
 * - API integration with the /profiles endpoint
 * - Error handling via ErrorHandlingService
 * - Loading states via LoadingStateManager
 */

class ProfileCreationWizard {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Container element with ID "${containerId}" not found`);
      return;
    }

    // Default options
    this.options = {
      redirectOnComplete: true,
      redirectUrl: '/questions',
      steps: ['basic', 'additional', 'confirm'],
      persistenceKey: 'profile_wizard_data',
      ...options
    };

    // State
    this.state = {
      currentStep: 0,
      formData: this.loadPersistedData() || {
        name: '',
        email: '',
        age: '',
        occupation: '',
        household_size: '1',
        currency: 'INR',
      },
      errors: {},
      isLoading: false,
      isComplete: false,
      profileId: null
    };

    // Bind methods
    this.renderCurrentStep = this.renderCurrentStep.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.nextStep = this.nextStep.bind(this);
    this.prevStep = this.prevStep.bind(this);
    this.persistFormData = this.persistFormData.bind(this);
    this.createProfile = this.createProfile.bind(this);
    this.validateStep = this.validateStep.bind(this);

    // Initialize the wizard
    this.init();
  }

  /**
   * Initialize the wizard
   */
  init() {
    // Create loading and error containers if they don't exist
    if (!document.getElementById('wizard-loading-indicator')) {
      const loadingIndicator = document.createElement('div');
      loadingIndicator.id = 'wizard-loading-indicator';
      loadingIndicator.className = 'loading-indicator';
      this.container.appendChild(loadingIndicator);
    }

    // Initial render
    this.renderCurrentStep();

    // Setup event listeners
    window.addEventListener('beforeunload', () => {
      // Persist form data before the page is unloaded
      this.persistFormData();
    });
  }

  /**
   * Render the current form step
   */
  renderCurrentStep() {
    const { currentStep, formData, errors, isLoading } = this.state;
    const steps = this.options.steps;
    const currentStepName = steps[currentStep];

    // Clear container
    this.container.innerHTML = '';

    // Create step indicator
    const stepIndicator = document.createElement('div');
    stepIndicator.className = 'step-indicator';
    for (let i = 0; i < steps.length; i++) {
      const stepDot = document.createElement('div');
      stepDot.className = `step-dot ${i === currentStep ? 'active' : i < currentStep ? 'completed' : ''}`;
      stepIndicator.appendChild(stepDot);
    }
    this.container.appendChild(stepIndicator);

    // Create form
    const form = document.createElement('form');
    form.className = 'wizard-form';
    form.id = `${currentStepName}-form`;
    form.addEventListener('submit', this.handleSubmit);

    // Create step content
    const formContent = this.createStepContent(currentStepName, formData, errors);
    form.appendChild(formContent);

    // Create navigation buttons
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'wizard-button-container';

    if (currentStep > 0) {
      const prevButton = document.createElement('button');
      prevButton.type = 'button';
      prevButton.className = 'wizard-button prev-button';
      prevButton.textContent = 'Back';
      prevButton.addEventListener('click', this.prevStep);
      buttonContainer.appendChild(prevButton);
    }

    const nextButton = document.createElement('button');
    nextButton.type = 'submit';
    nextButton.className = 'wizard-button next-button';
    nextButton.textContent = currentStep === steps.length - 1 ? 'Create Profile' : 'Next';
    buttonContainer.appendChild(nextButton);

    form.appendChild(buttonContainer);
    this.container.appendChild(form);

    // Display loading state if loading
    if (isLoading) {
      window.LoadingStateManager.setLoading('wizard-loading-indicator', true, {
        text: 'Processing...'
      });
    }
  }

  /**
   * Create the content for a specific form step
   * @param {string} stepName - Name of the current step
   * @param {Object} formData - Current form data
   * @param {Object} errors - Form validation errors
   * @returns {HTMLElement} Step content container
   */
  createStepContent(stepName, formData, errors) {
    const container = document.createElement('div');
    container.className = 'wizard-step-content';

    switch (stepName) {
      case 'basic':
        // Basic info (name, email)
        container.innerHTML = `
          <h2>Basic Information</h2>
          <p class="step-description">Let's start with your basic information.</p>
          
          <div class="form-group ${errors.name ? 'has-error' : ''}">
            <label for="name">Your Name</label>
            <input 
              type="text" 
              id="name" 
              name="name" 
              value="${formData.name || ''}" 
              placeholder="Enter your full name"
              required
            >
            ${errors.name ? `<div class="error-message">${errors.name}</div>` : ''}
          </div>
          
          <div class="form-group ${errors.email ? 'has-error' : ''}">
            <label for="email">Email Address</label>
            <input 
              type="email" 
              id="email" 
              name="email" 
              value="${formData.email || ''}" 
              placeholder="Enter your email address"
              required
            >
            ${errors.email ? `<div class="error-message">${errors.email}</div>` : ''}
            <div class="help-text">We'll use this to identify your profile</div>
          </div>
        `;
        break;
        
      case 'additional':
        // Additional info (age, occupation, household size)
        container.innerHTML = `
          <h2>Additional Information</h2>
          <p class="step-description">Tell us a bit more about yourself to help us customize your experience.</p>
          
          <div class="form-group ${errors.age ? 'has-error' : ''}">
            <label for="age">Your Age</label>
            <input 
              type="number" 
              id="age" 
              name="age" 
              value="${formData.age || ''}" 
              placeholder="Enter your age"
              min="18"
              max="120"
            >
            ${errors.age ? `<div class="error-message">${errors.age}</div>` : ''}
          </div>
          
          <div class="form-group ${errors.occupation ? 'has-error' : ''}">
            <label for="occupation">Occupation</label>
            <input 
              type="text" 
              id="occupation" 
              name="occupation" 
              value="${formData.occupation || ''}" 
              placeholder="Enter your occupation"
            >
            ${errors.occupation ? `<div class="error-message">${errors.occupation}</div>` : ''}
          </div>
          
          <div class="form-group ${errors.household_size ? 'has-error' : ''}">
            <label for="household_size">Household Size</label>
            <select id="household_size" name="household_size">
              <option value="1" ${formData.household_size === '1' ? 'selected' : ''}>1 (Just me)</option>
              <option value="2" ${formData.household_size === '2' ? 'selected' : ''}>2</option>
              <option value="3" ${formData.household_size === '3' ? 'selected' : ''}>3</option>
              <option value="4" ${formData.household_size === '4' ? 'selected' : ''}>4</option>
              <option value="5+" ${formData.household_size === '5+' ? 'selected' : ''}>5 or more</option>
            </select>
            ${errors.household_size ? `<div class="error-message">${errors.household_size}</div>` : ''}
          </div>
          
          <div class="form-group ${errors.currency ? 'has-error' : ''}">
            <label for="currency">Preferred Currency</label>
            <select id="currency" name="currency">
              <option value="INR" ${formData.currency === 'INR' ? 'selected' : ''}>Indian Rupee (₹)</option>
              <option value="USD" ${formData.currency === 'USD' ? 'selected' : ''}>US Dollar ($)</option>
              <option value="EUR" ${formData.currency === 'EUR' ? 'selected' : ''}>Euro (€)</option>
              <option value="GBP" ${formData.currency === 'GBP' ? 'selected' : ''}>British Pound (£)</option>
            </select>
            ${errors.currency ? `<div class="error-message">${errors.currency}</div>` : ''}
          </div>
        `;
        break;
        
      case 'confirm':
        // Confirmation step
        container.innerHTML = `
          <h2>Confirm Your Information</h2>
          <p class="step-description">Please review your information before creating your profile.</p>
          
          <div class="confirmation-data">
            <div class="data-group">
              <span class="data-label">Name:</span>
              <span class="data-value">${formData.name || 'Not provided'}</span>
            </div>
            
            <div class="data-group">
              <span class="data-label">Email:</span>
              <span class="data-value">${formData.email || 'Not provided'}</span>
            </div>
            
            <div class="data-group">
              <span class="data-label">Age:</span>
              <span class="data-value">${formData.age || 'Not provided'}</span>
            </div>
            
            <div class="data-group">
              <span class="data-label">Occupation:</span>
              <span class="data-value">${formData.occupation || 'Not provided'}</span>
            </div>
            
            <div class="data-group">
              <span class="data-label">Household Size:</span>
              <span class="data-value">${formData.household_size || 'Not provided'}</span>
            </div>
            
            <div class="data-group">
              <span class="data-label">Preferred Currency:</span>
              <span class="data-value">${this.getCurrencyLabel(formData.currency)}</span>
            </div>
          </div>
          
          <div class="notice-message">
            <p>By creating your profile, you agree to our <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>.</p>
          </div>
          
          ${errors.submit ? `<div class="error-message global-error">${errors.submit}</div>` : ''}
        `;
        break;
        
      default:
        container.innerHTML = '<p>Unknown step</p>';
    }

    // Add event listeners to form inputs
    setTimeout(() => {
      const inputs = container.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        input.addEventListener('change', this.handleInputChange);
        input.addEventListener('blur', this.handleInputChange);
      });
    }, 0);

    return container;
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
   * Handle form input changes
   * @param {Event} event - Input change event
   */
  handleInputChange(event) {
    const { name, value, type } = event.target;
    const inputValue = type === 'checkbox' ? event.target.checked : value;
    
    // Update state
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
    
    // Persist form data
    this.persistFormData();
  }

  /**
   * Handle form submission
   * @param {Event} event - Form submission event
   */
  handleSubmit(event) {
    event.preventDefault();
    
    // Validate current step
    const errors = this.validateStep();
    
    if (Object.keys(errors).length > 0) {
      // Show errors
      this.state.errors = errors;
      this.renderCurrentStep();
      return;
    }
    
    // If we're on the last step, submit the form
    if (this.state.currentStep === this.options.steps.length - 1) {
      this.createProfile();
    } else {
      // Otherwise, move to the next step
      this.nextStep();
    }
  }

  /**
   * Validate the current step
   * @returns {Object} Validation errors
   */
  validateStep() {
    const { currentStep, formData } = this.state;
    const stepName = this.options.steps[currentStep];
    const errors = {};
    
    switch (stepName) {
      case 'basic':
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
        break;
        
      case 'additional':
        // Validate age if provided
        if (formData.age) {
          const age = parseInt(formData.age, 10);
          if (isNaN(age) || age < 18 || age > 120) {
            errors.age = 'Please enter a valid age between 18 and 120';
          }
        }

        // Occupation validation is optional
        if (formData.occupation && formData.occupation.length > 100) {
          errors.occupation = 'Occupation must be less than 100 characters';
        }
        
        // Validate household size
        if (!formData.household_size) {
          errors.household_size = 'Please select a household size';
        }
        
        // Validate currency
        if (!formData.currency) {
          errors.currency = 'Please select a preferred currency';
        }
        break;
        
      case 'confirm':
        // No specific validations for confirmation step
        break;
    }
    
    return errors;
  }

  /**
   * Move to the next step
   */
  nextStep() {
    const { currentStep } = this.state;
    const maxStep = this.options.steps.length - 1;
    
    if (currentStep < maxStep) {
      this.state.currentStep = currentStep + 1;
      this.renderCurrentStep();
      
      // Scroll to top
      window.scrollTo(0, 0);
    }
  }

  /**
   * Move to the previous step
   */
  prevStep() {
    const { currentStep } = this.state;
    
    if (currentStep > 0) {
      this.state.currentStep = currentStep - 1;
      this.renderCurrentStep();
      
      // Scroll to top
      window.scrollTo(0, 0);
    }
  }

  /**
   * Persist form data to localStorage
   */
  persistFormData() {
    localStorage.setItem(
      this.options.persistenceKey, 
      JSON.stringify(this.state.formData)
    );
  }

  /**
   * Load persisted form data from localStorage
   * @returns {Object|null} Persisted form data or null
   */
  loadPersistedData() {
    const data = localStorage.getItem(this.options.persistenceKey);
    
    if (data) {
      try {
        return JSON.parse(data);
      } catch (e) {
        return null;
      }
    }
    
    return null;
  }

  /**
   * Clear persisted form data
   */
  clearPersistedData() {
    localStorage.removeItem(this.options.persistenceKey);
  }

  /**
   * Create profile via API
   */
  async createProfile() {
    // Set loading state
    this.state.isLoading = true;
    window.LoadingStateManager.setLoading('wizard-loading-indicator', true, {
      text: 'Creating profile...'
    });
    this.renderCurrentStep();
    
    try {
      // Prepare form data
      const profileData = {
        ...this.state.formData,
        // Convert household_size to number if it's a number string
        household_size: isNaN(parseInt(this.state.formData.household_size, 10)) 
          ? this.state.formData.household_size 
          : parseInt(this.state.formData.household_size, 10),
        // Convert age to number if provided
        age: this.state.formData.age ? parseInt(this.state.formData.age, 10) : null
      };
      
      // Call API using direct fetch since we're submitting to a different endpoint
      const response = await fetch('/create_profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(profileData)
      });
      
      // Check if response was successful
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
      }
      
      // Parse the response
      const result = await response.json();
      
      // Handle success
      this.state.isLoading = false;
      this.state.isComplete = true;
      this.state.profileId = result.id || result.profile_id;
      
      // Clear persisted data
      this.clearPersistedData();
      
      // Show success message
      if (window.ErrorHandlingService) {
        window.ErrorHandlingService.showErrorToast(
          'Profile created successfully!', 
          { level: 'success', duration: 3000 }
        );
      } else {
        alert('Profile created successfully!');
      }
      
      // Redirect if configured
      if (this.options.redirectOnComplete) {
        let redirectUrl = this.options.redirectUrl;
        
        // Add profile ID to redirect URL if it contains a placeholder
        if (redirectUrl.includes('{profile_id}')) {
          redirectUrl = redirectUrl.replace('{profile_id}', this.state.profileId);
        } else if (redirectUrl.includes('?')) {
          redirectUrl += `&profile_id=${this.state.profileId}`;
        } else {
          redirectUrl += `?profile_id=${this.state.profileId}`;
        }
        
        window.location.href = redirectUrl;
      } else {
        // Show completion message
        this.container.innerHTML = `
          <div class="wizard-completion">
            <h2>Profile Created!</h2>
            <p>Your profile has been created successfully.</p>
            <div class="wizard-buttons">
              <a href="/questions?profile_id=${this.state.profileId}" class="wizard-button">
                Start Questionnaire
              </a>
              <a href="/dashboard?profile_id=${this.state.profileId}" class="wizard-button secondary">
                Go to Dashboard
              </a>
            </div>
          </div>
        `;
      }
    } catch (error) {
      // Handle error
      this.state.isLoading = false;
      
      // Extract API error message if available
      let errorMessage = 'An error occurred while creating your profile.';
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
      
      // Re-render the form
      this.renderCurrentStep();
      
      // Log the error via ErrorHandlingService
      if (window.ErrorHandlingService) {
        window.ErrorHandlingService.handleError(
          error, 
          'profile_creation', 
          {
            showToast: true,
            metadata: { formData: this.state.formData }
          }
        );
      } else {
        console.error('Error creating profile:', error);
      }
    }
  }
}

// Export the ProfileCreationWizard class
window.ProfileCreationWizard = ProfileCreationWizard;