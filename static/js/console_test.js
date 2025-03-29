/**
 * Console Test Script
 * This script logs to the console to verify JavaScript loading
 */

console.log('JavaScript is loading correctly!');
console.log('LoadingStateManager exists:', typeof window.LoadingStateManager !== 'undefined');
console.log('GoalFormProbability exists:', typeof window.GoalFormProbability !== 'undefined');

// Check if elements exist
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    console.log('Document contains test-results element:', document.getElementById('test-results') !== null);
    console.log('Document contains api-test-results element:', document.getElementById('api-test-results') !== null);
});