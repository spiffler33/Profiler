/**
 * JavaScript module for handling user actions on goal adjustment recommendations.
 */

const GoalAdjustmentHandler = (function() {
  // Configuration
  const config = {
    apiEndpoint: '/api/v2/goals/{goal_id}/apply-adjustment',
    requestTimeout: 20000, // 20 second timeout for AJAX requests
    retryAttempts: 1,     // Number of retry attempts for failed requests
    loadingClass: 'is-applying-adjustment', // CSS class added to elements while adjustments are being applied
    successMessageDuration: 3000 // How long to show success message (ms)
  };

  // Track active requests
  const activeRequests = {};

  /**
   * Initializes event listeners for adjustment recommendations
   */
  function initialize() {
    // Listen for clicks on Apply buttons in adjustment panels
    document.addEventListener('click', handleAdjustmentClick);
    
    // Listen for selection events from React component
    document.addEventListener('goalAdjustmentSelected', handleAdjustmentSelected);
  }

  /**
   * Handles clicks on DOM elements related to adjustments
   * @param {Event} event - The click event
   */
  function handleAdjustmentClick(event) {
    // Find closest button with adjustment-apply class
    const applyButton = event.target.closest('.adjustment-apply-btn');
    if (!applyButton) return;
    
    // Prevent default action
    event.preventDefault();
    
    // Get adjustment ID and goal ID from data attributes
    const adjustmentId = applyButton.dataset.adjustmentId;
    const goalId = applyButton.dataset.goalId;
    
    if (!adjustmentId || !goalId) {
      console.error('Missing adjustment ID or goal ID');
      return;
    }
    
    // Apply the adjustment
    applyAdjustment(goalId, adjustmentId, applyButton);
  }

  /**
   * Handles adjustment selection from the React component
   * @param {CustomEvent} event - The custom event with adjustment details
   */
  function handleAdjustmentSelected(event) {
    const { goalId, adjustmentId, element } = event.detail;
    
    if (!adjustmentId || !goalId) {
      console.error('Missing adjustment ID or goal ID in custom event');
      return;
    }
    
    // Apply the selected adjustment
    applyAdjustment(goalId, adjustmentId, element);
  }

  /**
   * Applies an adjustment to a goal
   * @param {string} goalId - The goal ID
   * @param {string} adjustmentId - The adjustment ID
   * @param {HTMLElement} [triggerElement] - The element that triggered the adjustment (optional)
   * @returns {Promise} Promise resolving to adjustment result
   */
  async function applyAdjustment(goalId, adjustmentId, triggerElement = null) {
    // Check if there's already an active request for this adjustment
    const requestKey = `${goalId}_${adjustmentId}`;
    if (activeRequests[requestKey]) {
      console.warn('Adjustment application already in progress');
      return;
    }
    
    // Create a request tracker
    activeRequests[requestKey] = { timestamp: Date.now() };
    
    // Show loading state on trigger element if provided
    if (triggerElement) {
      triggerElement.classList.add(config.loadingClass);
      triggerElement.disabled = true;
      
      // Store original text if it's a button
      if (triggerElement.tagName === 'BUTTON') {
        activeRequests[requestKey].originalText = triggerElement.textContent;
        triggerElement.textContent = 'Applying...';
      }
    }
    
    // Show loading state on the adjustment panel container
    const panelElement = document.getElementById('adjustment-impact-panel');
    if (panelElement) {
      panelElement.classList.add(config.loadingClass);
    }
    
    try {
      // Construct API endpoint URL
      const endpoint = config.apiEndpoint.replace('{goal_id}', goalId);
      
      // Make the API request
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          adjustment_id: adjustmentId
        })
      });
      
      // Check if the request was successful
      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || `Failed to apply adjustment (HTTP ${response.status})`;
        } catch (e) {
          errorMessage = `Failed to apply adjustment (HTTP ${response.status})`;
        }
        
        throw new Error(errorMessage);
      }
      
      // Parse the response data
      const data = await response.json();
      
      // Show success state
      showSuccessMessage(triggerElement || panelElement, data);
      
      // Refresh the visualizations with new data
      refreshVisualizations(goalId, data);
      
      return data;
    } catch (error) {
      console.error('Error applying adjustment:', error);
      
      // Show error state
      showErrorMessage(triggerElement || panelElement, error.message);
      
      throw error;
    } finally {
      // Clean up the loading state
      if (triggerElement) {
        triggerElement.classList.remove(config.loadingClass);
        triggerElement.disabled = false;
        
        // Restore original text if it was saved
        if (activeRequests[requestKey]?.originalText && triggerElement.tagName === 'BUTTON') {
          triggerElement.textContent = activeRequests[requestKey].originalText;
        }
      }
      
      // Remove loading class from panel
      if (panelElement) {
        panelElement.classList.remove(config.loadingClass);
      }
      
      // Remove the active request
      delete activeRequests[requestKey];
    }
  }

  /**
   * Shows a success message after adjustment is applied
   * @param {HTMLElement} element - Element to show success message on or near
   * @param {Object} data - Response data from the API
   */
  function showSuccessMessage(element, data) {
    if (!element) return;
    
    // Create success message element
    const messageElement = document.createElement('div');
    messageElement.className = 'adjustment-success-message';
    messageElement.innerHTML = `
      <div class="p-2 rounded bg-green-100 text-green-800 text-sm mt-2 mb-2">
        <svg class="inline-block w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        Adjustment applied successfully
      </div>
    `;
    
    // Insert the message after the element
    element.parentNode.insertBefore(messageElement, element.nextSibling);
    
    // Remove the message after a delay
    setTimeout(() => {
      messageElement.classList.add('fade-out');
      setTimeout(() => {
        if (messageElement.parentNode) {
          messageElement.parentNode.removeChild(messageElement);
        }
      }, 300);
    }, config.successMessageDuration);
  }

  /**
   * Shows an error message when adjustment application fails
   * @param {HTMLElement} element - Element to show error message on or near
   * @param {string} errorMessage - The error message to display
   */
  function showErrorMessage(element, errorMessage) {
    if (!element) return;
    
    // Create error message element
    const messageElement = document.createElement('div');
    messageElement.className = 'adjustment-error-message';
    messageElement.innerHTML = `
      <div class="p-2 rounded bg-red-100 text-red-800 text-sm mt-2 mb-2">
        <svg class="inline-block w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        ${errorMessage || 'Failed to apply adjustment'}
      </div>
    `;
    
    // Insert the message after the element
    element.parentNode.insertBefore(messageElement, element.nextSibling);
    
    // Remove the message after a delay
    setTimeout(() => {
      messageElement.classList.add('fade-out');
      setTimeout(() => {
        if (messageElement.parentNode) {
          messageElement.parentNode.removeChild(messageElement);
        }
      }, 300);
    }, config.successMessageDuration * 1.5);
  }

  /**
   * Refreshes all visualizations with updated goal data
   * @param {string} goalId - The goal ID that was updated
   * @param {Object} data - New data from the API response
   */
  function refreshVisualizations(goalId, data) {
    if (!window.GoalVisualizationInitializer) {
      console.error('GoalVisualizationInitializer not found. Visualizations will not be updated.');
      return;
    }
    
    // Refresh all visualizations with the new data
    if (data.visualization_data) {
      window.GoalVisualizationInitializer.refreshAll(data.visualization_data);
    } else {
      // If the API didn't return visualization data, fetch it
      window.GoalVisualizationInitializer.fetchAndRefresh(goalId, {
        forceRefresh: true,
        onSuccess: (freshData) => {
          console.log('Visualizations refreshed with new data');
        },
        onError: (error) => {
          console.error('Failed to refresh visualizations:', error);
        }
      });
    }
    
    // Find and update any standalone probability displays
    const probabilityElements = document.querySelectorAll(`[data-goal-id="${goalId}"][data-probability]`);
    if (data.new_probability !== undefined && probabilityElements.length > 0) {
      probabilityElements.forEach(element => {
        element.textContent = `${Math.round(data.new_probability * 100)}%`;
        
        // Update classes based on new probability value
        const probability = data.new_probability;
        if (probability >= 0.7) {
          element.className = 'text-green-600 font-medium';
        } else if (probability >= 0.5) {
          element.className = 'text-amber-600 font-medium';
        } else {
          element.className = 'text-red-600 font-medium';
        }
        
        // Update the data attribute
        element.dataset.probability = data.new_probability;
      });
    }
    
    // Update the goal details if changed
    if (data.goal_details) {
      updateGoalDetails(goalId, data.goal_details);
    }
  }

  /**
   * Updates goal details in the DOM based on API response
   * @param {string} goalId - The goal ID
   * @param {Object} details - Updated goal details from API
   */
  function updateGoalDetails(goalId, details) {
    // Find goal detail elements by data attribute
    const detailElements = document.querySelectorAll(`[data-goal-id="${goalId}"][data-detail]`);
    
    detailElements.forEach(element => {
      const detailType = element.dataset.detail;
      
      // Update element based on detail type
      switch (detailType) {
        case 'target':
          if (details.target_amount !== undefined) {
            element.textContent = formatCurrency(details.target_amount);
          }
          break;
        
        case 'timeline':
        case 'timeframe':
          if (details.timeframe !== undefined) {
            element.textContent = details.timeframe;
          }
          break;
        
        case 'monthly-contribution':
        case 'contribution':
          if (details.monthly_contribution !== undefined) {
            element.textContent = formatCurrency(details.monthly_contribution);
          }
          break;
        
        case 'allocation':
          if (details.allocation !== undefined) {
            // Format allocation as percentages
            const allocationText = Object.entries(details.allocation)
              .map(([asset, percent]) => `${asset}: ${Math.round(percent * 100)}%`)
              .join(', ');
            element.textContent = allocationText;
          }
          break;
          
        // Add other detail types as needed
      }
    });
  }

  /**
   * Formats a number as currency (defaults to Indian Rupees)
   * @param {number} amount - The amount to format
   * @param {string} [locale='en-IN'] - The locale to use
   * @param {string} [currency='INR'] - The currency code
   * @returns {string} Formatted currency string
   */
  function formatCurrency(amount, locale = 'en-IN', currency = 'INR') {
    if (amount === undefined || amount === null) return '';
    
    try {
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        maximumFractionDigits: 0
      }).format(amount);
    } catch (e) {
      // Fallback to basic formatting
      return `₹${Math.round(amount).toLocaleString()}`;
    }
  }

  /**
   * Updates configuration options
   * @param {Object} options - New configuration options
   */
  function configure(options = {}) {
    Object.assign(config, options);
  }

  // Initialize when the DOM is ready
  document.addEventListener('DOMContentLoaded', initialize);

  // Public API
  return {
    initialize,
    applyAdjustment,
    configure,
    refreshVisualizations
  };
})();

// Make the handler available globally
window.GoalAdjustmentHandler = GoalAdjustmentHandler;