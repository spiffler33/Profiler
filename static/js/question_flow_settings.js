/**
 * JavaScript module for controlling question flow indicator display settings.
 * 
 * This module manages user preferences for how dynamic question indicators
 * and related information are displayed in the question flow. It handles
 * saving preferences to localStorage and applying them to the UI.
 */

const QuestionFlowSettings = (function() {
  // Default settings
  const defaultSettings = {
    showDynamicIndicators: true,
    showDataSources: true,
    showReasoning: true,
    showDetailedContextPanel: true,
    compactMode: false,
    animationEnabled: true
  };
  
  // Storage key for localStorage
  const STORAGE_KEY = 'financialProfiler_questionFlowSettings';
  
  // Current settings (initialized from localStorage or defaults)
  let currentSettings = loadSettings();
  
  /**
   * Initialize the question flow settings module
   * This attaches event handlers and applies initial settings
   */
  function init() {
    // Apply current settings on page load
    applySettings();
    
    // Initialize settings panel if it exists
    initSettingsPanel();
    
    // Listen for dynamically added content
    observeNewContent();
  }
  
  /**
   * Load settings from localStorage, falling back to defaults
   * @returns {Object} The loaded settings
   */
  function loadSettings() {
    try {
      const storedSettings = localStorage.getItem(STORAGE_KEY);
      if (storedSettings) {
        // Merge stored settings with defaults (so new settings are added)
        return { ...defaultSettings, ...JSON.parse(storedSettings) };
      }
    } catch (error) {
      console.error('Error loading question flow settings:', error);
    }
    
    // Return defaults if nothing in storage or on error
    return { ...defaultSettings };
  }
  
  /**
   * Save current settings to localStorage
   */
  function saveSettings() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(currentSettings));
    } catch (error) {
      console.error('Error saving question flow settings:', error);
    }
  }
  
  /**
   * Apply current settings to the UI
   */
  function applySettings() {
    // Add a body class reflecting compact mode setting
    document.body.classList.toggle('compact-questions', currentSettings.compactMode);
    
    // Apply show/hide settings for dynamic indicators
    if (!currentSettings.showDynamicIndicators) {
      document.querySelectorAll('.dynamic-question-indicator').forEach(el => {
        el.classList.add('hidden');
      });
      document.querySelectorAll('.dynamic-mini-badge').forEach(el => {
        el.classList.add('hidden');
      });
    } else {
      document.querySelectorAll('.dynamic-question-indicator').forEach(el => {
        el.classList.remove('hidden');
      });
      document.querySelectorAll('.dynamic-mini-badge').forEach(el => {
        el.classList.remove('hidden');
      });
    }
    
    // Apply data sources visibility setting
    document.querySelectorAll('.data-sources').forEach(el => {
      el.classList.toggle('hidden', !currentSettings.showDataSources);
    });
    
    // Apply reasoning visibility setting
    document.querySelectorAll('.generation-reasoning').forEach(el => {
      el.classList.toggle('hidden', !currentSettings.showReasoning);
    });
    
    // Apply detailed context panel setting
    if (!currentSettings.showDetailedContextPanel) {
      document.querySelectorAll('.context-panel-toggle').forEach(el => {
        el.classList.add('hidden');
      });
    } else {
      document.querySelectorAll('.context-panel-toggle').forEach(el => {
        el.classList.remove('hidden');
      });
    }
    
    // Apply animation setting to question transitions
    const questionCard = document.querySelector('.current-question-card');
    if (questionCard) {
      questionCard.style.animation = currentSettings.animationEnabled ? 'slide-in 0.3s ease-out' : 'none';
    }
  }
  
  /**
   * Initialize the settings panel UI
   */
  function initSettingsPanel() {
    // Check if settings panel exists
    const settingsPanel = document.getElementById('question-flow-settings-panel');
    if (!settingsPanel) {
      createSettingsPanel();
      return;
    }
    
    // Update toggle states based on current settings
    updateSettingsPanelToggles();
    
    // Add event listeners to toggles
    attachSettingsPanelEvents();
  }
  
  /**
   * Create and insert settings panel into the DOM
   */
  function createSettingsPanel() {
    // Check if we're on the questions page
    if (!document.querySelector('.questions-container')) {
      return;
    }
    
    // Create settings panel HTML
    const panelHTML = `
      <div id="question-flow-settings-panel" class="settings-panel">
        <div class="settings-header">
          <h4>Display Settings</h4>
          <button type="button" class="settings-close">&times;</button>
        </div>
        <div class="settings-body">
          <div class="setting-item">
            <label class="setting-label">
              <span>Show Dynamic Indicators</span>
              <div class="toggle-switch">
                <input type="checkbox" id="setting-dynamic-indicators" ${currentSettings.showDynamicIndicators ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </div>
            </label>
            <p class="setting-description">Show badges for dynamically generated questions</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <span>Show Data Sources</span>
              <div class="toggle-switch">
                <input type="checkbox" id="setting-data-sources" ${currentSettings.showDataSources ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </div>
            </label>
            <p class="setting-description">Show which data was used to generate questions</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <span>Show Reasoning</span>
              <div class="toggle-switch">
                <input type="checkbox" id="setting-reasoning" ${currentSettings.showReasoning ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </div>
            </label>
            <p class="setting-description">Show reasoning for dynamically generated questions</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <span>Enable Context Panels</span>
              <div class="toggle-switch">
                <input type="checkbox" id="setting-context-panel" ${currentSettings.showDetailedContextPanel ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </div>
            </label>
            <p class="setting-description">Allow viewing detailed context for questions</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <span>Compact Mode</span>
              <div class="toggle-switch">
                <input type="checkbox" id="setting-compact-mode" ${currentSettings.compactMode ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </div>
            </label>
            <p class="setting-description">Use more compact layout for questions</p>
          </div>
          
          <div class="setting-item">
            <label class="setting-label">
              <span>Enable Animations</span>
              <div class="toggle-switch">
                <input type="checkbox" id="setting-animations" ${currentSettings.animationEnabled ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </div>
            </label>
            <p class="setting-description">Show transition animations between questions</p>
          </div>
        </div>
        <div class="settings-footer">
          <button type="button" class="btn secondary reset-settings-btn">Reset to Defaults</button>
        </div>
      </div>
      
      <button type="button" id="settings-toggle-btn" class="settings-toggle-btn">
        <i class="fa fa-cog"></i>
      </button>
    `;
    
    // Create a container for the panel
    const container = document.createElement('div');
    container.className = 'question-flow-settings-container';
    container.innerHTML = panelHTML;
    
    // Add to document
    document.body.appendChild(container);
    
    // Add panel styling if not already present
    if (!document.getElementById('question-flow-settings-style')) {
      addSettingsPanelStyles();
    }
    
    // Initialize event listeners
    attachSettingsPanelEvents();
  }
  
  /**
   * Add CSS styles for the settings panel
   */
  function addSettingsPanelStyles() {
    const styleTag = document.createElement('style');
    styleTag.id = 'question-flow-settings-style';
    styleTag.textContent = `
      /* Settings panel container */
      .question-flow-settings-container {
        position: relative;
        z-index: 1000;
      }
      
      /* Settings toggle button */
      .settings-toggle-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #0d6efd;
        color: white;
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        transition: transform 0.3s, background-color 0.3s;
        z-index: 1001;
      }
      
      .settings-toggle-btn:hover {
        background-color: #0b5ed7;
        transform: scale(1.05);
      }
      
      /* Settings panel */
      .settings-panel {
        position: fixed;
        bottom: 80px;
        right: 20px;
        width: 320px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        z-index: 1000;
        transition: transform 0.3s, opacity 0.3s;
        transform: translateY(20px);
        opacity: 0;
        pointer-events: none;
        overflow: hidden;
        max-height: calc(100vh - 100px);
        display: flex;
        flex-direction: column;
      }
      
      .settings-panel.active {
        transform: translateY(0);
        opacity: 1;
        pointer-events: all;
      }
      
      /* Settings header */
      .settings-header {
        padding: 12px 15px;
        border-bottom: 1px solid #e9ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .settings-header h4 {
        margin: 0;
        font-size: 16px;
        color: #333;
      }
      
      .settings-close {
        background: transparent;
        border: none;
        font-size: 22px;
        line-height: 1;
        color: #6c757d;
        cursor: pointer;
      }
      
      /* Settings body */
      .settings-body {
        padding: 15px;
        overflow-y: auto;
      }
      
      /* Setting item */
      .setting-item {
        margin-bottom: 15px;
        padding-bottom: 15px;
        border-bottom: 1px solid #f0f0f0;
      }
      
      .setting-item:last-child {
        margin-bottom: 0;
        padding-bottom: 0;
        border-bottom: none;
      }
      
      .setting-label {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
        cursor: pointer;
      }
      
      .setting-description {
        font-size: 12px;
        color: #6c757d;
        margin: 5px 0 0 0;
      }
      
      /* Toggle switch */
      .toggle-switch {
        position: relative;
        display: inline-block;
        width: 44px;
        height: 24px;
      }
      
      .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
      }
      
      .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .3s;
        border-radius: 24px;
      }
      
      .toggle-slider:before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        transition: .3s;
        border-radius: 50%;
      }
      
      input:checked + .toggle-slider {
        background-color: #0d6efd;
      }
      
      input:checked + .toggle-slider:before {
        transform: translateX(20px);
      }
      
      /* Settings footer */
      .settings-footer {
        padding: 10px 15px;
        background-color: #f8f9fa;
        border-top: 1px solid #e9ecef;
        text-align: right;
      }
      
      .reset-settings-btn {
        font-size: 14px;
        padding: 6px 12px;
      }
      
      /* Compact mode styles */
      body.compact-questions .question-text {
        font-size: 1.1rem;
        margin-bottom: 0.75rem;
      }
      
      body.compact-questions .input-container {
        margin-bottom: 1rem;
      }
      
      body.compact-questions .help-text {
        padding: 0.5rem 0.75rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
      }
      
      body.compact-questions .question-type-badge,
      body.compact-questions .cat-badge {
        padding: 0.1rem 0.3rem;
        font-size: 0.7rem;
      }
      
      body.compact-questions .form-actions {
        margin-top: 0.75rem;
      }
      
      /* Mobile adjustments */
      @media (max-width: 768px) {
        .settings-panel {
          width: calc(100% - 40px);
          max-width: 320px;
          max-height: 80vh;
        }
      }
    `;
    
    document.head.appendChild(styleTag);
  }
  
  /**
   * Attach event listeners to the settings panel elements
   */
  function attachSettingsPanelEvents() {
    // Toggle button event
    const toggleBtn = document.getElementById('settings-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', function() {
        const panel = document.getElementById('question-flow-settings-panel');
        if (panel) {
          panel.classList.toggle('active');
        }
      });
    }
    
    // Close button event
    const closeBtn = document.querySelector('.settings-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        const panel = document.getElementById('question-flow-settings-panel');
        if (panel) {
          panel.classList.remove('active');
        }
      });
    }
    
    // Click outside to close
    document.addEventListener('click', function(event) {
      const panel = document.getElementById('question-flow-settings-panel');
      const toggleBtn = document.getElementById('settings-toggle-btn');
      
      if (panel && panel.classList.contains('active') && 
          !panel.contains(event.target) && 
          toggleBtn !== event.target && 
          !toggleBtn.contains(event.target)) {
        panel.classList.remove('active');
      }
    });
    
    // Setting toggle events
    document.getElementById('setting-dynamic-indicators')?.addEventListener('change', function() {
      currentSettings.showDynamicIndicators = this.checked;
      saveSettings();
      applySettings();
    });
    
    document.getElementById('setting-data-sources')?.addEventListener('change', function() {
      currentSettings.showDataSources = this.checked;
      saveSettings();
      applySettings();
    });
    
    document.getElementById('setting-reasoning')?.addEventListener('change', function() {
      currentSettings.showReasoning = this.checked;
      saveSettings();
      applySettings();
    });
    
    document.getElementById('setting-context-panel')?.addEventListener('change', function() {
      currentSettings.showDetailedContextPanel = this.checked;
      saveSettings();
      applySettings();
    });
    
    document.getElementById('setting-compact-mode')?.addEventListener('change', function() {
      currentSettings.compactMode = this.checked;
      saveSettings();
      applySettings();
    });
    
    document.getElementById('setting-animations')?.addEventListener('change', function() {
      currentSettings.animationEnabled = this.checked;
      saveSettings();
      applySettings();
    });
    
    // Reset button event
    const resetBtn = document.querySelector('.reset-settings-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', resetToDefaults);
    }
  }
  
  /**
   * Update the toggle states in the settings panel to reflect current settings
   */
  function updateSettingsPanelToggles() {
    document.getElementById('setting-dynamic-indicators')?.checked = currentSettings.showDynamicIndicators;
    document.getElementById('setting-data-sources')?.checked = currentSettings.showDataSources;
    document.getElementById('setting-reasoning')?.checked = currentSettings.showReasoning;
    document.getElementById('setting-context-panel')?.checked = currentSettings.showDetailedContextPanel;
    document.getElementById('setting-compact-mode')?.checked = currentSettings.compactMode;
    document.getElementById('setting-animations')?.checked = currentSettings.animationEnabled;
  }
  
  /**
   * Reset all settings to default values
   */
  function resetToDefaults() {
    currentSettings = { ...defaultSettings };
    saveSettings();
    updateSettingsPanelToggles();
    applySettings();
  }
  
  /**
   * Updates settings for a specific option
   * @param {string} settingName - The name of the setting to update
   * @param {*} value - The new value for the setting
   */
  function updateSetting(settingName, value) {
    if (settingName in currentSettings) {
      currentSettings[settingName] = value;
      saveSettings();
      applySettings();
      updateSettingsPanelToggles();
      return true;
    }
    return false;
  }
  
  /**
   * Observe DOM for dynamically added content to apply settings to
   */
  function observeNewContent() {
    // Create MutationObserver to watch for new dynamic question indicators
    const observer = new MutationObserver(function(mutations) {
      let needsUpdate = false;
      
      mutations.forEach(function(mutation) {
        if (mutation.addedNodes && mutation.addedNodes.length > 0) {
          for (let node of mutation.addedNodes) {
            if (node.nodeType === Node.ELEMENT_NODE) {
              if (node.classList?.contains('dynamic-question-indicator') || 
                  node.classList?.contains('dynamic-mini-badge') ||
                  node.querySelector('.dynamic-question-indicator, .dynamic-mini-badge')) {
                needsUpdate = true;
                break;
              }
            }
          }
        }
      });
      
      if (needsUpdate) {
        applySettings();
      }
    });
    
    // Start observing
    observer.observe(document.body, { 
      childList: true, 
      subtree: true 
    });
  }
  
  // Public API
  return {
    init,
    updateSetting,
    resetToDefaults,
    getSettings: () => ({ ...currentSettings })
  };
})();

// Initialize the module when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  QuestionFlowSettings.init();
});