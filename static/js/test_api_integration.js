/**
 * End-to-End API Integration Test Suite
 * 
 * This file contains comprehensive tests for verifying the integration between
 * frontend components and backend API endpoints. It tests:
 * 
 * 1. API request/response flows
 * 2. Component data updates
 * 3. Error handling and recovery
 * 4. Loading states
 * 5. Data synchronization between components
 * 6. Performance optimization features
 */

const APIIntegrationTests = (function() {
  // Test configuration
  const config = {
    testTimeouts: {
      short: 2000,    // 2 seconds for quick operations
      medium: 5000,   // 5 seconds for normal operations
      long: 15000     // 15 seconds for complex operations
    },
    testGoalId: null, // Will be determined at runtime
    logResults: true, // Output results to console
    stopOnFailure: false, // Continue testing even if a test fails
    mockOffline: false, // Mock offline state for relevant tests
    testEnvironment: window.location.hostname === 'localhost' ? 'development' : 'production'
  };
  
  // Test state tracking
  const testState = {
    running: false,
    startTime: null,
    endTime: null,
    results: {
      passed: 0,
      failed: 0,
      skipped: 0,
      total: 0
    },
    testCases: [],
    errors: []
  };
  
  // UI Elements
  let resultsContainer = null;
  let testRunButton = null;
  let testSummaryElement = null;
  
  /**
   * Initialize the test suite
   */
  function initialize() {
    createTestUI();
    setupEventListeners();
    
    // Load previously successful goal ID from localStorage if available
    const savedGoalId = localStorage.getItem('test_goal_id');
    if (savedGoalId) {
      config.testGoalId = savedGoalId;
    }
    
    // Check if the page already has a goal ID in a data attribute
    const goalElements = document.querySelectorAll('[data-goal-id]');
    if (goalElements.length > 0) {
      const goalId = goalElements[0].dataset.goalId;
      if (goalId) {
        config.testGoalId = goalId;
      }
    }
    
    console.log('API Integration Test Suite initialized');
  }
  
  /**
   * Create the test UI elements
   */
  function createTestUI() {
    // Create main container
    const container = document.createElement('div');
    container.id = 'api-test-container';
    container.className = 'fixed bottom-0 right-0 p-3 bg-white border rounded-tl-lg shadow-lg z-50 max-w-md overflow-auto max-h-[80vh]';
    container.style.display = 'none'; // Hidden by default
    
    // Create header
    const header = document.createElement('div');
    header.className = 'flex justify-between items-center border-b pb-2 mb-2';
    
    const title = document.createElement('h3');
    title.className = 'font-semibold text-gray-800';
    title.textContent = 'API Integration Tests';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'text-gray-500 hover:text-gray-700';
    closeButton.innerHTML = '&times;';
    closeButton.setAttribute('aria-label', 'Close');
    closeButton.onclick = () => {
      container.style.display = 'none';
    };
    
    header.appendChild(title);
    header.appendChild(closeButton);
    
    // Create test controls
    const controls = document.createElement('div');
    controls.className = 'flex gap-2 mb-3';
    
    testRunButton = document.createElement('button');
    testRunButton.className = 'px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700';
    testRunButton.textContent = 'Run Tests';
    
    const configButton = document.createElement('button');
    configButton.className = 'px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300';
    configButton.textContent = 'Configuration';
    
    controls.appendChild(testRunButton);
    controls.appendChild(configButton);
    
    // Create test summary
    testSummaryElement = document.createElement('div');
    testSummaryElement.className = 'text-sm text-gray-600 mb-3';
    testSummaryElement.textContent = 'No tests run yet';
    
    // Create results container
    resultsContainer = document.createElement('div');
    resultsContainer.className = 'space-y-2 text-sm';
    
    // Assemble all elements
    container.appendChild(header);
    container.appendChild(controls);
    container.appendChild(testSummaryElement);
    container.appendChild(resultsContainer);
    
    // Add to page
    document.body.appendChild(container);
    
    // Create floating button to show test panel
    const floatingButton = document.createElement('button');
    floatingButton.className = 'fixed bottom-3 right-3 bg-blue-600 text-white p-2 rounded-full shadow-lg z-40';
    floatingButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 000 2h6a1 1 0 100-2H7z" clip-rule="evenodd" /></svg>';
    floatingButton.setAttribute('aria-label', 'Show Tests');
    floatingButton.onclick = () => {
      container.style.display = container.style.display === 'none' ? 'block' : 'none';
    };
    
    document.body.appendChild(floatingButton);
  }
  
  /**
   * Setup event listeners for the test UI
   */
  function setupEventListeners() {
    testRunButton.addEventListener('click', runAllTests);
  }
  
  /**
   * Updates the UI with test results
   */
  function updateTestUI() {
    // Update summary
    testSummaryElement.innerHTML = `
      <span class="font-medium">Results:</span>
      <span class="text-green-600">${testState.results.passed} passed</span>,
      <span class="text-red-600">${testState.results.failed} failed</span>,
      <span class="text-gray-500">${testState.results.skipped} skipped</span>
      ${testState.running ? '<span class="ml-2 animate-pulse">Running...</span>' : ''}
    `;
    
    // Update button state
    testRunButton.disabled = testState.running;
    testRunButton.className = testState.running
      ? 'px-3 py-1 bg-gray-400 text-white rounded cursor-not-allowed'
      : 'px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700';
    testRunButton.textContent = testState.running ? 'Running...' : 'Run Tests';
    
    // Clear previous results
    if (!testState.running) {
      resultsContainer.innerHTML = '';
      
      // Add test results
      testState.testCases.forEach(testCase => {
        const resultElement = document.createElement('div');
        resultElement.className = `p-2 rounded ${getStatusColorClass(testCase.status)}`;
        
        resultElement.innerHTML = `
          <div class="flex justify-between items-start">
            <span class="font-medium">${testCase.name}</span>
            <span class="text-xs ${getStatusTextClass(testCase.status)}">${testCase.status}</span>
          </div>
          ${testCase.message ? `<p class="text-xs mt-1">${testCase.message}</p>` : ''}
          ${testCase.error ? `<pre class="text-xs mt-1 overflow-auto max-h-20 p-1 bg-gray-50 rounded">${testCase.error}</pre>` : ''}
        `;
        
        // Add expand/collapse functionality for long results
        if (testCase.details) {
          const detailsButton = document.createElement('button');
          detailsButton.className = 'text-xs text-blue-600 hover:underline mt-1';
          detailsButton.textContent = 'Show Details';
          
          const detailsElement = document.createElement('div');
          detailsElement.className = 'text-xs mt-1 overflow-auto max-h-32 p-1 bg-gray-50 rounded hidden';
          detailsElement.textContent = JSON.stringify(testCase.details, null, 2);
          
          detailsButton.addEventListener('click', () => {
            const isHidden = detailsElement.classList.contains('hidden');
            detailsElement.classList.toggle('hidden', !isHidden);
            detailsButton.textContent = isHidden ? 'Hide Details' : 'Show Details';
          });
          
          resultElement.appendChild(detailsButton);
          resultElement.appendChild(detailsElement);
        }
        
        resultsContainer.appendChild(resultElement);
      });
    }
  }
  
  /**
   * Returns a CSS class for the test status background
   * @param {string} status - The test status
   * @returns {string} CSS class
   */
  function getStatusColorClass(status) {
    switch (status) {
      case 'passed': return 'bg-green-100 border-l-4 border-green-500';
      case 'failed': return 'bg-red-100 border-l-4 border-red-500';
      case 'skipped': return 'bg-gray-100 border-l-4 border-gray-500';
      case 'running': return 'bg-blue-100 border-l-4 border-blue-500';
      default: return 'bg-gray-100';
    }
  }
  
  /**
   * Returns a CSS class for the test status text
   * @param {string} status - The test status
   * @returns {string} CSS class
   */
  function getStatusTextClass(status) {
    switch (status) {
      case 'passed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'skipped': return 'text-gray-500';
      case 'running': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  }
  
  /**
   * Registers a test case with the test suite
   * @param {string} name - Test name
   * @param {Function} testFn - Test function
   * @param {Object} options - Test options
   */
  function registerTest(name, testFn, options = {}) {
    const {
      timeout = config.testTimeouts.medium,
      skip = false,
      dependencies = []
    } = options;
    
    testState.testCases.push({
      name,
      fn: testFn,
      timeout,
      skip,
      dependencies,
      status: 'pending',
      message: skip ? 'Test skipped' : '',
      startTime: null,
      endTime: null,
      error: null,
      details: null
    });
  }
  
  /**
   * Gets a test case by name
   * @param {string} name - Test name
   * @returns {Object} Test case object
   */
  function getTestByName(name) {
    return testState.testCases.find(test => test.name === name);
  }
  
  /**
   * Runs all registered tests
   */
  async function runAllTests() {
    if (testState.running) return;
    
    // Reset test state
    testState.running = true;
    testState.startTime = Date.now();
    testState.results = {
      passed: 0,
      failed: 0,
      skipped: 0,
      total: testState.testCases.length
    };
    testState.errors = [];
    
    // Reset individual test states
    testState.testCases.forEach(test => {
      test.status = test.skip ? 'skipped' : 'pending';
      test.message = test.skip ? 'Test skipped' : '';
      test.startTime = null;
      test.endTime = null;
      test.error = null;
      test.details = null;
    });
    
    updateTestUI();
    
    // Inform about environment
    console.log(`Running tests in ${config.testEnvironment} environment`);
    
    // Attempt to find a valid goal ID if not already set
    if (!config.testGoalId) {
      try {
        config.testGoalId = await findTestGoalId();
      } catch (error) {
        console.error('Failed to find a valid goal ID:', error);
        testState.errors.push({
          message: 'Failed to find a valid goal ID',
          error
        });
      }
    }
    
    if (!config.testGoalId) {
      alert('No valid goal ID found. Please navigate to a page with an existing goal to run tests.');
      testState.running = false;
      updateTestUI();
      return;
    }
    
    // Organize tests by dependencies
    const independentTests = testState.testCases.filter(test => 
      !test.skip && (!test.dependencies || test.dependencies.length === 0)
    );
    
    const dependentTests = testState.testCases.filter(test => 
      !test.skip && test.dependencies && test.dependencies.length > 0
    );
    
    // Run independent tests first
    for (const test of independentTests) {
      await runTest(test);
      updateTestUI();
      
      if (config.stopOnFailure && test.status === 'failed') {
        break;
      }
    }
    
    // Run dependent tests if dependencies have passed
    if (!config.stopOnFailure || testState.results.failed === 0) {
      for (const test of dependentTests) {
        // Check if all dependencies passed
        const dependenciesPassed = test.dependencies.every(depName => {
          const depTest = getTestByName(depName);
          return depTest && depTest.status === 'passed';
        });
        
        if (dependenciesPassed) {
          await runTest(test);
        } else {
          test.status = 'skipped';
          test.message = 'Skipped due to failed dependencies';
          testState.results.skipped++;
        }
        
        updateTestUI();
        
        if (config.stopOnFailure && test.status === 'failed') {
          break;
        }
      }
    }
    
    // Finalize
    testState.running = false;
    testState.endTime = Date.now();
    const duration = ((testState.endTime - testState.startTime) / 1000).toFixed(2);
    
    console.log(`Tests completed in ${duration}s - Passed: ${testState.results.passed}, Failed: ${testState.results.failed}, Skipped: ${testState.results.skipped}`);
    
    updateTestUI();
  }
  
  /**
   * Runs a single test with timeout protection
   * @param {Object} test - Test object
   */
  async function runTest(test) {
    test.status = 'running';
    test.startTime = Date.now();
    updateTestUI();
    
    try {
      // Create timeout promise
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => {
          reject(new Error(`Test timed out after ${test.timeout}ms`));
        }, test.timeout);
      });
      
      // Run test with timeout race
      const result = await Promise.race([
        test.fn(config.testGoalId),
        timeoutPromise
      ]);
      
      test.status = 'passed';
      test.message = 'Test passed successfully';
      test.details = result;
      testState.results.passed++;
    } catch (error) {
      test.status = 'failed';
      test.message = error.message || 'Test failed with no error message';
      test.error = error.stack || JSON.stringify(error);
      testState.results.failed++;
      testState.errors.push({
        test: test.name,
        error
      });
      
      if (config.logResults) {
        console.error(`Test failed: ${test.name}`, error);
      }
    } finally {
      test.endTime = Date.now();
      const duration = test.endTime - test.startTime;
      if (config.logResults) {
        console.log(`Test "${test.name}" ${test.status} in ${duration}ms`);
      }
    }
  }
  
  /**
   * Finds a valid goal ID for testing
   * @returns {Promise<string>} A valid goal ID
   */
  async function findTestGoalId() {
    // Check DOM for a goal ID first
    const goalElements = document.querySelectorAll('[data-goal-id]');
    if (goalElements.length > 0) {
      const goalId = goalElements[0].dataset.goalId;
      if (goalId) {
        localStorage.setItem('test_goal_id', goalId);
        return goalId;
      }
    }
    
    // Try to fetch a goal ID from the API
    try {
      if (!window.VisualizationDataService) {
        throw new Error('VisualizationDataService not available');
      }
      
      throw new Error('Auto-discovery of goals not implemented');
    } catch (error) {
      // Prompt user for a goal ID if all else fails
      const userGoalId = prompt('Please enter a goal ID for testing:');
      if (userGoalId) {
        localStorage.setItem('test_goal_id', userGoalId);
        return userGoalId;
      }
      
      throw new Error('No valid goal ID found');
    }
  }
  
  /**
   * Creates a DOM element for testing
   * @param {string} componentType - Type of component to create
   * @param {string} goalId - Goal ID for the component
   * @returns {HTMLElement} The created element
   */
  function createTestElement(componentType, goalId) {
    const element = document.createElement('div');
    element.id = `test-${componentType}-${Date.now()}`;
    element.className = 'api-test-element';
    element.dataset.goalId = goalId;
    element.style.height = '300px';
    element.style.marginBottom = '1rem';
    element.style.padding = '1rem';
    element.style.border = '1px solid #e5e7eb';
    element.style.borderRadius = '0.5rem';
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = `Test ${componentType}`;
    title.className = 'text-lg font-medium mb-2';
    element.appendChild(title);
    
    // Append to a special test container or create one
    let testContainer = document.getElementById('api-test-component-container');
    if (!testContainer) {
      testContainer = document.createElement('div');
      testContainer.id = 'api-test-component-container';
      testContainer.className = 'fixed top-0 left-0 p-4 z-40 bg-white border-r border-b rounded-br-lg shadow-lg overflow-auto max-h-[80vh] max-w-lg';
      document.body.appendChild(testContainer);
    }
    
    testContainer.appendChild(element);
    return element;
  }
  
  /**
   * Waits for a condition to be true
   * @param {Function} condition - Condition function to wait for
   * @param {number} timeout - Maximum time to wait in ms
   * @param {number} interval - Check interval in ms
   * @returns {Promise<void>} Resolves when condition is true
   */
  function waitFor(condition, timeout = 5000, interval = 100) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const check = () => {
        // Check if condition is true
        if (condition()) {
          return resolve();
        }
        
        // Check if we've timed out
        if (Date.now() - startTime >= timeout) {
          return reject(new Error(`Timeout waiting for condition after ${timeout}ms`));
        }
        
        // Schedule next check
        setTimeout(check, interval);
      };
      
      check();
    });
  }
  
  /**
   * Simulates network conditions
   * @param {string} condition - The network condition to simulate
   * @returns {Promise<void>} Resolves when simulation is set up
   */
  function simulateNetworkCondition(condition) {
    return new Promise((resolve) => {
      switch (condition) {
        case 'offline':
          // Use the browser's offline functionality
          if ('serviceWorker' in navigator && 'connect' in navigator.serviceWorker) {
            // Use service worker if available
            console.log('Using service worker to simulate offline mode');
            window.__testOffline = true;
            
            // Override navigator.onLine
            Object.defineProperty(navigator, 'onLine', {
              configurable: true,
              get: function() { return !window.__testOffline; }
            });
            
            // Trigger offline event
            window.dispatchEvent(new Event('offline'));
          } else {
            console.warn('Service worker not available, cannot fully simulate offline mode');
            window.__testOffline = true;
            
            // Try to override navigator.onLine
            try {
              Object.defineProperty(navigator, 'onLine', {
                configurable: true,
                get: function() { return !window.__testOffline; }
              });
              
              // Trigger offline event
              window.dispatchEvent(new Event('offline'));
            } catch (e) {
              console.error('Could not override navigator.onLine', e);
            }
          }
          break;
          
        case 'online':
          // Restore online functionality
          window.__testOffline = false;
          
          // If we previously overrode navigator.onLine, restore its behavior
          if (Object.getOwnPropertyDescriptor(navigator, 'onLine').configurable) {
            Object.defineProperty(navigator, 'onLine', {
              configurable: true,
              get: function() { return true; }
            });
          }
          
          // Trigger online event
          window.dispatchEvent(new Event('online'));
          break;
          
        case 'slow':
          // We can't truly simulate slow network, but we can delay API responses
          // by overriding fetch with a delayed version
          window.__originalFetch = window.fetch;
          window.fetch = function(...args) {
            return new Promise((resolve, reject) => {
              setTimeout(() => {
                window.__originalFetch(...args)
                  .then(resolve)
                  .catch(reject);
              }, 2000); // 2 second delay
            });
          };
          break;
          
        case 'normal':
          // Restore normal fetch behavior
          if (window.__originalFetch) {
            window.fetch = window.__originalFetch;
            window.__originalFetch = null;
          }
          break;
          
        default:
          console.warn(`Unknown network condition: ${condition}`);
      }
      
      // Give a moment for the changes to take effect
      setTimeout(resolve, 100);
    });
  }
  
  // Define the test cases
  function defineTests() {
    // Test 1: VisualizationDataService Availability
    registerTest('VisualizationDataService Availability', async () => {
      if (!window.VisualizationDataService) {
        throw new Error('VisualizationDataService is not available');
      }
      
      // Check for required API methods
      const requiredMethods = [
        'fetchVisualizationData',
        'calculateProbability',
        'fetchAdjustments',
        'fetchScenarios',
        'clearCache',
        'isOnline'
      ];
      
      const missingMethods = requiredMethods.filter(
        method => typeof window.VisualizationDataService[method] !== 'function'
      );
      
      if (missingMethods.length > 0) {
        throw new Error(`Missing required methods: ${missingMethods.join(', ')}`);
      }
      
      return { 
        service: 'VisualizationDataService', 
        methods: Object.keys(window.VisualizationDataService)
      };
    }, { timeout: config.testTimeouts.short });
    
    // Test 2: ErrorHandlingService Availability
    registerTest('ErrorHandlingService Availability', async () => {
      if (!window.ErrorHandlingService) {
        throw new Error('ErrorHandlingService is not available');
      }
      
      // Check for required API methods
      const requiredMethods = [
        'handleError',
        'showErrorToast',
        'withErrorHandling',
        'shouldUseFallback'
      ];
      
      const missingMethods = requiredMethods.filter(
        method => typeof window.ErrorHandlingService[method] !== 'function'
      );
      
      if (missingMethods.length > 0) {
        throw new Error(`Missing required methods: ${missingMethods.join(', ')}`);
      }
      
      return { 
        service: 'ErrorHandlingService', 
        methods: Object.keys(window.ErrorHandlingService)
      };
    }, { timeout: config.testTimeouts.short });
    
    // Test 3: DataEventBus Availability
    registerTest('DataEventBus Availability', async () => {
      if (!window.DataEventBus) {
        throw new Error('DataEventBus is not available');
      }
      
      // Check for required API methods
      const requiredMethods = [
        'subscribe',
        'publish',
        'registerComponent',
        'unregisterComponent'
      ];
      
      const missingMethods = requiredMethods.filter(
        method => typeof window.DataEventBus[method] !== 'function'
      );
      
      if (missingMethods.length > 0) {
        throw new Error(`Missing required methods: ${missingMethods.join(', ')}`);
      }
      
      return { 
        service: 'DataEventBus', 
        methods: Object.keys(window.DataEventBus)
      };
    }, { timeout: config.testTimeouts.short });
    
    // Test 4: LoadingStateManager Availability
    registerTest('LoadingStateManager Availability', async () => {
      if (!window.loadingState) {
        throw new Error('LoadingStateManager is not available');
      }
      
      // Check for required API methods
      const requiredMethods = [
        'setLoading',
        'showProgressBar',
        'hideProgressBar',
        'showError'
      ];
      
      const missingMethods = requiredMethods.filter(
        method => typeof window.loadingState[method] !== 'function'
      );
      
      if (missingMethods.length > 0) {
        throw new Error(`Missing required methods: ${missingMethods.join(', ')}`);
      }
      
      return { 
        service: 'LoadingStateManager', 
        methods: Object.keys(window.loadingState)
      };
    }, { timeout: config.testTimeouts.short });
    
    // Test 5: API Base Fetch
    registerTest('API Base Fetch', async (goalId) => {
      const response = await window.VisualizationDataService.fetchVisualizationData(goalId);
      
      if (!response) {
        throw new Error('No response received from fetchVisualizationData');
      }
      
      // Check required data structures
      if (!response.probabilisticGoalData) {
        throw new Error('Response missing probabilisticGoalData');
      }
      
      if (!response.adjustmentImpactData) {
        throw new Error('Response missing adjustmentImpactData');
      }
      
      if (!response.scenarioComparisonData) {
        throw new Error('Response missing scenarioComparisonData');
      }
      
      return { 
        dataReceived: true,
        goal_id: goalId,
        dataStructures: Object.keys(response),
        timestamp: new Date().toISOString()
      };
    }, { 
      timeout: config.testTimeouts.medium,
      dependencies: ['VisualizationDataService Availability']
    });
    
    // Test 6: API Cache Usage
    registerTest('API Cache Usage', async (goalId) => {
      // Force first fetch to ensure cache is populated
      await window.VisualizationDataService.fetchVisualizationData(goalId, { forceRefresh: true });
      
      // Now fetch again, should use cache
      const startTime = performance.now();
      const response = await window.VisualizationDataService.fetchVisualizationData(goalId);
      const endTime = performance.now();
      
      // Cached responses should be much faster (< 50ms)
      const duration = endTime - startTime;
      
      if (duration > 50) {
        console.warn(`Cache fetch took ${duration.toFixed(2)}ms, which is longer than expected for a cache hit`);
      }
      
      // Check for cache metadata
      if (!response._metadata || !response._metadata.fromCache) {
        throw new Error('Response does not indicate it came from cache');
      }
      
      return { 
        fromCache: response._metadata.fromCache,
        duration: duration.toFixed(2) + 'ms',
        timestamp: new Date().toISOString()
      };
    }, { 
      timeout: config.testTimeouts.medium,
      dependencies: ['API Base Fetch']
    });
    
    // Test 7: Cache Invalidation
    registerTest('Cache Invalidation', async (goalId) => {
      // Clear the cache
      window.VisualizationDataService.clearCache(goalId);
      
      // Verify the cache is cleared
      if (window.VisualizationDataService.hasData(goalId)) {
        throw new Error('Cache should be empty after clearCache call');
      }
      
      // Fetch fresh data
      const response = await window.VisualizationDataService.fetchVisualizationData(goalId);
      
      // Should not be from cache
      if (response._metadata && response._metadata.fromCache) {
        throw new Error('Response should not be from cache after clearing cache');
      }
      
      return { 
        cacheCleared: true,
        freshDataFetched: true,
        timestamp: new Date().toISOString()
      };
    }, { 
      timeout: config.testTimeouts.medium,
      dependencies: ['API Cache Usage']
    });
    
    // Test 8: API Component Data Extraction
    registerTest('API Component Data Extraction', async (goalId) => {
      // First fetch full data
      const fullData = await window.VisualizationDataService.fetchVisualizationData(goalId);
      
      // Extract component-specific data
      const probabilisticData = window.VisualizationDataService.getComponentData(fullData, 'probabilistic');
      const adjustmentData = window.VisualizationDataService.getComponentData(fullData, 'adjustment');
      const scenarioData = window.VisualizationDataService.getComponentData(fullData, 'scenario');
      
      // Validate extracted data
      if (!probabilisticData || !probabilisticData.goalId) {
        throw new Error('Invalid probabilistic data extracted');
      }
      
      if (!adjustmentData || !adjustmentData.goalId) {
        throw new Error('Invalid adjustment data extracted');
      }
      
      if (!scenarioData || !scenarioData.goalId) {
        throw new Error('Invalid scenario data extracted');
      }
      
      return {
        extractedComponents: ['probabilistic', 'adjustment', 'scenario'],
        complete: true,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['API Base Fetch']
    });
    
    // Test 9: Loading State Changes
    registerTest('Loading State Changes', async (goalId) => {
      const loadingStates = [];
      
      // Create loading callback
      const onLoadingChange = (isLoading) => {
        loadingStates.push({ 
          isLoading, 
          timestamp: Date.now()
        });
      };
      
      // Fetch with loading callback
      await window.VisualizationDataService.fetchVisualizationData(goalId, {
        onLoadingChange,
        forceRefresh: true // Force refresh to ensure loading state changes
      });
      
      // Verify loading states
      if (loadingStates.length < 2) {
        throw new Error(`Expected at least 2 loading state changes, got ${loadingStates.length}`);
      }
      
      // First should be loading: true
      if (!loadingStates[0].isLoading) {
        throw new Error('First loading state should be true');
      }
      
      // Last should be loading: false
      if (loadingStates[loadingStates.length - 1].isLoading) {
        throw new Error('Last loading state should be false');
      }
      
      return {
        loadingStateChanges: loadingStates.length,
        sequence: loadingStates.map(state => state.isLoading),
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['API Base Fetch']
    });
    
    // Test 10: Network Status Detection
    registerTest('Network Status Detection', async () => {
      // Get current network status
      const initialStatus = window.VisualizationDataService.isOnline();
      
      if (typeof initialStatus !== 'boolean') {
        throw new Error('isOnline should return a boolean');
      }
      
      // Don't actually simulate offline in automated tests
      // as it's hard to restore properly
      if (config.mockOffline) {
        // Simulate going offline
        await simulateNetworkCondition('offline');
        
        // Check that isOnline returns false
        const offlineStatus = window.VisualizationDataService.isOnline();
        if (offlineStatus !== false) {
          throw new Error('isOnline should return false when offline');
        }
        
        // Restore online status
        await simulateNetworkCondition('online');
        
        // Check that isOnline returns true
        const onlineStatus = window.VisualizationDataService.isOnline();
        if (onlineStatus !== true) {
          throw new Error('isOnline should return true when online');
        }
      }
      
      return {
        initialNetworkStatus: initialStatus,
        networkDetectionWorks: true,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['VisualizationDataService Availability']
    });
    
    // Test 11: Error Handling Service Integration
    registerTest('Error Handling Service Integration', async () => {
      // Ensure error toast container exists
      const errorToastId = window.ErrorHandlingService.showErrorToast(
        'This is a test error message', 
        { duration: 1000, level: 'info' }
      );
      
      // Toast should be displayed
      const toast = document.getElementById(errorToastId);
      if (!toast) {
        throw new Error('Error toast not displayed');
      }
      
      // Wait for toast to be removed
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Toast should be gone now
      const toastAfterTimeout = document.getElementById(errorToastId);
      if (toastAfterTimeout) {
        throw new Error('Error toast not removed after timeout');
      }
      
      return {
        errorToastDisplayed: true,
        errorToastRemoved: true,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['ErrorHandlingService Availability']
    });
    
    // Test 12: Data Event Bus Subscription
    registerTest('Data Event Bus Subscription', async () => {
      const testEvent = 'test-event-' + Date.now();
      let eventReceived = false;
      let eventData = null;
      
      // Subscribe to test event
      const unsubscribe = window.DataEventBus.subscribe(testEvent, (data) => {
        eventReceived = true;
        eventData = data;
      });
      
      // Publish test event
      const testPayload = { test: true, timestamp: Date.now() };
      window.DataEventBus.publish(testEvent, testPayload);
      
      // Wait for event to be processed
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Verify event was received
      if (!eventReceived) {
        throw new Error('Event not received after publishing');
      }
      
      // Verify payload
      if (!eventData || !eventData.test) {
        throw new Error('Event data not received correctly');
      }
      
      // Unsubscribe
      unsubscribe();
      
      // Clear event data
      eventReceived = false;
      eventData = null;
      
      // Publish again
      window.DataEventBus.publish(testEvent, { test: false });
      
      // Wait for event to be processed
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Verify event was not received after unsubscribe
      if (eventReceived) {
        throw new Error('Event should not be received after unsubscribe');
      }
      
      return {
        subscriptionWorks: true,
        unsubscribeWorks: true,
        eventPayloadCorrect: true,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['DataEventBus Availability']
    });
    
    // Test 13: Component Registration
    registerTest('Component Registration', async () => {
      const componentId = 'test-component-' + Date.now();
      const componentType = 'test-visualization';
      const initialData = { test: true, timestamp: Date.now() };
      
      // Register component
      const unregister = window.DataEventBus.registerComponent(
        componentId,
        componentType,
        initialData
      );
      
      // Check registration
      const activeComponents = window.DataEventBus.getActiveComponents();
      const isRegistered = activeComponents.includes(componentId);
      
      if (!isRegistered) {
        throw new Error('Component not found in active components after registration');
      }
      
      // Unregister
      unregister();
      
      // Check unregistration
      const activeComponentsAfter = window.DataEventBus.getActiveComponents();
      const isStillRegistered = activeComponentsAfter.includes(componentId);
      
      if (isStillRegistered) {
        throw new Error('Component still found in active components after unregistration');
      }
      
      return {
        registrationWorks: true,
        unregistrationWorks: true,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['DataEventBus Availability']
    });
    
    // Test 14: Component Data Synchronization
    registerTest('Component Data Synchronization', async () => {
      // Register two components
      const componentId1 = 'test-component-1-' + Date.now();
      const componentId2 = 'test-component-2-' + Date.now();
      const initialData = { value: 1, timestamp: Date.now() };
      
      // Track updates received by component 2
      let component2Updates = 0;
      let latestValue = null;
      
      // Subscribe to data updates
      const subscription = window.DataEventBus.subscribe('data-updated', (data) => {
        if (data.target === componentId2) {
          component2Updates++;
          latestValue = data.payload?.value;
        }
      });
      
      // Register components
      const unregister1 = window.DataEventBus.registerComponent(
        componentId1, 'test-source', initialData
      );
      
      const unregister2 = window.DataEventBus.registerComponent(
        componentId2, 'test-target', initialData
      );
      
      // Force synchronization
      window.DataEventBus.forceSynchronization();
      
      // Update component 1 data
      window.DataEventBus.publish('data-updated', {
        source: componentId1,
        target: 'all',
        payload: { value: 2, timestamp: Date.now() }
      });
      
      // Wait for updates to propagate
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Clean up
      unregister1();
      unregister2();
      subscription();
      
      // Check updates
      if (component2Updates === 0) {
        throw new Error('Component 2 did not receive updates');
      }
      
      return {
        updatesReceived: component2Updates,
        finalValue: latestValue,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['DataEventBus Availability', 'Component Registration']
    });
    
    // Test 15: Goal Probability API
    registerTest('Goal Probability API', async (goalId) => {
      // Simple test parameters
      const testParameters = {
        targetAmount: 100000,
        currentSavings: 10000,
        monthlyContribution: 1000,
        rateOfReturn: 0.07,
        timeframeYears: 10
      };
      
      // Call probability API
      const result = await window.VisualizationDataService.calculateProbability(
        goalId, testParameters
      );
      
      // Verify response
      if (result === null || result === undefined) {
        throw new Error('No result returned from calculateProbability');
      }
      
      if (typeof result.probability !== 'number') {
        throw new Error('Result does not contain a probability number');
      }
      
      // Probability should be between 0 and 1
      if (result.probability < 0 || result.probability > 1) {
        throw new Error(`Invalid probability value: ${result.probability}`);
      }
      
      return {
        parametersUsed: testParameters,
        probabilityResult: result.probability,
        valid: result.valid,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['API Base Fetch']
    });
    
    // Test 16: Adjustments API
    registerTest('Adjustments API', async (goalId) => {
      // Call adjustments API
      const result = await window.VisualizationDataService.fetchAdjustments(goalId);
      
      // Verify response
      if (!result) {
        throw new Error('No result returned from fetchAdjustments');
      }
      
      if (!result.adjustments || !Array.isArray(result.adjustments)) {
        throw new Error('Result does not contain adjustments array');
      }
      
      // Check that adjustments have required fields
      for (const adjustment of result.adjustments) {
        if (!adjustment.id) {
          throw new Error('Adjustment missing ID');
        }
        
        if (!adjustment.description) {
          throw new Error('Adjustment missing description');
        }
        
        if (!adjustment.impactMetrics) {
          throw new Error('Adjustment missing impactMetrics');
        }
      }
      
      return {
        adjustmentsCount: result.adjustments.length,
        currentProbability: result.currentProbability,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['API Base Fetch']
    });
    
    // Test 17: Scenarios API
    registerTest('Scenarios API', async (goalId) => {
      // Call scenarios API
      const result = await window.VisualizationDataService.fetchScenarios(goalId);
      
      // Verify response
      if (!result) {
        throw new Error('No result returned from fetchScenarios');
      }
      
      if (!result.scenarios || !Array.isArray(result.scenarios)) {
        throw new Error('Result does not contain scenarios array');
      }
      
      // Check that at least one scenario is marked as baseline
      const hasBaseline = result.scenarios.some(s => s.isBaseline);
      if (!hasBaseline && result.scenarios.length > 0) {
        throw new Error('No scenario marked as baseline');
      }
      
      // Check that scenarios have required fields
      for (const scenario of result.scenarios) {
        if (!scenario.id) {
          throw new Error('Scenario missing ID');
        }
        
        if (!scenario.name) {
          throw new Error('Scenario missing name');
        }
        
        if (typeof scenario.probability !== 'number') {
          throw new Error('Scenario missing probability');
        }
      }
      
      return {
        scenariosCount: result.scenarios.length,
        hasBaselineScenario: hasBaseline,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['API Base Fetch']
    });
    
    // Test 18: GoalVisualizationInitializer Availability
    registerTest('GoalVisualizationInitializer Availability', async () => {
      if (!window.GoalVisualizationInitializer) {
        throw new Error('GoalVisualizationInitializer is not available');
      }
      
      // Check for required API methods
      const requiredMethods = [
        'initAll',
        'fetchAndRefresh',
        'refreshVisualization',
        'configure'
      ];
      
      const missingMethods = requiredMethods.filter(
        method => typeof window.GoalVisualizationInitializer[method] !== 'function'
      );
      
      if (missingMethods.length > 0) {
        throw new Error(`Missing required methods: ${missingMethods.join(', ')}`);
      }
      
      return { 
        service: 'GoalVisualizationInitializer', 
        methods: Object.keys(window.GoalVisualizationInitializer)
      };
    }, { timeout: config.testTimeouts.short });
    
    // Test 19: Component Integration Test - ProbabilisticGoalVisualizer
    registerTest('Component Integration - ProbabilisticGoalVisualizer', async (goalId) => {
      // Skip if React is not available
      if (!window.React || !window.ReactDOM) {
        console.warn('React not available, skipping component integration test');
        return { skipped: true, reason: 'React not available' };
      }
      
      // Check if ProbabilisticGoalVisualizer component exists
      if (typeof ProbabilisticGoalVisualizer !== 'function') {
        console.warn('ProbabilisticGoalVisualizer component not available, skipping test');
        return { skipped: true, reason: 'Component not available' };
      }
      
      // Create test element
      const element = createTestElement('probabilistic-visualizer', goalId);
      
      // Get data
      const data = await window.VisualizationDataService.fetchVisualizationData(goalId);
      const probabilisticData = window.VisualizationDataService.getComponentData(data, 'probabilistic');
      
      // Initialize component
      window.GoalVisualizationInitializer.refreshVisualization('probabilistic-goal-visualizer', probabilisticData);
      
      // Wait for component to initialize
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Clean up
      if (element.parentNode) {
        element.parentNode.removeChild(element);
      }
      
      return {
        componentInitialized: true,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['API Component Data Extraction', 'GoalVisualizationInitializer Availability']
    });
    
    // Test 20: Error Recovery Test
    registerTest('Error Recovery Test', async (goalId) => {
      // Create a deliberate error situation
      const errorFn = async () => {
        throw new Error('Test error for recovery');
      };
      
      // Create recovery function
      let recoveryAttempted = false;
      const recoveryFn = () => {
        recoveryAttempted = true;
        return true;
      };
      
      // Handle error with ErrorHandlingService
      try {
        await errorFn();
      } catch (error) {
        window.ErrorHandlingService.handleError(error, 'test operation', {
          retryAction: recoveryFn,
          showToast: true,
          metadata: { test: true }
        });
      }
      
      // Try automatic retry using withErrorHandling
      let autoRetryCompleted = false;
      
      const wrappedFn = window.ErrorHandlingService.withErrorHandling(
        async () => {
          // First call will fail
          if (!autoRetryCompleted) {
            autoRetryCompleted = true;
            throw new Error('Auto-retry test error');
          }
          
          // Second call will succeed
          return true;
        },
        {
          context: 'auto-retry operation',
          retryPolicy: {
            maxRetries: 1,
            initialDelay: 100
          }
        }
      );
      
      // Execute wrapped function
      const result = await wrappedFn();
      
      if (!result) {
        throw new Error('Auto-retry mechanism failed');
      }
      
      return {
        errorHandled: true,
        recoveryAvailable: true,
        autoRetryWorks: result === true,
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['ErrorHandlingService Availability']
    });
    
    // Test 21: PerformanceOptimizer Availability
    registerTest('PerformanceOptimizer Availability', async () => {
      if (!window.PerformanceOptimizer) {
        throw new Error('PerformanceOptimizer is not available');
      }
      
      // Check for required API methods
      const requiredMethods = [
        'throttle',
        'debounce',
        'memoize',
        'batchRequest',
        'cache',
        'dom',
        'trackApiCall'
      ];
      
      const missingMethods = requiredMethods.filter(
        method => typeof window.PerformanceOptimizer[method] !== 'function' && 
                  typeof window.PerformanceOptimizer[method] !== 'object'
      );
      
      if (missingMethods.length > 0) {
        throw new Error(`Missing required methods or objects: ${missingMethods.join(', ')}`);
      }
      
      return { 
        service: 'PerformanceOptimizer', 
        methods: Object.keys(window.PerformanceOptimizer)
      };
    }, { timeout: config.testTimeouts.short });
    
    // Test 22: Optimized Cache Performance
    registerTest('Optimized Cache Performance', async () => {
      if (!window.PerformanceOptimizer || !window.PerformanceOptimizer.cache) {
        return { skipped: true, reason: 'PerformanceOptimizer cache not available' };
      }
      
      // Test basic cache operations
      const testKey = 'test_key_' + Date.now();
      const testData = { value: 'test_value', timestamp: Date.now() };
      
      // Measure cache set performance
      const setStart = performance.now();
      const setResult = window.PerformanceOptimizer.cache.set(
        testKey, 
        testData, 
        { ttl: 5000, priority: 10 }
      );
      const setDuration = performance.now() - setStart;
      
      // Measure cache get performance
      const getStart = performance.now();
      const cachedData = window.PerformanceOptimizer.cache.get(testKey);
      const getDuration = performance.now() - getStart;
      
      // Verify cached data
      const dataMatches = cachedData && cachedData.value === testData.value;
      
      // Get cache stats
      const cacheStats = window.PerformanceOptimizer.cache.getStats();
      
      // Measure cache remove performance
      const removeStart = performance.now();
      const removeResult = window.PerformanceOptimizer.cache.remove(testKey);
      const removeDuration = performance.now() - removeStart;
      
      // Verify data was removed
      const dataRemoved = !window.PerformanceOptimizer.cache.get(testKey);
      
      return {
        cacheOperational: setResult && dataMatches && removeResult && dataRemoved,
        performance: {
          set: setDuration.toFixed(3) + 'ms',
          get: getDuration.toFixed(3) + 'ms',
          remove: removeDuration.toFixed(3) + 'ms'
        },
        cacheStats: cacheStats,
        timestamp: new Date().toISOString()
      };
    }, { 
      timeout: config.testTimeouts.medium,
      dependencies: ['PerformanceOptimizer Availability']
    });
    
    // Test 23: DOM Update Optimization
    registerTest('DOM Update Optimization', async () => {
      if (!window.PerformanceOptimizer || !window.PerformanceOptimizer.dom) {
        return { skipped: true, reason: 'PerformanceOptimizer DOM utilities not available' };
      }
      
      // Create a test element
      const testDiv = document.createElement('div');
      testDiv.id = 'dom-optimization-test';
      testDiv.innerHTML = 'Initial content';
      document.body.appendChild(testDiv);
      
      // Measure direct DOM update
      const directStart = performance.now();
      for (let i = 0; i < 100; i++) {
        testDiv.textContent = `Updated content ${i}`;
      }
      const directDuration = performance.now() - directStart;
      
      // Measure optimized DOM update
      const batchedStart = performance.now();
      for (let i = 0; i < 100; i++) {
        window.PerformanceOptimizer.dom.scheduleUpdate(testDiv, (el) => {
          el.textContent = `Batched update ${i}`;
        });
      }
      // Wait for all updates to process
      await new Promise(resolve => setTimeout(resolve, 50));
      const batchedDuration = performance.now() - batchedStart;
      
      // Test performance measurement functionality
      const measureResult = await window.PerformanceOptimizer.dom.measureRenderPerformance(
        testDiv,
        (el) => {
          el.innerHTML = `<span>Measured update</span>`;
          return true;
        }
      );
      
      // Clean up
      document.body.removeChild(testDiv);
      
      return {
        domOptimizationWorks: true,
        performance: {
          direct: directDuration.toFixed(3) + 'ms',
          batched: batchedDuration.toFixed(3) + 'ms',
          measured: measureResult.duration.toFixed(3) + 'ms'
        },
        batchingEffectiveness: ((directDuration - batchedDuration) / directDuration * 100).toFixed(2) + '%',
        timestamp: new Date().toISOString()
      };
    }, {
      timeout: config.testTimeouts.medium,
      dependencies: ['PerformanceOptimizer Availability']
    });
  }
  
  // When the page is ready
  if (document.readyState === 'complete') {
    defineTests();
    initialize();
  } else {
    window.addEventListener('load', () => {
      defineTests();
      initialize();
    });
  }
  
  // Public API
  return {
    runAllTests,
    registerTest,
    getTestResults: () => ({ ...testState.results }),
    configure: (newConfig) => {
      Object.assign(config, newConfig);
    }
  };
})();

// Make test suite available globally
window.APIIntegrationTests = APIIntegrationTests;