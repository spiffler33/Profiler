/**
 * SimpleProbabilityVisualizer
 * A simplified version of the ProbabilisticGoalVisualizer that works directly in the browser
 * without requiring bundling
 */

// Define the SimpleProbabilityVisualizer React component
class SimpleProbabilityVisualizer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      probability: this.props.successProbability || 0,
      targetAmount: this.props.targetAmount || 0,
      currentAmount: this.props.currentAmount || 0,
      adjustments: [
        { 
          id: 'extend_timeline', 
          description: 'Extend timeline by 2 years',
          impact: 0.15 
        },
        { 
          id: 'increase_contribution', 
          description: 'Increase monthly contribution by 15%',
          impact: 0.20 
        },
        { 
          id: 'adjust_target', 
          description: 'Adjust target amount by 10%',
          impact: 0.10 
        }
      ]
    };
  }

  componentDidMount() {
    // You could fetch data here if needed
    console.log('SimpleProbabilityVisualizer mounted with props:', this.props);
  }

  getProbabilityColorClass() {
    const { probability } = this.state;
    if (probability >= 0.7) return 'high-probability';
    if (probability >= 0.5) return 'medium-probability';
    return 'low-probability';
  }

  getProbabilityDescription() {
    const { probability } = this.state;
    if (probability >= 0.7) return 'You are on track to meet this goal.';
    if (probability >= 0.5) return 'This goal is achievable with some adjustments.';
    return 'This goal may be challenging to achieve. Consider adjustments.';
  }

  render() {
    const { probability, targetAmount, currentAmount, adjustments } = this.state;
    const percentProbability = Math.round(probability * 100);
    const colorClass = this.getProbabilityColorClass();
    const description = this.getProbabilityDescription();

    // Format currency
    const formatCurrency = (amount) => {
      return '$' + amount.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
    };

    return React.createElement(
      'div', 
      { className: 'visualization-container' },
      
      // Probability header
      React.createElement(
        'div',
        { className: 'visualization-header' },
        React.createElement('h3', {}, 'Goal Success Probability')
      ),

      // Probability gauge
      React.createElement(
        'div',
        { className: 'probability-gauge' },
        React.createElement(
          'div',
          { className: 'gauge-container' },
          React.createElement(
            'div',
            { className: 'gauge-value-container' },
            React.createElement(
              'span',
              { className: `gauge-value ${colorClass}` },
              `${percentProbability}%`
            )
          ),
          React.createElement(
            'div',
            { className: 'gauge-bar' },
            React.createElement(
              'div',
              {
                className: `gauge-fill ${colorClass}`,
                style: { width: `${percentProbability}%` }
              }
            )
          )
        )
      ),

      // Probability description
      React.createElement(
        'div',
        { className: 'probability-description' },
        React.createElement('p', {}, description)
      ),

      // Goal progress
      React.createElement(
        'div',
        { className: 'goal-progress-container' },
        React.createElement('h4', {}, 'Goal Progress'),
        React.createElement(
          'div',
          { className: 'goal-metrics' },
          React.createElement(
            'div',
            { className: 'goal-metric' },
            React.createElement('span', { className: 'metric-label' }, 'Target Amount:'),
            React.createElement('span', { className: 'metric-value' }, formatCurrency(targetAmount))
          ),
          React.createElement(
            'div',
            { className: 'goal-metric' },
            React.createElement('span', { className: 'metric-label' }, 'Current Amount:'),
            React.createElement('span', { className: 'metric-value' }, formatCurrency(currentAmount))
          ),
          React.createElement(
            'div',
            { className: 'goal-metric' },
            React.createElement('span', { className: 'metric-label' }, 'Progress:'),
            React.createElement(
              'span', 
              { className: 'metric-value' }, 
              `${Math.round((currentAmount / targetAmount) * 100)}%`
            )
          )
        )
      ),

      // Recommended adjustments
      React.createElement(
        'div',
        { className: 'recommended-adjustments' },
        React.createElement('h4', {}, 'Recommended Adjustments'),
        React.createElement(
          'ul',
          { className: 'adjustment-list' },
          adjustments.map(adjustment => 
            React.createElement(
              'li',
              { className: 'adjustment-item', key: adjustment.id },
              React.createElement('span', { className: 'adjustment-label' }, adjustment.description),
              React.createElement(
                'span', 
                { className: 'adjustment-impact positive' }, 
                `+${Math.round(adjustment.impact * 100)}%`
              )
            )
          )
        )
      )
    );
  }
}