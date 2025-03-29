/**
 * JavaScript module for handling scenario comparison and application.
 */

const ScenarioComparisonHandler = (function() {
  // Configuration
  const config = {
    apiEndpoint: '/api/v2/goals/{goal_id}/apply-scenario',
    requestTimeout: 20000, // 20 second timeout for AJAX requests
    retryAttempts: 1,      // Number of retry attempts for failed requests
    loadingClass: 'is-applying-scenario', // CSS class added to elements while scenarios are being applied
    successMessageDuration: 3000 // How long to show success message (ms)
  };

  // Track active requests
  const activeRequests = {};
  
  // Track state of the currently selected scenario for each goal
  const scenarioSelections = {};

  /**
   * Initializes event listeners for scenario comparison tools
   */
  function initialize() {
    // Listen for scenario selection changes
    document.addEventListener('change', handleScenarioSelectionChange);
    
    // Listen for apply scenario button clicks
    document.addEventListener('click', handleScenarioApplyClick);
    
    // Listen for custom events from React components
    document.addEventListener('scenarioSelected', handleScenarioSelectedEvent);
    
    // Initialize scenario selection toggles
    initializeScenarioToggles();
    
    // Initialize scenario detail expanders
    initializeScenarioDetailExpanders();
  }

  /**
   * Initializes scenario toggle buttons in the UI
   */
  function initializeScenarioToggles() {
    const toggles = document.querySelectorAll('.scenario-toggle');
    
    toggles.forEach(toggle => {
      // If this is a radio button or similar input, set up its change handler
      if (toggle.tagName === 'INPUT') {
        // Store initial selection
        if (toggle.checked && toggle.dataset.goalId && toggle.dataset.scenarioId) {
          scenarioSelections[toggle.dataset.goalId] = toggle.dataset.scenarioId;
        }
      }
      // For other toggle types (like buttons), set up click handler
      else {
        toggle.addEventListener('click', function(event) {
          const goalId = this.dataset.goalId;
          const scenarioId = this.dataset.scenarioId;
          
          if (!goalId || !scenarioId) return;
          
          // Remove active class from all toggles for this goal
          const togglesForThisGoal = document.querySelectorAll(`.scenario-toggle[data-goal-id="${goalId}"]`);
          togglesForThisGoal.forEach(t => t.classList.remove('active'));
          
          // Add active class to this toggle
          this.classList.add('active');
          
          // Update scenario selection state
          scenarioSelections[goalId] = scenarioId;
          
          // Trigger scenario display update
          updateScenarioDisplay(goalId, scenarioId);
        });
      }
    });
  }

  /**
   * Initializes expanders for scenario detail sections
   */
  function initializeScenarioDetailExpanders() {
    const expanders = document.querySelectorAll('.scenario-detail-expander');
    
    expanders.forEach(expander => {
      expander.addEventListener('click', function(event) {
        // Find the target detail section
        const targetId = this.dataset.target;
        if (!targetId) return;
        
        const detailSection = document.getElementById(targetId);
        if (!detailSection) return;
        
        // Toggle the visibility
        if (detailSection.classList.contains('hidden')) {
          detailSection.classList.remove('hidden');
          this.textContent = 'Hide Details';
        } else {
          detailSection.classList.add('hidden');
          this.textContent = 'Show Details';
        }
      });
    });
  }

  /**
   * Updates the display when a scenario is selected
   * @param {string} goalId - The goal ID
   * @param {string} scenarioId - The selected scenario ID
   */
  function updateScenarioDisplay(goalId, scenarioId) {
    // Find scenario content sections for this goal
    const scenarioSections = document.querySelectorAll(`.scenario-content[data-goal-id="${goalId}"]`);
    
    scenarioSections.forEach(section => {
      // Hide all sections initially
      section.classList.add('hidden');
      
      // Show the selected section
      if (section.dataset.scenarioId === scenarioId) {
        section.classList.remove('hidden');
      }
    });
    
    // Update any React components if available
    updateReactComponents(goalId, scenarioId);
    
    // Trigger a custom event for other parts of the application to react to
    const event = new CustomEvent('scenarioChanged', {
      detail: {
        goalId,
        scenarioId
      }
    });
    document.dispatchEvent(event);
  }

  /**
   * Updates React components when a scenario is selected
   * @param {string} goalId - The goal ID
   * @param {string} scenarioId - The selected scenario ID
   */
  function updateReactComponents(goalId, scenarioId) {
    // Find the scenario comparison chart component
    const chartElement = document.querySelector(`#scenario-comparison-chart[data-goal-id="${goalId}"]`);
    if (!chartElement) return;
    
    // If the GoalVisualizationInitializer is available, use it to update the component
    if (window.GoalVisualizationInitializer) {
      // Update the data attribute to reflect the selected scenario
      chartElement.dataset.selectedScenario = scenarioId;
      
      // Refresh the component with the new selection
      window.GoalVisualizationInitializer.refreshVisualization('scenario-comparison-chart', {
        selectedScenario: scenarioId
      });
    }
  }

  /**
   * Handles changes to scenario selection inputs
   * @param {Event} event - The change event
   */
  function handleScenarioSelectionChange(event) {
    // Check if this is a scenario selection input
    if (!event.target.classList.contains('scenario-toggle') || event.target.tagName !== 'INPUT') {
      return;
    }
    
    const toggle = event.target;
    const goalId = toggle.dataset.goalId;
    const scenarioId = toggle.dataset.scenarioId;
    
    if (!goalId || !scenarioId || !toggle.checked) return;
    
    // Update scenario selection state
    scenarioSelections[goalId] = scenarioId;
    
    // Update the display
    updateScenarioDisplay(goalId, scenarioId);
  }

  /**
   * Handles clicks on scenario apply buttons
   * @param {Event} event - The click event
   */
  function handleScenarioApplyClick(event) {
    // Find closest button with scenario-apply class
    const applyButton = event.target.closest('.scenario-apply-btn');
    if (!applyButton) return;
    
    // Prevent default action
    event.preventDefault();
    
    // Get scenario ID and goal ID from data attributes
    const scenarioId = applyButton.dataset.scenarioId;
    const goalId = applyButton.dataset.goalId;
    
    if (!scenarioId || !goalId) {
      console.error('Missing scenario ID or goal ID');
      return;
    }
    
    // Apply the scenario
    applyScenario(goalId, scenarioId, applyButton);
  }

  /**
   * Handles scenario selection events from React components
   * @param {CustomEvent} event - The custom event
   */
  function handleScenarioSelectedEvent(event) {
    const { goalId, scenarioId, element } = event.detail;
    
    if (!scenarioId || !goalId) {
      console.error('Missing scenario ID or goal ID in custom event');
      return;
    }
    
    // Update scenario selection state
    scenarioSelections[goalId] = scenarioId;
    
    // Update the display
    updateScenarioDisplay(goalId, scenarioId);
  }

  /**
   * Applies a scenario to a goal
   * @param {string} goalId - The goal ID
   * @param {string} scenarioId - The scenario ID to apply
   * @param {HTMLElement} [triggerElement] - The element that triggered the application (optional)
   * @returns {Promise} Promise resolving to scenario application result
   */
  async function applyScenario(goalId, scenarioId, triggerElement = null) {
    // Check if there's already an active request for this scenario
    const requestKey = `${goalId}_${scenarioId}`;
    if (activeRequests[requestKey]) {
      console.warn('Scenario application already in progress');
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
    
    // Show loading state on the scenario container
    const goalCard = document.querySelector(`.goal-card[data-goal-id="${goalId}"]`);
    const scenarioPanel = goalCard?.querySelector('.visualization-content[data-content="scenarios"]');
    if (scenarioPanel) {
      scenarioPanel.classList.add(config.loadingClass);
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
          scenario_id: scenarioId
        })
      });
      
      // Check if the request was successful
      if (!response.ok) {
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.message || `Failed to apply scenario (HTTP ${response.status})`;
        } catch (e) {
          errorMessage = `Failed to apply scenario (HTTP ${response.status})`;
        }
        
        throw new Error(errorMessage);
      }
      
      // Parse the response data
      const data = await response.json();
      
      // Show success state
      showSuccessMessage(triggerElement || scenarioPanel, data);
      
      // Refresh the visualizations with new data
      refreshVisualizations(goalId, data);
      
      return data;
    } catch (error) {
      console.error('Error applying scenario:', error);
      
      // Show error state
      showErrorMessage(triggerElement || scenarioPanel, error.message);
      
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
      if (scenarioPanel) {
        scenarioPanel.classList.remove(config.loadingClass);
      }
      
      // Remove the active request
      delete activeRequests[requestKey];
    }
  }

  /**
   * Shows a success message after scenario is applied
   * @param {HTMLElement} element - Element to show success message on or near
   * @param {Object} data - Response data from the API
   */
  function showSuccessMessage(element, data) {
    if (!element) return;
    
    // Create success message element
    const messageElement = document.createElement('div');
    messageElement.className = 'scenario-success-message';
    messageElement.innerHTML = `
      <div class="p-2 rounded bg-green-100 text-green-800 text-sm mt-2 mb-2">
        <svg class="inline-block w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
        </svg>
        Scenario applied successfully
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
   * Shows an error message when scenario application fails
   * @param {HTMLElement} element - Element to show error message on or near
   * @param {string} errorMessage - The error message to display
   */
  function showErrorMessage(element, errorMessage) {
    if (!element) return;
    
    // Create error message element
    const messageElement = document.createElement('div');
    messageElement.className = 'scenario-error-message';
    messageElement.innerHTML = `
      <div class="p-2 rounded bg-red-100 text-red-800 text-sm mt-2 mb-2">
        <svg class="inline-block w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        ${errorMessage || 'Failed to apply scenario'}
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
          console.log('Visualizations refreshed with new data after scenario application');
        },
        onError: (error) => {
          console.error('Failed to refresh visualizations:', error);
        }
      });
    }
    
    // Update goal details in the UI based on the new scenario
    if (data.goal_details) {
      updateGoalDetails(goalId, data.goal_details);
    }
    
    // Update scenario display to show it's now the current scenario
    if (data.applied_scenario_id) {
      // Mark this scenario as the current scenario in the UI
      markScenarioAsCurrent(goalId, data.applied_scenario_id);
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
          
        case 'success-probability':
        case 'probability':
          if (details.success_probability !== undefined) {
            element.textContent = `${Math.round(details.success_probability * 100)}%`;
            
            // Update classes for probability color coding
            const probability = details.success_probability;
            element.className = ''; // Reset classes
            if (probability >= 0.7) {
              element.classList.add('text-green-600', 'font-medium');
            } else if (probability >= 0.5) {
              element.classList.add('text-amber-600', 'font-medium');
            } else {
              element.classList.add('text-red-600', 'font-medium');
            }
          }
          break;
      }
    });
  }

  /**
   * Marks a scenario as the current scenario in the UI
   * @param {string} goalId - The goal ID
   * @param {string} scenarioId - The scenario ID to mark as current
   */
  function markScenarioAsCurrent(goalId, scenarioId) {
    // Find all scenario elements for this goal
    const scenarioElements = document.querySelectorAll(`.scenario-item[data-goal-id="${goalId}"]`);
    
    scenarioElements.forEach(element => {
      // Remove current class from all scenarios
      element.classList.remove('is-current');
      
      // Remove any "current" labels
      const currentLabel = element.querySelector('.current-scenario-label');
      if (currentLabel) {
        currentLabel.remove();
      }
      
      // If this is the applied scenario, mark it as current
      if (element.dataset.scenarioId === scenarioId) {
        element.classList.add('is-current');
        
        // Add a "Current" label
        const labelElement = document.createElement('span');
        labelElement.className = 'current-scenario-label px-2 py-1 ml-2 bg-green-100 text-green-800 text-xs rounded';
        labelElement.textContent = 'Current';
        
        // Find the title element to append the label to
        const titleElement = element.querySelector('.scenario-title');
        if (titleElement) {
          titleElement.appendChild(labelElement);
        } else {
          // If no title element, append to the scenario element itself
          element.appendChild(labelElement);
        }
        
        // Disable the "Apply" button for this scenario
        const applyButton = element.querySelector('.scenario-apply-btn');
        if (applyButton) {
          applyButton.disabled = true;
          applyButton.classList.add('opacity-50');
          applyButton.title = 'This scenario is already applied';
        }
      } else {
        // Enable the "Apply" button for other scenarios
        const applyButton = element.querySelector('.scenario-apply-btn');
        if (applyButton) {
          applyButton.disabled = false;
          applyButton.classList.remove('opacity-50');
          applyButton.title = 'Apply this scenario to your goal';
        }
      }
    });
  }

  /**
   * Gets the currently selected scenario for a goal
   * @param {string} goalId - The goal ID
   * @returns {string|null} The selected scenario ID or null if none selected
   */
  function getSelectedScenario(goalId) {
    return scenarioSelections[goalId] || null;
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
    getSelectedScenario,
    applyScenario,
    updateScenarioDisplay,
    refreshVisualizations,
    configure
  };
})();

// Make the handler available globally
window.ScenarioComparisonHandler = ScenarioComparisonHandler;