import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
import importlib

from .base_strategy import FundingStrategyGenerator

logger = logging.getLogger(__name__)

class RebalancingStrategy(FundingStrategyGenerator):
    """
    Specialized funding strategy for portfolio rebalancing with 
    considerations for Indian tax efficiency and market conditions.
    """
    
    def __init__(self):
        """Initialize with rebalancing-specific parameters"""
        super().__init__()
        
        # Try importing life event registry
        try:
            self.life_event_registry_module = importlib.import_module('models.life_event_registry')
            self.has_life_event_registry = True
            logger.info("Initialized with access to centralized LifeEventRegistry")
        except ImportError:
            self.life_event_registry_module = None
            self.has_life_event_registry = False
            logger.warning("LifeEventRegistry not available, falling back to built-in life event handling")
        
        # Additional rebalancing-specific parameters
        self.rebalancing_params = {
            "rebalancing_frequency": {
                "default": "annual",
                "conservative": "semi_annual",
                "aggressive": "quarterly"
            },
            "drift_thresholds": {
                "equity": 0.05,    # 5% drift threshold for equity
                "debt": 0.03,      # 3% drift threshold for debt
                "gold": 0.02,      # 2% drift threshold for gold
                "cash": 0.01,      # 1% drift threshold for cash
                "alternatives": 0.07  # 7% drift threshold for alternatives
            },
            "indian_market_factors": {
                "volatility_adjustment": {
                    "low": 0.8,     # Tighter bands in low volatility
                    "normal": 1.0,  # Normal bands
                    "high": 1.5     # Wider bands in high volatility
                },
                "seasonal_factors": {
                    "pre_budget": "postpone",   # Postpone rebalancing before budget
                    "post_budget": "expedite",  # Expedite after budget clarity
                    "tax_year_end": "tax_optimize"  # Tax optimization at fiscal year end
                }
            },
            "tax_efficiency": {
                "equity_lt_threshold": 12,     # 12 months for LTCG on equity
                "debt_lt_threshold": 36,       # 36 months for LTCG on debt
                "stcg_equity_rate": 0.15,      # 15% STCG on equity
                "ltcg_equity_rate": 0.10,      # 10% LTCG on equity above ₹1L
                "ltcg_exemption_limit": 100000,  # ₹1L exemption for equity LTCG
                "ltcg_debt_rate": 0.20,        # 20% LTCG on debt with indexation
                "stcg_debt_rate": 0.30,        # As per income tax slab
                "stt_rate": 0.001,             # 0.1% Securities Transaction Tax
                "stamp_duty_rate": 0.00015     # 0.015% Stamp Duty on equity
            },
            "cost_efficiency": {
                "minimum_transaction": 5000,    # Minimum transaction amount
                "trading_cost_threshold": 0.0025,  # 0.25% trading cost threshold
                "brokerage_fees": {
                    "equity": {
                        "discount_broker": 0.0005,  # 0.05% or flat ₹20 per trade
                        "full_service": 0.0030,     # 0.3% typical for full-service brokers
                        "minimum_fee": 20           # Minimum fee per trade (₹20)
                    },
                    "mutual_funds": {
                        "direct_plans": 0.0,        # No brokerage for direct plans
                        "regular_plans": 0.0010     # Hidden cost in expense ratio (~0.1%)
                    },
                    "gold_etf": 0.0005,             # 0.05% for gold ETF transactions
                    "debt_funds": 0.0003            # 0.03% for debt fund transactions
                },
                "exit_loads": {
                    "equity_funds": {
                        "under_30_days": 0.01,     # 1% exit load if redeemed within 30 days
                        "under_90_days": 0.005,    # 0.5% exit load if redeemed within 90 days
                        "under_180_days": 0.0025,  # 0.25% exit load if redeemed within 180 days
                        "above_180_days": 0.0      # No exit load after 180 days
                    },
                    "debt_funds": {
                        "under_7_days": 0.0025,    # 0.25% exit load if redeemed within 7 days
                        "above_7_days": 0.0        # No exit load after 7 days
                    },
                    "liquid_funds": {
                        "under_7_days": 0.001,     # 0.1% exit load if redeemed within 7 days
                        "above_7_days": 0.0        # No exit load after 7 days
                    }
                }
            },
            "performance_factors": {
                "indian_market_volatility": {
                    "equity": {
                        "nifty50_annual_sd": 0.18,     # 18% standard deviation for Nifty 50
                        "midcap_annual_sd": 0.22,      # 22% standard deviation for midcap
                        "smallcap_annual_sd": 0.25     # 25% standard deviation for smallcap
                    },
                    "debt": {
                        "g_sec_annual_sd": 0.05,       # 5% standard deviation for govt securities
                        "corporate_bond_annual_sd": 0.08  # 8% standard deviation for corporate bonds
                    },
                    "gold": {
                        "annual_sd": 0.15              # 15% standard deviation for gold
                    }
                },
                "market_scenarios": {
                    "bull": {
                        "equity_return": 0.20,          # 20% annual return in bull market
                        "debt_return": 0.08,            # 8% annual return for debt in bull market
                        "gold_return": 0.05,            # 5% annual return for gold in bull market
                        "probability": 0.25             # 25% probability of bull market
                    },
                    "bear": {
                        "equity_return": -0.15,         # -15% annual return in bear market
                        "debt_return": 0.06,            # 6% annual return for debt in bear market
                        "gold_return": 0.12,            # 12% annual return for gold in bear market
                        "probability": 0.25             # 25% probability of bear market
                    },
                    "sideways": {
                        "equity_return": 0.08,          # 8% annual return in sideways market
                        "debt_return": 0.07,            # 7% annual return for debt in sideways market
                        "gold_return": 0.07,            # 7% annual return for gold in sideways market
                        "probability": 0.50             # 50% probability of sideways market
                    }
                }
            }
        }
        
        # Load rebalancing-specific parameters
        self._load_rebalancing_parameters()
        
    def _load_rebalancing_parameters(self):
        """Load rebalancing-specific parameters from service"""
        if self.param_service:
            try:
                # Load rebalancing frequency
                frequency = self.param_service.get_parameter('rebalancing_frequency')
                if frequency:
                    self.rebalancing_params['rebalancing_frequency'].update(frequency)
                
                # Load drift thresholds
                thresholds = self.param_service.get_parameter('drift_thresholds')
                if thresholds:
                    self.rebalancing_params['drift_thresholds'].update(thresholds)
                
                # Load Indian market factors
                market_factors = self.param_service.get_parameter('indian_market_factors')
                if market_factors:
                    self.rebalancing_params['indian_market_factors'].update(market_factors)
                
                # Load tax efficiency parameters
                tax_efficiency = self.param_service.get_parameter('tax_efficiency')
                if tax_efficiency:
                    self.rebalancing_params['tax_efficiency'].update(tax_efficiency)
                
                # Load cost efficiency parameters
                cost_efficiency = self.param_service.get_parameter('cost_efficiency')
                if cost_efficiency:
                    self.rebalancing_params['cost_efficiency'].update(cost_efficiency)
                
                # Load performance factors
                performance_factors = self.param_service.get_parameter('rebalancing_performance_factors')
                if performance_factors:
                    self.rebalancing_params['performance_factors'].update(performance_factors)
                
            except Exception as e:
                logger.error(f"Error loading rebalancing parameters: {e}")
                # Continue with default parameters
    
    def design_rebalancing_schedule(self, goal, profile):
        """
        Determine optimal rebalancing frequency based on goal and profile characteristics.
        
        Args:
            goal: Goal object with details about the financial goal
            profile: Profile object with user's financial profile
            
        Returns:
            Dictionary with recommended rebalancing schedule
        """
        # Extract relevant information
        goal_type = goal.get('goal_type', 'general')
        time_horizon = goal.get('time_horizon', 10)
        risk_profile = profile.get('risk_profile', 'moderate')
        portfolio_size = profile.get('portfolio_value', 1000000)
        liquidity_needs = profile.get('liquidity_needs', {})
        
        # Get base frequency from risk profile
        if risk_profile.lower() in self.rebalancing_params['rebalancing_frequency']:
            base_frequency = self.rebalancing_params['rebalancing_frequency'][risk_profile.lower()]
        else:
            base_frequency = self.rebalancing_params['rebalancing_frequency']['default']
        
        # Adjust for goal type and timeline
        if goal_type == 'retirement' and time_horizon > 15:
            # Long-term retirement goals can use less frequent rebalancing
            adjusted_frequency = 'annual'
            frequency_rationale = "Long-term retirement goal benefits from lower rebalancing costs"
        elif goal_type in ['education', 'home_purchase'] and time_horizon < 5:
            # Shorter-term important goals require closer monitoring
            adjusted_frequency = 'quarterly'
            frequency_rationale = f"Critical {goal_type} goal with shorter timeline requires closer monitoring"
        elif goal_type == 'emergency_fund':
            # Emergency funds need minimal rebalancing
            adjusted_frequency = 'annual'
            frequency_rationale = "Emergency funds require minimal rebalancing due to conservative allocation"
        else:
            # Default to risk profile based frequency
            adjusted_frequency = base_frequency
            frequency_rationale = f"Standard {base_frequency} rebalancing based on {risk_profile} risk profile"
        
        # Adjust for portfolio size
        if portfolio_size < 500000:  # Under 5 lakhs
            # Smaller portfolios should rebalance less frequently to minimize costs
            if adjusted_frequency == 'quarterly':
                adjusted_frequency = 'semi_annual'
            elif adjusted_frequency == 'semi_annual':
                adjusted_frequency = 'annual'
            
            size_rationale = "Less frequent rebalancing to minimize transaction costs for smaller portfolio"
        elif portfolio_size > 5000000:  # Over 50 lakhs
            # Larger portfolios can handle more frequent rebalancing
            if adjusted_frequency == 'annual':
                adjusted_frequency = 'semi_annual'
            
            size_rationale = "Larger portfolio allows for more frequent rebalancing for optimal allocation"
        else:
            size_rationale = "Portfolio size supports standard rebalancing frequency"
        
        # Adjust for liquidity needs
        if liquidity_needs:
            near_term_liquidity = liquidity_needs.get('near_term', 0)
            liquidity_timeline = liquidity_needs.get('timeline_months', 12)
            
            if near_term_liquidity > 0.2 * portfolio_size and liquidity_timeline < 6:
                # Significant near-term liquidity needs require closer monitoring
                if adjusted_frequency == 'annual':
                    adjusted_frequency = 'semi_annual'
                
                liquidity_rationale = "Significant near-term liquidity needs require more frequent monitoring"
            else:
                liquidity_rationale = "Liquidity needs do not impact rebalancing frequency"
        else:
            liquidity_rationale = "No specific liquidity needs identified"
        
        # Adjust for Indian market volatility
        market_volatility = profile.get('market_volatility', 'normal')
        if market_volatility == 'high':
            # Higher volatility suggests more frequent rebalancing to capture opportunities
            if adjusted_frequency == 'annual':
                adjusted_frequency = 'semi_annual'
            
            volatility_rationale = "Higher market volatility suggests more frequent rebalancing to manage risk"
        else:
            volatility_rationale = f"{market_volatility.capitalize()} market volatility supports standard approach"
        
        # Map frequency to months
        frequency_months = {
            'monthly': 1,
            'quarterly': 3,
            'semi_annual': 6,
            'annual': 12
        }
        
        # Consider Indian tax year (April-March)
        current_month = datetime.now().month
        months_to_tax_year_end = (3 - current_month) % 12 + 1  # Months until March 31
        
        tax_year_adjustment = ""
        if months_to_tax_year_end <= 2:
            tax_year_adjustment = "Consider tax-loss harvesting before tax year end (March 31)"
        
        return {
            'recommended_frequency': adjusted_frequency,
            'months_between_rebalancing': frequency_months.get(adjusted_frequency, 12),
            'next_scheduled_rebalancing': (datetime.now().replace(day=1) + 
                                         pd.DateOffset(months=frequency_months.get(adjusted_frequency, 12))).strftime('%Y-%m-%d'),
            'rationale': {
                'goal_based': frequency_rationale,
                'portfolio_size': size_rationale,
                'liquidity': liquidity_rationale,
                'market_volatility': volatility_rationale,
                'tax_considerations': f"Indian tax year timing: {tax_year_adjustment}" if tax_year_adjustment else "No specific tax year timing considerations"
            }
        }
    
    def calculate_drift_thresholds(self, allocation):
        """
        Establish percentage-based rebalancing triggers for different asset classes.
        
        Args:
            allocation: Dictionary with target asset allocation percentages
            
        Returns:
            Dictionary with drift thresholds for each asset class
        """
        # Base thresholds from parameters
        base_thresholds = self.rebalancing_params['drift_thresholds']
        
        # Calculate absolute thresholds
        thresholds = {}
        for asset, target in allocation.items():
            # Minimum threshold regardless of allocation
            min_threshold = 0.01  # 1%
            
            # Get base threshold for this asset class
            if asset in base_thresholds:
                base = base_thresholds[asset]
            else:
                # Default to equity threshold if asset type not specified
                base = base_thresholds.get('equity', 0.05)
            
            # For very small allocations, use a fixed minimum threshold
            # For larger allocations, use percentage of allocation
            if target < 0.1:  # Less than 10% allocation
                thresholds[asset] = max(min_threshold, base * 0.5)
            else:
                thresholds[asset] = base
            
            # Adjust for Indian market factors
            if asset == 'equity':
                # Indian equity markets can be more volatile
                # Add a small buffer to reduce excessive trading
                thresholds[asset] = min(thresholds[asset] * 1.1, 0.06)  # Cap at 6%
            elif asset == 'gold':
                # Gold is important in Indian portfolios for cultural reasons
                # and often held for longer periods, so use conservative threshold
                thresholds[asset] = min(base_thresholds['gold'], 0.02)  # Max 2%
        
        # Create bands for each asset class
        bands = {}
        for asset, threshold in thresholds.items():
            target = allocation.get(asset, 0)
            
            # Upper and lower bands
            upper_band = target + threshold
            lower_band = max(0, target - threshold)  # Ensure non-negative
            
            bands[asset] = {
                'target': target,
                'threshold': threshold,
                'upper_band': upper_band,
                'lower_band': lower_band,
                'rebalance_when': f"< {lower_band:.2f} or > {upper_band:.2f}"
            }
        
        return {
            'threshold_rationale': "Asset-specific thresholds balancing risk management and transaction costs",
            'asset_bands': bands,
            'implementation_note': "Implement threshold-based rebalancing with calendar minimums"
        }
    
    def analyze_tax_implications(self, portfolio, target_allocation):
        """
        Analyze tax implications of rebalancing for Indian investors.
        
        Args:
            portfolio: Dictionary with current portfolio holdings and purchase dates
            target_allocation: Dictionary with target allocation percentages
            
        Returns:
            Dictionary with tax-efficient rebalancing strategy
        """
        # Extract tax parameters
        equity_lt_threshold = self.rebalancing_params['tax_efficiency']['equity_lt_threshold']
        debt_lt_threshold = self.rebalancing_params['tax_efficiency']['debt_lt_threshold']
        stcg_equity_rate = self.rebalancing_params['tax_efficiency']['stcg_equity_rate']
        ltcg_equity_rate = self.rebalancing_params['tax_efficiency']['ltcg_equity_rate']
        
        # Analyze each holding for tax status
        tax_status = {}
        for asset, details in portfolio.items():
            if 'purchase_date' in details:
                purchase_date = details['purchase_date']
                holding_months = (datetime.now() - datetime.strptime(purchase_date, '%Y-%m-%d')).days // 30
                
                if 'equity' in asset.lower():
                    # Equity taxation
                    if holding_months >= equity_lt_threshold:
                        tax_status[asset] = {
                            'status': 'long_term',
                            'rate': ltcg_equity_rate,
                            'tax_efficient': True
                        }
                    else:
                        tax_status[asset] = {
                            'status': 'short_term',
                            'rate': stcg_equity_rate,
                            'tax_efficient': False,
                            'months_to_lt': equity_lt_threshold - holding_months
                        }
                else:
                    # Debt/other taxation
                    if holding_months >= debt_lt_threshold:
                        tax_status[asset] = {
                            'status': 'long_term',
                            'rate': self.rebalancing_params['tax_efficiency']['ltcg_debt_rate'],
                            'tax_efficient': True,
                            'indexation_benefit': True
                        }
                    else:
                        tax_status[asset] = {
                            'status': 'short_term',
                            'rate': self.rebalancing_params['tax_efficiency']['stcg_debt_rate'],
                            'tax_efficient': False,
                            'months_to_lt': debt_lt_threshold - holding_months
                        }
        
        # Calculate current vs target allocation
        current_allocation = {asset: details.get('percent', 0) for asset, details in portfolio.items()}
        
        # Identify assets needing rebalancing
        rebalance_needed = {}
        for asset in set(list(current_allocation.keys()) + list(target_allocation.keys())):
            current = current_allocation.get(asset, 0)
            target = target_allocation.get(asset, 0)
            
            if abs(current - target) > 0.02:  # More than 2% difference
                rebalance_needed[asset] = {
                    'current': current,
                    'target': target,
                    'difference': target - current,
                    'action': 'buy' if target > current else 'sell'
                }
        
        # Tax-efficient rebalancing strategy
        tax_efficient_strategy = {
            'tax_year_timing': {
                'current_month': datetime.now().month,
                'months_to_tax_year_end': (3 - datetime.now().month) % 12 + 1,
                'consideration': "Consider tax-loss harvesting before March 31 fiscal year end"
            },
            'tax_efficient_actions': []
        }
        
        # Generate tax-efficient actions
        for asset, rebalance in rebalance_needed.items():
            if rebalance['action'] == 'sell' and asset in tax_status:
                if not tax_status[asset].get('tax_efficient', False):
                    # Not tax efficient to sell this asset now
                    months_to_lt = tax_status[asset].get('months_to_lt', 0)
                    if months_to_lt <= 3:
                        tax_efficient_strategy['tax_efficient_actions'].append({
                            'asset': asset,
                            'action': 'delay_sale',
                            'rationale': f"Wait {months_to_lt} months for long-term capital gains treatment"
                        })
                    else:
                        tax_efficient_strategy['tax_efficient_actions'].append({
                            'asset': asset,
                            'action': 'partial_sale',
                            'rationale': "Sell partially now and remainder after tax year end or LTCG qualification"
                        })
                else:
                    tax_efficient_strategy['tax_efficient_actions'].append({
                        'asset': asset,
                        'action': 'proceed',
                        'rationale': "Already qualifies for favorable tax treatment"
                    })
            elif rebalance['action'] == 'buy':
                tax_efficient_strategy['tax_efficient_actions'].append({
                    'asset': asset,
                    'action': 'proceed',
                    'rationale': "Buying does not trigger immediate tax consequences"
                })
        
        # Tax-efficiency best practices
        tax_efficient_strategy['best_practices'] = [
            "Harvest tax losses before fiscal year end (March 31)",
            "Prioritize selling assets already in LTCG territory",
            "Utilize new contributions for rebalancing when possible",
            "Consider STT (Securities Transaction Tax) impact for frequent equity trades",
            "For debt funds, consider indexation benefits after 3 years"
        ]
        
        return tax_efficient_strategy
    
    def estimate_rebalancing_costs(self, allocation, portfolio_value, rebalancing_frequency, broker_type="discount_broker", 
                             holding_period_months=None, tax_bracket="medium"):
        """
        Calculate transaction costs and tax implications for rebalancing.
        
        Args:
            allocation: Dictionary with current and target asset allocations
            portfolio_value: Total portfolio value in INR
            rebalancing_frequency: How often rebalancing is performed
            broker_type: Type of broker used ("discount_broker" or "full_service")
            holding_period_months: Dictionary of asset classes with holding periods
            tax_bracket: Tax bracket of the investor
            
        Returns:
            Dictionary with detailed cost analysis
        """
        if not holding_period_months:
            # Default holding periods if not specified
            holding_period_months = {
                "equity": 24,  # 2 years average holding
                "debt": 36,    # 3 years average holding
                "gold": 36,    # 3 years average holding
                "cash": 6,     # 6 months for cash instruments
                "alternatives": 48  # 4 years for alternatives
            }
        
        # Get parameters
        brokerage_rates = self.rebalancing_params['cost_efficiency']['brokerage_fees']
        tax_parameters = self.rebalancing_params['tax_efficiency']
        exit_loads = self.rebalancing_params['cost_efficiency']['exit_loads']
        
        # Calculate frequency multiplier (how many times per year)
        frequency_multipliers = {
            "monthly": 12,
            "quarterly": 4,
            "semi_annual": 2,
            "annual": 1
        }
        frequency_multiplier = frequency_multipliers.get(rebalancing_frequency, 1)
        
        # Initialize cost structure
        costs = {
            "brokerage_fees": 0,
            "stt_charges": 0,
            "stamp_duty": 0,
            "exit_loads": 0,
            "tax_implications": {
                "stcg": 0,
                "ltcg": 0
            },
            "total_annual_cost": 0,
            "total_percent_drag": 0,
            "per_rebalancing_cycle": {},
            "breakdown_by_asset": {}
        }
        
        # Calculate deviation from target that would trigger rebalancing
        current_allocation = allocation.get('current', {})
        target_allocation = allocation.get('target', {})
        
        # Calculate potential transactions required per rebalancing cycle
        transactions_per_cycle = {}
        total_rebalancing_amount = 0
        
        for asset, target in target_allocation.items():
            current = current_allocation.get(asset, 0)
            threshold = self.rebalancing_params['drift_thresholds'].get(asset, 0.05)
            
            # Check if rebalancing would be needed
            if abs(current - target) > threshold:
                # Calculate transaction value for this asset
                transaction_amount = abs(current - target) * portfolio_value
                total_rebalancing_amount += transaction_amount
                
                transactions_per_cycle[asset] = {
                    "current_allocation": current,
                    "target_allocation": target,
                    "deviation": current - target,
                    "threshold": threshold,
                    "transaction_amount": transaction_amount,
                    "action": "sell" if current > target else "buy"
                }
        
        # Calculate costs for each transaction
        for asset, transaction in transactions_per_cycle.items():
            amount = transaction["transaction_amount"]
            action = transaction["action"]
            
            # Initialize asset breakdown
            costs["breakdown_by_asset"][asset] = {
                "action": action,
                "amount": amount,
                "brokerage": 0,
                "stt": 0,
                "stamp_duty": 0,
                "exit_load": 0,
                "tax": 0,
                "total": 0
            }
            
            # 1. Brokerage fees
            brokerage_rate = 0
            if "equity" in asset.lower():
                brokerage_rate = brokerage_rates["equity"][broker_type]
            elif "mutual" in asset.lower() or "fund" in asset.lower():
                if "direct" in asset.lower():
                    brokerage_rate = brokerage_rates["mutual_funds"]["direct_plans"]
                else:
                    brokerage_rate = brokerage_rates["mutual_funds"]["regular_plans"]
            elif "gold" in asset.lower():
                brokerage_rate = brokerage_rates["gold_etf"]
            elif "debt" in asset.lower():
                brokerage_rate = brokerage_rates["debt_funds"]
            else:
                # Default to equity rate if unknown
                brokerage_rate = brokerage_rates["equity"][broker_type]
            
            brokerage_fee = amount * brokerage_rate
            if brokerage_fee < brokerage_rates["equity"]["minimum_fee"] and "equity" in asset.lower():
                brokerage_fee = brokerage_rates["equity"]["minimum_fee"]
            
            costs["breakdown_by_asset"][asset]["brokerage"] = brokerage_fee
            costs["brokerage_fees"] += brokerage_fee
            
            # 2. Securities Transaction Tax (only for equity and selling)
            if "equity" in asset.lower() and action == "sell":
                stt = amount * tax_parameters["stt_rate"]
                costs["breakdown_by_asset"][asset]["stt"] = stt
                costs["stt_charges"] += stt
            
            # 3. Stamp duty (for all buy transactions)
            if action == "buy":
                stamp_duty = amount * tax_parameters["stamp_duty_rate"]
                costs["breakdown_by_asset"][asset]["stamp_duty"] = stamp_duty
                costs["stamp_duty"] += stamp_duty
            
            # 4. Exit loads (only for sell transactions)
            if action == "sell":
                holding_period = holding_period_months.get(asset, 24)
                
                if "equity" in asset.lower() or "fund" in asset.lower():
                    if holding_period < 1:  # Less than 30 days
                        exit_load_rate = exit_loads["equity_funds"]["under_30_days"]
                    elif holding_period < 3:  # Less than 90 days
                        exit_load_rate = exit_loads["equity_funds"]["under_90_days"]
                    elif holding_period < 6:  # Less than 180 days
                        exit_load_rate = exit_loads["equity_funds"]["under_180_days"]
                    else:
                        exit_load_rate = exit_loads["equity_funds"]["above_180_days"]
                elif "debt" in asset.lower():
                    if holding_period < 0.25:  # Less than 7 days
                        exit_load_rate = exit_loads["debt_funds"]["under_7_days"]
                    else:
                        exit_load_rate = exit_loads["debt_funds"]["above_7_days"]
                elif "liquid" in asset.lower() or "cash" in asset.lower():
                    if holding_period < 0.25:  # Less than 7 days
                        exit_load_rate = exit_loads["liquid_funds"]["under_7_days"]
                    else:
                        exit_load_rate = exit_loads["liquid_funds"]["above_7_days"]
                else:
                    exit_load_rate = 0
                
                exit_load = amount * exit_load_rate
                costs["breakdown_by_asset"][asset]["exit_load"] = exit_load
                costs["exit_loads"] += exit_load
            
            # 5. Tax implications (only for sell transactions)
            if action == "sell":
                holding_period = holding_period_months.get(asset, 24)
                
                if "equity" in asset.lower():
                    # Equity taxation
                    if holding_period >= tax_parameters["equity_lt_threshold"]:
                        # LTCG on equity (10% above 1L exemption)
                        # Simplified assumption: Annually, gains ~2x the rebalancing amount * expected return
                        annual_gains = amount * self.params["expected_returns"]["equity"]
                        taxable_gain = max(0, annual_gains - tax_parameters["ltcg_exemption_limit"])
                        tax_amount = taxable_gain * tax_parameters["ltcg_equity_rate"]
                        costs["tax_implications"]["ltcg"] += tax_amount
                    else:
                        # STCG on equity (15%)
                        annual_gains = amount * self.params["expected_returns"]["equity"]
                        tax_amount = annual_gains * tax_parameters["stcg_equity_rate"]
                        costs["tax_implications"]["stcg"] += tax_amount
                else:
                    # Debt/other taxation
                    if holding_period >= tax_parameters["debt_lt_threshold"]:
                        # LTCG on debt (20% with indexation)
                        # Simplified indexation: reduces effective gains by ~inflation rate over 3 years
                        annual_gains = amount * self.params["expected_returns"]["debt"]
                        indexed_gains = annual_gains * (1 - self.params["inflation_rate"] * 3)
                        tax_amount = max(0, indexed_gains) * tax_parameters["ltcg_debt_rate"]
                        costs["tax_implications"]["ltcg"] += tax_amount
                    else:
                        # STCG on debt (as per income tax slab)
                        annual_gains = amount * self.params["expected_returns"]["debt"]
                        tax_amount = annual_gains * tax_parameters["stcg_debt_rate"]
                        costs["tax_implications"]["stcg"] += tax_amount
                
                costs["breakdown_by_asset"][asset]["tax"] = tax_amount
            
            # Calculate total cost for this asset
            asset_total = costs["breakdown_by_asset"][asset]["brokerage"] + \
                         costs["breakdown_by_asset"][asset]["stt"] + \
                         costs["breakdown_by_asset"][asset]["stamp_duty"] + \
                         costs["breakdown_by_asset"][asset]["exit_load"] + \
                         costs["breakdown_by_asset"][asset]["tax"]
            
            costs["breakdown_by_asset"][asset]["total"] = asset_total
        
        # Calculate per cycle costs
        total_direct_costs = costs["brokerage_fees"] + costs["stt_charges"] + costs["stamp_duty"] + costs["exit_loads"]
        total_tax_costs = costs["tax_implications"]["stcg"] + costs["tax_implications"]["ltcg"]
        cycle_total = total_direct_costs + total_tax_costs
        
        costs["per_rebalancing_cycle"] = {
            "direct_costs": total_direct_costs,
            "tax_costs": total_tax_costs,
            "total": cycle_total,
            "as_percentage_of_rebalanced_amount": round((cycle_total / total_rebalancing_amount * 100), 4) if total_rebalancing_amount > 0 else 0
        }
        
        # Calculate annual costs based on frequency
        costs["total_annual_cost"] = cycle_total * frequency_multiplier
        costs["total_percent_drag"] = round((costs["total_annual_cost"] / portfolio_value * 100), 4)
        
        # Add recommendations based on cost analysis
        if costs["total_percent_drag"] > 0.5:
            costs["recommendation"] = "High cost impact - consider less frequent rebalancing"
        elif costs["total_percent_drag"] > 0.25:
            costs["recommendation"] = "Moderate cost impact - current rebalancing frequency is reasonable"
        else:
            costs["recommendation"] = "Low cost impact - current rebalancing approach is cost-efficient"
        
        return costs
    
    def simulate_rebalancing_impact(self, portfolio_data, market_scenarios=None, simulation_years=5, 
                                    rebalancing_strategies=None):
        """
        Model the effect of different rebalancing strategies on portfolio returns.
        
        Args:
            portfolio_data: Dictionary with portfolio composition and value
            market_scenarios: Optional custom market scenarios (defaults to parameters)
            simulation_years: Number of years to run simulation
            rebalancing_strategies: List of rebalancing strategies to compare
            
        Returns:
            Dictionary with simulation results comparing strategies
        """
        # Extract portfolio data
        current_allocation = portfolio_data.get('current_allocation', {})
        target_allocation = portfolio_data.get('target_allocation', {})
        portfolio_value = portfolio_data.get('portfolio_value', 1000000)
        
        # Default to parameter-defined scenarios if not provided
        if not market_scenarios:
            market_scenarios = self.rebalancing_params['performance_factors']['market_scenarios']
        
        # Default rebalancing strategies if not provided
        if not rebalancing_strategies:
            rebalancing_strategies = [
                {"name": "no_rebalancing", "description": "Never rebalance"},
                {"name": "annual", "description": "Rebalance once per year"},
                {"name": "quarterly", "description": "Rebalance every quarter"},
                {"name": "threshold_only", "description": "Rebalance only when thresholds exceeded", 
                 "thresholds": self.rebalancing_params['drift_thresholds']}
            ]
        
        # Prepare results structure
        results = {
            "simulation_params": {
                "years": simulation_years,
                "initial_portfolio_value": portfolio_value,
                "initial_allocation": current_allocation,
                "target_allocation": target_allocation
            },
            "market_scenarios": {},
            "strategy_comparison": {},
            "rebalancing_frequency_impact": {},
            "threshold_sensitivity": {}
        }
        
        # Function to simulate a single path with given returns and strategy
        def simulate_path(initial_value, initial_allocation, target_allocation, annual_returns, 
                          strategy, simulation_years):
            
            # Initialize portfolio
            current_value = initial_value
            current_alloc = initial_allocation.copy()
            timeline = []
            rebalancing_events = 0
            total_rebalancing_costs = 0
            
            # Determine rebalancing intervals based on strategy
            intervals = 0
            if strategy['name'] == 'annual':
                intervals = 1
            elif strategy['name'] == 'semi_annual':
                intervals = 2
            elif strategy['name'] == 'quarterly':
                intervals = 4
            elif strategy['name'] == 'monthly':
                intervals = 12
                
            # For threshold-based, we'll check every month
            threshold_based = strategy['name'] == 'threshold_only'
            thresholds = strategy.get('thresholds', self.rebalancing_params['drift_thresholds'])
            
            # Simulate each month
            for month in range(1, simulation_years * 12 + 1):
                month_data = {"month": month, "portfolio_value": current_value, "allocation": {}}
                
                # Calculate growth for each asset class for this month
                for asset, alloc in current_alloc.items():
                    monthly_return = annual_returns.get(asset, 0) / 12
                    asset_value = current_value * alloc
                    new_asset_value = asset_value * (1 + monthly_return)
                    month_data["allocation"][asset] = {
                        "percentage": alloc,
                        "value": new_asset_value
                    }
                
                # Recalculate portfolio value and allocation
                new_portfolio_value = sum(data["value"] for asset, data in month_data["allocation"].items())
                
                for asset in month_data["allocation"]:
                    month_data["allocation"][asset]["percentage"] = month_data["allocation"][asset]["value"] / new_portfolio_value
                
                # Update current allocation
                current_alloc = {asset: data["percentage"] for asset, data in month_data["allocation"].items()}
                current_value = new_portfolio_value
                
                # Check if rebalancing is needed
                rebalance = False
                
                # Time-based rebalancing
                if intervals > 0 and month % (12 // intervals) == 0:
                    rebalance = True
                
                # Threshold-based rebalancing
                elif threshold_based:
                    for asset, target in target_allocation.items():
                        if asset in current_alloc:
                            deviation = abs(current_alloc[asset] - target)
                            asset_threshold = thresholds.get(asset, 0.05)
                            if deviation > asset_threshold:
                                rebalance = True
                                break
                
                # Perform rebalancing if needed
                if rebalance and strategy['name'] != 'no_rebalancing':
                    rebalancing_events += 1
                    month_data["rebalancing"] = True
                    
                    # Calculate rebalancing costs
                    rebalancing_allocation = {
                        "current": current_alloc,
                        "target": target_allocation
                    }
                    
                    cost_analysis = self.estimate_rebalancing_costs(
                        rebalancing_allocation, 
                        current_value,
                        "annual"  # Cost per event regardless of frequency
                    )
                    
                    rebalancing_cost = cost_analysis["per_rebalancing_cycle"]["total"]
                    total_rebalancing_costs += rebalancing_cost
                    
                    # Apply rebalancing (simplified - direct to target)
                    current_alloc = target_allocation.copy()
                    
                    # Deduct costs
                    current_value -= rebalancing_cost
                    month_data["rebalancing_cost"] = rebalancing_cost
                    month_data["portfolio_value_after_costs"] = current_value
                else:
                    month_data["rebalancing"] = False
                
                timeline.append(month_data)
            
            # Calculate final results
            final_value = timeline[-1]["portfolio_value"]
            cagr = (final_value / initial_value) ** (1 / simulation_years) - 1
            
            # Calculate risk metrics
            monthly_returns = []
            for i in range(1, len(timeline)):
                prev_value = timeline[i-1]["portfolio_value"]
                curr_value = timeline[i]["portfolio_value"]
                monthly_returns.append((curr_value - prev_value) / prev_value)
            
            volatility = np.std(monthly_returns) * np.sqrt(12)  # Annualized
            sharpe = (cagr - 0.05) / volatility if volatility > 0 else 0  # Assuming 5% risk-free rate
            
            path_results = {
                "initial_value": initial_value,
                "final_value": final_value,
                "absolute_return": final_value - initial_value,
                "percentage_return": (final_value - initial_value) / initial_value * 100,
                "cagr": cagr * 100,
                "volatility": volatility * 100,
                "sharpe_ratio": sharpe,
                "rebalancing_events": rebalancing_events,
                "total_rebalancing_costs": total_rebalancing_costs,
                "cost_drag": total_rebalancing_costs / initial_value * 100 / simulation_years,
                "final_allocation": current_alloc,
                "timeline": timeline
            }
            
            return path_results
        
        # Simulate each market scenario
        for scenario_name, scenario_params in market_scenarios.items():
            # Extract returns for this scenario
            annual_returns = {
                "equity": scenario_params.get("equity_return", 0.10),
                "debt": scenario_params.get("debt_return", 0.06),
                "gold": scenario_params.get("gold_return", 0.07),
                "cash": scenario_params.get("cash_return", 0.04),
                "alternatives": scenario_params.get("alternatives_return", 0.09)
            }
            
            # Compare strategies for this scenario
            strategy_results = {}
            
            for strategy in rebalancing_strategies:
                path_result = simulate_path(
                    portfolio_value,
                    current_allocation,
                    target_allocation,
                    annual_returns,
                    strategy,
                    simulation_years
                )
                strategy_results[strategy["name"]] = path_result
            
            results["market_scenarios"][scenario_name] = {
                "parameters": scenario_params,
                "strategy_results": strategy_results
            }
        
        # Aggregate results across scenarios by strategy
        for strategy in rebalancing_strategies:
            strategy_name = strategy["name"]
            aggregated_results = {
                "average_cagr": 0,
                "average_volatility": 0,
                "average_sharpe": 0,
                "average_cost_drag": 0,
                "average_rebalancing_events": 0,
                "scenario_performance": {}
            }
            
            for scenario_name, scenario_data in results["market_scenarios"].items():
                if strategy_name in scenario_data["strategy_results"]:
                    strategy_result = scenario_data["strategy_results"][strategy_name]
                    
                    # Weight by scenario probability
                    scenario_probability = market_scenarios[scenario_name].get("probability", 1/len(market_scenarios))
                    
                    aggregated_results["average_cagr"] += strategy_result["cagr"] * scenario_probability
                    aggregated_results["average_volatility"] += strategy_result["volatility"] * scenario_probability
                    aggregated_results["average_sharpe"] += strategy_result["sharpe_ratio"] * scenario_probability
                    aggregated_results["average_cost_drag"] += strategy_result["cost_drag"] * scenario_probability
                    aggregated_results["average_rebalancing_events"] += strategy_result["rebalancing_events"] * scenario_probability
                    
                    aggregated_results["scenario_performance"][scenario_name] = {
                        "cagr": strategy_result["cagr"],
                        "volatility": strategy_result["volatility"],
                        "sharpe_ratio": strategy_result["sharpe_ratio"]
                    }
            
            results["strategy_comparison"][strategy_name] = aggregated_results
        
        # Identify optimal strategy
        optimal_strategy = max(results["strategy_comparison"].items(), 
                             key=lambda x: x[1]["average_sharpe"])
        
        results["recommendations"] = {
            "optimal_strategy": optimal_strategy[0],
            "optimal_strategy_sharpe": optimal_strategy[1]["average_sharpe"],
            "performance_benefit_over_no_rebalancing": 0,
            "cost_considerations": ""
        }
        
        # Calculate benefit over no rebalancing
        if "no_rebalancing" in results["strategy_comparison"] and optimal_strategy[0] != "no_rebalancing":
            no_rebal_sharpe = results["strategy_comparison"]["no_rebalancing"]["average_sharpe"]
            optimal_sharpe = optimal_strategy[1]["average_sharpe"]
            results["recommendations"]["performance_benefit_over_no_rebalancing"] = optimal_sharpe - no_rebal_sharpe
        
        # Add cost considerations
        avg_cost_drag = optimal_strategy[1]["average_cost_drag"]
        if avg_cost_drag > 0.5:
            results["recommendations"]["cost_considerations"] = "High rebalancing costs - consider less frequent rebalancing"
        elif avg_cost_drag > 0.25:
            results["recommendations"]["cost_considerations"] = "Moderate rebalancing costs - current frequency is reasonable"
        else:
            results["recommendations"]["cost_considerations"] = "Low rebalancing costs - current approach is cost-efficient"
        
        # Add specific observation for Indian market conditions
        india_specific_findings = []
        
        if "bear" in results["market_scenarios"]:
            bear_data = results["market_scenarios"]["bear"]["strategy_results"]
            best_bear_strategy = max(bear_data.items(), key=lambda x: x[1]["sharpe_ratio"])[0]
            india_specific_findings.append(f"During bear markets, {best_bear_strategy} rebalancing performs best")
        
        if "bull" in results["market_scenarios"]:
            bull_data = results["market_scenarios"]["bull"]["strategy_results"]
            best_bull_strategy = max(bull_data.items(), key=lambda x: x[1]["sharpe_ratio"])[0]
            india_specific_findings.append(f"During bull markets, {best_bull_strategy} rebalancing performs best")
        
        # Add specific finding about gold's role in rebalancing (important in Indian portfolios)
        if "gold" in current_allocation and current_allocation["gold"] > 0.05:
            india_specific_findings.append("Gold allocation helps stabilize portfolio during market volatility, typical in Indian portfolios")
        
        results["recommendations"]["india_specific_findings"] = india_specific_findings
        
        return results
    
    def create_rebalancing_plan(self, goal_data, profile_data):
        """
        Create detailed rebalancing plan based on goal and profile data.
        
        Args:
            goal_data: Dictionary with goal details including target allocation
            profile_data: Dictionary with profile details including current portfolio
            
        Returns:
            Dictionary with comprehensive rebalancing plan
        """
        # Extract data
        current_portfolio = profile_data.get('portfolio', {})
        target_allocation = goal_data.get('target_allocation', {})
        risk_profile = profile_data.get('risk_profile', 'moderate')
        portfolio_value = profile_data.get('portfolio_value', 1000000)
        
        # Design rebalancing schedule
        rebalancing_schedule = self.design_rebalancing_schedule(goal_data, profile_data)
        
        # Calculate drift thresholds
        drift_thresholds = self.calculate_drift_thresholds(target_allocation)
        
        # Analyze tax implications
        tax_strategy = self.analyze_tax_implications(current_portfolio, target_allocation)
        
        # Estimate rebalancing costs
        allocation_data = {
            'current': {asset: details.get('percent', 0) for asset, details in current_portfolio.items()},
            'target': target_allocation
        }
        cost_analysis = self.estimate_rebalancing_costs(
            allocation_data, 
            portfolio_value,
            rebalancing_schedule['recommended_frequency']
        )
        
        # Simulate rebalancing impact
        portfolio_data = {
            'current_allocation': {asset: details.get('percent', 0) for asset, details in current_portfolio.items()},
            'target_allocation': target_allocation,
            'portfolio_value': portfolio_value
        }
        rebalancing_strategies = [
            {"name": "no_rebalancing", "description": "Never rebalance"},
            {"name": rebalancing_schedule['recommended_frequency'], 
             "description": f"Rebalance {rebalancing_schedule['recommended_frequency']}"},
            {"name": "threshold_only", "description": "Rebalance only when thresholds exceeded", 
             "thresholds": drift_thresholds['asset_bands']}
        ]
        simulation_results = self.simulate_rebalancing_impact(
            portfolio_data,
            rebalancing_strategies=rebalancing_strategies
        )
        
        # Create complete rebalancing plan
        rebalancing_plan = {
            'schedule': rebalancing_schedule,
            'drift_thresholds': drift_thresholds,
            'tax_strategy': tax_strategy,
            'cost_analysis': cost_analysis,
            'simulation_results': {
                'optimal_strategy': simulation_results['recommendations']['optimal_strategy'],
                'performance_metrics': simulation_results['strategy_comparison'][simulation_results['recommendations']['optimal_strategy']],
                'india_specific_findings': simulation_results['recommendations']['india_specific_findings']
            },
            'implementation_steps': [
                "1. Compare current allocation to target using defined thresholds",
                "2. Identify assets outside threshold bands requiring adjustment",
                "3. Check tax status of assets to be sold",
                "4. Determine tax-efficient selling sequence",
                "5. Execute trades while minimizing transaction costs",
                "6. Document new allocation and set next review date"
            ],
            'monitoring_plan': {
                'frequency': rebalancing_schedule['recommended_frequency'],
                'next_review_date': rebalancing_schedule['next_scheduled_rebalancing'],
                'automatic_triggers': "Review immediately if market moves more than 10% in either direction"
            }
        }
        
        return rebalancing_plan
    
    def generate_funding_strategy(self, goal_data):
        """
        Generate comprehensive rebalancing strategy.
        
        Args:
            goal_data: Dictionary with goal details including rebalancing info
            
        Returns:
            Dictionary with comprehensive rebalancing strategy
        """
        # Extract relevant data
        profile_data = goal_data.get('profile_data', {})
        target_allocation = goal_data.get('target_allocation', {})
        portfolio = profile_data.get('portfolio', {})
        
        # If this is a basic call without portfolio details, use base implementation
        if not portfolio and not target_allocation:
            return super().generate_funding_strategy(goal_data)
        
        # Create rebalancing plan
        rebalancing_plan = self.create_rebalancing_plan(goal_data, profile_data)
        
        # Construct the comprehensive strategy
        strategy = {
            'goal_type': 'portfolio_rebalancing',
            'target_allocation': target_allocation,
            'current_allocation': {asset: details.get('percent', 0) for asset, details in portfolio.items()},
            'rebalancing_plan': rebalancing_plan,
            'specific_advice': {
                'indian_market_considerations': [
                    "Consider fiscal year timing (April-March) for tax-efficient rebalancing",
                    "Gold allocation is culturally significant in Indian portfolios",
                    "Account for higher volatility in Indian equity markets",
                    "Monitor impact of monsoon season on certain sectors"
                ],
                'best_practices': [
                    "Use new contributions strategically to avoid selling when possible",
                    "Maintain discipline during market volatility",
                    "Review allocation after major life events",
                    "Combine rebalancing with tax planning at fiscal year end"
                ],
                'common_pitfalls': [
                    "Emotional decision-making during market downturns",
                    "Ignoring tax implications of frequent trading",
                    "Excessive trading leading to high costs",
                    "Neglecting international diversification"
                ]
            }
        }
        
        return strategy
        
    def schedule_strategy_review_points(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify strategic review points for portfolio rebalancing tailored to the Indian financial context.
        
        This method creates a comprehensive set of review triggers including:
        - Regular calendar-based review points
        - Indian fiscal year considerations (April-March)
        - Life event-based review triggers (now using centralized LifeEventRegistry)
        - Indian market event triggers
        
        Args:
            strategy: Existing rebalancing strategy dictionary
            
        Returns:
            Dictionary with review schedule and triggers
        """
        # Extract core strategy information
        goal_type = strategy.get('goal_type', 'general')
        rebalancing_schedule = strategy.get('rebalancing_schedule', {})
        base_frequency = rebalancing_schedule.get('recommended_frequency', 'annual')
        
        # Current date reference
        current_date = datetime.now()
        current_month = current_date.month
        
        # ---- Calendar-based review points ----
        
        # Calculate regular review dates based on rebalancing frequency
        frequency_months = {
            'monthly': 1,
            'quarterly': 3, 
            'semi_annual': 6,
            'annual': 12
        }
        
        months_interval = frequency_months.get(base_frequency, 12)
        regular_reviews = []
        
        # Generate next 3 regular review dates
        for i in range(1, 4):
            next_review = (current_date.replace(day=1) + 
                          pd.DateOffset(months=months_interval * i))
            regular_reviews.append({
                'type': 'regular',
                'date': next_review.strftime('%Y-%m-%d'),
                'description': f"Regular {base_frequency} portfolio review"
            })
            
        # ---- Indian fiscal year considerations ----
        
        # Tax year end (March 31st)
        next_tax_year_end = datetime(current_date.year + (1 if current_month > 3 else 0), 3, 31)
        tax_year_review = {
            'type': 'fiscal_event',
            'date': next_tax_year_end.strftime('%Y-%m-%d'),
            'description': "Indian tax year-end review (tax-loss harvesting opportunity)",
            'priority': 'high' if next_tax_year_end.month - current_month <= 3 else 'medium',
            'actions': [
                "Review capital gains/losses for tax optimization",
                "Consider tax-loss harvesting opportunities",
                "Evaluate Section 80C investments before year-end",
                "Review tax-advantaged allocations (ELSS, PPF, NPS)"
            ]
        }
        
        # Pre-budget review (typically January)
        next_budget_date = datetime(current_date.year + (1 if current_month > 1 else 0), 2, 1)
        budget_review = {
            'type': 'fiscal_event',
            'date': next_budget_date.strftime('%Y-%m-%d'),
            'description': "Pre-Budget review",
            'priority': 'medium',
            'actions': [
                "Position portfolio for potential tax policy changes",
                "Review sectors that may be impacted by budget announcements",
                "Prepare for potential changes in capital gains taxation"
            ]
        }
        
        # Post-budget review (typically February)
        post_budget_date = datetime(current_date.year + (1 if current_month > 2 else 0), 3, 1)
        post_budget_review = {
            'type': 'fiscal_event',
            'date': post_budget_date.strftime('%Y-%m-%d'),
            'description': "Post-Budget implementation review",
            'priority': 'medium',
            'actions': [
                "Adjust strategy based on budget announcements",
                "Implement changes required by tax policy modifications",
                "Revise sector allocations based on budget impact"
            ]
        }
        
        # ---- Life event review triggers ----
        # Now integrated with centralized LifeEventRegistry
        
        # Reference to the centralized life event system
        life_event_integration = {
            'registry_reference': 'models.life_event_registry.LifeEventRegistry',
            'integration_type': 'bidirectional',
            'subscription_method': {
                'primary': 'subscribe_to_profile_events', 
                'categories': ['FINANCIAL', 'FAMILY', 'CAREER', 'HOUSING'],
                'severities': ['HIGH', 'MEDIUM']
            },
            'notification_method': 'rebalancing_notification_callback',
            'impact_assessment_method': 'get_rebalancing_impacts'
        }
        
        # Fallback life event triggers (used if centralized registry is unavailable)
        life_event_triggers = [
            {
                'event': 'Income change',
                'description': "Significant change in income (±20%)",
                'actions': [
                    "Recalibrate monthly contribution strategy",
                    "Review risk capacity based on new income reality",
                    "Adjust emergency fund allocation if applicable"
                ],
                'registry_event_type': 'job_change'  # Mapping to registry event type
            },
            {
                'event': 'Family status change',
                'description': "Marriage, children, or dependent responsibilities",
                'actions': [
                    "Review goal prioritization",
                    "Assess insurance needs and coverage",
                    "Consider estate planning implications"
                ],
                'registry_event_types': ['marriage', 'birth_adoption', 'dependent_care']
            },
            {
                'event': 'Relocation',
                'description': "Change in city or country of residence",
                'actions': [
                    "Update housing-related goals",
                    "Adjust for cost of living differences",
                    "Review NRI taxation implications if applicable"
                ],
                'registry_event_types': ['relocation', 'nri_status_change']
            },
            {
                'event': 'Windfall',
                'description': "Inheritance, bonus, or ESOP liquidation",
                'actions': [
                    "Develop deployment strategy for lump sum",
                    "Review asset allocation with new portfolio size",
                    "Consider strategic debt reduction vs. investment"
                ],
                'registry_event_type': 'windfall'
            }
        ]
        
        # ---- Indian market event triggers ----
        
        market_event_triggers = [
            {
                'event': 'RBI policy changes',
                'description': "Changes in interest rates or monetary policy",
                'threshold': "±0.25% change in repo rate",
                'actions': [
                    "Review fixed income duration strategy",
                    "Assess impact on debt portfolio components",
                    "Evaluate sector exposures sensitive to interest rates",
                    "Consider impact on home loan and other debt strategies"
                ]
            },
            {
                'event': 'Significant market correction',
                'description': "Nifty or Sensex correction",
                'threshold': "10% market decline from peak",
                'actions': [
                    "Review rebalancing opportunities from debt to equity",
                    "Evaluate systematic transfer plans (STPs)",
                    "Consider accelerating equity deployments",
                    "Reassess risk tolerance alignment with market event"
                ]
            },
            {
                'event': 'Significant market rally',
                'description': "Nifty or Sensex rally",
                'threshold': "15% market rise in 3 months",
                'actions': [
                    "Review profit booking opportunities", 
                    "Check if equity allocation exceeds thresholds",
                    "Consider rebalancing to debt for goal-based strategies"
                ]
            },
            {
                'event': 'Extreme volatility',
                'description': "India VIX spike",
                'threshold': "India VIX above 25",
                'actions': [
                    "Consider defensive adjustments in equity allocation",
                    "Review hedging strategies if applicable",
                    "Postpone major allocation changes until volatility subsides",
                    "Consider quality/large-cap shift for near-term goals"
                ]
            },
            {
                'event': 'Currency movements',
                'description': "Significant INR movement vs USD",
                'threshold': "±5% movement in 1 month",
                'actions': [
                    "Review international investment exposure",
                    "Assess impact on import/export dependent sectors",
                    "Consider implications for gold allocation"
                ]
            }
        ]
        
        # ---- Goal-specific review triggers ----
        
        goal_specific_triggers = []
        
        if goal_type == 'education':
            goal_specific_triggers.append({
                'event': 'Education milestone',
                'description': "Academic transition points (5th, 8th, 10th, 12th standards)",
                'actions': [
                    "Adjust for education inflation trends in chosen field",
                    "Review timeline based on exam results and educational path",
                    "Assess international education funding needs if applicable"
                ]
            })
        elif goal_type == 'retirement':
            goal_specific_triggers.append({
                'event': 'Retirement milestone',
                'description': "10, 5, and 1 year retirement milestones",
                'actions': [
                    "Gradual shift to more conservative allocation",
                    "Review annuity and pension income strategies",
                    "Adjust withdrawal and tax optimization strategies"
                ]
            })
        elif goal_type == 'home_purchase':
            goal_specific_triggers.append({
                'event': 'Real estate market changes',
                'description': "Significant real estate price movements in target area",
                'threshold': "±10% price movement in 6 months",
                'actions': [
                    "Adjust timeline based on market opportunity",
                    "Review down payment size and loan strategy",
                    "Reconsider rent vs. buy analysis with new data"
                ]
            })
        
        # Compile all review points into a comprehensive schedule
        review_schedule = {
            'regular_reviews': regular_reviews,
            'fiscal_reviews': [tax_year_review, budget_review, post_budget_review],
            'life_event_triggers': {
                'centralized_registry': life_event_integration,
                'fallback_triggers': life_event_triggers
            },
            'market_event_triggers': market_event_triggers,
            'goal_specific_triggers': goal_specific_triggers,
            'next_scheduled_review': regular_reviews[0]['date'],
            'highest_priority_review': tax_year_review if tax_year_review['priority'] == 'high' else regular_reviews[0]['date']
        }
        
        # Add review schedule to strategy
        strategy['review_schedule'] = review_schedule
        
        return strategy
        
    def adapt_to_market_conditions(self, strategy: Dict[str, Any], market_environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust rebalancing strategy for extreme market conditions, with specific focus on
        Indian market indicators and volatility measures.
        
        This method implements tactical shifts based on:
        - Equity market volatility (Nifty VIX)
        - Interest rate cycles
        - Relative valuation metrics
        - Market sentiment and technical indicators
        
        Args:
            strategy: Existing rebalancing strategy dictionary
            market_environment: Dictionary with current market condition indicators
            
        Returns:
            Updated strategy with market adaptation provisions
        """
        # Extract core strategy information
        goal_type = strategy.get('goal_type', 'general')
        time_horizon = strategy.get('time_horizon', 5)
        drift_thresholds = strategy.get('drift_thresholds', {})
        base_allocation = strategy.get('target_allocation', {})
        
        # Extract market condition indicators
        vix_level = market_environment.get('india_vix', 15)  # Default to average VIX
        market_trend = market_environment.get('market_trend', 'neutral')  # bullish, bearish, neutral
        pe_ratio = market_environment.get('nifty_pe_ratio', 20)
        interest_rate_direction = market_environment.get('interest_rate_direction', 'stable')
        liquidity_condition = market_environment.get('liquidity_condition', 'normal')
        
        # ---- Volatility-based adjustments ----
        
        # Classify volatility regime based on India VIX
        volatility_regime = 'normal'
        if vix_level >= 25:
            volatility_regime = 'high'
        elif vix_level >= 18:
            volatility_regime = 'elevated'
        elif vix_level <= 12:
            volatility_regime = 'low'
            
        # Adjust drift thresholds based on volatility regime
        volatility_adjustment_factors = {
            'high': 1.5,       # Wider bands in high volatility
            'elevated': 1.2,   # Somewhat wider bands
            'normal': 1.0,     # Normal bands
            'low': 0.8         # Tighter bands in low volatility
        }
        
        volatility_factor = volatility_adjustment_factors.get(volatility_regime, 1.0)
        
        # Apply volatility adjustment to drift thresholds
        adjusted_thresholds = {}
        if 'asset_bands' in drift_thresholds:
            adjusted_asset_bands = {}
            for asset, band in drift_thresholds['asset_bands'].items():
                adjusted_threshold = band['threshold'] * volatility_factor
                
                adjusted_asset_bands[asset] = {
                    'target': band['target'],
                    'threshold': adjusted_threshold,
                    'upper_band': band['target'] + adjusted_threshold,
                    'lower_band': max(0, band['target'] - adjusted_threshold),
                    'rebalance_when': f"< {max(0, band['target'] - adjusted_threshold):.2f} or > {band['target'] + adjusted_threshold:.2f}",
                    'volatility_adjustment': f"{volatility_regime} volatility adjustment applied ({volatility_factor}x)"
                }
                
            adjusted_thresholds = {
                'threshold_rationale': f"{drift_thresholds.get('threshold_rationale', 'Standard')} with {volatility_regime} volatility adjustment",
                'asset_bands': adjusted_asset_bands,
                'implementation_note': drift_thresholds.get('implementation_note', '')
            }
        
        # ---- Tactical allocation shifts ----
        
        # Initialize tactical shifts dictionary
        tactical_shifts = {}
        
        # Determine if tactical shifts are appropriate based on goal type and time horizon
        allow_tactical_shifts = False
        if goal_type in ['retirement', 'wealth_building', 'custom'] and time_horizon > 7:
            allow_tactical_shifts = True  # Long-term goals allow tactical shifts
        elif goal_type in ['education', 'home_purchase'] and time_horizon > 5:
            allow_tactical_shifts = True  # Medium-term goals with sufficient horizon
        elif time_horizon < 2:
            allow_tactical_shifts = False  # Short-term goals avoid tactical shifts
        
        # Apply tactical shifts if allowed
        if allow_tactical_shifts:
            # Valuation-based shifts
            if pe_ratio > 25 and market_trend == 'bullish':
                # Overvalued market condition - defensive positioning
                tactical_shifts['valuation_shift'] = {
                    'direction': 'defensive',
                    'trigger': f"High Nifty P/E ratio ({pe_ratio}) with bullish trend",
                    'equity_adjustment': -0.05,  # Reduce equity by 5%
                    'debt_adjustment': 0.03,     # Increase debt by 3%
                    'gold_adjustment': 0.02,     # Increase gold by 2%
                    'rationale': "Defensive positioning due to elevated valuations"
                }
            elif pe_ratio < 15 and market_trend == 'bearish':
                # Undervalued market condition - opportunistic positioning
                tactical_shifts['valuation_shift'] = {
                    'direction': 'opportunistic',
                    'trigger': f"Low Nifty P/E ratio ({pe_ratio}) with bearish trend",
                    'equity_adjustment': 0.05,   # Increase equity by 5%
                    'debt_adjustment': -0.04,    # Reduce debt by 4%
                    'gold_adjustment': -0.01,    # Reduce gold by 1%
                    'rationale': "Opportunistic positioning due to attractive valuations"
                }
                
            # Interest rate cycle shifts
            if interest_rate_direction == 'rising':
                tactical_shifts['interest_rate_shift'] = {
                    'direction': 'duration_reduction',
                    'trigger': "Rising interest rate environment",
                    'recommendation': "Shift to shorter duration debt instruments",
                    'debt_instruments': [
                        "Ultra short-term debt funds",
                        "Floating rate bonds",
                        "Money market instruments"
                    ],
                    'equity_sectors_to_underweight': [
                        "Interest rate sensitive (Real Estate, Capital Goods)",
                        "High-leverage businesses",
                        "Utilities with regulated returns"
                    ]
                }
            elif interest_rate_direction == 'falling':
                tactical_shifts['interest_rate_shift'] = {
                    'direction': 'duration_extension',
                    'trigger': "Falling interest rate environment",
                    'recommendation': "Consider longer duration debt instruments",
                    'debt_instruments': [
                        "Long-term gilt funds",
                        "Dynamic bond funds",
                        "Corporate bond funds"
                    ],
                    'equity_sectors_to_overweight': [
                        "Interest rate sensitives (Banks, Real Estate)",
                        "Consumption sectors",
                        "Auto and consumer durables"
                    ]
                }
                
            # Liquidity-based shifts
            if liquidity_condition == 'tight':
                tactical_shifts['liquidity_shift'] = {
                    'direction': 'liquidity_focus',
                    'trigger': "Tight liquidity conditions in market",
                    'recommendation': "Prioritize quality and liquidity in investments",
                    'implementation': [
                        "Prefer large-caps over small-caps",
                        "Increase allocation to liquid funds",
                        "Focus on companies with strong balance sheets",
                        "Reduce exposure to leveraged businesses"
                    ]
                }
            elif liquidity_condition == 'abundant':
                tactical_shifts['liquidity_shift'] = {
                    'direction': 'broader_participation',
                    'trigger': "Abundant liquidity conditions in market",
                    'recommendation': "Consider broader market participation",
                    'implementation': [
                        "Selective mid/small-cap exposure",
                        "Consider high-yield debt opportunities",
                        "Evaluate emerging market allocations"
                    ]
                }
        
        # ---- Create adapted allocation ----
        
        # Apply tactical shifts to base allocation if allowed
        adapted_allocation = base_allocation.copy()
        
        if allow_tactical_shifts and 'valuation_shift' in tactical_shifts:
            shift = tactical_shifts['valuation_shift']
            
            # Apply equity adjustment
            if 'equity' in adapted_allocation and shift.get('equity_adjustment'):
                adapted_allocation['equity'] = max(0, min(1, adapted_allocation['equity'] + shift['equity_adjustment']))
                
            # Apply debt adjustment
            if 'debt' in adapted_allocation and shift.get('debt_adjustment'):
                adapted_allocation['debt'] = max(0, min(1, adapted_allocation['debt'] + shift['debt_adjustment']))
                
            # Apply gold adjustment
            if 'gold' in adapted_allocation and shift.get('gold_adjustment'):
                adapted_allocation['gold'] = max(0, min(1, adapted_allocation['gold'] + shift['gold_adjustment']))
        
        # ---- Defensive positioning for high volatility ----
        
        defensive_actions = None
        if volatility_regime == 'high':
            defensive_actions = {
                'description': "Defensive positioning due to high market volatility",
                'vix_level': vix_level,
                'temporary_adjustments': [
                    "Postpone lump sum equity investments, prefer staggered deployment",
                    "Consider increasing STP (Systematic Transfer Plan) duration",
                    "Focus on large-cap quality stocks in equity allocation",
                    "Consider option hedging for large portfolios if volatility persists"
                ],
                'implementation_approach': "Gradual adjustment without market timing",
                'indian_context': [
                    "Focus on domestic consumption and defensive sectors (FMCG, Pharma)",
                    "Consider sovereign gold bonds for tactical gold allocation",
                    "Prefer PSU debt instruments for flight to safety"
                ]
            }
        
        # Compile market adaptation strategy
        market_adaptation = {
            'volatility_regime': volatility_regime,
            'vix_level': vix_level,
            'market_trend': market_trend,
            'valuation_level': 'high' if pe_ratio > 24 else ('moderate' if pe_ratio > 16 else 'low'),
            'interest_rate_environment': interest_rate_direction,
            'adjusted_thresholds': adjusted_thresholds,
            'tactical_shifts': tactical_shifts if allow_tactical_shifts else {"note": "Tactical shifts limited due to goal constraints"},
            'adapted_allocation': adapted_allocation,
            'defensive_actions': defensive_actions,
            'recommendation': f"Implement {volatility_regime} volatility regime adjustments with {'tactical shifts' if tactical_shifts and allow_tactical_shifts else 'standard approach'}"
        }
        
        # Add market adaptation to strategy
        strategy['market_adaptation'] = market_adaptation
        if adjusted_thresholds:
            strategy['drift_thresholds'] = adjusted_thresholds
        
        return strategy
        
    def handle_contribution_variations(self, strategy: Dict[str, Any], contribution_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt rebalancing strategy for irregular contribution patterns common in Indian income scenarios,
        including seasonal incomes, bonuses, and inconsistent SIP patterns.
        
        This method optimizes for:
        - Variable monthly SIP contributions
        - Lump sum investments (annual bonus, festival bonus, etc.)
        - Handling contribution gaps and pauses
        - Seasonal income patterns (agricultural, business cycle, etc.)
        
        Args:
            strategy: Existing rebalancing strategy dictionary
            contribution_history: Dictionary with detailed contribution history
            
        Returns:
            Updated strategy with contribution adaptation features
        """
        # Extract core strategy information
        goal_type = strategy.get('goal_type', 'general')
        rebalancing_schedule = strategy.get('rebalancing_schedule', {})
        base_allocation = strategy.get('target_allocation', {})
        
        # Extract contribution history information
        monthly_contributions = contribution_history.get('monthly_contributions', [])
        lump_sum_contributions = contribution_history.get('lump_sum_contributions', [])
        missed_contributions = contribution_history.get('missed_contributions', 0)
        contribution_pattern = contribution_history.get('pattern', 'regular')
        
        # ---- Analyze contribution pattern ----
        
        # Calculate contribution statistics
        avg_monthly = sum(monthly_contributions) / len(monthly_contributions) if monthly_contributions else 0
        median_monthly = sorted(monthly_contributions)[len(monthly_contributions)//2] if monthly_contributions else 0
        total_lump_sum = sum(lump_sum_amount for _, lump_sum_amount in lump_sum_contributions)
        contribution_regularity = 1 - (missed_contributions / (len(monthly_contributions) + 0.01))
        
        # Determine contribution pattern characteristics
        pattern_analysis = {
            'average_monthly': round(avg_monthly),
            'median_monthly': round(median_monthly),
            'total_lump_sum': round(total_lump_sum),
            'missed_months': missed_contributions,
            'regularity_score': round(contribution_regularity * 100, 1),
            'pattern_type': contribution_pattern
        }
        
        # ---- Handle SIP variations ----
        
        sip_variation_strategy = None
        if contribution_pattern in ['variable', 'irregular']:
            sip_variation_strategy = {
                'pattern_detected': contribution_pattern,
                'recommendation': "Implement adaptive SIP strategy",
                'implementation': [
                    "Set minimum core SIP amount (never miss this component)",
                    "Define discretionary SIP component based on monthly cashflow",
                    "Consider quarterly frequency for better adherence if monthly is challenging",
                    "Use auto-increase feature to counterbalance missed contributions"
                ],
                'minimum_recommended_sip': round(median_monthly * 0.7),  # 70% of median as base
                'suggested_guardrails': {
                    'minimum': round(median_monthly * 0.7),
                    'target': round(avg_monthly),
                    'stretch': round(avg_monthly * 1.2)
                },
                'recovery_plan': [
                    f"Set recurring goal to increase SIP by 10% after {max(1, missed_contributions)} missed months",
                    "Consider annual 'catch-up' contribution to offset irregular patterns"
                ]
            }
        
        # ---- Handle lump sum deployment ----
        
        lump_sum_strategy = None
        if lump_sum_contributions:
            # Analyze lump sum timing patterns (annual bonus, tax refund, etc.)
            lump_sum_months = [month for month, _ in lump_sum_contributions]
            common_months = set()
            for month in lump_sum_months:
                if lump_sum_months.count(month) > 1:
                    common_months.add(month)
            
            # Market condition sensitivity based on goal type and time horizon
            market_sensitivity = "low"
            if goal_type in ['retirement', 'wealth_building'] and strategy.get('time_horizon', 0) > 10:
                market_sensitivity = "moderate"
            elif goal_type in ['custom', 'education'] and strategy.get('time_horizon', 0) > 5:
                market_sensitivity = "moderate"
                
            # STP vs lump sum decision framework
            stp_months = 1  # Default deployment period
            if market_sensitivity == "moderate":
                stp_months = 3  # Moderate sensitivity: 3-month STP
                
            # Handle seasonality in income patterns
            seasonal_income = len(common_months) > 1
            
            lump_sum_strategy = {
                'pattern_detected': "Recurring lump sum" if seasonal_income else "Occasional lump sum",
                'common_contribution_months': list(common_months) if seasonal_income else "No clear pattern",
                'market_sensitivity': market_sensitivity,
                'deployment_approach': {
                    'primary_method': "STP (Systematic Transfer Plan)" if market_sensitivity != "low" else "Direct deployment",
                    'deployment_period': f"{stp_months} months" if market_sensitivity != "low" else "Immediate",
                    'allocation_adjustments': [
                        "Maintain strategic allocation by deploying across assets",
                        "Use lump sum primarily to rebalance current allocation towards target"
                    ]
                },
                'upcoming_opportunities': [
                    month for month in common_months 
                    if datetime.now().month < month <= (datetime.now().month + 6) % 12
                ],
                'indian_context': [
                    "Utilize advance tax payment schedule for planning",
                    "Consider tax-harvesting with bonus deployment timing",
                    "Plan STP to complete before NFO (New Fund Offer) if relevant"
                ]
            }
            
            # Anticipatory planning for recurring lump sums
            if seasonal_income:
                next_expected_month = min([m for m in common_months if m > datetime.now().month % 12] or [min(common_months)])
                months_until_lump = (next_expected_month - datetime.now().month) % 12
                
                lump_sum_strategy['anticipatory_planning'] = {
                    'next_expected_contribution': f"{next_expected_month}/2025",
                    'months_until_contribution': months_until_lump,
                    'preparation_steps': [
                        "Review market conditions 1 month prior to expected lump sum",
                        "Prepare STP arrangements in advance",
                        "Identify tax-efficient deployment options"
                    ]
                }
        
        # ---- Handle contribution gaps ----
        
        gap_strategy = None
        if missed_contributions > 2:
            recovery_time_months = max(missed_contributions * 2, 6)  # Recover over twice the missed months
            increased_monthly = avg_monthly * (1 + (missed_contributions / recovery_time_months))
            
            gap_strategy = {
                'gap_detected': f"{missed_contributions} missed contributions",
                'impact_assessment': "Moderate impact" if missed_contributions <= 4 else "Significant impact",
                'recovery_options': [
                    {
                        'approach': "Increased future SIPs",
                        'implementation': f"Increase monthly SIP to ₹{round(increased_monthly)} for next {recovery_time_months} months",
                        'advantage': "Gradual recovery without significant lifestyle impact",
                        'suitable_for': "Steady income with temporary interruption"
                    },
                    {
                        'approach': "Partial lump sum catch-up",
                        'implementation': f"Contribute ₹{round(avg_monthly * missed_contributions * 0.5)} as lump sum + 10% increased SIPs",
                        'advantage': "Faster recovery with moderate immediate requirement",
                        'suitable_for': "Bonus or windfall recipients"
                    },
                    {
                        'approach': "Full catch-up",
                        'implementation': f"One-time contribution of ₹{round(avg_monthly * missed_contributions)}",
                        'advantage': "Immediate plan correction",
                        'suitable_for': "High priority goals with available funds"
                    }
                ],
                'preventive_measures': [
                    "Set up auto-debit mandate for core contribution amount",
                    "Schedule contributions immediately after income receipt",
                    "Create emergency buffer specifically for maintaining SIPs during income disruptions"
                ]
            }
            
            # Goal-specific recovery recommendations
            if goal_type == 'retirement':
                gap_strategy['goal_specific_recommendation'] = "Prioritize catch-up due to compounding benefits for long-term goal"
            elif goal_type == 'education' and strategy.get('time_horizon', 10) < 5:
                gap_strategy['goal_specific_recommendation'] = "Consider full catch-up due to shorter time horizon remaining"
        
        # ---- Adapt allocation for contribution patterns ----
        
        adapted_allocation = base_allocation.copy()
        allocation_adaptation = None
        
        # For irregular contributions, slightly adjust allocation for more stability
        if contribution_regularity < 0.8:
            # Increase debt/stable components slightly
            stability_shift = min(0.05, (1 - contribution_regularity) * 0.15)
            
            if 'equity' in adapted_allocation:
                adapted_allocation['equity'] = max(0, adapted_allocation['equity'] - stability_shift)
            
            if 'debt' in adapted_allocation:
                adapted_allocation['debt'] = min(1, adapted_allocation['debt'] + stability_shift * 0.7)
            
            if 'gold' in adapted_allocation:
                adapted_allocation['gold'] = min(1, adapted_allocation['gold'] + stability_shift * 0.3)
                
            allocation_adaptation = {
                'adjustment_type': "Stability enhancement",
                'trigger': f"Irregular contribution pattern (regularity score: {pattern_analysis['regularity_score']}%)",
                'allocation_shift': f"{round(stability_shift * 100, 1)}% shift from equity to more stable assets",
                'rationale': "Enhancing stability to compensate for contribution irregularity"
            }
        
        # Create comprehensive contribution adaptation plan
        contribution_adaptation = {
            'contribution_analysis': pattern_analysis,
            'sip_variation_strategy': sip_variation_strategy,
            'lump_sum_strategy': lump_sum_strategy,
            'gap_recovery_strategy': gap_strategy,
            'allocation_adaptation': allocation_adaptation,
            'adapted_allocation': adapted_allocation if allocation_adaptation else None,
            'behavioral_recommendations': [
                "Set automatic monthly transfers on salary receipt day",
                "Create separate 'SIP maintenance' buffer for income fluctuation periods",
                "Use 'Pay Yourself First' principle - allocate to goals before discretionary spending",
                "Plan 13th month contribution annually for psychologically easier catch-up"
            ],
            'indian_context': [
                "Align investment frequency with income pattern (weekly for business owners)",
                "Utilize 'Sweep-in FD' for SIP funding buffer",
                "Consider quarterly advance tax schedule in SIP planning",
                "Create festival bonus allocation plan (Diwali, annual holidays)"
            ]
        }
        
        # Add contribution adaptation to strategy
        strategy['contribution_adaptation'] = contribution_adaptation
        
        # Update allocation if adapted
        if allocation_adaptation:
            strategy['adapted_allocation'] = adapted_allocation
        
        return strategy
        
    def generate_strategy_summary(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produces a concise overview of the rebalancing strategy tailored for Indian investors.
        
        Creates formatted summaries for both technical and non-technical users, highlighting:
        - Core strategy parameters and asset allocation
        - Key Indian tax considerations
        - Rebalancing approach and drift thresholds
        - Expected outcomes and risk management
        
        Args:
            strategy: The rebalancing strategy dictionary
            
        Returns:
            Dictionary with formatted strategy summaries and key elements
        """
        # Extract core strategy elements
        goal_type = strategy.get('goal_type', 'general')
        time_horizon = strategy.get('time_horizon', 0)
        risk_profile = strategy.get('risk_profile', 'moderate')
        target_allocation = strategy.get('target_allocation', {})
        drift_thresholds = strategy.get('drift_thresholds', {})
        
        # Format time horizon in human-readable form
        horizon_text = f"{time_horizon} years"
        if time_horizon < 1:
            months = int(time_horizon * 12)
            horizon_text = f"{months} months"
        
        # Create concise executive summary (non-technical)
        executive_summary = [
            f"This is a {risk_profile.capitalize()} risk {goal_type.replace('_', ' ')} strategy with a {horizon_text} time horizon.",
            "The strategy includes:"
        ]
        
        # Add allocation summary
        if target_allocation:
            allocation_points = []
            for asset_class, value in target_allocation.items():
                if isinstance(value, (int, float)):
                    percentage = int(value * 100) if isinstance(value, float) else value
                    allocation_points.append(f"{asset_class.replace('_', ' ').title()}: {percentage}%")
            
            if allocation_points:
                executive_summary.append("• Asset allocation: " + ", ".join(allocation_points))
        
        # Add rebalancing approach summary
        rebalancing_schedule = strategy.get('rebalancing_schedule', {})
        if rebalancing_schedule:
            frequency = rebalancing_schedule.get('frequency', 'annual')
            executive_summary.append(f"• {frequency.capitalize()} rebalancing with threshold-based triggers")
        
        # Add tax considerations
        tax_summary = "• Tax efficiency through STCG/LTCG optimization and tax-loss harvesting"
        if 'tax_efficiency' in strategy:
            tax_strategy = strategy.get('tax_efficiency', {}).get('approach', '')
            if tax_strategy:
                tax_summary = f"• {tax_strategy} tax optimization approach"
        executive_summary.append(tax_summary)
        
        # Add India-specific considerations
        india_specific = []
        
        # Check for SIP approach
        if 'contribution_approach' in strategy:
            if strategy['contribution_approach'].get('method') == 'SIP':
                india_specific.append("• Systematic Investment Plan (SIP) for regular investments")
                
        # Check for tax-saving instruments
        tax_instruments = []
        if 'instruments' in strategy:
            for instrument in strategy.get('instruments', []):
                if instrument.get('tax_benefit') and instrument.get('name'):
                    tax_instruments.append(instrument['name'])
            
            if tax_instruments:
                india_specific.append(f"• Tax-advantaged instruments: {', '.join(tax_instruments)}")
        
        # Check for market volatility handling
        if 'market_adaptations' in strategy:
            india_specific.append("• India VIX-based volatility adjustments")
            
        # Add India-specific points to summary
        executive_summary.extend(india_specific)
        
        # Create technical summary with more detailed parameters
        technical_summary = {
            "strategy_type": f"{risk_profile}_{goal_type}",
            "time_horizon": time_horizon,
            "target_allocation": target_allocation,
            "drift_thresholds": {
                asset: threshold for asset, threshold in drift_thresholds.get('asset_bands', {}).items()
            },
            "tax_efficiency": {
                "equity_lt_threshold": "12 months",
                "debt_lt_threshold": "36 months",
                "debt_indexation_benefit": True,
                "tax_loss_harvesting_frequency": strategy.get('tax_efficiency', {}).get('harvesting_frequency', 'annual')
            },
            "india_specific": {
                "sip_approach": strategy.get('contribution_approach', {}).get('method') == 'SIP',
                "vix_adaptive": 'market_adaptations' in strategy,
                "fiscal_year_aligned": True
            }
        }
        
        # Create key metrics section
        key_metrics = {
            "expected_annual_rebalancing_actions": self._estimate_rebalancing_frequency(strategy),
            "tax_efficiency_score": self._calculate_tax_efficiency_score(strategy),
            "implementation_complexity": self._assess_implementation_complexity(strategy),
            "volatility_adaptation_level": "High" if 'market_adaptations' in strategy else "Standard"
        }
        
        # Compile the complete strategy summary
        strategy_summary = {
            "executive_summary": executive_summary,
            "technical_summary": technical_summary,
            "key_metrics": key_metrics,
            "key_indian_considerations": {
                "tax_implications": self._extract_tax_implications(strategy),
                "market_specific_factors": self._extract_market_factors(strategy)
            }
        }
        
        return strategy_summary
    
    def create_implementation_checklist(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provides actionable steps for implementing the rebalancing strategy with Indian instruments.
        
        Creates a comprehensive checklist covering:
        - Account setup requirements
        - Instrument selection (mutual funds, ETFs)
        - SIP setup and configuration
        - Tax-optimized investment approach
        - Step-by-step implementation guidance
        
        Args:
            strategy: The rebalancing strategy dictionary
            
        Returns:
            Dictionary with implementation steps and instrument recommendations
        """
        # Extract core strategy elements
        goal_type = strategy.get('goal_type', 'general')
        risk_profile = strategy.get('risk_profile', 'moderate')
        target_allocation = strategy.get('target_allocation', {})
        
        # Create account setup steps
        account_setup = [
            {
                "step": "Open a demat and trading account",
                "description": "Select a broker with low fees and reliable service (Zerodha, HDFC Securities, etc.)",
                "importance": "Required",
                "timeline": "Before implementation"
            },
            {
                "step": "Complete KYC verification",
                "description": "Ensure PAN, Aadhaar, and bank accounts are linked for seamless transactions",
                "importance": "Required",
                "timeline": "Before implementation"
            },
            {
                "step": "Set up online banking and UPI",
                "description": "For efficient fund transfers and SIP mandates",
                "importance": "Required",
                "timeline": "Before implementation"
            }
        ]
        
        # Create steps for instrument selection
        investment_selection = []
        
        # Equity components
        if target_allocation.get('equity', 0) > 0:
            equity_allocation = target_allocation.get('equity', 0)
            equity_step = {
                "step": "Select equity instruments",
                "allocation": f"{int(equity_allocation*100)}%",
                "recommended_instruments": []
            }
            
            # Add recommendations based on risk profile
            if risk_profile == 'conservative':
                equity_step["recommended_instruments"] = [
                    {"type": "Index Fund", "example": "UTI Nifty 50 Index Fund", "allocation": "50-70%"},
                    {"type": "Large Cap Fund", "example": "Axis Bluechip Fund", "allocation": "30-50%"}
                ]
            elif risk_profile == 'moderate':
                equity_step["recommended_instruments"] = [
                    {"type": "Index Fund", "example": "UTI Nifty 50 Index Fund", "allocation": "40-50%"},
                    {"type": "Multi Cap Fund", "example": "Parag Parikh Flexi Cap Fund", "allocation": "30-40%"},
                    {"type": "Mid Cap Fund", "example": "Kotak Emerging Equity Fund", "allocation": "20-30%"}
                ]
            else:  # aggressive
                equity_step["recommended_instruments"] = [
                    {"type": "Index Fund", "example": "UTI Nifty 50 Index Fund", "allocation": "30-40%"},
                    {"type": "Mid Cap Fund", "example": "Kotak Emerging Equity Fund", "allocation": "25-35%"},
                    {"type": "Small Cap Fund", "example": "SBI Small Cap Fund", "allocation": "20-30%"},
                    {"type": "Thematic/Sectoral", "example": "ICICI Prudential Technology Fund", "allocation": "10-15%"}
                ]
                
            investment_selection.append(equity_step)
        
        # Debt components
        if target_allocation.get('debt', 0) > 0:
            debt_allocation = target_allocation.get('debt', 0)
            debt_step = {
                "step": "Select debt instruments",
                "allocation": f"{int(debt_allocation*100)}%",
                "recommended_instruments": []
            }
            
            # Add recommendations based on risk profile
            if risk_profile == 'conservative':
                debt_step["recommended_instruments"] = [
                    {"type": "Government Securities", "example": "SBI Magnum Constant Maturity Fund", "allocation": "40-50%"},
                    {"type": "Corporate Bond Fund", "example": "Kotak Corporate Bond Fund", "allocation": "30-40%"},
                    {"type": "Banking & PSU Fund", "example": "Axis Banking & PSU Debt Fund", "allocation": "20-30%"}
                ]
            elif risk_profile == 'moderate':
                debt_step["recommended_instruments"] = [
                    {"type": "Corporate Bond Fund", "example": "Kotak Corporate Bond Fund", "allocation": "40-50%"},
                    {"type": "Short Duration Fund", "example": "Aditya Birla Sun Life Short Term Fund", "allocation": "30-40%"},
                    {"type": "Banking & PSU Fund", "example": "Axis Banking & PSU Debt Fund", "allocation": "20-30%"}
                ]
            else:  # aggressive
                debt_step["recommended_instruments"] = [
                    {"type": "Credit Risk Fund", "example": "ICICI Prudential Credit Risk Fund", "allocation": "30-40%"},
                    {"type": "Short Duration Fund", "example": "Aditya Birla Sun Life Short Term Fund", "allocation": "30-40%"},
                    {"type": "Dynamic Bond Fund", "example": "ICICI Prudential All Seasons Bond Fund", "allocation": "30-40%"}
                ]
                
            investment_selection.append(debt_step)
        
        # Gold components
        if target_allocation.get('gold', 0) > 0:
            gold_allocation = target_allocation.get('gold', 0)
            gold_step = {
                "step": "Select gold instruments",
                "allocation": f"{int(gold_allocation*100)}%",
                "recommended_instruments": [
                    {"type": "Gold ETF", "example": "Nippon India Gold ETF", "allocation": "60-70%"},
                    {"type": "Gold Fund", "example": "SBI Gold Fund", "allocation": "30-40%"}
                ]
            }
            investment_selection.append(gold_step)
        
        # Tax-saving components if applicable
        if goal_type in ['retirement', 'children_education']:
            tax_step = {
                "step": "Select tax-saving instruments",
                "description": "Allocate Section 80C investments (₹1.5 lakh limit)",
                "recommended_instruments": [
                    {"type": "ELSS Fund", "example": "Axis Long Term Equity Fund", "notes": "3-year lock-in, tax deduction under Sec 80C"},
                    {"type": "PPF", "notes": "15-year tenure, tax-free interest, Sec 80C benefit"},
                    {"type": "NPS Tier 1", "notes": "Additional ₹50,000 deduction under Sec 80CCD(1B)"}
                ]
            }
            investment_selection.append(tax_step)
        
        # SIP setup guidelines
        sip_guidelines = {
            "recommended_dates": ["7th", "15th", "22nd"],
            "sip_frequency": "Monthly (recommended) or Quarterly",
            "auto_debit_setup": "Through NACH mandate with your bank",
            "step_up_strategy": "Consider 5-10% annual increase in SIP amount to account for inflation and income growth"
        }
        
        # Implementation steps
        implementation_steps = [
            {
                "step": 1,
                "action": "Register with recommended platforms",
                "timeline": "Week 1",
                "details": "Complete registration, KYC and bank account linking"
            },
            {
                "step": 2,
                "action": "Initial funds allocation",
                "timeline": "Week 2-3",
                "details": "Make initial lump sum investments following target allocation"
            },
            {
                "step": 3,
                "action": "Set up SIPs",
                "timeline": "Week 3",
                "details": "Configure monthly/quarterly SIPs for each selected instrument"
            },
            {
                "step": 4,
                "action": "Configure tracking system",
                "timeline": "Week 4",
                "details": "Set up portfolio tracking (spreadsheet or app like MProfit, ValueResearch)"
            },
            {
                "step": 5,
                "action": "Calendar review points",
                "timeline": "Week 4",
                "details": "Set reminders for quarterly/annual rebalancing reviews"
            }
        ]
        
        # Compile complete implementation checklist
        implementation_checklist = {
            "account_setup": account_setup,
            "investment_selection": investment_selection,
            "sip_setup": sip_guidelines,
            "implementation_steps": implementation_steps,
            "india_specific_considerations": {
                "direct_vs_regular": "Select 'Direct' plans to avoid distributor commissions (0.5-1.5% lower expense ratio)",
                "kyc_requirements": "Valid PAN, Aadhaar, address proof, bank statements, photo ID, and cancelled cheque",
                "taxation_notes": self._get_tax_implementation_notes(strategy),
                "stamp_duty": "Consider 0.005% stamp duty on mutual fund purchases (effective July 2020)"
            }
        }
        
        return implementation_checklist
    
    def produce_monitoring_guidelines(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates comprehensive monitoring guidelines for the rebalancing strategy.
        
        Outlines metrics, review frequency, and warning signs structured for Indian investors:
        - Performance tracking metrics and benchmarks
        - Rebalancing triggers with specific thresholds
        - Regular review schedule aligned to Indian fiscal year
        - Warning signs warranting strategy adjustments
        
        Args:
            strategy: The rebalancing strategy dictionary
            
        Returns:
            Dictionary with monitoring guidelines and adjustment triggers
        """
        # Extract key strategy elements
        goal_type = strategy.get('goal_type', 'general')
        risk_profile = strategy.get('risk_profile', 'moderate')
        drift_thresholds = strategy.get('drift_thresholds', {})
        
        # Define performance tracking metrics
        performance_metrics = [
            {
                "metric": "Absolute Returns",
                "description": "Total portfolio growth compared to initial investment",
                "frequency": "Monthly and Annual",
                "benchmark": "Compare to target required return for goal",
                "tracking_method": "Portfolio tracking app/spreadsheet"
            },
            {
                "metric": "Goal Progress",
                "description": "Progress toward target amount as percentage",
                "frequency": "Quarterly",
                "benchmark": "Time-weighted progress (e.g., 25% of time = approximately 25% of goal)",
                "tracking_method": "Portfolio tracking app/spreadsheet"
            },
            {
                "metric": "Asset Class Performance",
                "description": "Returns by asset class (equity, debt, gold, etc.)",
                "frequency": "Quarterly",
                "benchmark": "Respective indices (Nifty 50, CRISIL Composite Bond Fund Index, etc.)",
                "tracking_method": "Portfolio tracking app/spreadsheet"
            },
            {
                "metric": "Instrument Performance",
                "description": "Individual fund/security performance",
                "frequency": "Semi-Annual",
                "benchmark": "Category average and respective benchmark indices",
                "tracking_method": "ValueResearch, MorningStar or similar"
            }
        ]
        
        # Define appropriate review frequency
        review_schedule = {
            "routine_monitoring": "Monthly (15-30 minutes)",
            "in_depth_review": "Quarterly (60-90 minutes)",
            "comprehensive_assessment": "Annual (2-3 hours)",
            "special_reviews": [
                "Post Budget (February-March)",
                "After major market movements (±7% in a week)",
                "After significant life events",
                "During major economic policy changes"
            ],
            "fiscal_year_alignment": {
                "tax_harvesting_review": "January-February (before fiscal year end)",
                "tax_planning_review": "April-May (start of fiscal year)",
                "major_rebalancing": "Preferably April or October (start/mid of fiscal year)"
            }
        }
        
        # Define rebalancing triggers
        rebalancing_triggers = {
            "percentage_drift_triggers": {}
        }
        
        # Add asset-specific drift thresholds
        asset_bands = drift_thresholds.get('asset_bands', {})
        for asset, band in asset_bands.items():
            if isinstance(band, dict) and 'threshold' in band:
                rebalancing_triggers["percentage_drift_triggers"][asset] = f"±{int(band['threshold']*100)}%"
            elif isinstance(band, (int, float)):
                rebalancing_triggers["percentage_drift_triggers"][asset] = f"±{int(band*100)}%"
        
        # Add time-based triggers
        rebalancing_triggers["time_based_triggers"] = [
            {
                "period": "Annual",
                "condition": "Mandatory review even if thresholds not breached",
                "rationale": "Ensures at least yearly rebalancing to maintain risk profile"
            }
        ]
        
        # Add market condition triggers
        rebalancing_triggers["market_condition_triggers"] = [
            {
                "condition": "India VIX > 25",
                "action": "Review defensive asset allocation",
                "rationale": "High volatility may warrant temporary protective adjustments"
            },
            {
                "condition": "10%+ market correction",
                "action": "Consider rebalancing to target weights",
                "rationale": "Opportunity to buy equities at lower valuations"
            },
            {
                "condition": "Change in interest rate cycle",
                "action": "Review debt portfolio duration",
                "rationale": "Different duration strategies for rising vs falling rate environments"
            }
        ]
        
        # Define warning signs
        warning_signs = [
            {
                "indicator": "Consistent underperformance",
                "description": "Fund underperforms its benchmark and category average for 4+ quarters",
                "action": "Evaluate replacement with similar fund with better performance"
            },
            {
                "indicator": "Large tracking error",
                "description": "Index funds/ETFs showing >1% deviation from benchmark returns",
                "action": "Consider alternatives with lower tracking error"
            },
            {
                "indicator": "Significant manager change",
                "description": "Fund manager change followed by strategy shifts",
                "action": "Monitor closely for 2 quarters, consider replacement if performance declines"
            },
            {
                "indicator": "Rising expense ratio",
                "description": "Fund increases expense ratio significantly without proportional performance improvement",
                "action": "Evaluate alternatives with better expense-to-performance ratio"
            },
            {
                "indicator": "Style drift",
                "description": "Fund shifts from stated investment style/mandate",
                "action": "Replace with fund that maintains consistent investment approach"
            }
        ]
        
        # India-specific monitoring factors
        india_specific = {
            "tax_efficiency_monitoring": {
                "capital_gains_tracking": "Track holding periods for equity (1 year) and debt (3 years) to optimize LTCG vs STCG",
                "dividend_taxation": "Monitor impact of dividend taxation at slab rates (post 2020 budget change)",
                "indexation_benefits": "Track purchase date and cost inflation index for debt instruments"
            },
            "regulatory_monitoring": {
                "sebi_regulations": "Stay informed on SEBI changes to mutual fund regulations",
                "rbi_policy": "Monitor RBI monetary policy for interest rate impacts on debt portfolio",
                "budget_impacts": "Annual review post-budget for tax policy changes affecting investments"
            },
            "market_phases": {
                "bull_market_considerations": "Avoid chasing returns and high-flying sectors",
                "bear_market_actions": "Maintain SIPs, consider additional lump sum investments if holding sufficient emergency fund",
                "sideways_market_approach": "Focus on asset class rotation based on relative valuation"
            }
        }
        
        # Portfolio health checks
        health_checks = self._create_portfolio_health_checks(strategy)
        
        # Compile complete monitoring guidelines
        monitoring_guidelines = {
            "performance_metrics": performance_metrics,
            "review_schedule": review_schedule,
            "rebalancing_triggers": rebalancing_triggers,
            "warning_signs": warning_signs,
            "india_specific_monitoring": india_specific,
            "portfolio_health_checks": health_checks
        }
        
        return monitoring_guidelines
    
    def _estimate_rebalancing_frequency(self, strategy: Dict[str, Any]) -> str:
        """Estimate number of rebalancing actions per year based on strategy details"""
        frequency = strategy.get('rebalancing_schedule', {}).get('frequency', 'annual')
        
        frequency_map = {
            'monthly': '10-12',
            'quarterly': '4-6',
            'semi_annual': '2-3',
            'annual': '1-2'
        }
        
        return frequency_map.get(frequency, '1-2')
    
    def _calculate_tax_efficiency_score(self, strategy: Dict[str, Any]) -> str:
        """Calculate the tax efficiency score for the strategy"""
        score = 3  # Default moderate score
        
        # Check for tax-specific optimizations
        if 'tax_efficiency' in strategy:
            tax_efficiency = strategy['tax_efficiency']
            if tax_efficiency.get('approach') == 'Aggressive tax-loss harvesting':
                score += 2
            elif tax_efficiency.get('approach') == 'Strategic LTCG planning':
                score += 1
            
            if tax_efficiency.get('harvesting_frequency') == 'quarterly':
                score += 1
        
        # Check for tax-advantaged instruments
        if 'instruments' in strategy:
            tax_instruments = [i for i in strategy.get('instruments', []) if i.get('tax_benefit')]
            if len(tax_instruments) >= 3:
                score += 1
            elif len(tax_instruments) >= 1:
                score += 0.5
        
        # Format the result
        if score >= 5:
            return "Excellent (5/5)"
        elif score >= 4:
            return "Good (4/5)"
        elif score >= 3:
            return "Average (3/5)"
        elif score >= 2:
            return "Basic (2/5)"
        else:
            return "Minimal (1/5)"
    
    def _assess_implementation_complexity(self, strategy: Dict[str, Any]) -> str:
        """Assess the implementation complexity of the strategy"""
        complexity = 3  # Default moderate complexity
        
        # More instruments = more complexity
        instruments_count = len(strategy.get('instruments', []))
        if instruments_count > 8:
            complexity += 1
        elif instruments_count < 4:
            complexity -= 1
        
        # More frequent rebalancing = more complexity
        frequency = strategy.get('rebalancing_schedule', {}).get('frequency', 'annual')
        if frequency == 'monthly':
            complexity += 1
        elif frequency == 'quarterly':
            complexity += 0.5
        elif frequency == 'annual':
            complexity -= 0.5
        
        # Advanced strategies increase complexity
        if strategy.get('tactical_adjustments', {}).get('enabled', False):
            complexity += 1
        
        # Tax-loss harvesting increases complexity
        if strategy.get('tax_efficiency', {}).get('harvesting_frequency') in ['monthly', 'quarterly']:
            complexity += 1
        
        # Format the result
        if complexity >= 5:
            return "Complex (5/5)"
        elif complexity >= 4:
            return "Moderately Complex (4/5)"
        elif complexity >= 3:
            return "Average (3/5)"
        elif complexity >= 2:
            return "Simple (2/5)"
        else:
            return "Very Simple (1/5)"
    
    def _extract_tax_implications(self, strategy: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract tax implications from the strategy"""
        implications = [
            {
                "aspect": "Equity Holding Period",
                "implication": "1+ year qualifies for LTCG at 10% above ₹1 lakh exemption; less than 1 year STCG at 15%"
            },
            {
                "aspect": "Debt Holding Period",
                "implication": "3+ years qualifies for LTCG at 20% with indexation benefit; less than 3 years STCG at income tax slab rate"
            },
            {
                "aspect": "Dividends",
                "implication": "Taxed at investor's income tax slab rate (post 2020 budget changes)"
            }
        ]
        
        if 'tax_efficiency' in strategy:
            tax_strategy = strategy['tax_efficiency'].get('approach', '')
            if tax_strategy:
                implications.append({
                    "aspect": "Tax Strategy",
                    "implication": tax_strategy
                })
        
        return implications
    
    def _extract_market_factors(self, strategy: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract Indian market-specific factors from the strategy"""
        factors = [
            {
                "factor": "Equity Market",
                "consideration": "High volatility and growth potential; Nifty index historically returned ~12% CAGR"
            },
            {
                "factor": "Debt Market",
                "consideration": "Dynamic interest rate cycle requiring active duration management"
            },
            {
                "factor": "Gold",
                "consideration": "Traditional store of value in Indian context; hedge against currency depreciation"
            }
        ]
        
        # Add VIX adaptation if present
        if 'market_adaptations' in strategy:
            factors.append({
                "factor": "Volatility Management",
                "consideration": "India VIX-based adjustments to navigate market turbulence"
            })
        
        return factors
    
    def _get_tax_implementation_notes(self, strategy: Dict[str, Any]) -> List[str]:
        """Get tax implementation notes for the strategy"""
        notes = [
            "Equity funds held > 1 year: 10% LTCG tax above ₹1 lakh exemption per financial year",
            "Equity funds held < 1 year: 15% STCG tax",
            "Debt funds held > 3 years: 20% LTCG tax with indexation benefit",
            "Debt funds held < 3 years: STCG taxed at income tax slab rate"
        ]
        
        # Add Section 80C notes if applicable
        if strategy.get('goal_type') in ['retirement', 'children_education']:
            notes.append("ELSS funds qualify for Sec 80C tax deduction up to ₹1.5 lakh with 3-year lock-in")
            notes.append("PPF contributions qualify for Sec 80C with 15-year tenure")
            notes.append("NPS qualifies for additional ₹50,000 deduction under Sec 80CCD(1B)")
        
        return notes
    
    def _create_portfolio_health_checks(self, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create portfolio health check items for the monitoring guidelines"""
        goal_type = strategy.get('goal_type', 'general')
        
        # Core health checks for any strategy
        health_checks = [
            {
                "check": "Asset Allocation Drift",
                "frequency": "Quarterly",
                "target": "Within ±5% of target allocation for major asset classes",
                "action_if_failed": "Rebalance to target allocation if drift exceeds thresholds"
            },
            {
                "check": "Goal Progress",
                "frequency": "Semi-Annual",
                "target": "On track to meet goal timeline (proportional to time elapsed)",
                "action_if_failed": "Increase contributions or extend goal timeline"
            },
            {
                "check": "Fund Performance vs Benchmark",
                "frequency": "Annual",
                "target": "At least 80% of funds should not underperform their benchmark over 1-year period",
                "action_if_failed": "Replace consistently underperforming funds with better alternatives"
            },
            {
                "check": "Expense Ratio Efficiency",
                "frequency": "Annual",
                "target": "Portfolio weighted average expense ratio below 1%",
                "action_if_failed": "Identify high-expense funds and consider lower-cost alternatives"
            }
        ]
        
        # Add goal-specific health checks
        if goal_type == 'retirement':
            health_checks.append({
                "check": "Retirement Corpus Adequacy",
                "frequency": "Annual",
                "target": "On track for 25-30x annual expenses by retirement age",
                "action_if_failed": "Increase savings rate or adjust retirement lifestyle expectations"
            })
        elif goal_type == 'education':
            health_checks.append({
                "check": "Education Inflation Adjustment",
                "frequency": "Annual",
                "target": "Target amount updated to reflect education inflation (10-12% for Indian higher education)",
                "action_if_failed": "Increase target amount and contribution rate"
            })
        elif goal_type == 'home_purchase':
            health_checks.append({
                "check": "Down Payment Readiness",
                "frequency": "Quarterly",
                "target": "Liquid portion growing in proportion to goal timeline",
                "action_if_failed": "Adjust asset allocation to increase liquidity as purchase date approaches"
            })
        
        return health_checks