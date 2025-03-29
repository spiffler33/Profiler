/**
 * Goal Form Probability Calculator
 * Handles real-time probability calculations for financial goals based on form input
 * Interacts with the /api/v2/goals/calculate-probability endpoint
 */

const GoalFormProbability = (function() {
  // Configuration
  const config = {
    apiEndpoint: '/api/v2/goals/calculate-probability',
    debounceTime: 500, // ms before making API calls after input changes
    defaultProbability: 0,
    useEnhancedLoadingStates: true, // Use the new loading state system
    failureRetryCount: 3 // Number of times to retry on failure
  };

  // DOM Elements cache
  let elements = {};
  
  // State
  let state = {
    updateTimeout: null,
    isLoading: false,
    lastCalculatedProbability: null,
    currentParameters: {},
    goalId: null,
    lastChangeTimestamp: Date.now(),
    animationInProgress: false
  };

  /**
   * Initialize the probability calculator
   * @param {Object} options - Initialization options
   */
  function init(options = {}) {
    // Override default config with options
    Object.assign(config, options);
    
    // Cache DOM elements
    cacheElements();
    
    // Set initial goal ID if editing existing goal
    const goalFormElement = document.getElementById('goal-form');
    if (goalFormElement && goalFormElement.action) {
      const urlParts = goalFormElement.action.split('/');
      const potentialId = urlParts[urlParts.length - 1];
      if (potentialId && potentialId.length > 8) {
        state.goalId = potentialId;
        
        // Add goal ID as data attribute to the form for easier access by other components
        goalFormElement.dataset.goalId = state.goalId;
      }
    }
    
    // Set up event listeners
    setupEventListeners();
    
    // Subscribe to data events from other components
    subscribeToDataEvents();
    
    // If we're in edit mode, do an initial calculation
    const isEditMode = window.location.pathname.includes('/edit/');
    if (isEditMode && elements.probabilityValue && elements.probabilityValue.textContent !== '--') {
      setTimeout(calculateProbability, 500);
    }
    
    // For new goals, calculate as soon as form is filled enough
    if (!isEditMode) {
      // Set up mutation observer to watch for changes to form fields
      setupFormChangeObserver();
    }
    
    // Log initialization
    console.log('Goal Form Probability Calculator initialized', { 
      goalId: state.goalId,
      isEditMode,
      config
    });
  }

  /**
   * Cache DOM elements for better performance
   */
  function cacheElements() {
    elements = {
      // Form container
      goalForm: document.getElementById('goal-form'),
      probabilitySection: document.querySelector('.probability-container'),
      
      // Input elements
      categorySelect: document.getElementById('category'),
      targetAmountInput: document.getElementById('target_amount'),
      currentAmountInput: document.getElementById('current_amount'),
      timeframeInput: document.getElementById('timeframe'),
      importanceSelect: document.getElementById('importance'),
      flexibilitySelect: document.getElementById('flexibility'),
      
      // Output elements
      probabilityValue: document.getElementById('success-probability-value'),
      probabilityBarFill: document.getElementById('probability-bar-fill'),
      probabilityStatusText: document.getElementById('probability-status-text'),
      probabilityLoading: document.querySelector('.probability-loading'),
      adjustmentImpacts: document.getElementById('adjustment-impacts'),
      
      // Visualization container
      visualizerMount: document.getElementById('goal-probability-visualizer')
    };
  }

  /**
   * Set up event listeners for form inputs
   */
  function setupEventListeners() {
    // Track all form inputs that affect probability
    const allFormInputs = [
      // Main form inputs
      { el: elements.categorySelect, type: 'critical' },
      { el: elements.targetAmountInput, type: 'critical' },
      { el: elements.currentAmountInput, type: 'standard' },
      { el: elements.timeframeInput, type: 'critical' },
      { el: elements.importanceSelect, type: 'standard' },
      { el: elements.flexibilitySelect, type: 'standard' }
    ];
    
    // Mark key inputs with data attribute for styling
    allFormInputs.forEach(item => {
      if (item.el) {
        item.el.dataset.affectsProbability = 'true';
        
        if (item.type === 'critical') {
          item.el.dataset.probabilityImpact = 'critical';
        }
      }
    });
    
    // Add change and input listeners to all probability-affecting inputs
    document.querySelectorAll('[data-affects-probability="true"]').forEach(input => {
      input.addEventListener('change', triggerProbabilityUpdate);
      input.addEventListener('input', triggerProbabilityUpdate);
    });
    
    // Add listeners to category-specific inputs
    const categorySpecificInputs = document.querySelectorAll('.category-specific-section input, .category-specific-section select');
    categorySpecificInputs.forEach(input => {
      input.dataset.affectsProbability = 'true';
      input.addEventListener('change', triggerProbabilityUpdate);
      input.addEventListener('input', triggerProbabilityUpdate);
    });
    
    // Add special animation class to the success probability value for smooth transitions
    if (elements.probabilityValue) {
      elements.probabilityValue.classList.add('animated-value');
    }
    
    // Add form submission handler to ensure probability is calculated before submission
    if (elements.goalForm) {
      elements.goalForm.addEventListener('submit', function(e) {
        // If we have any critical inputs empty, don't proceed yet
        const criticalInputs = document.querySelectorAll('[data-probability-impact="critical"]');
        let hasMissingCritical = false;
        
        criticalInputs.forEach(input => {
          if (!input.value) {
            hasMissingCritical = true;
          }
        });
        
        // If we're loading, or haven't yet calculated probability, prevent submission
        if (state.isLoading || (hasMissingCritical && !state.lastCalculatedProbability)) {
          e.preventDefault();
          
          // Highlight the missing critical fields
          criticalInputs.forEach(input => {
            if (!input.value) {
              input.classList.add('highlight-required');
              setTimeout(() => {
                input.classList.remove('highlight-required');
              }, 2000);
            }
          });
          
          // Show a message
          if (hasMissingCritical) {
            if (window.loadingState && window.loadingState.showError) {
              window.loadingState.showError('Please fill in all required fields to calculate probability.');
            } else {
              alert('Please fill in all required fields to calculate probability.');
            }
          }
        }
      });
    }
  }
  
  /**
   * Set up a mutation observer to watch for changes to the form
   * This helps us detect when a new goal form gets populated enough to calculate probability
   */
  function setupFormChangeObserver() {
    // We'll only observe the minimal requirement inputs to trigger calculation
    const criticalInputs = [
      elements.categorySelect,
      elements.targetAmountInput,
      elements.timeframeInput
    ].filter(Boolean);
    
    // Don't proceed if we don't have the critical inputs
    if (criticalInputs.length < 3) return;
    
    // Create a function to check if we should calculate probability
    const checkForCalculation = () => {
      if (elements.categorySelect?.value &&
          elements.targetAmountInput?.value && 
          elements.timeframeInput?.value &&
          !state.lastCalculatedProbability) {
        
        // All critical fields are filled and we haven't calculated yet
        triggerProbabilityUpdate();
      }
    };
    
    // Set up observers for each input
    criticalInputs.forEach(input => {
      // Create mutation observer
      const observer = new MutationObserver((mutations) => {
        mutations.forEach(mutation => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
            checkForCalculation();
          }
        });
      });
      
      // Observe value attribute changes
      observer.observe(input, { attributes: true, attributeFilter: ['value'] });
    });
    
    // Also check on any value change
    criticalInputs.forEach(input => {
      input.addEventListener('change', checkForCalculation);
    });
  }

  /**
   * Trigger probability update with debouncing
   */
  function triggerProbabilityUpdate() {
    // Clear previous timeout
    if (state.updateTimeout) {
      clearTimeout(state.updateTimeout);
    }
    
    // Track when the change was made
    state.lastChangeTimestamp = Date.now();
    
    // Show subtle indication that an update is pending
    if (elements.probabilityValue && !state.isLoading) {
      elements.probabilityValue.classList.add('update-pending');
    }
    
    // Set new timeout to debounce API calls
    state.updateTimeout = setTimeout(calculateProbability, config.debounceTime);
  }

  /**
   * Calculate probability based on current form values
   */
  function calculateProbability() {
    // Remove pending update class
    if (elements.probabilityValue) {
      elements.probabilityValue.classList.remove('update-pending');
    }
    
    // Show loading state
    setLoadingState(true);
    
    // Get current values
    const formData = getFormValues();
    
    // Store current parameters for later use
    state.currentParameters = formData;
    
    // Validate required fields
    if (!formData.category || !formData.target_amount || !formData.timeframe) {
      setLoadingState(false);
      updateProbabilityUI(config.defaultProbability, 'Please fill in all required fields to calculate probability.');
      return;
    }
    
    // Make API call to calculate probability
    fetchProbability(formData)
      .then(result => {
        // Update UI with result
        updateProbabilityUI(result.success_probability, getStatusMessage(result.success_probability));
        
        // Store the calculated probability
        state.lastCalculatedProbability = result.success_probability;
        
        // Calculate and update adjustment impacts
        updateAdjustmentImpacts(result.adjustments || []);
        
        // Optionally update visualizer if available
        updateVisualizer(result);
      })
      .catch(error => {
        console.error('Error calculating probability:', error);
        setLoadingState(false);
        
        // Show error in UI
        elements.probabilityValue.textContent = 'Error';
        elements.probabilityStatusText.textContent = 'An error occurred calculating the probability.';
        
        // Use global error handler if available
        if (window.loadingState && window.loadingState.showError) {
          window.loadingState.showError(`Error calculating probability: ${error.message}`);
        }
      });
  }

  /**
   * Get current values from form elements
   * @returns {Object} Form values as an object
   */
  function getFormValues() {
    // Basic parameters
    const category = elements.categorySelect?.value || '';
    const target_amount = parseFloat(elements.targetAmountInput?.value) || 0;
    const current_amount = parseFloat(elements.currentAmountInput?.value) || 0;
    const timeframe = elements.timeframeInput?.value || '';
    const importance = elements.importanceSelect?.value || 'medium';
    const flexibility = elements.flexibilitySelect?.value || 'somewhat_flexible';
    
    // Parse timeframe to determine months remaining
    let months_remaining = 0;
    if (timeframe) {
      const targetDate = new Date(timeframe);
      const currentDate = new Date();
      months_remaining = (targetDate.getFullYear() - currentDate.getFullYear()) * 12 + 
                         (targetDate.getMonth() - currentDate.getMonth());
    }
    
    // Create base data object
    const formData = {
      category,
      target_amount,
      current_amount,
      timeframe,
      months_remaining,
      importance,
      flexibility
    };
    
    // Add category-specific parameters
    addCategorySpecificParameters(formData, category);
    
    // Publish parameter changes event
    if (window.DataEventBus && state.goalId) {
      window.DataEventBus.publish('parameters-changed', {
        source: 'goal-form',
        goalId: state.goalId,
        parameters: formData,
        timestamp: Date.now()
      });
    }
    
    return formData;
  }

  /**
   * Add category-specific parameters to form data
   * @param {Object} formData - Base form data object to add parameters to
   * @param {string} category - The goal category
   */
  function addCategorySpecificParameters(formData, category) {
    // Emergency fund parameters
    if (category === 'emergency_fund') {
      const monthsInput = document.getElementById('emergency_fund_months');
      const expensesInput = document.getElementById('monthly_expenses');
      
      if (monthsInput && monthsInput.value) {
        formData.emergency_fund_months = parseFloat(monthsInput.value);
      }
      
      if (expensesInput && expensesInput.value) {
        formData.monthly_expenses = parseFloat(expensesInput.value);
      }
    }
    
    // Retirement parameters
    else if (category === 'traditional_retirement' || category === 'early_retirement') {
      const retirementAgeInput = document.getElementById('retirement_age');
      const withdrawalRateInput = document.getElementById('withdrawal_rate');
      const yearlyExpensesInput = document.getElementById('yearly_expenses');
      
      if (retirementAgeInput && retirementAgeInput.value) {
        formData.retirement_age = parseInt(retirementAgeInput.value);
      }
      
      if (withdrawalRateInput && withdrawalRateInput.value) {
        formData.withdrawal_rate = parseFloat(withdrawalRateInput.value) / 100; // Convert to decimal
      }
      
      if (yearlyExpensesInput && yearlyExpensesInput.value) {
        formData.yearly_expenses = parseFloat(yearlyExpensesInput.value);
      }
    }
    
    // Education parameters
    else if (category === 'education') {
      const educationTypeInput = document.getElementById('education_type');
      const educationYearsInput = document.getElementById('education_years');
      const yearlyCostInput = document.getElementById('yearly_cost');
      
      if (educationTypeInput && educationTypeInput.value) {
        formData.education_type = educationTypeInput.value;
      }
      
      if (educationYearsInput && educationYearsInput.value) {
        formData.education_years = parseInt(educationYearsInput.value);
      }
      
      if (yearlyCostInput && yearlyCostInput.value) {
        formData.yearly_cost = parseFloat(yearlyCostInput.value);
      }
    }
    
    // Home purchase parameters
    else if (category === 'home_purchase') {
      const propertyValueInput = document.getElementById('property_value');
      const downPaymentPercentInput = document.getElementById('down_payment_percent');
      
      if (propertyValueInput && propertyValueInput.value) {
        formData.property_value = parseFloat(propertyValueInput.value);
      }
      
      if (downPaymentPercentInput && downPaymentPercentInput.value) {
        formData.down_payment_percent = parseFloat(downPaymentPercentInput.value) / 100; // Convert to decimal
      }
    }
    
    // Add goal ID if available (for editing mode)
    if (state.goalId) {
      formData.goal_id = state.goalId;
    }
    
    return formData;
  }

  /**
   * Make API call to calculate probability
   * @param {Object} formData - Goal parameters to submit
   * @returns {Promise<Object>} - Promise resolving to calculation results
   */
  function fetchProbability(formData) {
    // Use enhanced loading state system if available and enabled
    if (config.useEnhancedLoadingStates && window.loadingState) {
      // Show loading state on the probability section
      if (elements.probabilitySection) {
        window.loadingState.setLoading(elements.probabilitySection, true, {
          size: 'sm',
          showProgressBar: true
        });
      }
    }
    
    // Track retry count
    let retries = 0;
    
    // Function to handle API calls with retry logic
    const callApiWithRetry = () => {
      // Check if enhanced API service is available
      if (window.VisualizationDataService && window.VisualizationDataService.calculateProbability) {
        console.log('Using enhanced VisualizationDataService for probability calculation');
        
        return window.VisualizationDataService.calculateProbability(
          state.goalId || 'new', // Use 'new' as ID for new goals
          formData,
          {
            // Callback for loading state changes
            onLoadingChange: (isLoading) => {
              setLoadingState(isLoading);
            },
            // Increase timeout for complex calculations
            timeout: 20000 // 20 seconds
          }
        ).then(result => {
          // Hide loading state using enhanced system
          if (config.useEnhancedLoadingStates && window.loadingState && elements.probabilitySection) {
            window.loadingState.setLoading(elements.probabilitySection, false);
          }
          
          // Ensure the result has valid probability
          const successProbability = result.successProbability !== undefined ? 
            parseFloat(result.successProbability) : 
            (result.success_probability !== undefined ? 
              parseFloat(result.success_probability) : 0);
              
          // Validate that we have a proper number
          if (isNaN(successProbability)) {
            console.warn("Received invalid probability value:", result.successProbability || result.success_probability);
            
            // Try to retry if we haven't exceeded retry count
            if (retries < config.failureRetryCount) {
              retries++;
              console.log(`Retrying probability calculation (attempt ${retries}/${config.failureRetryCount})`);
              return callApiWithRetry();
            }
          }
          
          // Transform result format if needed to match expected structure
          return {
            success_probability: isNaN(successProbability) ? 0 : successProbability,
            adjustments: result.adjustments || [],
            simulation_data: result.simulationData || {}
          };
        })
        .catch(error => {
          // Hide loading state using enhanced system
          if (config.useEnhancedLoadingStates && window.loadingState && elements.probabilitySection) {
            window.loadingState.setLoading(elements.probabilitySection, false);
          }
          
          // Try to retry if we haven't exceeded retry count
          if (retries < config.failureRetryCount) {
            retries++;
            console.log(`Retrying probability calculation after error (attempt ${retries}/${config.failureRetryCount}):`, error);
            return callApiWithRetry();
          }
          
          throw error;
        });
      } else {
        // Fall back to original implementation
        console.log('Using fallback fetch for probability calculation');
        return fetch(config.apiEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData)
        })
        .then(response => {
          // Hide loading state using enhanced system
          if (config.useEnhancedLoadingStates && window.loadingState && elements.probabilitySection) {
            window.loadingState.setLoading(elements.probabilitySection, false);
          }
          
          if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
          }
          return response.json();
        })
        .then(result => {
          // Ensure the result has valid probability
          const successProbability = result.success_probability !== undefined ? 
            parseFloat(result.success_probability) : 0;
            
          // Validate that we have a proper number
          if (isNaN(successProbability)) {
            console.warn("Received invalid probability value:", result.success_probability);
            
            // Try to retry if we haven't exceeded retry count
            if (retries < config.failureRetryCount) {
              retries++;
              console.log(`Retrying probability calculation (attempt ${retries}/${config.failureRetryCount})`);
              return callApiWithRetry();
            }
            
            // If we've exhausted retries, return 0
            result.success_probability = 0;
          } else {
            result.success_probability = successProbability;
          }
          
          return result;
        })
        .catch(error => {
          // Hide loading state using enhanced system
          if (config.useEnhancedLoadingStates && window.loadingState && elements.probabilitySection) {
            window.loadingState.setLoading(elements.probabilitySection, false);
          }
          
          // Try to retry if we haven't exceeded retry count
          if (retries < config.failureRetryCount) {
            retries++;
            console.log(`Retrying probability calculation after error (attempt ${retries}/${config.failureRetryCount}):`, error);
            return callApiWithRetry();
          }
          
          throw error;
        });
      }
    };
    
    // Start the API call with retry logic
    return callApiWithRetry();
  }

  /**
   * Update probability UI elements
   * @param {number} probability - Success probability (0-100)
   * @param {string} statusText - Status message to display
   */
  function updateProbabilityUI(probability, statusText) {
    // Ensure probability is a number in the 0-100 range
    const validProbability = isNaN(probability) ? 0 : Math.max(0, Math.min(100, probability));
    
    // Format probability to one decimal place
    const formattedProbability = validProbability.toFixed(1);
    
    // Check if there's a significant change to animate
    const previousValue = parseFloat(elements.probabilityValue.textContent || '0');
    const shouldAnimate = Math.abs(previousValue - validProbability) > 1 && !state.animationInProgress;
    
    // Update display elements with animation if needed
    if (shouldAnimate && !elements.probabilityValue.classList.contains('hidden')) {
      state.animationInProgress = true;
      
      // Add animation class
      elements.probabilityValue.classList.add('probability-changing');
      
      // Set a timeout to update the value and remove the animation class
      setTimeout(() => {
        elements.probabilityValue.textContent = `${formattedProbability}%`;
        
        // Set another timeout to remove the animation class
        setTimeout(() => {
          elements.probabilityValue.classList.remove('probability-changing');
          state.animationInProgress = false;
        }, 300);
      }, 300);
    } else {
      // Just update the value without animation
      elements.probabilityValue.textContent = `${formattedProbability}%`;
    }
    
    // Update loading state
    setLoadingState(false);
    
    // Animate progress bar if there's a change
    if (elements.probabilityBarFill) {
      // Add transition for smooth width change
      elements.probabilityBarFill.style.transition = 'width 0.5s ease-out, background-color 0.5s ease-out';
      
      // Update width after a tiny delay to ensure transition happens
      setTimeout(() => {
        elements.probabilityBarFill.style.width = `${validProbability}%`;
      }, 10);
      
      // Update color based on probability
      if (validProbability >= 70) {
        elements.probabilityBarFill.style.backgroundColor = '#28a745'; // Green
      } else if (validProbability >= 40) {
        elements.probabilityBarFill.style.backgroundColor = '#ffc107'; // Yellow
      } else {
        elements.probabilityBarFill.style.backgroundColor = '#dc3545'; // Red
      }
    }
    
    // Update status text with subtle animation
    if (elements.probabilityStatusText) {
      elements.probabilityStatusText.classList.add('text-changing');
      
      // Change the text after a small delay for transition effect
      setTimeout(() => {
        elements.probabilityStatusText.textContent = statusText;
        
        // Remove the animation class after transition completes
        setTimeout(() => {
          elements.probabilityStatusText.classList.remove('text-changing');
        }, 300);
      }, 200);
    }
  }

  /**
   * Set loading state for UI elements
   * @param {boolean} isLoading - Whether loading is in progress
   */
  function setLoadingState(isLoading) {
    state.isLoading = isLoading;
    
    // Update old loading indicator (for backward compatibility)
    if (elements.probabilityValue && elements.probabilityLoading) {
      if (isLoading) {
        elements.probabilityValue.classList.add('hidden');
        elements.probabilityLoading.classList.remove('hidden');
      } else {
        elements.probabilityValue.classList.remove('hidden');
        elements.probabilityLoading.classList.add('hidden');
      }
    }
    
    // Set aria attributes on the container for accessibility
    if (elements.probabilitySection) {
      elements.probabilitySection.setAttribute('aria-busy', isLoading ? 'true' : 'false');
    }
    
    // Use new loading state system if available and enabled
    if (config.useEnhancedLoadingStates && window.loadingState) {
      if (elements.goalForm) {
        // Add loading class to the input elements but don't show spinner
        document.querySelectorAll('[data-affects-probability="true"]').forEach(input => {
          input.classList.toggle('probability-calculating', isLoading);
        });
      }
    }
  }

  /**
   * Get status message based on probability
   * @param {number} probability - Success probability (0-100)
   * @returns {string} Status message
   */
  function getStatusMessage(probability) {
    if (probability >= 80) {
      return 'You are on track to achieve this goal on schedule.';
    } else if (probability >= 60) {
      return 'You have a good chance of achieving this goal with consistent effort.';
    } else if (probability >= 40) {
      return 'This goal may require some adjustments to improve your chances.';
    } else {
      return 'This goal appears challenging. Consider adjusting the parameters.';
    }
  }
  
  /**
   * Format currency with proper symbol and formatting
   * @param {number} amount - The amount to format
   * @param {string} currency - Currency code (default: 'INR')
   * @param {string} locale - Locale for formatting (default: 'en-IN')
   * @returns {string} Formatted currency string
   */
  function formatCurrency(amount, currency = 'INR', locale = 'en-IN') {
    try {
      // Ensure we use the Indian Rupee symbol
      return new Intl.NumberFormat(locale, { 
        style: 'currency',
        currency: currency,
        maximumFractionDigits: 0
      }).format(amount);
    } catch (e) {
      // Fallback to simple formatting
      return '₹' + Math.round(amount).toLocaleString('en-IN');
    }
  }

  /**
   * Update adjustment impacts based on API response
   * @param {Array} adjustments - Adjustment data from API
   */
  function updateAdjustmentImpacts(adjustments) {
    if (!elements.adjustmentImpacts) return;
    
    // Clear existing items
    elements.adjustmentImpacts.innerHTML = '';
    
    if (!adjustments || adjustments.length === 0) {
      elements.adjustmentImpacts.innerHTML = '<div class="no-adjustments">Fill in goal details to see potential adjustments.</div>';
      return;
    }
    
    // Add adjustment items to the UI with fade-in animation
    adjustments.forEach((adjustment, index) => {
      const impactEl = document.createElement('div');
      impactEl.className = 'adjustment-impact-item';
      impactEl.style.animationDelay = `${index * 100}ms`;
      
      const labelEl = document.createElement('div');
      labelEl.className = 'adjustment-label';
      labelEl.textContent = adjustment.description || 'Adjustment';
      
      const valueEl = document.createElement('div');
      const impact = adjustment.impact_metrics?.probability_increase || 0;
      const isPositive = impact > 0;
      valueEl.className = `adjustment-impact ${isPositive ? 'positive' : 'negative'}`;
      valueEl.textContent = isPositive ? `+${(impact * 100).toFixed(1)}%` : `${(impact * 100).toFixed(1)}%`;
      
      impactEl.appendChild(labelEl);
      impactEl.appendChild(valueEl);
      elements.adjustmentImpacts.appendChild(impactEl);
      
      // Add fade-in class after a small delay to trigger animation
      setTimeout(() => {
        impactEl.classList.add('fade-in');
      }, 10);
    });
  }

  /**
   * Update the visualization component if available
   * @param {Object} result - Probability calculation result from API
   */
  function updateVisualizer(result) {
    if (!window.GoalVisualizationInitializer || !elements.visualizerMount) return;
    
    // Update data attributes with new data
    elements.visualizerMount.dataset.goalProbability = result.success_probability || 0;
    
    // Extract simulation data if available
    if (result.simulation_data) {
      elements.visualizerMount.dataset.simulationData = JSON.stringify(result.simulation_data);
    }
    
    // Refresh the visualizer component
    try {
      window.GoalVisualizationInitializer.refreshVisualization('probabilistic-goal-visualizer', {
        successProbability: result.success_probability || 0,
        simulationData: result.simulation_data || {}
      });
      
      // Publish the event to notify other components
      if (window.DataEventBus) {
        window.DataEventBus.publish('probability-updated', {
          goalId: state.goalId,
          probability: result.success_probability || 0,
          simulationData: result.simulation_data || {},
          adjustments: result.adjustments || [],
          parameters: state.currentParameters,
          timestamp: Date.now()
        });
      }
    } catch (e) {
      console.warn('Error refreshing goal visualizer:', e);
      
      // Use global error handler if available
      if (window.loadingState && window.loadingState.showError) {
        window.loadingState.showError(`Error updating visualizations: ${e.message}`);
      }
    }
  }
  
  /**
   * Subscribe to data events from other components
   */
  function subscribeToDataEvents() {
    // Only proceed if the event bus is available
    if (!window.DataEventBus) return;
    
    // Listen for parameter changes from other components
    window.DataEventBus.subscribe('parameters-changed', (data) => {
      // Ignore if this is from the same component (prevent loops)
      if (data.source === 'goal-form') return;
      
      // Only process if it's for the current goal
      if (data.goalId && data.goalId === state.goalId) {
        // Check if this event is newer than our last change
        if (data.timestamp && data.timestamp < state.lastChangeTimestamp) {
          console.log('Ignoring outdated parameter change event');
          return;
        }
        
        console.log('Received parameters-changed event from another component', data);
        
        // Update the form values if they differ from current
        const parameters = data.parameters || {};
        let hasChanges = false;
        
        Object.keys(parameters).forEach(param => {
          const input = document.querySelector(`[name="${param}"]`);
          if (input && input.value !== parameters[param].toString()) {
            input.value = parameters[param];
            hasChanges = true;
          }
        });
        
        // Only trigger calculation if there were actual changes
        if (hasChanges) {
          triggerProbabilityUpdate();
        }
      }
    });
    
    // Listen for probability updates from other components
    window.DataEventBus.subscribe('probability-updated', (data) => {
      // Ignore if this is from the current component
      if (data.source === 'goal-form') return;
      
      // Only process if it's for the current goal
      if (data.goalId && data.goalId === state.goalId) {
        console.log('Received probability-updated event from another component', data);
        
        // If we're not currently calculating, update the UI
        if (!state.isLoading && data.probability !== undefined) {
          updateProbabilityUI(data.probability, getStatusMessage(data.probability));
          
          // Update visualization if simulation data is provided
          if (data.simulationData && window.GoalVisualizationInitializer && elements.visualizerMount) {
            window.GoalVisualizationInitializer.refreshVisualization('probabilistic-goal-visualizer', {
              successProbability: data.probability,
              simulationData: data.simulationData
            });
          }
          
          // Update adjustment impacts if provided
          if (data.adjustments) {
            updateAdjustmentImpacts(data.adjustments);
          }
        }
      }
    });
  }

  // Public API
  return {
    init,
    calculateProbability,
    getFormValues,
    updateProbabilityUI
  };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  GoalFormProbability.init();
  
  // Add CSS transitions for smooth updates
  const style = document.createElement('style');
  style.textContent = `
    /* Animated value transitions */
    .animated-value {
      transition: color 0.3s ease-out;
    }
    
    .probability-changing {
      opacity: 0.5;
      transition: opacity 0.3s ease-in-out;
    }
    
    .text-changing {
      opacity: 0.5;
      transition: opacity 0.3s ease-in-out;
    }
    
    .update-pending {
      animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.7; }
      100% { opacity: 1; }
    }
    
    /* Inputs that affect probability */
    [data-affects-probability="true"] {
      transition: border-color 0.3s ease-out;
    }
    
    [data-affects-probability="true"].probability-calculating {
      border-color: #add8e6;
      background-color: rgba(173, 216, 230, 0.05);
    }
    
    /* Required input highlighting */
    .highlight-required {
      animation: highlightBorder 1s ease-in-out;
    }
    
    @keyframes highlightBorder {
      0% { border-color: inherit; }
      50% { border-color: #ff0000; box-shadow: 0 0 5px rgba(255, 0, 0, 0.5); }
      100% { border-color: inherit; }
    }
    
    /* Fade-in animation for adjustment impacts */
    .adjustment-impact-item {
      opacity: 0;
      transform: translateY(10px);
    }
    
    .adjustment-impact-item.fade-in {
      opacity: 1;
      transform: translateY(0);
      transition: opacity 0.5s ease-out, transform 0.5s ease-out;
    }
  `;
  document.head.appendChild(style);
});