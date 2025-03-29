/**
 * Tooltips functionality for Financial Profiler
 * Dynamically adds tooltips to UI elements based on help text data
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Add tooltips to dynamic content when needed
    const contentObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                // Check if we need to add tooltips to the new content
                initializeTooltips();
            }
        });
    });
    
    // Start observing for dynamic content changes
    contentObserver.observe(document.body, { childList: true, subtree: true });
});

/**
 * Initialize tooltips on page elements
 */
function initializeTooltips() {
    // Add tooltips to all elements with data-tooltip attribute
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        // Skip if tooltip already initialized
        if (element.classList.contains('tooltip-initialized')) {
            return;
        }
        
        // Get tooltip content and optional placement
        const tooltipText = element.getAttribute('data-tooltip');
        const tooltipPlacement = element.getAttribute('data-tooltip-placement') || 'top';
        const tooltipType = element.getAttribute('data-tooltip-type') || 'info';
        
        // Create tooltip container if not a direct tooltip element
        if (!element.classList.contains('tooltip-container')) {
            // Wrap the element or add tooltip icon based on element type
            if (['INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName)) {
                // For form elements, add an icon after the label
                const formGroup = element.closest('.form-group');
                if (formGroup) {
                    const tooltipIcon = document.createElement('span');
                    tooltipIcon.className = `tooltip-icon ${tooltipType}-tooltip`;
                    tooltipIcon.innerHTML = 'i';
                    tooltipIcon.setAttribute('data-tooltip', tooltipText);
                    tooltipIcon.setAttribute('data-tooltip-placement', tooltipPlacement);
                    
                    const label = formGroup.querySelector('label');
                    if (label) {
                        label.appendChild(tooltipIcon);
                    } else {
                        formGroup.appendChild(tooltipIcon);
                    }
                    
                    createTooltipContent(tooltipIcon, tooltipText, tooltipPlacement, tooltipType);
                }
            } else if (element.classList.contains('term-tooltip')) {
                // For term definitions, make the element itself a tooltip container
                element.classList.add('tooltip-container');
                createTooltipContent(element, tooltipText, tooltipPlacement, tooltipType);
            } else {
                // For general elements, create a wrapper
                const parent = element.parentNode;
                const wrapper = document.createElement('div');
                wrapper.className = 'tooltip-container';
                
                // Replace element with wrapper containing the element
                parent.replaceChild(wrapper, element);
                wrapper.appendChild(element);
                
                // Create tooltip content in the wrapper
                createTooltipContent(wrapper, tooltipText, tooltipPlacement, tooltipType);
            }
        } else {
            // Element is already a tooltip container, just add the content
            createTooltipContent(element, tooltipText, tooltipPlacement, tooltipType);
        }
        
        // Mark as initialized
        element.classList.add('tooltip-initialized');
    });
    
    // Add tooltips to goal form fields based on goal type
    setupGoalFormTooltips();
}

/**
 * Create tooltip content element with the specified text and placement
 */
function createTooltipContent(container, text, placement, type) {
    // Create tooltip content element
    const tooltip = document.createElement('div');
    tooltip.className = `tooltip-content tooltip-${placement}`;
    
    // Check if tooltip content has a title format (Title: Content)
    if (text.includes(':')) {
        const parts = text.split(':', 2);
        const title = parts[0].trim();
        const content = parts[1].trim();
        
        const titleElement = document.createElement('div');
        titleElement.className = 'tooltip-title';
        titleElement.textContent = title;
        tooltip.appendChild(titleElement);
        
        const contentElement = document.createElement('div');
        contentElement.textContent = content;
        tooltip.appendChild(contentElement);
    } else {
        // Simple tooltip without title
        tooltip.textContent = text;
    }
    
    // Add tooltip to container
    container.appendChild(tooltip);
}

/**
 * Set up specialized tooltips for the goal form based on selected category
 */
function setupGoalFormTooltips() {
    const goalForm = document.getElementById('goal-form');
    if (!goalForm) return;
    
    const categorySelect = document.getElementById('category');
    if (!categorySelect) return;
    
    // Update tooltips when category changes
    categorySelect.addEventListener('change', updateGoalFormTooltips);
    
    // Initialize tooltips with current category
    updateGoalFormTooltips();
    
    // Add help text tooltips under form fields
    const helpTexts = goalForm.querySelectorAll('.form-help-text');
    helpTexts.forEach(helpText => {
        const text = helpText.textContent;
        helpText.closest('.form-group').setAttribute('data-tooltip', text);
    });
}

/**
 * Update tooltips based on the selected goal category
 */
function updateGoalFormTooltips() {
    const categorySelect = document.getElementById('category');
    if (!categorySelect) return;
    
    const selectedCategory = categorySelect.value;
    if (!selectedCategory) return;
    
    // Category-specific tooltips
    const categoryTooltips = {
        'emergency_fund': {
            'target_amount': 'Typically calculated as 3-6 months of your essential expenses. This provides a financial buffer for unexpected events.',
            'timeframe': 'Emergency funds should ideally be built within 6-12 months, depending on your saving capacity.'
        },
        'traditional_retirement': {
            'target_amount': 'Calculated based on your expected annual expenses in retirement multiplied by 25-30 (depending on withdrawal rate).',
            'timeframe': 'Your expected retirement date. Traditional retirement typically occurs between ages 60-65.'
        },
        'early_retirement': {
            'target_amount': 'Early retirement requires a larger corpus, typically 28-33 times your annual expenses due to longer retirement period.',
            'timeframe': 'Your target date for achieving financial independence, typically before age 55.'
        },
        'education': {
            'target_amount': 'Total education cost calculated as annual cost × number of years, adjusted for education inflation.',
            'timeframe': 'The date when the education program will begin.'
        },
        'home_purchase': {
            'target_amount': 'Typically 20% of the property value for a down payment, plus closing costs (2-5% of loan amount).',
            'timeframe': 'Your target date for purchasing the property.'
        }
    };
    
    // Update tooltips for common fields based on category
    if (categoryTooltips[selectedCategory]) {
        Object.entries(categoryTooltips[selectedCategory]).forEach(([field, text]) => {
            const element = document.getElementById(field);
            if (element) {
                element.setAttribute('data-tooltip', text);
                element.classList.add('tooltip-initialized');
            }
        });
    }
    
    // Re-initialize tooltips
    initializeTooltips();
}

/**
 * Add rich tooltip to an element with title, content and optional icon
 */
function addRichTooltip(element, title, content, iconType = 'info') {
    if (!element) return;
    
    // Make sure element has tooltip container
    if (!element.classList.contains('tooltip-container')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'tooltip-container';
        element.parentNode.insertBefore(wrapper, element);
        wrapper.appendChild(element);
        element = wrapper;
    }
    
    // Create rich tooltip content
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip-content tooltip-top';
    
    // Add title with icon
    const titleElement = document.createElement('div');
    titleElement.className = 'tooltip-title';
    
    const iconElement = document.createElement('span');
    iconElement.className = `tooltip-icon-${iconType}`;
    iconElement.innerHTML = getIconForType(iconType);
    titleElement.appendChild(iconElement);
    
    const titleText = document.createTextNode(title);
    titleElement.appendChild(titleText);
    tooltip.appendChild(titleElement);
    
    // Add content
    const contentElement = document.createElement('div');
    contentElement.textContent = content;
    tooltip.appendChild(contentElement);
    
    // Add tooltip to element
    element.appendChild(tooltip);
}

/**
 * Get icon HTML for a specific tooltip type
 */
function getIconForType(type) {
    switch (type) {
        case 'info':
            return '&#9432;'; // Information icon
        case 'warning':
            return '&#9888;'; // Warning icon
        case 'tip':
            return '&#128161;'; // Light bulb icon
        default:
            return 'i';
    }
}