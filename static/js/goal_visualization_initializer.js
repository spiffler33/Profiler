/**
 * JavaScript module for initializing and mounting React visualization components 
 * with real-time data from the backend API.
 * 
 * ENHANCED VERSION: Improved data synchronization between components
 */

const GoalVisualizationInitializer = (function() {
  // Default configuration
  const config = {
    apiEndpoint: '/api/v2/goals/{goal_id}/visualization-data',
    requestTimeout: 15000, // 15 second timeout for fetch requests
    retryAttempts: 2,      // Number of retry attempts for failed requests
    retryDelay: 1000,      // Delay between retry attempts (ms)
    refreshInterval: null, // Auto-refresh interval (set to null to disable)
    loadingIndicatorDelay: 200, // Delay before showing loading indicators (ms)
    debug: true,           // Enable debug logging
    enableEventBus: true,   // Use DataEventBus for component synchronization
    
    // Performance optimization
    usePerformanceOptimizer: true,           // Use performance optimization features
    throttleDomUpdates: true,                // Throttle DOM updates for better performance
    batchComponentUpdates: true,             // Batch component updates using requestAnimationFrame
    useDebounceForInputs: true,              // Debounce input events for performance
    debounceDelay: 250,                      // Debounce delay for inputs (ms)
    measureComponentPerformance: false,      // Track component render times
    enableMemoization: true,                 // Memoize expensive operations
    logPerformanceWarnings: false,           // Log slow operations
    slowRenderThreshold: 50,                 // Threshold for slow render warnings (ms)
    useOptimizedCache: true                  // Use optimized caching from PerformanceOptimizer
  };
  
  // Component states to track loading/error states
  const componentStates = {
    'probabilistic-goal-visualizer': { loading: false, error: null },
    'adjustment-impact-panel': { loading: false, error: null },
    'scenario-comparison-chart': { loading: false, error: null }
  };
  
  // Abort controllers for fetch requests (allows cancelling in-flight requests)
  const abortControllers = {};
  
  // Tracking for active components and their registrations with the event bus
  const componentRegistrations = {};
  
  // Event subscriptions for cleanup
  const eventSubscriptions = [];

  /**
   * Safely parses JSON data from data attributes
   * @param {string} jsonString - The JSON string to parse
   * @param {any} defaultValue - Default value if parsing fails
   * @return {any} Parsed object or default value
   */
  function safeJSONParse(jsonString, defaultValue) {
    if (!jsonString) return defaultValue;
    
    try {
      return JSON.parse(jsonString);
    } catch (error) {
      console.error('Error parsing JSON data:', error);
      return defaultValue;
    }
  }
  
  /**
   * Sets the loading state for a component and updates the UI accordingly
   * @param {string} componentId - ID of the component
   * @param {boolean} isLoading - Whether the component is loading
   */
  function setComponentLoading(componentId, isLoading) {
    // Update internal state
    if (componentStates[componentId]) {
      componentStates[componentId].loading = isLoading;
    }
    
    // Get mount element
    const mountElement = document.getElementById(componentId);
    if (!mountElement) return;
    
    // Use the common loading state system if available
    if (window.loadingState && typeof window.loadingState.setLoading === 'function') {
      window.loadingState.setLoading(mountElement, isLoading, {
        size: 'default',
        text: 'Loading visualization...',
        showProgressBar: false
      });
      return;
    }
    
    // Fallback to legacy loading UI implementation
    if (isLoading) {
      // Add loading class to mount element
      mountElement.classList.add('loading');
      
      // Get or create loading indicator
      let loadingIndicator = mountElement.querySelector('.visualization-loading');
      if (!loadingIndicator) {
        loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'visualization-loading';
        loadingIndicator.innerHTML = `
          <div class="loading-spinner"></div>
          <div class="loading-text">Loading visualization...</div>
        `;
        mountElement.appendChild(loadingIndicator);
      } else {
        loadingIndicator.classList.remove('hidden');
      }
    } else {
      // Remove loading class
      mountElement.classList.remove('loading');
      
      // Hide loading indicator if it exists
      const loadingIndicator = mountElement.querySelector('.visualization-loading');
      if (loadingIndicator) {
        loadingIndicator.classList.add('hidden');
      }
    }
  }
  
  /**
   * Sets the error state for a component and updates the UI accordingly
   * @param {string} componentId - ID of the component
   * @param {Error|null} error - Error object or null to clear error
   */
  function setComponentError(componentId, error) {
    // Update internal state
    if (componentStates[componentId]) {
      componentStates[componentId].error = error;
    }
    
    // Get mount element
    const mountElement = document.getElementById(componentId);
    if (!mountElement) return;
    
    // For errors, use the global error message if available
    if (error && window.loadingState && typeof window.loadingState.showError === 'function') {
      window.loadingState.showError(`Visualization Error: ${error.message || 'Unknown error'}`);
      
      // Still mark the component as having an error
      mountElement.classList.add('error');
      
      // Create a simplified error message in the component
      let errorElement = mountElement.querySelector('.visualization-error');
      if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'visualization-error';
        mountElement.appendChild(errorElement);
      }
      
      // Add basic error message and retry button
      errorElement.innerHTML = `
        <div class="error-message">Unable to load visualization</div>
        <button class="retry-button">Retry</button>
      `;
      
      // Add retry button listener
      const retryButton = errorElement.querySelector('.retry-button');
      if (retryButton) {
        retryButton.addEventListener('click', () => {
          // Clear error state
          setComponentError(componentId, null);
          
          // Extract goal ID from element data attributes
          const goalId = mountElement.dataset.goalId;
          if (goalId) {
            // Retry fetching data for this component
            fetchComponentData(goalId, componentId);
          }
        });
      }
      
      errorElement.classList.remove('hidden');
      return;
    }
    
    // Fallback to legacy error UI implementation
    if (error) {
      // Add error class to mount element
      mountElement.classList.add('error');
      
      // Get or create error message element
      let errorElement = mountElement.querySelector('.visualization-error');
      if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'visualization-error';
        mountElement.appendChild(errorElement);
      }
      
      // Set error message
      errorElement.textContent = `Unable to load visualization: ${error.message || 'Unknown error'}`;
      errorElement.classList.remove('hidden');
      
      // Add retry button
      let retryButton = errorElement.querySelector('.retry-button');
      if (!retryButton) {
        retryButton = document.createElement('button');
        retryButton.className = 'retry-button';
        retryButton.textContent = 'Retry';
        retryButton.addEventListener('click', () => {
          // Extract goal ID from element data attributes
          const goalId = mountElement.dataset.goalId;
          if (goalId) {
            // Retry fetching data for this component
            fetchComponentData(goalId, componentId);
          }
        });
        errorElement.appendChild(retryButton);
      }
    } else {
      // Remove error class
      mountElement.classList.remove('error');
      
      // Hide error message if it exists
      const errorElement = mountElement.querySelector('.visualization-error');
      if (errorElement) {
        errorElement.classList.add('hidden');
      }
    }
  }
  
  /**
   * Initializes the Probabilistic Goal Visualizer component with data
   * @param {Object} data - Component data from API or data attributes
   */
  function initProbabilisticGoalVisualizer(data = null) {
    const mountElement = document.getElementById('probabilistic-goal-visualizer');
    if (!mountElement) return;
    
    try {
      // Clear any previous error state
      setComponentError('probabilistic-goal-visualizer', null);
      
      // Use provided data or extract from data attributes
      let visualizerData = data;
      if (!visualizerData) {
        const dataset = mountElement.dataset;
        visualizerData = {
          goalId: dataset.goalId,
          targetAmount: parseFloat(dataset.goalTarget) || 0,
          timeframe: dataset.goalTimeline || '',
          successProbability: parseFloat(dataset.goalProbability) || 0,
          simulationData: safeJSONParse(dataset.simulationData, {})
        };
      }
      
      // Validate required data
      if (!visualizerData.goalId) {
        console.warn('Goal ID is missing for ProbabilisticGoalVisualizer');
        mountElement.innerHTML = '<div class="error-message">Missing goal identifier</div>';
        return;
      }
      
      // Ensure we have default values for any missing properties
      const completeData = {
        goalId: visualizerData.goalId,
        targetAmount: visualizerData.targetAmount || 0,
        timeframe: visualizerData.timeframe || '',
        successProbability: visualizerData.successProbability || 0,
        simulationData: visualizerData.simulationData || {},
        simulationOutcomes: visualizerData.simulationOutcomes || (visualizerData.simulationData?.simulationOutcomes || {
          median: visualizerData.targetAmount || 0,
          percentiles: {
            '10': 0, '25': 0, '50': 0, '75': 0, '90': 0
          }
        }),
        timeBasedMetrics: visualizerData.timeBasedMetrics || (visualizerData.simulationData?.timeBasedMetrics || {
          probabilityOverTime: {
            labels: ['Start', 'End'],
            values: [0, visualizerData.successProbability || 0]
          }
        })
      };
      
      // Render the React component
      ReactDOM.render(
        React.createElement(ProbabilisticGoalVisualizer, {
          goalId: completeData.goalId,
          targetAmount: completeData.targetAmount,
          timeframe: completeData.timeframe,
          successProbability: completeData.successProbability,
          simulationOutcomes: completeData.simulationOutcomes,
          timeBasedMetrics: completeData.timeBasedMetrics,
          onError: (err) => {
            console.error('ProbabilisticGoalVisualizer error:', err);
            setComponentError('probabilistic-goal-visualizer', err);
          }
        }),
        mountElement
      );
    } catch (error) {
      console.error('Failed to initialize ProbabilisticGoalVisualizer:', error);
      setComponentError('probabilistic-goal-visualizer', error);
    }
  }
  
  /**
   * Initializes the Adjustment Impact Panel component with data
   * @param {Object} data - Component data from API or data attributes
   */
  function initAdjustmentImpactPanel(data = null) {
    const mountElement = document.getElementById('adjustment-impact-panel');
    if (!mountElement) return;
    
    try {
      // Clear any previous error state
      setComponentError('adjustment-impact-panel', null);
      
      // Use provided data or extract from data attributes
      let adjustmentData = data;
      if (!adjustmentData) {
        const dataset = mountElement.dataset;
        adjustmentData = {
          goalId: dataset.goalId,
          adjustments: safeJSONParse(dataset.adjustments, []),
          currentProbability: parseFloat(dataset.currentProbability) || 0
        };
      }
      
      // Validate required data
      if (!adjustmentData.goalId) {
        console.warn('Goal ID is missing for AdjustmentImpactPanel');
        mountElement.style.display = 'none';
        return;
      }
      
      // Ensure adjustments is an array
      const adjustments = Array.isArray(adjustmentData.adjustments) 
        ? adjustmentData.adjustments 
        : [];
      
      // If no adjustments, hide the panel
      if (adjustments.length === 0) {
        mountElement.style.display = 'none';
        return;
      }
      
      // Show the panel
      mountElement.style.display = '';
      
      // Ensure each adjustment has required fields
      const processedAdjustments = adjustments.map(adj => {
        return {
          id: adj.id || `adj_${Math.random().toString(36).substr(2, 9)}`,
          description: adj.description || 'Adjustment',
          impactMetrics: adj.impactMetrics || {
            probabilityIncrease: 0,
            newProbability: adjustmentData.currentProbability || 0
          },
          ...adj
        };
      });
      
      // Render the React component
      ReactDOM.render(
        React.createElement(AdjustmentImpactPanel, {
          goalId: adjustmentData.goalId,
          adjustments: processedAdjustments,
          currentProbability: adjustmentData.currentProbability || 0,
          onAdjustmentSelect: (adjustmentId) => {
            // Publish an event that can be subscribed to
            const event = new CustomEvent('goalAdjustmentSelected', {
              detail: { 
                goalId: adjustmentData.goalId, 
                adjustmentId 
              }
            });
            document.dispatchEvent(event);
          },
          onError: (err) => {
            console.error('AdjustmentImpactPanel error:', err);
            setComponentError('adjustment-impact-panel', err);
          }
        }),
        mountElement
      );
    } catch (error) {
      console.error('Failed to initialize AdjustmentImpactPanel:', error);
      setComponentError('adjustment-impact-panel', error);
    }
  }
  
  /**
   * Initializes the Scenario Comparison Chart component with data
   * @param {Object} data - Component data from API or data attributes
   */
  function initScenarioComparisonChart(data = null) {
    const mountElement = document.getElementById('scenario-comparison-chart');
    if (!mountElement) return;
    
    try {
      // Clear any previous error state
      setComponentError('scenario-comparison-chart', null);
      
      // Use provided data or extract from data attributes
      let scenarioData = data;
      if (!scenarioData) {
        const dataset = mountElement.dataset;
        scenarioData = {
          goalId: dataset.goalId,
          scenarios: safeJSONParse(dataset.scenarios, [])
        };
      }
      
      // Validate required data
      if (!scenarioData.goalId) {
        console.warn('Goal ID is missing for ScenarioComparisonChart');
        mountElement.style.display = 'none';
        return;
      }
      
      // Ensure scenarios is an array
      const scenarios = Array.isArray(scenarioData.scenarios) 
        ? scenarioData.scenarios 
        : [];
      
      // If no scenarios, hide the chart
      if (scenarios.length === 0) {
        mountElement.style.display = 'none';
        return;
      }
      
      // Show the chart
      mountElement.style.display = '';
      
      // Ensure at least one scenario is marked as baseline
      const hasBaseline = scenarios.some(s => s.isBaseline);
      if (!hasBaseline && scenarios.length > 0) {
        scenarios[0].isBaseline = true;
      }
      
      // Render the React component
      ReactDOM.render(
        React.createElement(ScenarioComparisonChart, {
          goalId: scenarioData.goalId,
          scenarios: scenarios,
          onError: (err) => {
            console.error('ScenarioComparisonChart error:', err);
            setComponentError('scenario-comparison-chart', err);
          }
        }),
        mountElement
      );
    } catch (error) {
      console.error('Failed to initialize ScenarioComparisonChart:', error);
      setComponentError('scenario-comparison-chart', error);
    }
  }
  
  /**
   * Refreshes a specific visualization component with new data
   * @param {string} componentId - ID of the component to refresh
   * @param {Object} newData - New data for the component
   */
  function refreshVisualization(componentId, newData) {
    const mountElement = document.getElementById(componentId);
    if (!mountElement) {
      console.warn(`Element with ID ${componentId} not found`);
      return;
    }
    
    // Measure performance if enabled
    if (config.usePerformanceOptimizer && config.measureComponentPerformance && window.PerformanceOptimizer?.dom) {
      // Use the performance measurement wrapper
      window.PerformanceOptimizer.dom.measureRenderPerformance(componentId, (element) => {
        // Update the component (tracked for performance)
        updateComponentWithData(componentId, element, newData);
        return true;
      }).then(result => {
        // Log performance warning if render was slow
        if (result.duration > config.slowRenderThreshold && config.logPerformanceWarnings) {
          console.warn(`Slow render detected for ${componentId}: ${result.duration.toFixed(1)}ms`);
        }
      });
    } else {
      // Just update the component normally
      updateComponentWithData(componentId, mountElement, newData);
    }
  }
  
  /**
   * Updates a component with new data (internal helper)
   * @param {string} componentId - ID of the component to update
   * @param {HTMLElement} element - The component's DOM element
   * @param {Object} newData - New data for the component
   * @private
   */
  function updateComponentWithData(componentId, element, newData) {
    // Update data attributes with new data
    if (newData) {
      Object.keys(newData).forEach(key => {
        // Convert camelCase to kebab-case for data attributes
        const dataAttrKey = key.replace(/([A-Z])/g, '-$1').toLowerCase();
        
        // Handle different data types properly
        let value;
        if (typeof newData[key] === 'object' && newData[key] !== null) {
          value = JSON.stringify(newData[key]);
        } else if (newData[key] !== null && newData[key] !== undefined) {
          value = newData[key].toString();
        } else {
          // Skip null/undefined values
          return;
        }
        
        // Update the data attribute
        element.dataset[key] = value;
      });
    }
    
    // Re-initialize the component based on its ID
    switch (componentId) {
      case 'probabilistic-goal-visualizer':
        initProbabilisticGoalVisualizer(newData);
        break;
      case 'adjustment-impact-panel':
        initAdjustmentImpactPanel(newData);
        break;
      case 'scenario-comparison-chart':
        initScenarioComparisonChart(newData);
        break;
      default:
        console.warn(`Unknown component ID: ${componentId}`);
    }
  }
  
  /**
   * Register components with the event bus
   * @param {Object} componentData - Component data to register
   */
  function registerWithEventBus(componentData) {
    if (!config.enableEventBus || !window.DataEventBus) return;
    
    const goalId = componentData.goalId;
    if (!goalId) return;
    
    // Initialize each component with the event bus
    Object.keys(componentStates).forEach(componentId => {
      if (document.getElementById(componentId)) {
        // Generate a unique ID for this component instance
        const uniqueId = `${componentId}_${Date.now()}`;
        
        if (config.debug) {
          console.log(`Registering component ${componentId} with DataEventBus as ${uniqueId}`);
        }
        
        // Register the component
        const unregister = window.DataEventBus.registerComponent(
          uniqueId,
          componentId,
          {
            goalId: goalId,
            initialData: componentData
          }
        );
        
        // Store the registration for cleanup
        componentRegistrations[componentId] = {
          id: uniqueId,
          unregister: unregister
        };
      }
    });
    
    // Subscribe to relevant events
    setupEventSubscriptions(goalId);
  }
  
  /**
   * Set up event subscriptions for component synchronization
   * @param {string} goalId - The goal ID to filter events on
   */
  function setupEventSubscriptions(goalId) {
    if (!config.enableEventBus || !window.DataEventBus) return;
    
    // Clear any existing subscriptions
    eventSubscriptions.forEach(unsubscribe => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    });
    eventSubscriptions.length = 0;
    
    // Create optimized handlers if performance optimizer is available
    let probabilityUpdateHandler;
    let fetchDataHandler;
    
    if (config.usePerformanceOptimizer && window.PerformanceOptimizer) {
      // Create a debounced probability update handler
      probabilityUpdateHandler = window.PerformanceOptimizer.debounce((data) => {
        // Update UI if needed
        if (data.probability !== undefined) {
          updateProbabilityDisplay(data.probability, goalId);
        }
        
        // Refresh visualizations if this is a major update
        if (data.simulationData) {
          refreshAll({
            probabilisticGoalData: {
              goalId: goalId,
              successProbability: data.probability,
              simulationData: data.simulationData
            }
          });
        }
        
        if (config.debug) {
          console.log(`Received probability update: ${data.probability} from ${data.source}`);
        }
      }, config.debounceDelay, { leading: true });
      
      // Create a throttled data fetch handler to avoid too many refreshes
      fetchDataHandler = window.PerformanceOptimizer.throttle((refreshOptions) => {
        fetchAndRefresh(goalId, refreshOptions);
      }, 500);
    } else {
      // Create regular handlers if optimizer not available
      probabilityUpdateHandler = (data) => {
        // Update UI if needed
        if (data.probability !== undefined) {
          updateProbabilityDisplay(data.probability, goalId);
        }
        
        // Refresh visualizations if this is a major update
        if (data.simulationData) {
          refreshAll({
            probabilisticGoalData: {
              goalId: goalId,
              successProbability: data.probability,
              simulationData: data.simulationData
            }
          });
        }
        
        if (config.debug) {
          console.log(`Received probability update: ${data.probability} from ${data.source}`);
        }
      };
      
      fetchDataHandler = (refreshOptions) => {
        setTimeout(() => {
          fetchAndRefresh(goalId, refreshOptions);
        }, 500);
      };
    }
    
    // Subscribe to probability updates
    const probabilitySubscription = window.DataEventBus.subscribe(
      'probability-updated',
      (data) => {
        // Ignore events for other goals
        if (data.goalId !== goalId) return;
        
        // Use the optimized handler
        probabilityUpdateHandler(data);
      }
    );
    eventSubscriptions.push(probabilitySubscription);
    
    // Subscribe to adjustment selection
    const adjustmentSubscription = window.DataEventBus.subscribe(
      'adjustment-selected',
      (data) => {
        // Ignore events for other goals
        if (data.goalId !== goalId) return;
        
        if (config.debug) {
          console.log(`Adjustment selected: ${data.adjustmentId} from ${data.source}`);
        }
        
        // Create a custom event for backward compatibility
        const event = new CustomEvent('goalAdjustmentSelected', {
          detail: { 
            goalId: data.goalId, 
            adjustmentId: data.adjustmentId 
          }
        });
        document.dispatchEvent(event);
        
        // Request fresh data with throttling for better performance
        fetchDataHandler({ forceRefresh: true });
      }
    );
    eventSubscriptions.push(adjustmentSubscription);
    
    // Subscribe to scenario selection
    const scenarioSubscription = window.DataEventBus.subscribe(
      'scenario-selected',
      (data) => {
        // Ignore events for other goals
        if (data.goalId !== goalId) return;
        
        if (config.debug) {
          console.log(`Scenario selected: ${data.scenarioId} from ${data.source}`);
        }
        
        // Fetch fresh data with throttling for better performance
        fetchDataHandler({ forceRefresh: true });
      }
    );
    eventSubscriptions.push(scenarioSubscription);
    
    // Subscribe to sync requests
    const syncSubscription = window.DataEventBus.subscribe(
      'sync-requested',
      (data) => {
        if (config.debug) {
          console.log(`Sync requested from ${data.source}`);
        }
        
        // Fetch fresh data (sync requests should be processed immediately,
        // so we don't use the throttled handler)
        fetchAndRefresh(goalId, { forceRefresh: true });
      }
    );
    eventSubscriptions.push(syncSubscription);
    
    // Force synchronization if more than one component is registered
    if (Object.keys(componentRegistrations).length > 1 && window.DataEventBus.forceSynchronization) {
      window.DataEventBus.forceSynchronization();
    }
  }
  
  /**
   * Update probability display in the DOM
   * @param {number} probability - Probability value between 0 and 1
   * @param {string} goalId - Goal ID for targeting specific elements
   */
  function updateProbabilityDisplay(probability, goalId) {
    // Find probability display elements
    const displayElements = document.querySelectorAll('.goal-probability-display');
    
    if (displayElements.length === 0) return;
    
    // Format probability as percentage
    const percentage = Math.round(probability * 100);
    
    // Use PerformanceOptimizer for DOM updates if available
    if (config.usePerformanceOptimizer && window.PerformanceOptimizer?.dom) {
      // Batch DOM updates for better performance
      displayElements.forEach(element => {
        // Skip elements for other goals if a goal ID is provided
        if (goalId && element.dataset.goalId && element.dataset.goalId !== goalId) {
          return;
        }
        
        // Schedule optimized update
        window.PerformanceOptimizer.dom.scheduleUpdate(element, (el) => {
          // Update text content
          el.textContent = `${percentage}%`;
          
          // Update color class
          if (percentage >= 70) {
            el.classList.remove('text-amber-600', 'text-red-600');
            el.classList.add('text-green-600');
          } else if (percentage >= 50) {
            el.classList.remove('text-green-600', 'text-red-600');
            el.classList.add('text-amber-600');
          } else {
            el.classList.remove('text-green-600', 'text-amber-600');
            el.classList.add('text-red-600');
          }
          
          // Add animation class
          el.classList.add('probability-updated');
          setTimeout(() => {
            el.classList.remove('probability-updated');
          }, 1000);
        });
      });
    } else {
      // Legacy DOM update approach
      displayElements.forEach(element => {
        // Skip elements for other goals if a goal ID is provided
        if (goalId && element.dataset.goalId && element.dataset.goalId !== goalId) {
          return;
        }
        
        // Update text content
        element.textContent = `${percentage}%`;
        
        // Update color class
        if (percentage >= 70) {
          element.classList.remove('text-amber-600', 'text-red-600');
          element.classList.add('text-green-600');
        } else if (percentage >= 50) {
          element.classList.remove('text-green-600', 'text-red-600');
          element.classList.add('text-amber-600');
        } else {
          element.classList.remove('text-green-600', 'text-amber-600');
          element.classList.add('text-red-600');
        }
        
        // Add animation class
        element.classList.add('probability-updated');
        setTimeout(() => {
          element.classList.remove('probability-updated');
        }, 1000);
      });
    }
  }

  /**
   * Initializes all visualization components
   */
  function initAll() {
    initProbabilisticGoalVisualizer();
    initAdjustmentImpactPanel();
    initScenarioComparisonChart();
    
    // Check if auto-initialization from API is enabled
    const visualizerElement = document.getElementById('probabilistic-goal-visualizer');
    if (visualizerElement && visualizerElement.dataset.goalId && visualizerElement.dataset.autoFetch === 'true') {
      const goalId = visualizerElement.dataset.goalId;
      
      // Set up event bus if available
      if (config.enableEventBus && window.DataEventBus) {
        registerWithEventBus({ goalId });
      }
      
      // Fetch data for all components
      fetchAndRefresh(goalId);
    }
  }
  
  /**
   * Refreshes all visualization components with new data
   * @param {Object} data - New data for all components
   */
  function refreshAll(data = {}) {
    if (data.probabilisticGoalData) {
      refreshVisualization('probabilistic-goal-visualizer', data.probabilisticGoalData);
    }
    
    if (data.adjustmentImpactData) {
      refreshVisualization('adjustment-impact-panel', data.adjustmentImpactData);
    }
    
    if (data.scenarioComparisonData) {
      refreshVisualization('scenario-comparison-chart', data.scenarioComparisonData);
    }
  }
  
  /**
   * Fetches data for a specific component
   * @param {string} goalId - ID of the goal
   * @param {string} componentId - ID of the component
   * @param {Object} options - Fetch options
   * @returns {Promise} Promise resolving to component data
   */
  async function fetchComponentData(goalId, componentId, options = {}) {
    // Check if component exists
    const mountElement = document.getElementById(componentId);
    if (!mountElement) {
      console.warn(`Component with ID ${componentId} not found`);
      return null;
    }
    
    // Show loading state after a short delay to avoid flashing for fast responses
    const loadingTimeout = setTimeout(() => {
      setComponentLoading(componentId, true);
    }, config.loadingIndicatorDelay);
    
    try {
      // Fetch the full visualization data
      const data = await fetchVisualizationData(goalId, options);
      
      // Extract component-specific data
      let componentData = null;
      switch (componentId) {
        case 'probabilistic-goal-visualizer':
          componentData = data.probabilisticGoalData;
          break;
        case 'adjustment-impact-panel':
          componentData = data.adjustmentImpactData;
          break;
        case 'scenario-comparison-chart':
          componentData = data.scenarioComparisonData;
          break;
      }
      
      // Clear loading timeout and state
      clearTimeout(loadingTimeout);
      setComponentLoading(componentId, false);
      
      // Clear error state
      setComponentError(componentId, null);
      
      return componentData;
    } catch (error) {
      // Clear loading timeout and state
      clearTimeout(loadingTimeout);
      setComponentLoading(componentId, false);
      
      // Set error state
      setComponentError(componentId, error);
      
      console.error(`Error fetching data for ${componentId}:`, error);
      return null;
    }
  }
  
  /**
   * Fetches visualization data from the API with retry logic
   * @param {string} goalId - ID of the goal to fetch data for
   * @param {Object} options - Fetch options
   * @returns {Promise} Promise resolving to visualization data
   */
  async function fetchVisualizationData(goalId, options = {}) {
    const {
      retryAttempts = config.retryAttempts,
      retryDelay = config.retryDelay,
      timeout = config.requestTimeout,
      signal = null,
      forceRefresh = false
    } = options;
    
    // Performance tracking
    const startTime = performance.now();
    
    // If VisualizationDataService is available, use it (much more optimized)
    if (window.VisualizationDataService) {
      try {
        // Use the optimized fetch with caching and recovery features
        const result = await window.VisualizationDataService.fetchVisualizationData(goalId, {
          forceRefresh,
          timeout,
          retryAttempts,
          onLoadingChange: null // We handle loading state ourselves
        });
        
        // Track performance if enabled
        if (config.usePerformanceOptimizer && config.logPerformanceWarnings && window.PerformanceOptimizer) {
          const duration = performance.now() - startTime;
          window.PerformanceOptimizer.trackApiCall(
            `visualization_fetch_${goalId}`,
            duration,
            true,
            result._metadata?.fromCache || false
          );
        }
        
        return result;
      } catch (error) {
        // Track performance for failed request
        if (config.usePerformanceOptimizer && config.logPerformanceWarnings && window.PerformanceOptimizer) {
          const duration = performance.now() - startTime;
          window.PerformanceOptimizer.trackApiCall(
            `visualization_fetch_${goalId}`,
            duration,
            false,
            false
          );
        }
        
        throw error;
      }
    }
    
    // Fallback to traditional fetch if service is not available
    
    // Create abort controller for this request if not provided
    let abortController;
    if (signal) {
      // Use provided signal
      abortController = null;
    } else {
      // Create new abort controller
      abortController = new AbortController();
      
      // Store controller to allow cancelling from outside
      abortControllers[goalId] = abortController;
    }
    
    // Get the actual abort signal
    const abortSignal = signal || (abortController ? abortController.signal : null);
    
    // Setup request timeout
    let timeoutId;
    if (timeout > 0) {
      timeoutId = setTimeout(() => {
        if (abortController) {
          abortController.abort();
        }
      }, timeout);
    }
    
    // Track retry attempts
    let attempt = 0;
    let lastError = null;
    
    try {
      // Retry loop
      while (attempt <= retryAttempts) {
        try {
          // Construct the endpoint URL
          const endpoint = config.apiEndpoint.replace('{goal_id}', goalId);
          
          // Make the request
          const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            signal: abortSignal
          });
          
          // Check if request was successful
          if (!response.ok) {
            let errorMessage;
            try {
              const errorData = await response.json();
              errorMessage = errorData.message || `API request failed with status ${response.status}`;
            } catch (e) {
              errorMessage = `API request failed with status ${response.status}`;
            }
            
            throw new Error(errorMessage);
          }
          
          // Parse and process the response
          const data = await response.json();
          
          // Process the data
          const processedData = processApiResponse(data);
          
          // Clear timeout if set
          if (timeoutId) {
            clearTimeout(timeoutId);
          }
          
          // Remove abort controller from storage
          if (abortController) {
            delete abortControllers[goalId];
          }
          
          // Track performance if enabled
          if (config.usePerformanceOptimizer && config.logPerformanceWarnings && window.PerformanceOptimizer) {
            const duration = performance.now() - startTime;
            window.PerformanceOptimizer.trackApiCall(
              `visualization_fetch_${goalId}`,
              duration,
              true,
              false
            );
          }
          
          return processedData;
        } catch (error) {
          // Store the error
          lastError = error;
          
          // Check if the request was aborted
          if (error.name === 'AbortError') {
            throw new Error('Request timed out or was aborted');
          }
          
          // Check if we should retry
          if (attempt >= retryAttempts) {
            break;
          }
          
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, retryDelay));
          
          // Increment attempt counter
          attempt++;
        }
      }
      
      // If we get here, all retry attempts failed
      throw lastError || new Error('Failed to fetch visualization data');
    } catch (error) {
      // Track performance for failed request
      if (config.usePerformanceOptimizer && config.logPerformanceWarnings && window.PerformanceOptimizer) {
        const duration = performance.now() - startTime;
        window.PerformanceOptimizer.trackApiCall(
          `visualization_fetch_${goalId}`,
          duration,
          false,
          false
        );
      }
      
      // Clear timeout if set
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      
      // Remove abort controller from storage
      if (abortController) {
        delete abortControllers[goalId];
      }
      
      // Re-throw the error
      throw error;
    }
  }
  
  /**
   * Process the API response to ensure it matches the expected format for components
   * @param {Object} apiResponse - The raw API response
   * @returns {Object} Processed data ready for visualization components
   */
  function processApiResponse(apiResponse) {
    // Create a deep copy to avoid modifying the original data
    const processed = JSON.parse(JSON.stringify(apiResponse));
    
    // Extract the goal ID
    const goalId = processed.goal_id || '';
    
    // Process probabilistic goal data
    if (!processed.probabilisticGoalData && processed.goal_id) {
      // Check if the data might be at the root level
      if (processed.successProbability !== undefined || processed.simulationOutcomes) {
        processed.probabilisticGoalData = {
          goalId: goalId,
          targetAmount: processed.targetAmount || 0,
          timeframe: processed.timeframe || '',
          successProbability: processed.successProbability || 0,
          simulationOutcomes: processed.simulationOutcomes || {},
          timeBasedMetrics: processed.timeBasedMetrics || {}
        };
      } else {
        // Create empty data structure
        processed.probabilisticGoalData = {
          goalId: goalId,
          targetAmount: 0,
          timeframe: '',
          successProbability: 0,
          simulationOutcomes: {},
          timeBasedMetrics: {}
        };
      }
    }
    
    // Ensure probabilistic data has required fields
    if (processed.probabilisticGoalData) {
      const probData = processed.probabilisticGoalData;
      
      // Add goalId if missing
      if (!probData.goalId) {
        probData.goalId = goalId;
      }
      
      // Ensure simulationOutcomes exists
      if (!probData.simulationOutcomes) {
        probData.simulationOutcomes = {
          median: probData.targetAmount || 0,
          percentiles: {
            '10': 0, '25': 0, '50': 0, '75': 0, '90': 0
          }
        };
      }
      
      // Ensure timeBasedMetrics exists
      if (!probData.timeBasedMetrics) {
        probData.timeBasedMetrics = {
          probabilityOverTime: {
            labels: ['Start', 'End'],
            values: [0, probData.successProbability || 0]
          }
        };
      }
    }
    
    // Process adjustment data
    if (!processed.adjustmentImpactData && processed.goal_id) {
      // Check if adjustments might be at the root level
      if (processed.adjustments) {
        processed.adjustmentImpactData = {
          goalId: goalId,
          currentProbability: processed.successProbability || processed.currentProbability || 0,
          adjustments: processed.adjustments
        };
      } else {
        // Create empty data structure
        processed.adjustmentImpactData = {
          goalId: goalId,
          currentProbability: 0,
          adjustments: []
        };
      }
    }
    
    // Ensure adjustment data has required fields
    if (processed.adjustmentImpactData) {
      const adjData = processed.adjustmentImpactData;
      
      // Add goalId if missing
      if (!adjData.goalId) {
        adjData.goalId = goalId;
      }
      
      // Ensure adjustments array exists
      if (!adjData.adjustments || !Array.isArray(adjData.adjustments)) {
        adjData.adjustments = [];
      }
      
      // Ensure each adjustment has an ID and impactMetrics
      adjData.adjustments.forEach((adjustment, index) => {
        if (!adjustment.id) {
          adjustment.id = `${goalId}_adj_${index}`;
        }
        
        if (!adjustment.impactMetrics) {
          adjustment.impactMetrics = {
            probabilityIncrease: 0,
            newProbability: adjData.currentProbability || 0
          };
        }
      });
    }
    
    // Process scenario data
    if (!processed.scenarioComparisonData && processed.goal_id) {
      // Check if scenarios might be at the root level
      if (processed.scenarios) {
        processed.scenarioComparisonData = {
          goalId: goalId,
          scenarios: processed.scenarios
        };
      } else {
        // Create empty data structure
        processed.scenarioComparisonData = {
          goalId: goalId,
          scenarios: []
        };
      }
    }
    
    // Ensure scenario data has required fields
    if (processed.scenarioComparisonData) {
      const scenData = processed.scenarioComparisonData;
      
      // Add goalId if missing
      if (!scenData.goalId) {
        scenData.goalId = goalId;
      }
      
      // Ensure scenarios array exists
      if (!scenData.scenarios || !Array.isArray(scenData.scenarios)) {
        scenData.scenarios = [];
      }
      
      // If no scenarios, add a default baseline scenario
      if (scenData.scenarios.length === 0 && processed.probabilisticGoalData) {
        scenData.scenarios.push({
          id: `${goalId}_baseline`,
          name: 'Current Plan',
          description: 'Your current financial plan with no changes',
          probability: processed.probabilisticGoalData.successProbability || 0,
          isBaseline: true
        });
      }
      
      // Ensure at least one scenario is marked as baseline
      const hasBaseline = scenData.scenarios.some(s => s.isBaseline);
      if (!hasBaseline && scenData.scenarios.length > 0) {
        scenData.scenarios[0].isBaseline = true;
      }
      
      // Ensure each scenario has an ID
      scenData.scenarios.forEach((scenario, index) => {
        if (!scenario.id) {
          scenario.id = `${goalId}_scenario_${index}`;
        }
      });
    }
    
    return processed;
  }
  
  /**
   * Fetches fresh data from the server and updates visualizations
   * @param {string} goalId - ID of the goal to refresh data for
   * @param {Object} options - Optional configuration
   * @param {boolean} options.forceRefresh - Force refresh data from API ignoring cache
   * @param {function} options.onSuccess - Callback for successful data fetch
   * @param {function} options.onError - Callback for error handling
   * @param {boolean} options.updateDOM - Whether to update the DOM with new data
   */
  function fetchAndRefresh(goalId, options = {}) {
    if (!goalId) {
      console.error('Goal ID is required for refreshing data');
      return;
    }
    
    const {
      forceRefresh = false,
      onSuccess = null,
      onError = null,
      updateDOM = true
    } = options;
    
    // Show global loading indicator if available
    const loaderElement = document.getElementById('visualization-loader');
    if (loaderElement) {
      loaderElement.classList.remove('hidden');
    }
    
    // Also use the common loading state system if available
    if (window.loadingState && typeof window.loadingState.showProgressBar === 'function') {
      window.loadingState.showProgressBar();
    }
    
    // Set all component loading states after a short delay
    const loadingTimeouts = [];
    if (updateDOM) {
      Object.keys(componentStates).forEach(componentId => {
        const timeout = setTimeout(() => {
          setComponentLoading(componentId, true);
        }, config.loadingIndicatorDelay);
        loadingTimeouts.push(timeout);
      });
    }
    
    // Cancel any in-flight requests for this goal
    if (abortControllers[goalId]) {
      abortControllers[goalId].abort();
      delete abortControllers[goalId];
    }
    
    // Publish data-fetched event to indicate loading state
    if (config.enableEventBus && window.DataEventBus) {
      window.DataEventBus.publish('data-fetched', {
        goalId: goalId,
        state: 'loading',
        source: 'goal-visualization-initializer'
      });
    }
    
    // Fetch data from API
    fetchVisualizationData(goalId, { retryAttempts: 1 })
      .then(data => {
        // Clear loading timeouts
        loadingTimeouts.forEach(timeout => clearTimeout(timeout));
        
        // Hide global loading indicator
        if (loaderElement) {
          loaderElement.classList.add('hidden');
        }
        
        // Hide progress bar
        if (window.loadingState && typeof window.loadingState.hideProgressBar === 'function') {
          window.loadingState.hideProgressBar();
        }
        
        // Publish success event for data fetching
        if (config.enableEventBus && window.DataEventBus) {
          window.DataEventBus.publish('data-fetched', {
            goalId: goalId,
            state: 'success',
            data: data,
            source: 'goal-visualization-initializer'
          });
          
          // Update component data in the event bus system
          Object.keys(componentRegistrations).forEach(componentId => {
            const registration = componentRegistrations[componentId];
            let componentData = null;
            
            // Select the right data for this component
            switch (componentId) {
              case 'probabilistic-goal-visualizer':
                componentData = data.probabilisticGoalData;
                break;
              case 'adjustment-impact-panel':
                componentData = data.adjustmentImpactData;
                break;
              case 'scenario-comparison-chart':
                componentData = data.scenarioComparisonData;
                break;
            }
            
            if (componentData && window.DataEventBus.updateComponentData) {
              window.DataEventBus.updateComponentData(
                registration.id,
                'data-fetched',
                componentData
              );
            }
          });
        }
        
        if (updateDOM) {
          // Extract component-specific data
          const probabilisticGoalData = data.probabilisticGoalData || null;
          const adjustmentImpactData = data.adjustmentImpactData || null;
          const scenarioComparisonData = data.scenarioComparisonData || null;
          
          // Update all visualizations with the new data
          refreshAll({
            probabilisticGoalData,
            adjustmentImpactData,
            scenarioComparisonData
          });
          
          // Clear all component loading and error states
          Object.keys(componentStates).forEach(componentId => {
            setComponentLoading(componentId, false);
            setComponentError(componentId, null);
          });
          
          // Publish visualization-refreshed event
          if (config.enableEventBus && window.DataEventBus) {
            window.DataEventBus.publish('visualization-refreshed', {
              goalId: goalId,
              timestamp: Date.now(),
              source: 'goal-visualization-initializer'
            });
          }
        }
        
        // Call success callback if provided
        if (typeof onSuccess === 'function') {
          onSuccess(data);
        }
        
        return data;
      })
      .catch(error => {
        if (config.debug) {
          console.error('Error fetching visualization data:', error);
        }
        
        // Clear loading timeouts
        loadingTimeouts.forEach(timeout => clearTimeout(timeout));
        
        // Hide global loader
        if (loaderElement) {
          loaderElement.classList.add('hidden');
        }
        
        // Hide progress bar
        if (window.loadingState && typeof window.loadingState.hideProgressBar === 'function') {
          window.loadingState.hideProgressBar();
        }
        
        // Publish error event for data fetching
        if (config.enableEventBus && window.DataEventBus) {
          window.DataEventBus.publish('data-fetched', {
            goalId: goalId,
            state: 'error',
            error: error.message || 'Unknown error',
            source: 'goal-visualization-initializer'
          });
        }
        
        if (updateDOM) {
          // Set error state for all components
          Object.keys(componentStates).forEach(componentId => {
            setComponentLoading(componentId, false);
            setComponentError(componentId, error);
          });
          
          // Show global error message to user
          if (window.loadingState && typeof window.loadingState.showError === 'function') {
            window.loadingState.showError('Failed to load visualization data. Please try again later.');
          } else {
            // Fallback to older error display
            const errorElement = document.getElementById('visualization-error');
            if (errorElement) {
              errorElement.textContent = 'Failed to load visualization data. Please try again later.';
              errorElement.classList.remove('hidden');
              
              // Hide error after 5 seconds
              setTimeout(() => {
                errorElement.classList.add('hidden');
              }, 5000);
            }
          }
        }
        
        // Call error callback if provided
        if (typeof onError === 'function') {
          onError(error);
        }
        
        throw error;
      });
  }
  
  /**
   * Cancels any in-flight fetch requests
   */
  function cancelRequests() {
    // Abort all pending requests
    Object.values(abortControllers).forEach(controller => {
      try {
        controller.abort();
      } catch (e) {
        console.error('Error aborting request:', e);
      }
    });
    
    // Clear the controllers object
    Object.keys(abortControllers).forEach(key => {
      delete abortControllers[key];
    });
  }
  
  /**
   * Updates configuration options
   * @param {Object} options - New configuration options
   */
  function configure(options = {}) {
    // Update configuration
    Object.assign(config, options);
    
    // Setup or clear auto-refresh interval
    if (config.refreshInterval) {
      // Get goal ID from probabilistic visualizer
      const visualizerElement = document.getElementById('probabilistic-goal-visualizer');
      if (visualizerElement && visualizerElement.dataset.goalId) {
        // Setup interval
        const intervalId = setInterval(() => {
          fetchAndRefresh(visualizerElement.dataset.goalId, { forceRefresh: true });
        }, config.refreshInterval);
        
        // Store interval ID for cleanup
        config.refreshIntervalId = intervalId;
      }
    } else if (config.refreshIntervalId) {
      // Clear existing interval
      clearInterval(config.refreshIntervalId);
      config.refreshIntervalId = null;
    }
  }
  
  // Initialize components when DOM is ready
  document.addEventListener('DOMContentLoaded', initAll);
  
  // Clean up resources when page is unloaded
  window.addEventListener('unload', () => {
    // Cancel any pending requests
    cancelRequests();
    
    // Clear any intervals
    if (config.refreshIntervalId) {
      clearInterval(config.refreshIntervalId);
    }
  });
  
  // Public API
  return {
    initAll,
    refreshVisualization,
    refreshAll,
    fetchAndRefresh,
    cancelRequests,
    configure
  };
})();

// Make the initializer available globally
window.GoalVisualizationInitializer = GoalVisualizationInitializer;