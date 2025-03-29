/**
 * Test script for loading states and real-time probability updates
 * 
 * This script tests the functionality of:
 * 1. LoadingStateManager.js - Phase 3, Item 1
 * 2. goal_form_probability.js - Phase 3, Item 2
 * 
 * Run this by including it in a test HTML page.
 */

const LoadingStateTests = (function() {
  // Test results container
  const results = {
    total: 0,
    passed: 0,
    failed: 0,
    details: []
  };

  // Log a test result
  function logTest(name, result, error = null) {
    results.total++;
    
    if (result) {
      results.passed++;
      results.details.push({
        name,
        result: 'PASS',
        error: null
      });
      
      console.log(`✅ PASS: ${name}`);
    } else {
      results.failed++;
      results.details.push({
        name,
        result: 'FAIL',
        error
      });
      
      console.error(`❌ FAIL: ${name}`, error);
    }
  }

  // Test LoadingStateManager functionality
  function testLoadingStateManager() {
    console.group('Testing LoadingStateManager');
    
    // Test 1: LoadingStateManager is defined
    try {
      logTest('LoadingStateManager is defined', typeof window.LoadingStateManager !== 'undefined');
    } catch (error) {
      logTest('LoadingStateManager is defined', false, error);
    }
    
    // Test 2: LoadingStateManager methods are available
    try {
      const methods = ['setLoading', 'showProgressBar', 'hideProgressBar', 
        'showGlobalLoading', 'hideGlobalLoading', 'showError', 'createSkeletons'];
      
      const allMethodsExist = methods.every(method => 
        typeof window.loadingState === 'object' && 
        typeof window.loadingState[method] === 'function'
      );
      
      logTest('LoadingStateManager methods are available', allMethodsExist);
    } catch (error) {
      logTest('LoadingStateManager methods are available', false, error);
    }
    
    // Test 3: Create test element and set loading state
    try {
      // Create test element
      const testElement = document.createElement('div');
      testElement.id = 'test-loading-element';
      document.body.appendChild(testElement);
      
      // Set loading state
      const result = window.loadingState.setLoading(testElement, true);
      
      // Check if loading state was applied
      const hasLoadingClass = testElement.classList.contains('is-loading');
      const hasAriaBusy = testElement.getAttribute('aria-busy') === 'true';
      
      // Cleanup
      window.loadingState.setLoading(testElement, false);
      document.body.removeChild(testElement);
      
      logTest('SetLoading applies correct attributes', result && hasLoadingClass && hasAriaBusy);
    } catch (error) {
      logTest('SetLoading applies correct attributes', false, error);
    }
    
    // Test 4: Show and hide progress bar
    try {
      // First make sure the progress bar exists
      if (!document.getElementById('global-progress-loader')) {
        const progressLoader = document.createElement('div');
        progressLoader.id = 'global-progress-loader';
        progressLoader.className = 'progress-loader hidden';
        document.body.appendChild(progressLoader);
      }
      
      // Show progress bar
      const showResult = window.loadingState.showProgressBar();
      
      // Check if progress bar is visible
      const progressBar = document.getElementById('global-progress-loader');
      const isVisible = !progressBar.classList.contains('hidden');
      
      // Hide progress bar
      const hideResult = window.loadingState.hideProgressBar();
      
      // Check if progress bar is hidden
      const isHidden = progressBar.classList.contains('hidden');
      
      logTest('Progress bar can be shown and hidden', showResult && hideResult && isVisible && isHidden);
    } catch (error) {
      logTest('Progress bar can be shown and hidden', false, error);
    }
    
    // Test 5: Show error message
    try {
      // Make sure error toast exists
      if (!document.getElementById('global-error-toast')) {
        const errorToast = document.createElement('div');
        errorToast.id = 'global-error-toast';
        errorToast.className = 'hidden';
        
        const errorContent = document.createElement('div');
        errorContent.id = 'global-error-content';
        
        errorToast.appendChild(errorContent);
        document.body.appendChild(errorToast);
      }
      
      // Show error with very short duration
      const result = window.loadingState.showError('Test error message', 100);
      
      // Check if error is visible
      const errorToast = document.getElementById('global-error-toast');
      const errorContent = document.getElementById('global-error-content');
      
      const isVisible = !errorToast.classList.contains('hidden');
      const hasCorrectMessage = errorContent.textContent === 'Test error message';
      
      // Wait for error to auto-hide
      setTimeout(() => {
        const isHiddenAgain = errorToast.classList.contains('hidden');
        logTest('Error toast auto-hides after timeout', isHiddenAgain);
      }, 200);
      
      logTest('Error message can be shown', result && isVisible && hasCorrectMessage);
    } catch (error) {
      logTest('Error message can be shown', false, error);
    }
    
    console.groupEnd();
  }

  // Test GoalFormProbability functionality
  function testGoalFormProbability() {
    console.group('Testing GoalFormProbability');
    
    // Test 1: GoalFormProbability is defined
    try {
      logTest('GoalFormProbability is defined', typeof GoalFormProbability !== 'undefined');
    } catch (error) {
      logTest('GoalFormProbability is defined', false, error);
    }
    
    // Test 2: GoalFormProbability methods are available
    try {
      const methods = ['init', 'calculateProbability', 'getFormValues', 'updateProbabilityUI'];
      
      const allMethodsExist = methods.every(method => 
        typeof GoalFormProbability === 'object' && 
        typeof GoalFormProbability[method] === 'function'
      );
      
      logTest('GoalFormProbability methods are available', allMethodsExist);
    } catch (error) {
      logTest('GoalFormProbability methods are available', false, error);
    }
    
    // Test 3: Test updateProbabilityUI with mock elements
    try {
      // Create test elements
      const probabilityValue = document.createElement('div');
      probabilityValue.id = 'success-probability-value';
      
      const probabilityBarFill = document.createElement('div');
      probabilityBarFill.id = 'probability-bar-fill';
      
      const probabilityStatusText = document.createElement('div');
      probabilityStatusText.id = 'probability-status-text';
      
      const probabilityLoading = document.createElement('div');
      probabilityLoading.className = 'probability-loading';
      
      // Add elements to document
      document.body.appendChild(probabilityValue);
      document.body.appendChild(probabilityBarFill);
      document.body.appendChild(probabilityStatusText);
      document.body.appendChild(probabilityLoading);
      
      // Call updateProbabilityUI directly
      // This is a partial test since it requires DOM elements that would be in the form
      const mockProbability = 75.5;
      const mockStatusText = 'Test status message';
      
      // Store the original updateProbabilityUI function
      const originalUpdateProbabilityUI = GoalFormProbability.updateProbabilityUI;
      
      // Update the UI
      originalUpdateProbabilityUI(mockProbability, mockStatusText);
      
      // Check if UI was updated
      const hasCorrectProbability = probabilityValue.textContent === '75.5%';
      const hasCorrectBarWidth = probabilityBarFill.style.width === '75.5%';
      const hasCorrectStatusText = probabilityStatusText.textContent === mockStatusText;
      
      // Cleanup
      document.body.removeChild(probabilityValue);
      document.body.removeChild(probabilityBarFill);
      document.body.removeChild(probabilityStatusText);
      document.body.removeChild(probabilityLoading);
      
      logTest('UpdateProbabilityUI updates UI elements', hasCorrectProbability && hasCorrectBarWidth && hasCorrectStatusText);
    } catch (error) {
      logTest('UpdateProbabilityUI updates UI elements', false, error);
    }
    
    console.groupEnd();
  }

  // Test integration between components
  function testIntegration() {
    console.group('Testing Integration');
    
    // Test 1: GoalFormProbability uses LoadingStateManager
    try {
      // Create a spy for loadingState.setLoading
      let loadingStateUsed = false;
      const originalSetLoading = window.loadingState.setLoading;
      
      window.loadingState.setLoading = function(...args) {
        loadingStateUsed = true;
        return originalSetLoading.apply(this, args);
      };
      
      // Create minimal form elements
      const form = document.createElement('form');
      form.id = 'goal-form';
      
      const categorySelect = document.createElement('select');
      categorySelect.id = 'category';
      categorySelect.name = 'category';
      const option = document.createElement('option');
      option.value = 'test_category';
      option.textContent = 'Test Category';
      categorySelect.appendChild(option);
      categorySelect.value = 'test_category';
      
      const targetAmountInput = document.createElement('input');
      targetAmountInput.id = 'target_amount';
      targetAmountInput.name = 'target_amount';
      targetAmountInput.value = '1000';
      
      const timeframeInput = document.createElement('input');
      timeframeInput.id = 'timeframe';
      timeframeInput.name = 'timeframe';
      timeframeInput.value = '2026-01-01';
      
      // Success probability elements
      const probabilityContainer = document.createElement('div');
      probabilityContainer.className = 'probability-container';
      
      const probabilityValue = document.createElement('div');
      probabilityValue.id = 'success-probability-value';
      
      const probabilityBarFill = document.createElement('div');
      probabilityBarFill.id = 'probability-bar-fill';
      
      const probabilityStatusText = document.createElement('div');
      probabilityStatusText.id = 'probability-status-text';
      
      const probabilityLoading = document.createElement('div');
      probabilityLoading.className = 'probability-loading';
      
      // Add elements to document
      probabilityContainer.appendChild(probabilityValue);
      probabilityContainer.appendChild(probabilityBarFill);
      probabilityContainer.appendChild(probabilityStatusText);
      probabilityContainer.appendChild(probabilityLoading);
      
      form.appendChild(categorySelect);
      form.appendChild(targetAmountInput);
      form.appendChild(timeframeInput);
      form.appendChild(probabilityContainer);
      document.body.appendChild(form);
      
      // Mock the DataEventBus if it's used
      window.DataEventBus = {
        publish: function() {},
        subscribe: function() {}
      };
      
      // Mock VisualizationDataService too
      window.VisualizationDataService = {
        calculateProbability: function(goalId, params, options) {
          if (options && typeof options.onLoadingChange === 'function') {
            options.onLoadingChange(true); // Call loading callback
          }
          
          // Return mock result after delay
          return new Promise((resolve) => {
            setTimeout(() => {
              if (options && typeof options.onLoadingChange === 'function') {
                options.onLoadingChange(false);
              }
              
              resolve({
                successProbability: 85.5,
                adjustments: [],
                simulationData: {}
              });
            }, 100);
          });
        }
      };
      
      // Initialize GoalFormProbability
      GoalFormProbability.init({
        useEnhancedLoadingStates: true,
        debounceTime: 50 // Short debounce for testing
      });
      
      // Trigger calculation
      targetAmountInput.value = "2000"; // Change a value
      targetAmountInput.dispatchEvent(new Event('change')); // Trigger change event
      
      // Check after calculation should be complete
      setTimeout(() => {
        // Restore original setLoading
        window.loadingState.setLoading = originalSetLoading;
        
        // Clean up
        document.body.removeChild(form);
        
        logTest('GoalFormProbability uses LoadingStateManager', loadingStateUsed);
      }, 200);
    } catch (error) {
      logTest('GoalFormProbability uses LoadingStateManager', false, error);
    }
    
    console.groupEnd();
  }

  // Run all tests
  function runTests() {
    console.log('Starting tests...');
    
    // Run individual component tests
    testLoadingStateManager();
    testGoalFormProbability();
    
    // Run integration tests
    testIntegration();
    
    // Display final results
    setTimeout(() => {
      console.log('\nTest Results:');
      console.log(`Total: ${results.total}`);
      console.log(`Passed: ${results.passed}`);
      console.log(`Failed: ${results.failed}`);
      
      // Add results to page
      const resultsContainer = document.getElementById('test-results');
      if (resultsContainer) {
        let html = `
          <div class="test-summary">
            <h3>Test Results</h3>
            <div>Total: ${results.total}</div>
            <div>Passed: ${results.passed}</div>
            <div>Failed: ${results.failed}</div>
          </div>
          <table class="test-details">
            <thead>
              <tr>
                <th>Test</th>
                <th>Result</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
        `;
        
        results.details.forEach(detail => {
          html += `
            <tr class="${detail.result === 'PASS' ? 'pass' : 'fail'}">
              <td>${detail.name}</td>
              <td>${detail.result}</td>
              <td>${detail.error ? detail.error.message || 'Error' : ''}</td>
            </tr>
          `;
        });
        
        html += `
            </tbody>
          </table>
        `;
        
        resultsContainer.innerHTML = html;
      }
    }, 500);
  }

  // Public API
  return {
    runTests
  };
})();

// Run tests when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(LoadingStateTests.runTests, 100);
});