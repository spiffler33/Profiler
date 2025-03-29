/**
 * Question Flow Manager Integration
 * 
 * This script integrates the QuestionFlowManager with the existing question
 * flow system in the application. It handles the connection between the
 * API-based question flow and the server-rendered templates.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Check if we're on the questions page
  const questionsContainer = document.querySelector('.questions-container');
  if (!questionsContainer) return;
  
  // Check if ApiService is loaded
  const hasApiService = typeof ApiService !== 'undefined';
  if (!hasApiService) {
    console.warn('ApiService not found. Question Flow API integration will be limited.');
  }
  
  // Extract profile ID
  const profileIdFromUrl = extractProfileIdFromUrl();
  
  // Initialize the question flow manager
  QuestionFlowManager.initialize({
    profileId: profileIdFromUrl,
    containerSelector: '.question-answer-section',
    onQuestionLoad: function(question, progress) {
      console.log('Question loaded:', question.id);
    }
  });
  
  // Listen for form submissions to intercept and handle via API
  const answerForm = document.getElementById('answer-form');
  if (answerForm) {
    // We need to let the existing form handler run for now until the API is fully implemented
    // This is a bridging solution to ensure backward compatibility
    
    // We'll enhance the existing form handling by tracking the submission
    setupEnhancedFormTracking(answerForm);
    
    // Provide backward compatibility
    provideBackwardCompatibility();
  }
  
  // Connect to server-side events for question flow coordination
  setupServerCoordination();
  
  // Set up answer submission tracking for analytics
  setupAnswerTracking();
  
  // Log initialization
  console.log('Question Flow Manager integrated successfully');
});

/**
 * Extract profile ID from the URL
 */
function extractProfileIdFromUrl() {
  // Extract from URL path /profile/:id/questions
  const profileMatch = window.location.pathname.match(/\/profile\/([^\/]+)\/questions/);
  if (profileMatch && profileMatch[1]) {
    return profileMatch[1];
  }
  
  // Extract from query string ?profile_id=...
  const urlParams = new URLSearchParams(window.location.search);
  const profileId = urlParams.get('profile_id');
  
  if (profileId) return profileId;
  
  // Try to find it in the DOM
  const profileIdElement = document.querySelector('[data-profile-id]');
  if (profileIdElement) {
    return profileIdElement.dataset.profileId;
  }
  
  // Fall back to extracting from page content
  const profileInfoText = document.body.textContent;
  const profileIdMatch = profileInfoText.match(/Profile ID:\s*([a-zA-Z0-9-]+)/);
  if (profileIdMatch && profileIdMatch[1]) {
    return profileIdMatch[1];
  }
  
  console.warn('Could not extract profile ID from URL or DOM');
  return null;
}

/**
 * Set up enhanced form tracking to collect analytics
 * while maintaining compatibility with existing form handling
 */
function setupEnhancedFormTracking(form) {
  // Create a copy of the existing submit handler
  const originalSubmitHandler = form.onsubmit;
  
  // Replace with our tracking wrapper
  form.addEventListener('submit', function(event) {
    // Don't prevent default yet, as we're still using the server handling
    // event.preventDefault();
    
    // Extract form data
    const formData = new FormData(form);
    const questionId = formData.get('question_id');
    const inputType = formData.get('input_type');
    const profileId = extractProfileIdFromUrl();
    
    // Process answer data based on input type
    let answer = formData.get('answer');
    
    // Handle multiselect type
    if (inputType === 'multiselect') {
      const checkboxes = form.querySelectorAll('input[type="checkbox"]:checked');
      if (checkboxes.length > 0) {
        answer = Array.from(checkboxes).map(cb => cb.value);
      }
    }
    
    // Track the answer in the QuestionFlowManager
    // This doesn't submit to API yet, just tracks locally
    const answerRecord = {
      questionId,
      answer,
      timestamp: new Date().toISOString()
    };
    QuestionFlowManager.answerHistory.push(answerRecord);
    
    // Save state
    QuestionFlowManager._saveCurrentState();
    
    // Emit tracking event
    QuestionFlowManager._emit('answerTracked', {
      questionId,
      answer,
      inputType
    });
    
    // Also make an API backup call to ensure the answer gets saved
    if (typeof ApiService !== 'undefined' && profileId) {
      try {
        console.log('Making backup API call to save answer:', questionId);
        // Don't await this - let it happen in the background
        ApiService.post('/api/v2/questions/submit', {
          profile_id: profileId,
          question_id: questionId,
          answer: answer
        }, {
          // Don't show errors from this backup call
          showErrorToast: false,
          // Don't redirect on auth errors
          redirectOnAuthError: false,
          // In case of failure, log the error but don't interrupt user
          useErrorService: false
        }).catch(error => {
          console.log('Backup API answer submission had an error, but continuing:', error);
        });
      } catch (e) {
        console.log('Error in backup API submission:', e);
      }
    }
    
    // Allow original handler to continue
    return true;
  });
}

/**
 * Provide backward compatibility with existing question flow system
 */
function provideBackwardCompatibility() {
  // Monitor for form submission via XHR
  const originalFetch = window.fetch;
  window.fetch = function(input, init) {
    // Check if this is a form submission
    if (typeof input === 'string' && input.includes('/submit_answer') && 
        init && init.method === 'POST') {
      
      // Let the server-side handling proceed
      return originalFetch(input, init).then(response => {
        if (response.ok) {
          // If successful, extract the response to notify QuestionFlowManager
          return response.clone().json().then(data => {
            // Notify QuestionFlowManager of the successful submission
            if (data.success) {
              QuestionFlowManager._emit('serverSubmissionSuccess', {
                result: data
              });
            }
            return response;
          }).catch(() => {
            // If we can't parse the JSON, just return the original response
            return response;
          });
        }
        return response;
      });
    }
    
    // Otherwise, proceed with normal fetch
    return originalFetch(input, init);
  };
}

/**
 * Set up coordination with server-side rendering
 */
function setupServerCoordination() {
  // Check for updates to question flow state from server
  if (window.EventSource && false) { // Disabled for now until server has SSE support
    const eventSource = new EventSource('/api/v2/questions/updates?profile_id=' + 
                                      QuestionFlowManager.currentProfileId);
    
    eventSource.addEventListener('question_updated', function(event) {
      const data = JSON.parse(event.data);
      QuestionFlowManager._emit('serverQuestionUpdate', data);
    });
    
    eventSource.addEventListener('error', function() {
      console.warn('EventSource connection error. Falling back to polling.');
      eventSource.close();
    });
  }
  
  // Listen for server-rendered page changes
  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      // Check if current question card was modified
      const questionCard = document.querySelector('.current-question-card');
      if (mutation.target === questionCard || questionCard?.contains(mutation.target)) {
        // Extract question data from DOM
        extractAndUpdateQuestionData(questionCard);
      }
      
      // Check if progress indicators were updated
      const progressSection = document.querySelector('.progress-section');
      if (mutation.target === progressSection || progressSection?.contains(mutation.target)) {
        extractAndUpdateProgressData();
      }
    });
  });
  
  // Start observing
  observer.observe(document.body, { 
    childList: true, 
    subtree: true,
    characterData: true,
    attributes: true 
  });
  
  // Initial extraction of current state
  const currentQuestionCard = document.querySelector('.current-question-card');
  if (currentQuestionCard) {
    extractAndUpdateQuestionData(currentQuestionCard);
  }
  
  extractAndUpdateProgressData();
}

/**
 * Extract and update question data from DOM
 */
function extractAndUpdateQuestionData(questionCard) {
  if (!questionCard) return;
  
  // Extract question data from the DOM
  const questionText = questionCard.querySelector('.question-text')?.textContent?.trim();
  const questionId = questionCard.querySelector('input[name="question_id"]')?.value;
  const inputType = questionCard.querySelector('input[name="input_type"]')?.value;
  
  if (!questionId || !questionText) return;
  
  // Extract category and type
  const categoryBadge = questionCard.querySelector('.cat-badge');
  const typeBadge = questionCard.querySelector('.question-type-badge');
  
  const category = categoryBadge?.textContent?.trim() || 
                   categoryBadge?.className?.match(/cat-badge\s+([^\s]+)/)?.[1];
                   
  const type = typeBadge?.textContent?.trim() ||
               typeBadge?.className?.match(/question-type-badge\s+([^\s]+)/)?.[1];
  
  // Extract help text if present
  const helpText = questionCard.querySelector('.help-text')?.textContent?.trim();
  
  // Create question object
  const questionData = {
    id: questionId,
    text: questionText,
    input_type: inputType,
    category: category,
    type: type
  };
  
  if (helpText) {
    questionData.help_text = helpText;
  }
  
  // Extract options for select, radio, or multiselect
  if (['select', 'radio', 'multiselect'].includes(inputType)) {
    const optionElements = questionCard.querySelectorAll('select option, .radio-option input, .checkbox-option input');
    if (optionElements.length > 0) {
      questionData.options = Array.from(optionElements)
        .filter(el => el.value) // Filter out placeholder option
        .map(el => el.value);
    }
  }
  
  // Update QuestionFlowManager with extracted data
  QuestionFlowManager.currentQuestionData = questionData;
  QuestionFlowManager._saveCurrentState();
  
  // Emit event
  QuestionFlowManager._emit('questionExtracted', { question: questionData });
}

/**
 * Extract and update progress data from DOM
 */
function extractAndUpdateProgressData() {
  // Extract overall progress
  const overallProgressText = document.querySelector('.overall-progress .progress-label')?.textContent;
  let overall = 0;
  if (overallProgressText) {
    const match = overallProgressText.match(/Overall:\s*(\d+)%/);
    if (match && match[1]) {
      overall = parseInt(match[1], 10);
    }
  }
  
  // Extract category progress
  const progressData = { overall };
  
  // Core progress
  const coreProgressText = document.querySelector('.progress-tier:nth-child(1) .progress-label')?.textContent;
  if (coreProgressText) {
    const match = coreProgressText.match(/Core Questions:\s*(\d+)%/);
    if (match && match[1]) {
      progressData.core = {
        overall: parseInt(match[1], 10)
      };
    }
  }
  
  // Next level progress
  const nextLevelProgressText = document.querySelector('.progress-tier:nth-child(2) .progress-label')?.textContent;
  const nextLevelStatsText = document.querySelector('.progress-tier:nth-child(2) .progress-stats')?.textContent;
  
  if (nextLevelProgressText) {
    const match = nextLevelProgressText.match(/Follow-Up Questions:\s*(\d+)%/);
    if (match && match[1]) {
      progressData.next_level = {
        completion: parseInt(match[1], 10)
      };
      
      // Extract counts if available
      if (nextLevelStatsText) {
        const statsMatch = nextLevelStatsText.match(/(\d+)\s+of\s+(\d+)/);
        if (statsMatch && statsMatch[1] && statsMatch[2]) {
          progressData.next_level.questions_answered = parseInt(statsMatch[1], 10);
          progressData.next_level.questions_count = parseInt(statsMatch[2], 10);
        }
      }
    }
  }
  
  // Behavioral progress
  const behavioralProgressText = document.querySelector('.progress-tier:nth-child(3) .progress-label')?.textContent;
  const behavioralStatsText = document.querySelector('.progress-tier:nth-child(3) .progress-stats')?.textContent;
  
  if (behavioralProgressText) {
    const match = behavioralProgressText.match(/Financial Psychology:\s*(\d+)%/);
    if (match && match[1]) {
      progressData.behavioral = {
        completion: parseInt(match[1], 10)
      };
      
      // Extract counts if available
      if (behavioralStatsText) {
        const statsMatch = behavioralStatsText.match(/(\d+)\s+of\s+(\d+)/);
        if (statsMatch && statsMatch[1] && statsMatch[2]) {
          progressData.behavioral.questions_answered = parseInt(statsMatch[1], 10);
          progressData.behavioral.questions_count = parseInt(statsMatch[2], 10);
        }
      }
    }
  }
  
  // Update QuestionFlowManager with extracted progress data
  QuestionFlowManager.progressData = progressData;
  QuestionFlowManager._saveCurrentState();
  
  // Emit event
  QuestionFlowManager._emit('progressExtracted', { progress: progressData });
}

/**
 * Set up answer tracking for analytics
 */
function setupAnswerTracking() {
  // Listen for answer submission events
  QuestionFlowManager.on('answerTracked', function(data) {
    // Send answer tracking to analytics if available
    if (window.AnalyticsService) {
      window.AnalyticsService.trackEvent('question_answered', {
        question_id: data.questionId,
        input_type: data.inputType,
        has_answer: data.answer !== null && data.answer !== undefined,
        timestamp: new Date().toISOString()
      });
    }
  });
}