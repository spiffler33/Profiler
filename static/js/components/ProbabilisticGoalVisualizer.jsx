import React, { useState, useEffect, useMemo, lazy, Suspense } from 'react';
import PropTypes from 'prop-types';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, ReferenceLine, ReferenceArea
} from 'recharts';
import { GaugeChart } from 'react-gauge-chart';

// Lazy load the heavier components
const ScenarioComparisonChart = lazy(() => import('./ScenarioComparisonChart'));
const AdjustmentImpactPanel = lazy(() => import('./AdjustmentImpactPanel'));

/**
 * ProbabilisticGoalVisualizer - Component for visualizing probabilistic goal outcomes
 * 
 * Displays Monte Carlo simulation results for financial goals with Indian context
 * 
 * Features:
 * - API integration with the VisualizationDataService
 * - Real-time updates via DataEventBus
 * - Loading states during data fetching
 * - Error handling with retry capability
 * - Fallback to static data when API unavailable
 */
const ProbabilisticGoalVisualizer = ({
  goalData,
  timeHorizon = 20,
  confidenceIntervals = [25, 50, 75, 90],
  theme = {},
  onScenarioSelect,
  isLoading: initialLoading = false,
  error: initialError = null,
}) => {
  // Component state
  const [selectedScenario, setSelectedScenario] = useState('current');
  const [contributionMultiplier, setContributionMultiplier] = useState(1);
  const [showBenchmarks, setShowBenchmarks] = useState(false);
  const [expandedSection, setExpandedSection] = useState('distribution');
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  
  // API integration state
  const [isLoading, setIsLoading] = useState(initialLoading);
  const [error, setError] = useState(initialError);
  const [apiData, setApiData] = useState(null);
  const [dataSource, setDataSource] = useState('props'); // 'props' or 'api'
  
  // Refs for event listeners
  const eventSubscriptions = useRef([]);
  const goalIdRef = useRef(goalData?.id || null);

  // Define theme with defaults that blend Western charting standards with Indian cultural context
  const defaultTheme = {
    primary: '#00A86B', // Muted green - positive/growth in Indian context
    secondary: '#FFC107', // Amber - attention/caution
    accent: '#FF5722', // Deep orange - important/warning
    neutral: '#6B7280', // Gray - neutral information
    success: '#388E3C', // Dark green - success state
    warning: '#FFA000', // Amber - warning state
    error: '#D32F2F', // Red - error state
    background: '#F9FAFB', // Off-white
    surface: '#FFFFFF', // White
    text: '#111827', // Near-black
    percentile90: 'rgba(0, 168, 107, 0.1)', // Very light green
    percentile75: 'rgba(0, 168, 107, 0.2)', // Light green
    percentile50: 'rgba(0, 168, 107, 0.3)', // Medium green
    percentile25: 'rgba(0, 168, 107, 0.5)', // Darker green
    medianLine: '#00A86B', // Solid green for median
  };

  // Merge provided theme with defaults
  const mergedTheme = { ...defaultTheme, ...theme };

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Fetch data from API when component mounts or goalId changes
  useEffect(() => {
    // Skip if no goal ID or if the window.VisualizationDataService is not available
    if (!goalData?.id || typeof window.VisualizationDataService === 'undefined') {
      return;
    }
    
    // Update ref for event handlers
    goalIdRef.current = goalData.id;
    
    // Set loading state
    setIsLoading(true);
    setError(null);
    
    // Fetch data using the VisualizationDataService
    window.VisualizationDataService.fetchVisualizationData(goalData.id, {
      onLoadingChange: (loading) => {
        setIsLoading(loading);
      }
    })
    .then(response => {
      // Process the data
      if (response && response.probabilisticGoalData) {
        setApiData(response.probabilisticGoalData);
        setDataSource('api');
      } else {
        console.warn('API response does not contain probabilistic goal data', response);
        // Fall back to props data
        setDataSource('props');
      }
    })
    .catch(err => {
      console.error('Error fetching visualization data:', err);
      setError(err);
      // Fall back to props data
      setDataSource('props');
    })
    .finally(() => {
      setIsLoading(false);
    });
  }, [goalData?.id]);
  
  // Subscribe to data events
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
        
        // Update with new probability data
        if (data.simulationData) {
          setApiData(prev => ({
            ...prev,
            successProbability: data.probability,
            simulationData: data.simulationData
          }));
          setDataSource('api');
        }
      }
    );
    
    // Store subscription for cleanup
    eventSubscriptions.current.push(probabilitySubscription);
    
    // Subscribe to parameter changes
    const parameterSubscription = window.DataEventBus.subscribe(
      'parameters-changed',
      (data) => {
        // Ignore if not for this goal
        if (data.goalId !== goalIdRef.current) return;
        
        // No direct action needed here as it will trigger a probability calculation
        // which will then publish a probability-updated event
        console.log('Parameters changed for goal', goalIdRef.current);
      }
    );
    
    // Store subscription for cleanup
    eventSubscriptions.current.push(parameterSubscription);
    
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

  // Format rupee values
  const formatRupees = (value) => {
    if (!value && value !== 0) return '—';
    
    // For values larger than 1 crore (10M), show in crores
    if (Math.abs(value) >= 10000000) {
      return `₹${(value / 10000000).toFixed(2)} Cr`;
    }
    // For values larger than 1 lakh (100K), show in lakhs
    else if (Math.abs(value) >= 100000) {
      return `₹${(value / 100000).toFixed(2)} L`;
    }
    // Otherwise show with thousand separators
    else {
      return `₹${value.toLocaleString('en-IN')}`;
    }
  };

  // Error and loading states
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
            <h3 className="text-sm font-medium text-red-800">Visualization Error</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error.message || "Failed to load goal visualization. Please try again."}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading || !goalData) {
    return (
      <div className="flex justify-center items-center h-64 bg-gray-50 rounded-lg border border-gray-200">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your financial projection...</p>
        </div>
      </div>
    );
  }

  // Helper to get active data based on source
  const getActiveData = useCallback(() => {
    // Use API data if available, otherwise fall back to props data
    return dataSource === 'api' && apiData ? apiData : goalData;
  }, [dataSource, apiData, goalData]);

  // Process data for visualization
  const processedData = useMemo(() => {
    const activeData = getActiveData();
    if (!activeData) return [];

    // Check if we have projection data in the correct format
    const projections = activeData.projections || 
                        activeData.simulationData?.projections || 
                        [];
    
    if (projections.length === 0) return [];

    // Cap the time horizon to provided value or available data
    const effectiveTimeHorizon = Math.min(timeHorizon, projections.length);
    
    // Get projections up to the time horizon
    const limitedProjections = projections.slice(0, effectiveTimeHorizon);

    // Determine start year
    const startYear = activeData.startYear || 
                      new Date().getFullYear();
    
    // Get success probability
    const successProbability = typeof activeData.successProbability === 'number' ? 
                               activeData.successProbability : 
                               (typeof activeData.success_probability === 'number' ? 
                                activeData.success_probability : 0);
    
    return limitedProjections.map((yearData, index) => {
      const year = startYear + index;
      
      // Apply contribution multiplier to adjust the projection
      const adjustedMedian = successProbability < 0.7 
        ? yearData.median * (1 + (contributionMultiplier - 1) * 0.8 * index / effectiveTimeHorizon)
        : yearData.median;
        
      return {
        year,
        median: yearData.median,
        adjustedMedian: adjustedMedian,
        p10: yearData.percentiles?.[10] || 0,
        p25: yearData.percentiles?.[25] || 0,
        p50: yearData.median || 0,
        p75: yearData.percentiles?.[75] || 0,
        p90: yearData.percentiles?.[90] || 0,
        targetAmount: activeData.targetAmount || activeData.target_amount || 0,
      };
    });
  }, [getActiveData, timeHorizon, contributionMultiplier]);

  // Calculate metrics for display
  const metrics = useMemo(() => {
    const activeData = getActiveData();
    if (!activeData) return {};
    
    const lastProjection = processedData[processedData.length - 1] || {};
    
    // Extract data with fallbacks for different property naming conventions
    const successProbability = typeof activeData.successProbability === 'number' ? 
                               activeData.successProbability : 
                               (typeof activeData.success_probability === 'number' ? 
                                activeData.success_probability : 0);
                                
    const targetAmount = activeData.targetAmount || activeData.target_amount || 0;
    const currentAmount = activeData.currentAmount || activeData.current_amount || 0;
    const monthlyContribution = activeData.monthlyContribution || 
                                activeData.monthly_contribution || 0;
    
    // Calculate shortfall or surplus
    const expectedFinalAmount = lastProjection.median || 0;
    const shortfall = targetAmount - expectedFinalAmount;
    
    // Calculate achievement year (when median crosses target)
    let achievementYear = null;
    for (let i = 0; i < processedData.length; i++) {
      if (processedData[i].median >= targetAmount) {
        achievementYear = processedData[i].year;
        break;
      }
    }
    
    return {
      successProbability,
      targetAmount,
      currentAmount,
      monthlyContribution,
      expectedFinalAmount,
      shortfall,
      achievementYear,
      // Indian context: Add SIP impact metrics
      sipTotalInvestment: monthlyContribution * 12 * timeHorizon,
      sipGrowthMultiple: expectedFinalAmount / (monthlyContribution * 12 * timeHorizon),
    };
  }, [getActiveData, processedData, timeHorizon]);

  // City benchmark data (cost of living comparison for Indian context)
  const cityBenchmarks = [
    { city: 'Mumbai', amount: 50000000, label: 'Mumbai Home' },  // 5 Cr
    { city: 'Delhi', amount: 40000000, label: 'Delhi Home' },    // 4 Cr
    { city: 'Bangalore', amount: 30000000, label: 'Bangalore Home' }, // 3 Cr
    { city: 'Annual Expenses', amount: 1200000, label: 'Annual Expenses' }, // 12 L
    { city: 'Education', amount: 2500000, label: 'Education (4yr)' }, // 25 L
  ];

  // Handle scenario selection
  const handleScenarioChange = (scenario) => {
    setSelectedScenario(scenario);
    if (onScenarioSelect) {
      onScenarioSelect(scenario);
    }
  };

  // Custom styles for recharts tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 shadow-lg rounded-md">
          <p className="font-semibold text-gray-800">{`Year: ${label}`}</p>
          <p className="text-green-600">
            <span className="font-medium">Median: </span> 
            {formatRupees(payload[0]?.value)}
          </p>
          {payload.length > 1 && (
            <>
              <p className="text-green-800">
                <span className="font-medium">90th Percentile: </span>
                {formatRupees(payload[1]?.value)}
              </p>
              <p className="text-amber-600">
                <span className="font-medium">10th Percentile: </span>
                {formatRupees(payload[2]?.value)}
              </p>
            </>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 max-w-6xl mx-auto">
      {/* Header section with goal details */}
      <div className="border-b border-gray-200 pb-4 mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-gray-800">
          {goalData.title || "Goal Projection"}
        </h2>
        <p className="text-gray-600 mt-1">
          {goalData.description || `Financial goal analysis with ${timeHorizon} year projection`}
        </p>
      </div>

      {/* Main metrics panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {/* Success probability gauge */}
        <div className="bg-gray-50 rounded-lg p-4 flex flex-col items-center">
          <h3 className="text-gray-700 font-medium mb-2 text-center">Success Probability</h3>
          <div className="w-full h-32">
            <GaugeChart 
              id="goal-probability-gauge"
              nrOfLevels={5}
              colors={[mergedTheme.error, mergedTheme.warning, mergedTheme.success]}
              percent={metrics.successProbability}
              formatTextValue={value => `${parseInt(value)}%`}
              textColor={mergedTheme.text}
            />
          </div>
          <div className="text-center mt-2">
            <span className={`font-semibold text-lg ${
              metrics.successProbability >= 0.7 ? 'text-green-600' : 
              metrics.successProbability >= 0.5 ? 'text-amber-600' : 'text-red-600'
            }`}>
              {(metrics.successProbability * 100).toFixed(0)}%
            </span>
            <span className="text-gray-600 text-sm block mt-1">
              {metrics.successProbability >= 0.7 ? 'On Track' : 
               metrics.successProbability >= 0.5 ? 'Needs Attention' : 'At Risk'}
            </span>
          </div>
        </div>

        {/* Goal details */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-gray-700 font-medium mb-3">Goal Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Target Amount:</span>
              <span className="font-semibold">{formatRupees(metrics.targetAmount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Current Amount:</span>
              <span className="font-semibold">{formatRupees(metrics.currentAmount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Monthly SIP:</span>
              <span className="font-semibold">{formatRupees(metrics.monthlyContribution)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Target Year:</span>
              <span className="font-semibold">{goalData.targetYear || 'Not specified'}</span>
            </div>
          </div>
        </div>

        {/* Projection results */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-gray-700 font-medium mb-3">Projection Results</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Expected Amount:</span>
              <span className={`font-semibold ${metrics.shortfall > 0 ? 'text-amber-600' : 'text-green-600'}`}>
                {formatRupees(metrics.expectedFinalAmount)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">
                {metrics.shortfall > 0 ? 'Projected Shortfall:' : 'Projected Surplus:'}
              </span>
              <span className={`font-semibold ${metrics.shortfall > 0 ? 'text-red-600' : 'text-green-600'}`}>
                {formatRupees(Math.abs(metrics.shortfall))}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Achievement Year:</span>
              <span className="font-semibold">
                {metrics.achievementYear ? metrics.achievementYear : 'Beyond Projection'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">SIP Growth Multiple:</span>
              <span className="font-semibold">
                {metrics.sipGrowthMultiple ? metrics.sipGrowthMultiple.toFixed(2) + 'x' : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tab navigation for mobile */}
      {isMobile && (
        <div className="flex justify-between border-b border-gray-200 mb-4">
          <button 
            className={`pb-2 px-1 ${expandedSection === 'distribution' ? 
              'border-b-2 border-green-500 text-green-600 font-medium' : 
              'text-gray-500'}`}
            onClick={() => setExpandedSection('distribution')}
          >
            Probability Fan
          </button>
          <button 
            className={`pb-2 px-1 ${expandedSection === 'timeline' ? 
              'border-b-2 border-green-500 text-green-600 font-medium' : 
              'text-gray-500'}`}
            onClick={() => setExpandedSection('timeline')}
          >
            Timeline
          </button>
          <button 
            className={`pb-2 px-1 ${expandedSection === 'adjustments' ? 
              'border-b-2 border-green-500 text-green-600 font-medium' : 
              'text-gray-500'}`}
            onClick={() => setExpandedSection('adjustments')}
          >
            Adjustments
          </button>
          <button 
            className={`pb-2 px-1 ${expandedSection === 'scenarios' ? 
              'border-b-2 border-green-500 text-green-600 font-medium' : 
              'text-gray-500'}`}
            onClick={() => setExpandedSection('scenarios')}
          >
            Scenarios
          </button>
        </div>
      )}

      {/* Charts and visualizations */}
      <div className={`${isMobile ? '' : 'grid grid-cols-1 md:grid-cols-2 gap-6'}`}>
        {/* Fan chart section */}
        {(!isMobile || expandedSection === 'distribution') && (
          <div className="mb-6 md:mb-0">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-gray-800 font-medium">Probability Distribution</h3>
              <div className="flex items-center">
                <button 
                  className={`text-xs px-2 py-1 rounded mr-2 ${showBenchmarks ? 
                    'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}
                  onClick={() => setShowBenchmarks(!showBenchmarks)}
                >
                  {showBenchmarks ? 'Hide Benchmarks' : 'Show Benchmarks'}
                </button>
              </div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4 h-64 md:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={processedData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="year" 
                    tick={{ fontSize: 12 }} 
                    tickFormatter={(value) => value}
                  />
                  <YAxis 
                    tickFormatter={(value) => formatRupees(value)}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  
                  {/* Confidence interval areas */}
                  <Area 
                    type="monotone"
                    dataKey="p90"
                    stackId="1"
                    stroke="none"
                    fill={mergedTheme.percentile90}
                  />
                  <Area 
                    type="monotone"
                    dataKey="p75"
                    stackId="1"
                    stroke="none"
                    fill={mergedTheme.percentile75}
                  />
                  <Area 
                    type="monotone"
                    dataKey="p50"
                    stackId="1"
                    stroke="none"
                    fill={mergedTheme.percentile50}
                  />
                  <Area 
                    type="monotone"
                    dataKey="p25"
                    stackId="1"
                    stroke="none"
                    fill={mergedTheme.percentile25}
                  />
                  
                  {/* Median line */}
                  <Line 
                    type="monotone"
                    dataKey="median"
                    stroke={mergedTheme.medianLine}
                    strokeWidth={2}
                    dot={false}
                  />
                  
                  {/* Target line */}
                  <ReferenceLine 
                    y={goalData.targetAmount} 
                    stroke={mergedTheme.accent}
                    strokeDasharray="3 3"
                    label={{
                      value: 'Target',
                      fill: mergedTheme.accent,
                      fontSize: 12,
                      position: 'right'
                    }}
                  />
                  
                  {/* City benchmarks */}
                  {showBenchmarks && cityBenchmarks
                    .filter(benchmark => benchmark.amount <= goalData.targetAmount * 2)
                    .map((benchmark, index) => (
                      <ReferenceLine 
                        key={index}
                        y={benchmark.amount} 
                        stroke="#9CA3AF"
                        strokeDasharray="2 4"
                        label={{
                          value: benchmark.label,
                          fill: '#6B7280',
                          fontSize: 10,
                          position: 'insideTopRight'
                        }}
                      />
                    ))
                  }
                </AreaChart>
              </ResponsiveContainer>
            </div>
            
            <div className="mt-2 text-xs text-gray-500 flex justify-between">
              <div className="flex items-center">
                <span className="inline-block w-3 h-3 bg-green-300 mr-1"></span>
                <span>25-75th Percentile</span>
              </div>
              <div className="flex items-center">
                <span className="inline-block w-3 h-3 bg-green-200 mr-1"></span>
                <span>10-90th Percentile</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Timeline projection */}
        {(!isMobile || expandedSection === 'timeline') && (
          <div className="mb-6 md:mb-0">
            <h3 className="text-gray-800 font-medium mb-4">Timeline Projection</h3>
            <div className="bg-white border border-gray-200 rounded-lg p-4 h-64 md:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={processedData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="year" 
                    tick={{ fontSize: 12 }} 
                  />
                  <YAxis 
                    tickFormatter={(value) => formatRupees(value)}
                    tick={{ fontSize: 12 }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  
                  {/* Line for base projection */}
                  <Line 
                    type="monotone" 
                    dataKey="median" 
                    name="Current Path"
                    stroke={mergedTheme.primary} 
                    activeDot={{ r: 8 }}
                  />
                  
                  {/* Line for adjusted projection (with SIP increase) */}
                  {contributionMultiplier > 1 && (
                    <Line 
                      type="monotone" 
                      dataKey="adjustedMedian"
                      name={`With ${(contributionMultiplier*100).toFixed(0)}% SIP`}
                      stroke={mergedTheme.secondary} 
                      strokeDasharray="5 5"
                    />
                  )}
                  
                  {/* Target line */}
                  <ReferenceLine 
                    y={goalData.targetAmount} 
                    stroke={mergedTheme.accent}
                    strokeDasharray="3 3"
                    label={{
                      value: 'Target',
                      fill: mergedTheme.accent,
                      fontSize: 12,
                      position: 'right'
                    }}
                  />
                  
                  {/* Achievement point if within timeline */}
                  {metrics.achievementYear && (
                    <ReferenceLine 
                      x={metrics.achievementYear}
                      stroke={mergedTheme.success}
                      label={{
                        value: 'Goal Achieved',
                        fill: mergedTheme.success,
                        fontSize: 12
                      }}
                    />
                  )}
                  
                  {/* Life events markers if provided */}
                  {goalData.lifeEvents?.map((event, i) => (
                    <ReferenceLine 
                      key={i}
                      x={event.year}
                      stroke="#9CA3AF"
                      label={{
                        value: event.name,
                        fill: '#6B7280',
                        fontSize: 10,
                        position: 'top'
                      }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            {/* Contribution adjustment slider */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SIP Contribution Adjustment
              </label>
              <div className="flex items-center">
                <input
                  type="range"
                  min={0.5}
                  max={2}
                  step={0.1}
                  value={contributionMultiplier}
                  onChange={(e) => {
                    const newValue = parseFloat(e.target.value);
                    setContributionMultiplier(newValue);
                    
                    // Publish parameter change event if DataEventBus is available
                    if (window.DataEventBus && goalIdRef.current) {
                      window.DataEventBus.publish('parameters-changed', {
                        source: 'probabilistic-visualizer',
                        goalId: goalIdRef.current,
                        parameters: {
                          contribution_multiplier: newValue
                        }
                      });
                    }
                  }}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <span className="ml-3 text-sm font-medium text-gray-900 min-w-[60px]">
                  {(contributionMultiplier * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>50%</span>
                <span>100%</span>
                <span>200%</span>
              </div>
              <p className="mt-2 text-xs text-gray-500">
                {contributionMultiplier === 1 
                  ? 'Current monthly SIP: ' + formatRupees(metrics.monthlyContribution)
                  : `Adjusted monthly SIP: ${formatRupees(metrics.monthlyContribution * contributionMultiplier)} 
                     (${contributionMultiplier > 1 ? '+' : ''}${((contributionMultiplier - 1) * 100).toFixed(0)}%)`
                }
              </p>
            </div>
          </div>
        )}
      </div>
      
      {/* Additional analysis sections */}
      <div className={`mt-8 ${isMobile ? '' : 'grid grid-cols-1 md:grid-cols-2 gap-6'}`}>
        {/* Adjustments Impact section */}
        {(!isMobile || expandedSection === 'adjustments') && (
          <div className="mb-6 md:mb-0">
            <h3 className="text-gray-800 font-medium mb-4">Adjustment Impact</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <Suspense fallback={<div className="text-center py-6">Loading adjustment impact analysis...</div>}>
                {goalData.adjustments ? (
                  <AdjustmentImpactPanel 
                    adjustments={goalData.adjustments}
                    currentProbability={metrics.successProbability}
                    formatRupees={formatRupees}
                    theme={mergedTheme}
                  />
                ) : (
                  <div className="text-center py-6 text-gray-500">
                    <svg className="w-12 h-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="mt-2">Adjustment recommendations will appear here when available.</p>
                  </div>
                )}
              </Suspense>
            </div>
          </div>
        )}
        
        {/* Scenario Comparison section */}
        {(!isMobile || expandedSection === 'scenarios') && (
          <div className="mb-6 md:mb-0">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-gray-800 font-medium">Scenario Comparison</h3>
              <div className="flex text-sm">
                <button 
                  className={`px-3 py-1 rounded-l-md ${selectedScenario === 'current' ? 
                    'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                  onClick={() => handleScenarioChange('current')}
                >
                  Current
                </button>
                <button 
                  className={`px-3 py-1 rounded-r-md ${selectedScenario === 'optimized' ? 
                    'bg-green-600 text-white' : 'bg-gray-200 text-gray-700'}`}
                  onClick={() => handleScenarioChange('optimized')}
                  disabled={!goalData.scenarios?.optimized}
                >
                  Optimized
                </button>
              </div>
            </div>
            
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <Suspense fallback={<div className="text-center py-8">Loading scenario comparison...</div>}>
                {goalData.scenarios ? (
                  <ScenarioComparisonChart 
                    currentScenario={goalData.scenarios.current}
                    optimizedScenario={goalData.scenarios.optimized}
                    selectedScenario={selectedScenario}
                    targetAmount={goalData.targetAmount}
                    formatRupees={formatRupees}
                    theme={mergedTheme}
                  />
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <p>Alternative scenarios are not available for this goal.</p>
                    <p className="text-sm mt-2">Complete your financial profile to enable scenario comparison.</p>
                  </div>
                )}
              </Suspense>
            </div>
          </div>
        )}
      </div>

      {/* Indian-specific insights */}
      <div className="mt-8 bg-green-50 rounded-lg p-4 border border-green-200">
        <h3 className="text-green-800 font-medium flex items-center mb-3">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          SIP Impact Analysis
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-white rounded p-3 border border-green-100">
            <p className="text-gray-600 mb-1">Total SIP Investment</p>
            <p className="text-lg font-semibold text-gray-800">{formatRupees(metrics.sipTotalInvestment || 0)}</p>
          </div>
          <div className="bg-white rounded p-3 border border-green-100">
            <p className="text-gray-600 mb-1">Expected Returns</p>
            <p className="text-lg font-semibold text-green-600">
              {formatRupees((metrics.expectedFinalAmount || 0) - (metrics.sipTotalInvestment || 0))}
            </p>
          </div>
          <div className="bg-white rounded p-3 border border-green-100">
            <p className="text-gray-600 mb-1">Growth Multiple</p>
            <p className="text-lg font-semibold text-green-600">
              {(metrics.sipGrowthMultiple || 0).toFixed(2)}x
            </p>
          </div>
        </div>
        <p className="mt-3 text-sm text-green-700">
          {metrics.sipGrowthMultiple > 2.5 ? 
            "Your SIP investments are projected to grow significantly due to the power of compounding." :
            "Consider increasing your SIP amount to improve your growth multiple and goal success probability."}
        </p>
      </div>

      {/* Disclaimer footer */}
      <div className="mt-6 text-xs text-gray-500 border-t border-gray-200 pt-4">
        <p>
          <strong>Disclaimer:</strong> Projections are based on Monte Carlo simulations and historical data. 
          Actual results may vary. These projections are for informational purposes only and should not be 
          considered as financial advice.
        </p>
      </div>
    </div>
  );
};

// Define prop types
ProbabilisticGoalVisualizer.propTypes = {
  goalData: PropTypes.shape({
    id: PropTypes.string,
    title: PropTypes.string,
    description: PropTypes.string,
    targetAmount: PropTypes.number,
    currentAmount: PropTypes.number,
    targetYear: PropTypes.number,
    startYear: PropTypes.number,
    monthlyContribution: PropTypes.number,
    successProbability: PropTypes.number,
    projections: PropTypes.arrayOf(
      PropTypes.shape({
        median: PropTypes.number,
        percentiles: PropTypes.object
      })
    ),
    lifeEvents: PropTypes.arrayOf(
      PropTypes.shape({
        year: PropTypes.number,
        name: PropTypes.string
      })
    ),
    adjustments: PropTypes.arrayOf(
      PropTypes.shape({
        type: PropTypes.string,
        description: PropTypes.string,
        impact: PropTypes.number,
        value: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
      })
    ),
    scenarios: PropTypes.object
  }),
  timeHorizon: PropTypes.number,
  confidenceIntervals: PropTypes.arrayOf(PropTypes.number),
  theme: PropTypes.object,
  onScenarioSelect: PropTypes.func,
  isLoading: PropTypes.bool,
  error: PropTypes.object
};

export default ProbabilisticGoalVisualizer;