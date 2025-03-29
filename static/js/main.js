/**
 * Financial Profiler - Main JavaScript
 * Handles interactive elements and form submissions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initializeFormValidation();
    initializeSliders();
    initializeAnswerForms();
    
    // Initialize goal components
    setupGoalForm();
    setupGoalDisplays();
    
    // Initialize handlers for interactive goal features
    initializeGoalAdjustmentHandlers();
    initializeScenarioComparisonHandlers();
    
    // Initialize loading state handlers
    initializeLoadingStateSystem();
    
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

/**
 * Initialize client-side form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Validate required fields
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    highlightInvalidField(field);
                } else {
                    removeInvalidHighlight(field);
                }
            });
            
            // Validate number fields
            const numberFields = form.querySelectorAll('input[type="number"]');
            numberFields.forEach(field => {
                if (field.value) {
                    const value = parseFloat(field.value);
                    const min = field.getAttribute('min');
                    const max = field.getAttribute('max');
                    
                    if (min && value < parseFloat(min)) {
                        isValid = false;
                        highlightInvalidField(field, `Value must be at least ${min}`);
                    } else if (max && value > parseFloat(max)) {
                        isValid = false;
                        highlightInvalidField(field, `Value must be at most ${max}`);
                    } else {
                        removeInvalidHighlight(field);
                    }
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Highlight invalid form fields
 */
function highlightInvalidField(field, message) {
    field.classList.add('invalid-field');
    
    // Add error message if not already present
    let errorMessage = field.nextElementSibling;
    if (!errorMessage || !errorMessage.classList.contains('error-message')) {
        errorMessage = document.createElement('div');
        errorMessage.classList.add('error-message');
        errorMessage.style.color = '#dc3545';
        errorMessage.style.fontSize = '0.85rem';
        errorMessage.style.marginTop = '0.25rem';
        field.parentNode.insertBefore(errorMessage, field.nextSibling);
    }
    
    errorMessage.textContent = message || 'This field is required';
}

/**
 * Remove invalid highlighting from field
 */
function removeInvalidHighlight(field) {
    field.classList.remove('invalid-field');
    
    // Remove error message if present
    const errorMessage = field.nextElementSibling;
    if (errorMessage && errorMessage.classList.contains('error-message')) {
        errorMessage.remove();
    }
}

/**
 * Initialize slider controls
 */
function initializeSliders() {
    const sliders = document.querySelectorAll('.slider');
    
    sliders.forEach(slider => {
        const valueDisplay = slider.parentElement.querySelector('.slider-value');
        if (!valueDisplay) return;
        
        // Update value display on load
        valueDisplay.textContent = slider.value;
        
        // Update on change
        slider.addEventListener('input', function() {
            valueDisplay.textContent = this.value;
        });
    });
}

/**
 * Initialize answer form submission handling
 */
function initializeAnswerForms() {
    const answerForm = document.getElementById('answer-form');
    
    if (answerForm) {
        answerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(answerForm);
            
            // Handle multiselect checkboxes
            const multiselectCheckboxes = answerForm.querySelectorAll('.multiselect-checkbox:checked');
            
            // Remove any existing answer values from formData for multiselect
            if (multiselectCheckboxes.length > 0) {
                // Remove the single answer entries that FormData created automatically
                formData.delete('answer');
                
                // Add all checked values
                multiselectCheckboxes.forEach(checkbox => {
                    formData.append('answer', checkbox.value);
                });
                
                // Add a special flag to indicate this is a multiselect answer
                formData.append('is_multiselect', 'true');
                
                console.log('Multiselect values:', Array.from(formData.getAll('answer')));
            }
            
            // Show loading indicator
            const submitButton = answerForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            submitButton.textContent = 'Saving...';
            submitButton.disabled = true;
            
            fetch(answerForm.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirect to next question
                    window.location.href = data.next_url;
                } else {
                    // Show error
                    submitButton.textContent = originalButtonText;
                    submitButton.disabled = false;
                    
                    // Display error message
                    const errorMessage = document.createElement('div');
                    errorMessage.classList.add('error-message');
                    errorMessage.style.color = '#dc3545';
                    errorMessage.style.padding = '0.75rem';
                    errorMessage.style.marginTop = '1rem';
                    errorMessage.style.border = '1px solid #f5c6cb';
                    errorMessage.style.borderRadius = '0.25rem';
                    errorMessage.style.backgroundColor = '#f8d7da';
                    
                    // For invalid question ID errors, provide additional help
                    let errorText = data.error || 'An error occurred while saving your answer. Please try again.';
                    if (data.error && data.error.includes('Question not found')) {
                        errorText = 'This question could not be processed. Please try refreshing the page to continue with a new question.';
                        
                        // Add a refresh button to make it easier
                        const refreshButton = document.createElement('button');
                        refreshButton.textContent = 'Refresh Page';
                        refreshButton.className = 'btn btn-secondary mt-2';
                        refreshButton.style.marginLeft = '10px';
                        refreshButton.onclick = function() {
                            window.location.reload();
                        };
                        
                        errorMessage.textContent = errorText;
                        errorMessage.appendChild(document.createElement('br'));
                        errorMessage.appendChild(refreshButton);
                    } else {
                        // Add a "continue anyway" button for other errors
                        errorMessage.textContent = errorText;
                        
                        // Add a continue button that will take user to next question
                        const continueButton = document.createElement('button');
                        continueButton.textContent = 'Continue Anyway';
                        continueButton.className = 'btn btn-primary mt-2';
                        continueButton.style.marginLeft = '10px';
                        continueButton.onclick = function() {
                            // Redirect to the questions page to get the next question
                            const profileId = document.querySelector('input[name="profile_id"]').value;
                            if (profileId) {
                                window.location.href = `/questions?profile_id=${profileId}`;
                            } else {
                                window.location.reload();
                            }
                        };
                        
                        errorMessage.appendChild(document.createElement('br'));
                        errorMessage.appendChild(continueButton);
                    }
                    
                    // Remove any existing error messages
                    const existingErrors = answerForm.querySelectorAll('.error-message');
                    existingErrors.forEach(err => err.remove());
                    
                    answerForm.appendChild(errorMessage);
                }
            })
            .catch(error => {
                console.error('Error submitting answer:', error);
                
                // Reset button
                submitButton.textContent = originalButtonText;
                submitButton.disabled = false;
                
                // Show more detailed error when possible
                let errorMessage = 'An error occurred while saving your answer. Please try again.';
                if (error && error.message) {
                    errorMessage = error.message;
                    console.log('Error message:', error.message);
                }
                
                // Create error message element rather than using alert
                const errorElement = document.createElement('div');
                errorElement.classList.add('error-message');
                errorElement.style.color = '#dc3545';
                errorElement.style.padding = '0.75rem';
                errorElement.style.marginTop = '1rem';
                errorElement.style.border = '1px solid #f5c6cb';
                errorElement.style.borderRadius = '0.25rem';
                errorElement.style.backgroundColor = '#f8d7da';
                errorElement.textContent = errorMessage;
                
                // Remove any existing error messages
                const existingErrors = answerForm.querySelectorAll('.error-message');
                existingErrors.forEach(err => err.remove());
                
                answerForm.appendChild(errorElement);
            });
            
            // Prevent default form submission, forcing AJAX only
            return false;
        });
    }
}

/**
 * Update progress bars for profile completion
 */
function updateProgressBars(completion) {
    if (!completion) return;
    
    // Update overall progress
    const overallFill = document.querySelector('.overall-progress .progress-fill');
    if (overallFill) {
        overallFill.style.width = `${completion.overall}%`;
        
        const overallLabel = document.querySelector('.overall-progress .progress-label');
        if (overallLabel) {
            overallLabel.textContent = `Overall: ${completion.overall}%`;
        }
    }
    
    // Update category progress
    const categories = ['demographics', 'financial_basics', 'assets_and_debts', 'special_cases'];
    
    categories.forEach(category => {
        const categoryFill = document.querySelector(`.progress-item .progress-fill.${category}`);
        const categoryPercentage = document.querySelector(`.progress-item:has(.progress-fill.${category}) .progress-percentage`);
        
        if (categoryFill && completion.by_category && completion.by_category[category] !== undefined) {
            categoryFill.style.width = `${completion.by_category[category]}%`;
            
            if (categoryPercentage) {
                categoryPercentage.textContent = `${completion.by_category[category]}%`;
            }
        }
    });
}

/**
 * Setup the goal form with dynamic behavior
 */
function setupGoalForm() {
    const goalForm = document.getElementById('goal-form');
    if (!goalForm) return;
    
    const categorySelect = document.getElementById('category');
    if (!categorySelect) return;
    
    // Handle category selection to show/hide specific fields
    categorySelect.addEventListener('change', function() {
        updateCategorySpecificFields(this.value);
    });
    
    // Initialize with the current value
    if (categorySelect.value) {
        updateCategorySpecificFields(categorySelect.value);
    }
    
    // Handle advanced options toggle
    const advancedToggle = document.getElementById('advanced-toggle');
    const advancedOptions = document.getElementById('advanced-options');
    
    if (advancedToggle && advancedOptions) {
        advancedToggle.addEventListener('click', function(e) {
            e.preventDefault();
            if (advancedOptions.classList.contains('hidden')) {
                advancedOptions.classList.remove('hidden');
                advancedToggle.textContent = 'Hide Advanced Options';
            } else {
                advancedOptions.classList.add('hidden');
                advancedToggle.textContent = 'Show Advanced Options';
            }
        });
    }
    
    // Handle emergency fund monthly expenses
    const emergencyMonthsInput = document.getElementById('emergency_fund_months');
    const monthlyExpensesInput = document.getElementById('monthly_expenses');
    const targetAmountInput = document.getElementById('target_amount');
    
    // Function to fetch monthly expenses from API
    function fetchMonthlyExpenses() {
        fetch('/api/monthly_expenses')
            .then(response => response.json())
            .then(data => {
                if (data.monthly_expenses && monthlyExpensesInput) {
                    monthlyExpensesInput.value = data.monthly_expenses.toFixed(2);
                    updateEmergencyFundTarget();
                }
            })
            .catch(error => console.error('Error fetching monthly expenses:', error));
    }
    
    // Function to update emergency fund target amount based on months and expenses
    function updateEmergencyFundTarget() {
        if (categorySelect.value === 'emergency_fund' && 
            emergencyMonthsInput && monthlyExpensesInput && targetAmountInput) {
            
            const months = parseFloat(emergencyMonthsInput.value) || 6;
            const expenses = parseFloat(monthlyExpensesInput.value) || 0;
            
            if (months > 0 && expenses > 0) {
                const targetAmount = months * expenses;
                targetAmountInput.value = targetAmount.toFixed(2);
            }
        }
    }
    
    // Set up emergency fund calculations
    if (emergencyMonthsInput && monthlyExpensesInput) {
        // When the page loads, fetch monthly expenses
        if (categorySelect.value === 'emergency_fund') {
            fetchMonthlyExpenses();
        }
        
        // When emergency fund months change, update target
        emergencyMonthsInput.addEventListener('input', updateEmergencyFundTarget);
        
        // When monthly expenses change, update target
        monthlyExpensesInput.addEventListener('input', updateEmergencyFundTarget);
    }
    
    // Handle home purchase down payment calculations
    const downPaymentPercentInput = document.getElementById('down_payment_percent');
    const propertyValueInput = document.getElementById('property_value');
    
    function updateDownPaymentTarget() {
        if (categorySelect.value === 'home_purchase' && 
            downPaymentPercentInput && propertyValueInput && targetAmountInput) {
            
            const percentage = parseFloat(downPaymentPercentInput.value) || 20;
            const propertyValue = parseFloat(propertyValueInput.value) || 0;
            
            if (percentage > 0 && propertyValue > 0) {
                const targetAmount = (percentage / 100) * propertyValue;
                targetAmountInput.value = targetAmount.toFixed(2);
            }
        }
    }
    
    // Set up home purchase calculations
    if (downPaymentPercentInput && propertyValueInput) {
        downPaymentPercentInput.addEventListener('input', updateDownPaymentTarget);
        propertyValueInput.addEventListener('input', updateDownPaymentTarget);
    }
    
    // Handle education goal calculations
    const educationYearsInput = document.getElementById('education_years');
    const yearlyEducationCostInput = document.getElementById('yearly_cost');
    
    function updateEducationTarget() {
        if (categorySelect.value === 'education' && 
            educationYearsInput && yearlyEducationCostInput && targetAmountInput) {
            
            const years = parseInt(educationYearsInput.value) || 4;
            const yearlyCost = parseFloat(yearlyEducationCostInput.value) || 0;
            
            if (years > 0 && yearlyCost > 0) {
                const targetAmount = years * yearlyCost;
                targetAmountInput.value = targetAmount.toFixed(2);
            }
        }
    }
    
    // Set up education calculations
    if (educationYearsInput && yearlyEducationCostInput) {
        educationYearsInput.addEventListener('input', updateEducationTarget);
        yearlyEducationCostInput.addEventListener('input', updateEducationTarget);
    }
}

/**
 * Show or hide category-specific fields based on the selected category
 */
function updateCategorySpecificFields(category) {
    // Hide all category-specific sections first
    document.querySelectorAll('.category-specific-section').forEach(section => {
        section.classList.add('hidden');
    });
    
    // Show the specific section for the selected category
    const specificSection = document.getElementById(`${category}-section`);
    if (specificSection) {
        specificSection.classList.remove('hidden');
    }
    
    // If it's emergency fund, fetch expenses
    if (category === 'emergency_fund') {
        fetch('/api/monthly_expenses')
            .then(response => response.json())
            .then(data => {
                const expensesInput = document.getElementById('monthly_expenses');
                if (expensesInput && data.monthly_expenses) {
                    expensesInput.value = data.monthly_expenses.toFixed(2);
                    
                    // Update target amount
                    const monthsInput = document.getElementById('emergency_fund_months');
                    const targetInput = document.getElementById('target_amount');
                    if (monthsInput && targetInput) {
                        const months = parseFloat(monthsInput.value) || 6;
                        const amount = months * data.monthly_expenses;
                        targetInput.value = amount.toFixed(2);
                    }
                }
            })
            .catch(error => console.error('Error:', error));
    }
}

/**
 * Setup expanding goal displays and goal deletion
 */
function setupGoalDisplays() {
    const goalCards = document.querySelectorAll('.goal-card');
    if (goalCards.length === 0) return;
    
    // Set up expand/collapse for each goal card
    goalCards.forEach(card => {
        const expandButton = card.querySelector('.goal-expand-button');
        const expandedContent = card.querySelector('.goal-expanded-content');
        
        if (expandButton && expandedContent) {
            // Remove any existing click handlers to prevent duplicates
            expandButton.removeEventListener('click', expandButtonClickHandler);
            
            // Add the click event handler
            expandButton.addEventListener('click', expandButtonClickHandler);
            
            // Define the handler function for expand/collapse
            function expandButtonClickHandler(e) {
                // Prevent default action to avoid any navigation
                e.preventDefault();
                e.stopPropagation(); // Prevent event bubbling
                
                console.log('Expand button clicked for goal:', card.dataset.goalId);
                
                if (expandedContent.classList.contains('hidden')) {
                    // Show expanded content
                    expandedContent.classList.remove('hidden');
                    expandButton.textContent = 'Collapse';
                    
                    // Load additional details if allocation chart is present
                    const allocationChart = expandedContent.querySelector('.allocation-chart');
                    const goalId = card.dataset.goalId;
                    
                    console.log('Expanding content, goal ID:', goalId);
                    
                    if (allocationChart && goalId) {
                        console.log('Loading allocation data for chart');
                        loadGoalAllocationData(goalId, allocationChart);
                    }
                    
                    // Initialize visualization components when expanded
                    if (window.GoalVisualizationInitializer && goalId) {
                        // Wait for the content to be visible before initializing
                        setTimeout(() => {
                            // Fetch fresh data and initialize visualizations
                            window.GoalVisualizationInitializer.fetchAndRefresh(goalId);
                        }, 100);
                    }
                } else {
                    // Hide expanded content
                    expandedContent.classList.add('hidden');
                    expandButton.textContent = 'Expand';
                    console.log('Collapsing content');
                }
            }
        }
        
        // Set up progress update form
        const progressForm = card.querySelector('.progress-update-form');
        if (progressForm) {
            progressForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(progressForm);
                const goalId = card.dataset.goalId;
                
                // Convert to a standard goal update
                formData.append('id', goalId);
                formData.append('current_amount', formData.get('progress_amount'));
                
                // Submit the update
                fetch(`/goals/edit/${goalId}`, {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        throw new Error('Failed to update progress');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to update progress. Please try again.');
                });
            });
        }
        
        // Set up goal deletion
        const deleteButton = card.querySelector('.goal-delete-button');
        if (deleteButton) {
            deleteButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                if (confirm('Are you sure you want to delete this goal? This action cannot be undone.')) {
                    const goalId = card.dataset.goalId;
                    
                    fetch(`/goals/delete/${goalId}`, {
                        method: 'POST'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Remove the card from the DOM
                            card.remove();
                            
                            // Show success message
                            alert('Goal deleted successfully');
                        } else {
                            alert('Error: ' + (data.error || 'Failed to delete goal'));
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred. Please try again.');
                    });
                }
            });
        }
    });
}

/**
 * Load and display asset allocation data for a goal
 */
function loadGoalAllocationData(goalId, chartElement) {
    // Load allocation data from API
    fetch(`/api/v2/goals/allocation_data/${goalId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                chartElement.innerHTML = `<p class="error">${data.error}</p>`;
                return;
            }
            
            // Create a pie chart using HTML and CSS (simple version)
            const totalValue = data.datasets[0].data.reduce((a, b) => a + b, 0);
            let chartHtml = '<div class="pie-chart-container">';
            
            data.labels.forEach((label, index) => {
                const value = data.datasets[0].data[index];
                const percentage = ((value / totalValue) * 100).toFixed(1);
                const color = data.datasets[0].backgroundColor[index % data.datasets[0].backgroundColor.length];
                
                chartHtml += `
                    <div class="pie-segment" style="background-color: ${color};">
                        <span class="segment-label">${label}: ${percentage}%</span>
                    </div>
                `;
            });
            
            chartHtml += '</div>';
            chartElement.innerHTML = chartHtml;
        })
        .catch(error => {
            console.error('Error loading allocation data:', error);
            chartElement.innerHTML = '<p class="error">Failed to load allocation data</p>';
        });
}

/**
 * Initialize goal adjustment handlers for adjustment recommendations
 */
function initializeGoalAdjustmentHandlers() {
    // Check if we have the handler available
    if (typeof GoalAdjustmentHandler === 'undefined') {
        console.warn('GoalAdjustmentHandler not loaded. Adjustment functionality will be limited.');
        return;
    }

    // Find all adjustment panels in the DOM
    const adjustmentPanels = document.querySelectorAll('.adjustment-panel, #adjustment-impact-panel');
    
    if (adjustmentPanels.length === 0) {
        // No adjustment panels found, no need to initialize
        return;
    }

    // Look for static Apply buttons (non-React buttons)
    const applyButtons = document.querySelectorAll('.adjustment-apply-btn');
    
    // Add adjustment-apply-btn class to any buttons that need it
    applyButtons.forEach(button => {
        // Ensure each button has needed data attributes
        if (!button.dataset.adjustmentId && button.dataset.id) {
            button.dataset.adjustmentId = button.dataset.id;
        }
        
        if (!button.dataset.goalId && button.closest('[data-goal-id]')) {
            button.dataset.goalId = button.closest('[data-goal-id]').dataset.goalId;
        }
    });

    // Initialize the adjustment handler with any custom configuration
    GoalAdjustmentHandler.configure({
        apiEndpoint: '/api/v2/goals/{goal_id}/apply-adjustment',
        loadingClass: 'is-applying-adjustment',
        successMessageDuration: 3000
    });

    // Initialize handler (although it should auto-initialize on DOMContentLoaded)
    GoalAdjustmentHandler.initialize();
    
    // Register for any custom events that might indicate an adjustment was applied
    document.addEventListener('goalUpdated', function(event) {
        // If we have a goal ID and the visualization initializer, refresh the visualizations
        if (event.detail && event.detail.goalId && window.GoalVisualizationInitializer) {
            window.GoalVisualizationInitializer.fetchAndRefresh(event.detail.goalId, {
                forceRefresh: true
            });
        }
    });
}

/**
 * Initialize scenario comparison handlers
 */
function initializeScenarioComparisonHandlers() {
    // Check if we have the handler available
    if (typeof ScenarioComparisonHandler === 'undefined') {
        console.warn('ScenarioComparisonHandler not loaded. Scenario comparison functionality will be limited.');
        return;
    }

    // Find all scenario containers in the DOM
    const scenarioContainers = document.querySelectorAll('.scenarios-section, #scenario-comparison-chart');
    
    if (scenarioContainers.length === 0) {
        // No scenario containers found, no need to initialize
        return;
    }

    // Look for static Apply buttons (non-React buttons)
    const applyButtons = document.querySelectorAll('.scenario-apply-btn');
    
    // Add scenario-apply-btn class to any buttons that need it
    applyButtons.forEach(button => {
        // Ensure each button has needed data attributes
        if (!button.dataset.scenarioId && button.dataset.id) {
            button.dataset.scenarioId = button.dataset.id;
        }
        
        if (!button.dataset.goalId && button.closest('[data-goal-id]')) {
            button.dataset.goalId = button.closest('[data-goal-id]').dataset.goalId;
        }
    });

    // Initialize the scenario handler with any custom configuration
    ScenarioComparisonHandler.configure({
        apiEndpoint: '/api/v2/goals/{goal_id}/apply-scenario',
        loadingClass: 'is-applying-scenario',
        successMessageDuration: 3000
    });

    // Initialize handler (although it should auto-initialize on DOMContentLoaded)
    ScenarioComparisonHandler.initialize();
    
    // Register for any custom events that might indicate a scenario was applied
    document.addEventListener('scenarioChanged', function(event) {
        console.log('Scenario changed:', event.detail);
        // You can add any additional handling here if needed
    });
}

/**
 * Initialize shared loading state system
 * 
 * This function sets up a shared loading state system for consistent
 * loading indications across all components in the application.
 */
function initializeLoadingStateSystem() {
    // Check if LoadingStateManager is loaded as a module
    if (typeof LoadingStateManager !== 'undefined') {
        console.log('Using LoadingStateManager module for loading states');
        return;
    }
    
    // Dynamically load the LoadingStateManager script
    const script = document.createElement('script');
    script.src = '/static/js/services/LoadingStateManager.js';
    script.async = true;
    script.onload = function() {
        console.log('LoadingStateManager loaded dynamically');
    };
    script.onerror = function() {
        console.error('Failed to load LoadingStateManager. Using inline fallback.');
        initializeInlineLoadingState();
    };
    
    document.head.appendChild(script);
}

/**
 * Fallback inline loading state if the module fails to load
 * This is a simplified version of the LoadingStateManager
 */
function initializeInlineLoadingState() {
    // Add a simplified loading state directly to window
    window.loadingState = {
        setLoading: function(element, isLoading) {
            const el = typeof element === 'string' ? document.getElementById(element) : element;
            if (!el) return false;
            
            if (isLoading) {
                el.classList.add('is-loading');
                el.setAttribute('aria-busy', 'true');
            } else {
                el.classList.remove('is-loading');
                el.setAttribute('aria-busy', 'false');
            }
            return true;
        },
        
        showError: function(message, duration = 5000) {
            alert('Error: ' + message);
            return true;
        }
    };
}