import unittest
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the RebalancingStrategy class
from models.funding_strategies.rebalancing_strategy import RebalancingStrategy

class TestRebalancingDocumentation(unittest.TestCase):
    """Test the documentation generator methods of the RebalancingStrategy class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.rebalancing_strategy = RebalancingStrategy()
        
        # Create test strategy dictionaries for different scenarios
        
        # 1. Emergency Fund Strategy
        self.emergency_fund_strategy = {
            'goal_type': 'emergency_fund',
            'approach': 'conservative_minimal',
            'risk_profile': 'conservative',
            'rationale': 'Maintaining liquidity and safety for unexpected expenses',
            'target_allocation': {
                'cash': 0.50,
                'debt': 0.50,
                'equity': 0.00,
                'gold': 0.00
            },
            'rebalancing_schedule': {
                'recommended_frequency': 'annual',
                'months_between_rebalancing': 12,
                'next_scheduled_rebalancing': '2026-03-20',
                'rationale': {
                    'goal_based': 'Emergency funds require minimal rebalancing due to conservative allocation',
                    'portfolio_size': 'Portfolio size supports standard rebalancing frequency',
                    'liquidity': 'High liquidity needs require maintaining appropriate cash levels',
                    'market_volatility': 'Normal market volatility supports standard approach',
                    'tax_considerations': 'No specific tax year timing considerations'
                }
            },
            'drift_thresholds': {
                'threshold_rationale': 'Asset-specific thresholds balancing risk management and transaction costs',
                'asset_bands': {
                    'cash': {
                        'target': 0.50,
                        'threshold': 0.02,
                        'upper_band': 0.52,
                        'lower_band': 0.48,
                        'rebalance_when': '< 0.48 or > 0.52'
                    },
                    'debt': {
                        'target': 0.50,
                        'threshold': 0.02,
                        'upper_band': 0.52,
                        'lower_band': 0.48,
                        'rebalance_when': '< 0.48 or > 0.52'
                    }
                },
                'implementation_note': 'Implement threshold-based rebalancing with calendar minimums'
            },
            'emergency_specific_considerations': {
                'liquidity_focus': 'Maintain high liquidity for unexpected expenses',
                'accessibility': 'Ensure funds are quickly accessible without penalties',
                'safety_priority': 'Capital preservation takes precedence over returns'
            },
            'implementation_priorities': [
                'Establish high-interest savings account for cash portion',
                'Select liquid debt funds with minimal exit loads',
                'Minimize rebalancing frequency to reduce costs'
            ],
            'simulation_results': {
                'performance_metrics': {
                    'expected_return': 0.06,
                    'volatility': 0.02,
                    'sharpe_ratio': 0.8,
                    'max_drawdown': 0.01
                }
            }
        }
        
        # 2. Retirement Strategy
        self.retirement_strategy = {
            'goal_type': 'retirement',
            'approach': 'balanced_growth',
            'risk_profile': 'moderate',
            'rationale': 'Long-term growth with gradual risk reduction as retirement approaches',
            'target_allocation': {
                'equity': 0.60,
                'debt': 0.30,
                'gold': 0.05,
                'cash': 0.05
            },
            'rebalancing_schedule': {
                'recommended_frequency': 'semi_annual',
                'months_between_rebalancing': 6,
                'next_scheduled_rebalancing': '2025-09-20',
                'rationale': {
                    'goal_based': 'Long-term retirement goal with periodic risk assessment',
                    'portfolio_size': 'Larger portfolio allows for more frequent rebalancing for optimal allocation',
                    'liquidity': 'No significant near-term liquidity needs',
                    'market_volatility': 'Normal market volatility supports standard approach',
                    'tax_considerations': 'Consider tax-loss harvesting before tax year end (March 31)'
                }
            },
            'drift_thresholds': {
                'threshold_rationale': 'Asset-specific thresholds balancing risk management and transaction costs',
                'asset_bands': {
                    'equity': {
                        'target': 0.60,
                        'threshold': 0.05,
                        'upper_band': 0.65,
                        'lower_band': 0.55,
                        'rebalance_when': '< 0.55 or > 0.65'
                    },
                    'debt': {
                        'target': 0.30,
                        'threshold': 0.03,
                        'upper_band': 0.33,
                        'lower_band': 0.27,
                        'rebalance_when': '< 0.27 or > 0.33'
                    },
                    'gold': {
                        'target': 0.05,
                        'threshold': 0.02,
                        'upper_band': 0.07,
                        'lower_band': 0.03,
                        'rebalance_when': '< 0.03 or > 0.07'
                    },
                    'cash': {
                        'target': 0.05,
                        'threshold': 0.01,
                        'upper_band': 0.06,
                        'lower_band': 0.04,
                        'rebalance_when': '< 0.04 or > 0.06'
                    }
                },
                'implementation_note': 'Implement threshold-based rebalancing with calendar minimums'
            },
            'retirement_specific_considerations': {
                'time_horizon': 'Long-term investment approach with 25 years to retirement',
                'income_needs': 'Goal to replace 70% of pre-retirement income',
                'inflation_protection': 'Equity allocation helps combat long-term inflation',
                'bucket_approach': 'Consider implementing bucket strategy 5 years before retirement'
            },
            'age_based_factors': {
                'current_age': 35,
                'retirement_age': 60,
                'life_expectancy': 85,
                'glide_path': 'Reduce equity by 1% annually starting 10 years before retirement'
            },
            'implementation_priorities': [
                'Maximize tax-advantaged accounts (EPF, NPS)',
                'Establish core equity positions in index funds',
                'Add alpha through active equity funds',
                'Maintain debt allocation for stability'
            ],
            'simulation_results': {
                'performance_metrics': {
                    'expected_return': 0.10,
                    'volatility': 0.12,
                    'sharpe_ratio': 0.6,
                    'max_drawdown': 0.25
                }
            }
        }
        
        # 3. Education Strategy
        self.education_strategy = {
            'goal_type': 'education',
            'approach': 'progressive_conservative',
            'risk_profile': 'moderate_conservative',
            'rationale': 'Balanced growth transitioning to capital preservation as education date approaches',
            'target_allocation': {
                'equity': 0.40,
                'debt': 0.45,
                'gold': 0.05,
                'cash': 0.10
            },
            'rebalancing_schedule': {
                'recommended_frequency': 'quarterly',
                'months_between_rebalancing': 3,
                'next_scheduled_rebalancing': '2025-06-20',
                'rationale': {
                    'goal_based': 'Critical education goal with medium timeline requires closer monitoring',
                    'portfolio_size': 'Portfolio size supports standard rebalancing frequency',
                    'liquidity': 'Future liquidity needs require proactive management',
                    'market_volatility': 'Normal market volatility supports standard approach',
                    'tax_considerations': 'No specific tax year timing considerations'
                }
            },
            'drift_thresholds': {
                'threshold_rationale': 'Tighter thresholds due to education goal criticality',
                'asset_bands': {
                    'equity': {
                        'target': 0.40,
                        'threshold': 0.04,
                        'upper_band': 0.44,
                        'lower_band': 0.36,
                        'rebalance_when': '< 0.36 or > 0.44'
                    },
                    'debt': {
                        'target': 0.45,
                        'threshold': 0.03,
                        'upper_band': 0.48,
                        'lower_band': 0.42,
                        'rebalance_when': '< 0.42 or > 0.48'
                    },
                    'gold': {
                        'target': 0.05,
                        'threshold': 0.02,
                        'upper_band': 0.07,
                        'lower_band': 0.03,
                        'rebalance_when': '< 0.03 or > 0.07'
                    },
                    'cash': {
                        'target': 0.10,
                        'threshold': 0.02,
                        'upper_band': 0.12,
                        'lower_band': 0.08,
                        'rebalance_when': '< 0.08 or > 0.12'
                    }
                },
                'implementation_note': 'Progressive risk reduction as education start date approaches'
            },
            'education_specific_considerations': {
                'academic_calendar_sync': 'Align liquidation with admission and fee payment cycles',
                'progressive_risk_reduction': 'Shift 5% from equity to debt annually in last 5 years',
                'fee_payment_schedule': 'Plan for semester-wise liquidity needs',
                'contingency_buffer': 'Maintain 10% buffer for unexpected education expenses'
            },
            'implementation_priorities': [
                'Establish diversified equity core for growth in early years',
                'Schedule automatic risk reduction as education date approaches',
                'Build liquidity buffer 12-18 months before first payment due',
                'Ensure tax-efficient withdrawal strategy'
            ],
            'simulation_results': {
                'performance_metrics': {
                    'expected_return': 0.08,
                    'volatility': 0.08,
                    'sharpe_ratio': 0.7,
                    'max_drawdown': 0.15
                }
            }
        }

    def test_generate_strategy_summary(self):
        """Test the generate_strategy_summary method with different goal types."""
        print("\n=== Testing generate_strategy_summary ===")
        
        # Test with Emergency Fund strategy
        emergency_summary = self.rebalancing_strategy.generate_strategy_summary(self.emergency_fund_strategy)
        self.assertIsInstance(emergency_summary, dict)
        self.assertIn('executive_summary', emergency_summary)
        self.assertIn('technical_summary', emergency_summary)
        self.assertIn('key_metrics', emergency_summary)
        self.assertIn('key_indian_considerations', emergency_summary)
        
        # Print summary for inspection
        print("\nEmergency Fund Strategy Summary:")
        print(json.dumps(emergency_summary, indent=2))
        
        # Test with Retirement strategy
        retirement_summary = self.rebalancing_strategy.generate_strategy_summary(self.retirement_strategy)
        self.assertIsInstance(retirement_summary, dict)
        self.assertIn('executive_summary', retirement_summary)
        self.assertIn('technical_summary', retirement_summary)
        self.assertIn('key_metrics', retirement_summary)
        
        # Print summary for inspection
        print("\nRetirement Strategy Summary:")
        print(json.dumps(retirement_summary, indent=2))
        
        # Test with Education strategy
        education_summary = self.rebalancing_strategy.generate_strategy_summary(self.education_strategy)
        self.assertIsInstance(education_summary, dict)
        self.assertIn('executive_summary', education_summary)
        self.assertIn('technical_summary', education_summary)
        self.assertIn('key_metrics', education_summary)
        
        # Print summary for inspection
        print("\nEducation Strategy Summary:")
        print(json.dumps(education_summary, indent=2))

    def test_create_implementation_checklist(self):
        """Test the create_implementation_checklist method with different goal types."""
        print("\n=== Testing create_implementation_checklist ===")
        
        # Test with Emergency Fund strategy
        emergency_checklist = self.rebalancing_strategy.create_implementation_checklist(self.emergency_fund_strategy)
        self.assertIsInstance(emergency_checklist, dict)
        self.assertIn('account_setup', emergency_checklist)
        self.assertIn('investment_selection', emergency_checklist)
        self.assertIn('sip_setup', emergency_checklist)
        
        # Print checklist for inspection
        print("\nEmergency Fund Implementation Checklist:")
        print(json.dumps(emergency_checklist, indent=2))
        
        # Test with Retirement strategy
        retirement_checklist = self.rebalancing_strategy.create_implementation_checklist(self.retirement_strategy)
        self.assertIsInstance(retirement_checklist, dict)
        self.assertIn('account_setup', retirement_checklist)
        self.assertIn('investment_selection', retirement_checklist)
        
        # Print checklist for inspection
        print("\nRetirement Implementation Checklist:")
        print(json.dumps(retirement_checklist, indent=2))
        
        # Test with Education strategy
        education_checklist = self.rebalancing_strategy.create_implementation_checklist(self.education_strategy)
        self.assertIsInstance(education_checklist, dict)
        self.assertIn('account_setup', education_checklist)
        self.assertIn('investment_selection', education_checklist)
        
        # Print checklist for inspection
        print("\nEducation Implementation Checklist:")
        print(json.dumps(education_checklist, indent=2))

    def test_produce_monitoring_guidelines(self):
        """Test the produce_monitoring_guidelines method with different goal types."""
        print("\n=== Testing produce_monitoring_guidelines ===")
        
        # Test with Emergency Fund strategy
        emergency_guidelines = self.rebalancing_strategy.produce_monitoring_guidelines(self.emergency_fund_strategy)
        self.assertIsInstance(emergency_guidelines, dict)
        self.assertIn('performance_metrics', emergency_guidelines)
        self.assertIn('review_schedule', emergency_guidelines)
        self.assertIn('rebalancing_triggers', emergency_guidelines)
        
        # Print guidelines for inspection
        print("\nEmergency Fund Monitoring Guidelines:")
        print(json.dumps(emergency_guidelines, indent=2))
        
        # Test with Retirement strategy
        retirement_guidelines = self.rebalancing_strategy.produce_monitoring_guidelines(self.retirement_strategy)
        self.assertIsInstance(retirement_guidelines, dict)
        self.assertIn('performance_metrics', retirement_guidelines)
        self.assertIn('review_schedule', retirement_guidelines)
        
        # Print guidelines for inspection
        print("\nRetirement Monitoring Guidelines:")
        print(json.dumps(retirement_guidelines, indent=2))
        
        # Test with Education strategy
        education_guidelines = self.rebalancing_strategy.produce_monitoring_guidelines(self.education_strategy)
        self.assertIsInstance(education_guidelines, dict)
        self.assertIn('performance_metrics', education_guidelines)
        self.assertIn('review_schedule', education_guidelines)
        
        # Print guidelines for inspection
        print("\nEducation Monitoring Guidelines:")
        print(json.dumps(education_guidelines, indent=2))

if __name__ == '__main__':
    unittest.main()