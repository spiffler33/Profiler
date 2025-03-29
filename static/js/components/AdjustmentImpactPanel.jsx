import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * AdjustmentImpactPanel - Component to display recommended adjustments and their impact
 * 
 * This component shows different adjustment options with their impact on goal success probability.
 * Optimized for Indian financial context with appropriate terminology and content.
 * 
 * Features:
 * - API integration with VisualizationDataService
 * - Real-time updates via DataEventBus
 * - Loading states during data fetching
 * - Error handling with fallback to props data
 */
const AdjustmentImpactPanel = ({
  adjustments: propAdjustments,
  currentProbability: propProbability,
  formatRupees,
  theme,
  goalId,
  onAdjustmentSelect,
  isLoading: initialLoading = false,
  error: initialError = null
}) => {
  // Component state
  const [selectedAdjustment, setSelectedAdjustment] = useState(null);
  
  // API integration state
  const [isLoading, setIsLoading] = useState(initialLoading);
  const [error, setError] = useState(initialError);
  const [adjustments, setAdjustments] = useState(propAdjustments || []);
  const [currentProbability, setCurrentProbability] = useState(propProbability || 0);
  const [dataSource, setDataSource] = useState('props'); // 'props' or 'api'
  
  // Refs for event listeners
  const eventSubscriptions = useRef([]);
  const goalIdRef = useRef(goalId);
  
  // Update goal ID ref when prop changes
  useEffect(() => {
    goalIdRef.current = goalId;
  }, [goalId]);
  
  // Format rupees function with fallback
  const formatRupeeValue = useCallback((value) => {
    if (typeof formatRupees === 'function') {
      return formatRupees(value);
    }
    
    // Fallback implementation if not provided
    if (value === undefined || value === null) return '—';
    
    const formatter = new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    });
    
    return formatter.format(value);
  }, [formatRupees]);
  
  // Fetch adjustments from API
  const fetchAdjustments = useCallback(async () => {
    // Skip if no goal ID or if VisualizationDataService is not available
    if (!goalId || typeof window.VisualizationDataService === 'undefined') {
      return;
    }
    
    // Set loading state
    setIsLoading(true);
    setError(null);
    
    try {
      // Use the service to fetch adjustments
      const result = await window.VisualizationDataService.fetchAdjustments(goalId, {
        onLoadingChange: (loading) => setIsLoading(loading)
      });
      
      // Check if we have valid adjustment data
      if (result && Array.isArray(result.adjustments)) {
        setAdjustments(result.adjustments);
        setDataSource('api');
        
        // Also update probability if provided
        if (typeof result.currentProbability === 'number') {
          setCurrentProbability(result.currentProbability);
        }
      } else {
        console.warn('API response does not contain valid adjustments', result);
        // Fall back to props data
        setDataSource('props');
      }
    } catch (err) {
      console.error('Error fetching adjustments:', err);
      setError(err);
      // Fall back to props data
      setDataSource('props');
    } finally {
      setIsLoading(false);
    }
  }, [goalId]);
  
  // Connect to data events
  useEffect(() => {
    // Skip if DataEventBus is not available
    if (typeof window.DataEventBus === 'undefined') {
      return;
    }
    
    // Subscribe to probability updates
    const probabilitySubscription = window.DataEventBus.subscribe(
      'probability-updated',
      (data) => {
        // Ignore if not for this goal
        if (data.goalId !== goalIdRef.current) return;
        
        // Update probability and adjustments
        if (typeof data.probability === 'number') {
          setCurrentProbability(data.probability);
        }
        
        if (Array.isArray(data.adjustments)) {
          setAdjustments(data.adjustments);
        }
      }
    );
    
    // Store subscription for cleanup
    eventSubscriptions.current.push(probabilitySubscription);
    
    // Cleanup function to unsubscribe
    return () => {
      eventSubscriptions.current.forEach(unsubscribe => {
        if (typeof unsubscribe === 'function') {
          unsubscribe();
        }
      });
      eventSubscriptions.current = [];
    };
  }, []);
  
  // Initially fetch data from API if available
  useEffect(() => {
    if (goalId && window.VisualizationDataService) {
      fetchAdjustments();
    }
  }, [fetchAdjustments, goalId]);
  
  // Handle selection of adjustment - notify parent component
  const handleAdjustmentClick = useCallback((adjustment) => {
    // Toggle selection if same adjustment is clicked
    const newSelection = selectedAdjustment === adjustment ? null : adjustment;
    setSelectedAdjustment(newSelection);
    
    // Call onAdjustmentSelect if provided
    if (onAdjustmentSelect && newSelection) {
      onAdjustmentSelect(newSelection);
    }
    
    // Publish event via DataEventBus if available
    if (window.DataEventBus && goalIdRef.current && newSelection) {
      window.DataEventBus.publish('adjustment-selected', {
        source: 'adjustment-panel',
        goalId: goalIdRef.current,
        adjustment: newSelection
      });
    }
  }, [selectedAdjustment, onAdjustmentSelect]);

  // Group adjustments by type
  const adjustmentsByType = adjustments.reduce((acc, adjustment) => {
    const type = adjustment.type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(adjustment);
    return acc;
  }, {});

  // Define user-friendly type labels
  const typeLabels = {
    'contribution': 'SIP Amount',
    'allocation': 'Asset Allocation',
    'target': 'Target Amount',
    'timeframe': 'Timeline',
    'tax': 'Tax Optimization',
    'other': 'Other Adjustments'
  };

  // Get adjustment types in order of impact
  const sortedTypes = Object.keys(adjustmentsByType).sort((a, b) => {
    const maxImpactA = Math.max(...adjustmentsByType[a].map(adj => adj.impact || 0));
    const maxImpactB = Math.max(...adjustmentsByType[b].map(adj => adj.impact || 0));
    return maxImpactB - maxImpactA;
  });

  // Function to render impact gauge
  const renderImpactGauge = (impact) => {
    const percentage = impact * 100;
    const newProbability = Math.min(1, Math.max(0, currentProbability + impact));
    
    // Determine gauge color based on impact
    let gaugeColor;
    if (percentage >= 15) gaugeColor = theme?.success || 'green';
    else if (percentage >= 5) gaugeColor = theme?.secondary || 'amber';
    else gaugeColor = theme?.neutral || 'gray';
    
    // Determine text color based on new probability
    let textColor;
    if (newProbability >= 0.7) textColor = 'text-green-600';
    else if (newProbability >= 0.5) textColor = 'text-amber-600';
    else textColor = 'text-red-600';
    
    return (
      <div className="flex items-center">
        <div className="w-24 bg-gray-200 rounded-full h-2.5 mr-2">
          <div 
            className={`h-2.5 rounded-full bg-${gaugeColor}-500`} 
            style={{ width: `${Math.min(100, percentage * 3)}%` }} // Scale for visual impact
          ></div>
        </div>
        <span className={`text-sm ${textColor} font-medium`}>
          +{percentage.toFixed(0)}% → {(newProbability * 100).toFixed(0)}%
        </span>
      </div>
    );
  };

  // Render adjustment details when selected
  const renderAdjustmentDetails = (adjustment) => {
    if (!adjustment) return null;
    
    return (
      <div className="mt-4 bg-white p-4 rounded-lg border border-gray-200">
        <h4 className="font-medium text-gray-800 mb-2">{adjustment.description}</h4>
        
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <p className="text-gray-500 text-xs">Probability Impact</p>
            <p className="font-medium text-green-600">+{(adjustment.impact * 100).toFixed(0)}%</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs">New Probability</p>
            <p className={`font-medium ${
              currentProbability + adjustment.impact >= 0.7 ? 'text-green-600' : 
              currentProbability + adjustment.impact >= 0.5 ? 'text-amber-600' : 'text-red-600'
            }`}>
              {((currentProbability + adjustment.impact) * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        
        {/* Type-specific details */}
        {adjustment.type === 'contribution' && (
          <div className="mt-2">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Monthly SIP: </span>
              {formatRupeeValue(adjustment.value)} 
              {adjustment.previousValue && ` (from ${formatRupeeValue(adjustment.previousValue)})`}
            </p>
            {adjustment.yearlyImpact && (
              <p className="text-sm text-gray-600 mt-1">
                <span className="font-medium">Yearly Impact: </span>
                {formatRupeeValue(adjustment.yearlyImpact)}
              </p>
            )}
          </div>
        )}
        
        {adjustment.type === 'allocation' && (
          <div className="mt-2">
            <p className="text-sm text-gray-600 font-medium">Recommended Allocation:</p>
            <div className="flex space-x-2 mt-1">
              {adjustment.value && Object.entries(adjustment.value).map(([asset, percentage]) => (
                <div key={asset} className="px-2 py-1 bg-gray-100 rounded text-xs">
                  {asset}: {(percentage * 100).toFixed(0)}%
                </div>
              ))}
            </div>
          </div>
        )}
        
        {adjustment.type === 'timeframe' && (
          <div className="mt-2">
            <p className="text-sm text-gray-600">
              <span className="font-medium">New Timeline: </span>
              {adjustment.value} years
              {adjustment.previousValue && ` (from ${adjustment.previousValue} years)`}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              <span className="font-medium">Extension: </span>
              {adjustment.value - (adjustment.previousValue || 0)} years
            </p>
          </div>
        )}
        
        {adjustment.type === 'target' && (
          <div className="mt-2">
            <p className="text-sm text-gray-600">
              <span className="font-medium">New Target: </span>
              {formatRupeeValue(adjustment.value)}
              {adjustment.previousValue && ` (from ${formatRupeeValue(adjustment.previousValue)})`}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              <span className="font-medium">Reduction: </span>
              {formatRupeeValue(adjustment.previousValue - adjustment.value)}
              {adjustment.previousValue && ` (${(((adjustment.previousValue - adjustment.value) / adjustment.previousValue) * 100).toFixed(0)}%)`}
            </p>
          </div>
        )}
        
        {adjustment.type === 'tax' && (
          <div className="mt-2">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Tax Savings: </span>
              {formatRupeeValue(adjustment.taxSavings || 0)} per year
            </p>
            {adjustment.section && (
              <p className="text-sm text-gray-600 mt-1">
                <span className="font-medium">Under Section: </span>
                {adjustment.section}
              </p>
            )}
          </div>
        )}
        
        {/* Notes specific to Indian context */}
        {adjustment.indiaSpecificNotes && (
          <div className="mt-3 bg-blue-50 p-2 rounded text-sm text-blue-800">
            <p className="font-medium">Note:</p>
            <p>{adjustment.indiaSpecificNotes}</p>
          </div>
        )}
      </div>
    );
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <div className="w-12 h-12 rounded-full border-4 border-t-4 border-gray-200 border-t-green-500 animate-spin"></div>
        <p className="mt-4 text-gray-600">Loading adjustment recommendations...</p>
      </div>
    );
  }
  
  // Show error state
  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded shadow">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading adjustments</h3>
            <div className="mt-2 text-xs text-red-700">
              <p>{error.message || "Failed to load adjustment recommendations"}</p>
              <button 
                className="mt-2 bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
                onClick={fetchAdjustments}
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // If no adjustments, show a message
  if (!adjustments || adjustments.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        <p>No adjustment recommendations available.</p>
        <p className="text-sm mt-1">Complete your financial profile for personalized recommendations.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Current probability indicator */}
      <div className="mb-4 flex items-center">
        <span className="text-gray-600 text-sm mr-2">Current Success Probability:</span>
        <span className={`font-medium ${
          currentProbability >= 0.7 ? 'text-green-600' : 
          currentProbability >= 0.5 ? 'text-amber-600' : 'text-red-600'
        }`}>
          {(currentProbability * 100).toFixed(0)}%
        </span>
        
        {/* Data source indicator (useful during development) */}
        {process.env.NODE_ENV === 'development' && (
          <span className="ml-2 text-xs text-gray-400">
            ({dataSource === 'api' ? 'API' : 'Props'})
          </span>
        )}
      </div>
      
      {/* Adjustment recommendations by type */}
      <div className="space-y-4">
        {sortedTypes.map(type => (
          <div key={type} className="bg-gray-50 p-3 rounded">
            <h4 className="font-medium text-gray-700 mb-2">{typeLabels[type] || type}</h4>
            
            {/* List the adjustments for this type */}
            <div className="space-y-2">
              {adjustmentsByType[type].map((adjustment, index) => (
                <div 
                  key={index}
                  className={`p-2 rounded cursor-pointer transition-colors ${
                    selectedAdjustment === adjustment ? 'bg-green-50 border border-green-200' : 'bg-white border border-gray-200 hover:border-green-200'
                  }`}
                  onClick={() => handleAdjustmentClick(adjustment)}
                >
                  <div className="flex justify-between items-center">
                    <p className="text-sm text-gray-700 truncate max-w-[60%]">{adjustment.description}</p>
                    {renderImpactGauge(adjustment.impact || 0)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {/* Selected adjustment details */}
      {renderAdjustmentDetails(selectedAdjustment)}
      
      {/* Disclaimer for Indian context */}
      <div className="mt-5 text-xs text-gray-500">
        <p>
          <strong>Note:</strong> Recommendations may include tax benefits under applicable sections of the 
          Income Tax Act. Consult a tax advisor for personalized advice.
        </p>
      </div>
    </div>
  );
};

// Define prop types
AdjustmentImpactPanel.propTypes = {
  // Data props
  adjustments: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      description: PropTypes.string,
      impact: PropTypes.number,
      value: PropTypes.oneOfType([
        PropTypes.number, 
        PropTypes.string,
        PropTypes.object
      ]),
      previousValue: PropTypes.oneOfType([
        PropTypes.number, 
        PropTypes.string
      ]),
      yearlyImpact: PropTypes.number,
      taxSavings: PropTypes.number,
      section: PropTypes.string,
      indiaSpecificNotes: PropTypes.string
    })
  ),
  currentProbability: PropTypes.number,
  
  // API integration props
  goalId: PropTypes.string,
  isLoading: PropTypes.bool,
  error: PropTypes.object,
  
  // Callback props
  onAdjustmentSelect: PropTypes.func,
  
  // Formatting and styling props
  formatRupees: PropTypes.func,
  theme: PropTypes.object
};

// Set default props for backward compatibility
AdjustmentImpactPanel.defaultProps = {
  adjustments: [],
  currentProbability: 0,
  isLoading: false,
  error: null
};

export default AdjustmentImpactPanel;