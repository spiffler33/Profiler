"""
Tests for the integrated use of asset and income projection classes.
"""

import unittest
import numpy as np
import pandas as pd
from models.financial_projection import (
    AssetProjection, 
    AssetClass,
    ContributionPattern,
    AllocationStrategy,
    IncomeProjection,
    IncomeSource,
    IncomeMilestone,
    TaxRegime
)

class TestIntegratedProjection(unittest.TestCase):
    """Test cases for integrated asset and income projections"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create both projections with deterministic seed for reproducible tests
        self.asset_projection = AssetProjection(
            inflation_rate=0.06,  # Match the inflation rate with income projection
            seed=42
        )
        
        self.income_projection = IncomeProjection(
            inflation_rate=0.06,
            tax_regime=TaxRegime.NEW,
            seed=42
        )
        
        # Basic test inputs
        self.current_age = 30
        self.retirement_age = 55
        self.planning_horizon = 85 - self.current_age  # Plan until age 85
        self.pre_retirement_years = self.retirement_age - self.current_age
        self.post_retirement_years = 85 - self.retirement_age
        
        # Initial portfolio
        self.initial_assets = 2000000  # 20L
        
        # Initial income
        self.salary = 1200000  # 12L per annum
        self.rental_income = 240000  # 2.4L per annum

    def test_retirement_planning_integration(self):
        """Test integrated retirement planning with income and asset projections"""
        # 1. Income projection
        income_sources = {
            IncomeSource.SALARY: self.salary,
            IncomeSource.RENTAL: self.rental_income
        }
        
        # Career milestones
        milestones = {
            IncomeSource.SALARY: [
                IncomeMilestone(year=3, description="Promotion", income_multiplier=1.2),
                IncomeMilestone(year=8, description="Job Change", income_multiplier=1.25),
                IncomeMilestone(year=15, description="Senior Position", income_multiplier=1.3)
            ],
            IncomeSource.RENTAL: [
                IncomeMilestone(year=5, description="Rent Increase", income_multiplier=1.15),
                IncomeMilestone(year=10, description="Additional Property", 
                               absolute_income_change=300000)
            ]
        }
        
        # Project income until retirement
        income_result = self.income_projection.project_multiple_income_streams(
            income_sources=income_sources,
            years=self.pre_retirement_years,
            milestones_by_source=milestones
        )
        
        # Apply volatility to get different scenarios
        income_scenarios = self.income_projection.apply_career_volatility(
            income_result=income_result,
            simulations=100
        )
        
        # 2. Savings rate calculation based on expected income
        expected_income = income_scenarios["expected"]
        
        # Calculate annual savings (assume saving 30% of after-tax income)
        annual_savings = []
        for year in range(self.pre_retirement_years + 1):
            savings = expected_income.after_tax_income[year] * 0.3
            annual_savings.append(savings)
        
        # 3. Asset projection using income-derived contributions
        contribution_pattern = ContributionPattern(
            annual_amount=annual_savings[1],  # First year's contribution
            irregular_schedule={year+1: savings for year, savings in enumerate(annual_savings[1:])}
        )
        
        # Define initial allocation (aggressive at younger age)
        initial_allocation = AllocationStrategy(
            initial_allocation={
                AssetClass.EQUITY: 0.70,
                AssetClass.DEBT: 0.20,
                AssetClass.GOLD: 0.05,
                AssetClass.REAL_ESTATE: 0.05
            },
            target_allocation={
                AssetClass.EQUITY: 0.40,
                AssetClass.DEBT: 0.40,
                AssetClass.GOLD: 0.10,
                AssetClass.REAL_ESTATE: 0.10
            },
            glide_path_years=self.pre_retirement_years  # Gradually shift to conservative
        )
        
        # Project asset growth until retirement
        asset_result = self.asset_projection.project_asset_growth(
            initial_amount=self.initial_assets,
            contribution_pattern=contribution_pattern,
            years=self.pre_retirement_years,
            allocation_strategy=initial_allocation
        )
        
        # 4. Retirement corpus calculation
        retirement_corpus = asset_result.projected_values[-1]
        
        # 5. Project post-retirement income
        retirement_income = self.income_projection.project_retirement_income(
            current_age=self.current_age,
            retirement_age=self.retirement_age,
            life_expectancy=85,
            current_income=income_sources,
            retirement_corpus=retirement_corpus,
            withdrawal_rate=0.04,  # 4% withdrawal rule
            pension_monthly=20000,  # Assume 20K monthly pension
            epf_balance=1500000,    # Assume 15L EPF
            nps_balance=1000000     # Assume 10L NPS
        )
        
        # 6. Verify results
        # Check that we have values for the full planning horizon
        self.assertEqual(len(retirement_income.years), self.planning_horizon + 1)
        
        # Check retirement corpus is positive
        self.assertGreater(retirement_corpus, 0)
        print(f"Projected retirement corpus at age {self.retirement_age}: ₹{retirement_corpus:,.2f}")
        
        # Check that accumulated assets exceed total contributions (positive return)
        total_contributions = sum(asset_result.contributions)
        self.assertGreater(retirement_corpus, self.initial_assets + total_contributions)
        
        # Print key results
        print(f"Initial portfolio: ₹{self.initial_assets:,.2f}")
        print(f"Total contributions over {self.pre_retirement_years} years: ₹{total_contributions:,.2f}")
        print(f"Investment growth: ₹{retirement_corpus - self.initial_assets - total_contributions:,.2f}")
        print(f"Final pre-retirement annual income: ₹{income_result.total_income[-1]:,.2f}")
        print(f"First year retirement income: ₹{retirement_income.total_income[self.pre_retirement_years + 1]:,.2f}")
        
        # Calculate income replacement ratio
        replacement_ratio = (retirement_income.total_income[self.pre_retirement_years + 1] / 
                            income_result.total_income[-1])
        print(f"Income replacement ratio: {replacement_ratio:.2%}")
        
        # Basic check - retirement income should provide reasonable replacement ratio
        self.assertGreater(replacement_ratio, 0.4)  # At least 40% income replacement
        
        # 7. Apply inflation adjustment to see real values
        real_retirement_income = self.income_projection.apply_inflation_adjustment(retirement_income)
        real_corpus_value = retirement_corpus * ((1 / (1 + self.income_projection.inflation_rate)) 
                                              ** self.pre_retirement_years)
        
        print(f"Retirement corpus in today's money: ₹{real_corpus_value:,.2f}")
        print(f"First year retirement income in today's money: "
              f"₹{real_retirement_income.total_income[self.pre_retirement_years + 1]:,.2f}")


if __name__ == "__main__":
    unittest.main()