import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ReferenceLine
} from 'recharts';

/**
 * ScenarioComparisonChart - Component to compare different financial scenarios
 * 
 * This component displays a bar chart comparing the current scenario with optimized alternatives.
 * 
 * Features:
 * - API integration with VisualizationDataService
 * - Real-time updates via DataEventBus
 * - Loading states during data fetching
 * - Error handling with fallback to props data
 */
const ScenarioComparisonChart = ({
  currentScenario: propCurrentScenario,
  optimizedScenario: propOptimizedScenario,
  selectedScenario: propSelectedScenario = 'current',
  targetAmount: propTargetAmount,
  formatRupees,
  theme,
  goalId,
  isLoading: initialLoading = false,
  error: initialError = null
}) => {
  // Component state
  const [selectedScenario, setSelectedScenario] = useState(propSelectedScenario);
  
  // API integration state
  const [isLoading, setIsLoading] = useState(initialLoading);
  const [error, setError] = useState(initialError);
  const [currentScenario, setCurrentScenario] = useState(propCurrentScenario);
  const [optimizedScenario, setOptimizedScenario] = useState(propOptimizedScenario);
  const [targetAmount, setTargetAmount] = useState(propTargetAmount);
  const [dataSource, setDataSource] = useState('props'); // 'props' or 'api'
  
  // Refs for event listeners
  const eventSubscriptions = useRef([]);
  const goalIdRef = useRef(goalId);
  
  // Update goal ID ref when prop changes
  useEffect(() => {
    goalIdRef.current = goalId;
  }, [goalId]);
  
  // Handle scenario selection change
  useEffect(() => {
    setSelectedScenario(propSelectedScenario);
  }, [propSelectedScenario]);
  
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
  
  // Fetch scenarios from API
  const fetchScenarios = useCallback(async () => {
    // Skip if no goal ID or if VisualizationDataService is not available
    if (!goalId || typeof window.VisualizationDataService === 'undefined') {
      return;
    }
    
    // Set loading state
    setIsLoading(true);
    setError(null);
    
    try {
      // Use the service to fetch visualization data which includes scenarios
      const result = await window.VisualizationDataService.fetchVisualizationData(goalId, {
        onLoadingChange: (loading) => setIsLoading(loading)
      });
      
      // Check if we have valid scenario data
      if (result && result.scenarioComparisonData && result.scenarioComparisonData.scenarios) {
        const scenarios = result.scenarioComparisonData.scenarios;
        
        // Find current and optimized scenarios
        const current = scenarios.find(s => s.isBaseline) || scenarios[0];
        const optimized = scenarios.find(s => !s.isBaseline) || null;
        
        // Update state with fetched data
        setCurrentScenario(current);
        setOptimizedScenario(optimized);
        setDataSource('api');
        
        // Set target amount if available
        if (result.probabilisticGoalData && result.probabilisticGoalData.targetAmount) {
          setTargetAmount(result.probabilisticGoalData.targetAmount);
        }
      } else {
        console.warn('API response does not contain valid scenario data', result);
        // Fall back to props data
        setDataSource('props');
      }
    } catch (err) {
      console.error('Error fetching scenarios:', err);
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
        
        // Refresh scenarios if probability has changed
        fetchScenarios();
      }
    );
    
    // Store subscription for cleanup
    eventSubscriptions.current.push(probabilitySubscription);
    
    // Subscribe to scenario selection changes
    const scenarioSubscription = window.DataEventBus.subscribe(
      'scenario-selected',
      (data) => {
        // Ignore if not for this goal
        if (data.goalId !== goalIdRef.current) return;
        
        // Update selected scenario
        if (data.scenario && (data.scenario === 'current' || data.scenario === 'optimized')) {
          setSelectedScenario(data.scenario);
        }
      }
    );
    
    // Store subscription for cleanup
    eventSubscriptions.current.push(scenarioSubscription);
    
    // Cleanup function to unsubscribe
    return () => {
      eventSubscriptions.current.forEach(unsubscribe => {
        if (typeof unsubscribe === 'function') {
          unsubscribe();
        }
      });
      eventSubscriptions.current = [];
    };
  }, [fetchScenarios]);
  
  // Initially fetch data from API if available
  useEffect(() => {
    if (goalId && window.VisualizationDataService) {
      fetchScenarios();
    }
  }, [fetchScenarios, goalId]);
  
  // Handle scenario selection change - publish event
  const handleScenarioChange = useCallback((scenario) => {
    setSelectedScenario(scenario);
    
    // Publish event via DataEventBus if available
    if (window.DataEventBus && goalIdRef.current) {
      window.DataEventBus.publish('scenario-selected', {
        source: 'scenario-chart',
        goalId: goalIdRef.current,
        scenario: scenario
      });
    }
  }, []);
  
  // Prepare data for the selected scenario
  const scenarioData = selectedScenario === 'current' ? currentScenario : optimizedScenario;
  
  // Show loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-8">
        <div className="w-12 h-12 rounded-full border-4 border-t-4 border-gray-200 border-t-green-500 animate-spin"></div>
        <p className="mt-4 text-gray-600">Loading scenario comparison data...</p>
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
            <h3 className="text-sm font-medium text-red-800">Error loading scenarios</h3>
            <div className="mt-2 text-xs text-red-700">
              <p>{error.message || "Failed to load scenario comparison data"}</p>
              <button 
                className="mt-2 bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
                onClick={fetchScenarios}
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // If no scenario data is available
  if (!scenarioData) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>The selected scenario is not available.</p>
        {goalId && window.VisualizationDataService && (
          <button 
            className="mt-2 bg-gray-100 text-gray-800 px-3 py-1 rounded hover:bg-gray-200"
            onClick={fetchScenarios}
          >
            Fetch Scenarios
          </button>
        )}
      </div>
    );
  }
  
  // Prepare metrics for display
  const successProbability = scenarioData.successProbability || 0;
  const expectedValue = scenarioData.expectedValue || 0;
  const timeToAchievement = scenarioData.timeToAchievement || null;
  const monthlyContribution = scenarioData.monthlyContribution || 0;
  
  // Prepare chart data
  const chartData = [
    { year: 5, value: scenarioData.projections?.[4]?.median || 0 },
    { year: 10, value: scenarioData.projections?.[9]?.median || 0 },
    { year: 15, value: scenarioData.projections?.[14]?.median || 0 },
    { year: 20, value: scenarioData.projections?.[19]?.median || 0 }
  ].filter(d => d.value > 0); // Filter out years beyond the projection
  
  // Custom tooltip for the chart
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 shadow-lg rounded-md">
          <p className="font-semibold text-gray-800">{`Year ${label}`}</p>
          <p className="text-green-600 font-medium">
            {formatRupeeValue(payload[0]?.value)}
          </p>
          <p className="text-sm text-gray-600 mt-1">
            {payload[0]?.value >= targetAmount 
              ? 'Goal achieved' 
              : `${((payload[0]?.value / targetAmount) * 100).toFixed(0)}% of target`}
          </p>
        </div>
      );
    }
    return null;
  };
  
  return (
    <div>
      {/* Scenario selector buttons */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-800">Scenario Analysis</h3>
        <div className="flex space-x-2">
          <button
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              selectedScenario === 'current' 
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            onClick={() => handleScenarioChange('current')}
          >
            Current
          </button>
          <button
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              selectedScenario === 'optimized' 
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            onClick={() => handleScenarioChange('optimized')}
            disabled={!optimizedScenario}
          >
            Optimized
          </button>
        </div>
      </div>
      
      {/* Data source indicator (useful during development) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mb-2 text-xs text-gray-400 text-right">
          Data source: {dataSource === 'api' ? 'API' : 'Props'}
        </div>
      )}
      
      {/* Scenario summary */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-gray-600 text-xs">Success Probability</p>
          <p className={`text-lg font-semibold ${
            successProbability >= 0.7 ? 'text-green-600' : 
            successProbability >= 0.5 ? 'text-amber-600' : 'text-red-600'
          }`}>
            {(successProbability * 100).toFixed(0)}%
          </p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-gray-600 text-xs">Monthly SIP</p>
          <p className="text-lg font-semibold text-gray-800">
            {formatRupeeValue(monthlyContribution)}
          </p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-gray-600 text-xs">Expected Outcome</p>
          <p className="text-lg font-semibold text-gray-800">
            {formatRupeeValue(expectedValue)}
          </p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-gray-600 text-xs">Achievement Time</p>
          <p className="text-lg font-semibold text-gray-800">
            {timeToAchievement ? `${timeToAchievement} years` : 'Beyond horizon'}
          </p>
        </div>
      </div>
      
      {/* Bar chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" label={{ value: 'Year', position: 'insideBottom', offset: -5 }} />
            <YAxis tickFormatter={(value) => formatRupeeValue(value)} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine 
              y={targetAmount} 
              stroke={theme?.accent || "#FF5722"} 
              strokeDasharray="3 3" 
              label={{ value: 'Target', position: 'right', fill: theme?.accent || "#FF5722" }} 
            />
            <Bar 
              dataKey="value" 
              name="Projected Amount" 
              fill={theme?.primary || "#00A86B"} 
              barSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      {/* Scenario-specific insights */}
      <div className="mt-4 text-sm">
        <h4 className="font-medium text-gray-800 mb-2">Key Insights</h4>
        <ul className="list-disc pl-5 text-gray-600 space-y-1">
          {/* Dynamic insights based on the scenario data */}
          {successProbability >= 0.9 && (
            <li>High confidence scenario with excellent success probability.</li>
          )}
          {successProbability < 0.5 && (
            <li>This scenario has a high risk of not meeting your goal target.</li>
          )}
          {timeToAchievement && targetAmount && (
            <li>
              Goal {timeToAchievement <= 20 ? `achieved in year ${timeToAchievement}` : 'not achieved within 20 years'}.
            </li>
          )}
          {/* SIP-specific insight for Indian context */}
          {monthlyContribution > 0 && (
            <li>
              {`Monthly SIP of ${formatRupeeValue(monthlyContribution)} builds to ${formatRupeeValue(expectedValue)} 
              over ${scenarioData.projections?.length || 20} years.`}
            </li>
          )}
          {/* Tax efficiency insight for Indian context */}
          {selectedScenario === 'optimized' && (
            <li>
              Optimized scenario includes tax-efficient instruments like ELSS for Section 80C benefits.
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

// Define prop types
ScenarioComparisonChart.propTypes = {
  // Data props
  currentScenario: PropTypes.shape({
    successProbability: PropTypes.number,
    expectedValue: PropTypes.number,
    timeToAchievement: PropTypes.number,
    monthlyContribution: PropTypes.number,
    projections: PropTypes.arrayOf(PropTypes.object)
  }),
  optimizedScenario: PropTypes.shape({
    successProbability: PropTypes.number,
    expectedValue: PropTypes.number,
    timeToAchievement: PropTypes.number,
    monthlyContribution: PropTypes.number,
    projections: PropTypes.arrayOf(PropTypes.object)
  }),
  selectedScenario: PropTypes.oneOf(['current', 'optimized']),
  targetAmount: PropTypes.number,
  
  // API integration props
  goalId: PropTypes.string,
  isLoading: PropTypes.bool,
  error: PropTypes.object,
  
  // Formatting and styling props
  formatRupees: PropTypes.func,
  theme: PropTypes.object
};

// Default props for backward compatibility
ScenarioComparisonChart.defaultProps = {
  selectedScenario: 'current',
  isLoading: false,
  error: null
};

export default ScenarioComparisonChart;