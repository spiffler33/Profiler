/**
 * Financial Profiler - Main JavaScript
 * Handles interactive elements and form submissions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initializeFormValidation();
    initializeSliders();
    initializeAnswerForms();
    
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
                        errorMessage.textContent = errorText;
                    }
                    
                    // Remove any existing error messages
                    const existingErrors = answerForm.querySelectorAll('.error-message');
                    existingErrors.forEach(err => err.remove());
                    
                    answerForm.appendChild(errorMessage);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Reset button
                submitButton.textContent = originalButtonText;
                submitButton.disabled = false;
                
                // Show generic error
                alert('An error occurred. Please try again.');
            });
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