# UI Component Help Text

This document contains help text and tooltips for user interface components in the Financial Profiler application.

## Goal Creation Form

### Basic Information Section

**Goal Title**
- *Help text:* "Give your goal a clear, specific name"
- *Tooltip:* "A descriptive name helps you identify your goal and its purpose. For example, 'Emergency Fund' or 'Down Payment for Home'"

**Goal Category**
- *Help text:* "Different categories have specialized calculations and advice"
- *Tooltip:* "The category determines which specialized calculator is used and what additional information will be requested. Choose the category that best matches your goal's purpose."

**Target Amount ($)**
- *Help text:* "The total amount you need to achieve this goal"
- *Tooltip:* "Enter the full amount needed to complete this goal. For some goal types, this may be calculated automatically based on other information you provide."

**Current Amount ($)**
- *Help text:* "How much you've already saved toward this goal"
- *Tooltip:* "Enter the amount you've already set aside specifically for this goal. This helps track your progress and calculate required savings."

**Target Date**
- *Help text:* "When you need to achieve this goal"
- *Tooltip:* "Set a realistic date for completing this goal. This determines the timeframe for savings calculations and investment strategies."

### Emergency Fund Section

**Months of Expenses**
- *Help text:* "Typically 3-6 months recommended"
- *Tooltip:* "Financial experts generally recommend saving 3-6 months of expenses for emergencies. If you have variable income or dependents, consider aiming for the higher end of this range."

**Monthly Expenses ($)**
- *Help text:* "Your typical monthly expenses"
- *Tooltip:* "Enter your average monthly expenses including rent/mortgage, utilities, food, transportation, and other regular costs. This helps calculate your total emergency fund target."

### Retirement Section

**Retirement Age**
- *Help text:* "Age when you plan to retire"
- *Tooltip:* "This helps determine your savings timeline. Early retirement requires more savings, while a later retirement age gives you more time to save."

**Withdrawal Rate (%)**
- *Help text:* "Typically 4% (traditional) or 3-3.5% (early retirement)"
- *Tooltip:* "The percentage of your retirement savings you plan to withdraw each year. The '4% rule' is a common guideline, but early retirement may require a more conservative rate."

**Annual Expenses in Retirement ($)**
- *Help text:* "Your expected yearly spending in retirement"
- *Tooltip:* "Estimate your annual expenses in retirement. Many financial planners suggest budgeting 70-80% of your pre-retirement income, but this varies based on your planned lifestyle."

### Education Section

**Education Type**
- *Help text:* "Type of education this goal will fund"
- *Tooltip:* "Different education types have different costs and durations. Select the option that best matches your education goal."

**Years of Education**
- *Help text:* "Duration of the educational program"
- *Tooltip:* "Enter the expected number of years for the program. This helps calculate the total cost based on annual expenses."

**Annual Cost ($)**
- *Help text:* "Yearly tuition and related expenses"
- *Tooltip:* "Enter the expected annual cost including tuition, books, fees, and living expenses if applicable. Education inflation will be factored into future costs."

### Home Purchase Section

**Property Value ($)**
- *Help text:* "Total expected purchase price of the property"
- *Tooltip:* "Enter the estimated total cost of the property you're saving for. This helps calculate how much you need for a down payment."

**Down Payment (%)**
- *Help text:* "Typically 20% for best rates"
- *Tooltip:* "The percentage of the property value you plan to save for a down payment. While some loans allow lower percentages, 20% typically provides better rates and avoids mortgage insurance."

### Goal Priority Section

**Importance**
- *Help text:* "How critical this goal is to your financial well-being"
- *Tooltip:* "High importance goals are prioritized when allocating resources. This affects the goal's priority score and recommendations."

**Flexibility**
- *Help text:* "How adaptable this goal is in terms of timeline and amount"
- *Tooltip:* "Fixed goals have specific deadlines that cannot be moved. Flexible goals can be adjusted based on circumstances. This affects risk recommendations and priority scoring."

### Advanced Options Section

**Notes**
- *Help text:* "Add any additional details or thoughts about this goal"
- *Tooltip:* "Record any relevant information about your plans or strategy for this goal. This is for your reference only."

**Additional Funding Sources**
- *Help text:* "List any other sources of funding besides regular savings (gifts, windfalls, etc.)"
- *Tooltip:* "Include any planned or potential sources of funds beyond your regular savings, such as bonuses, tax refunds, gifts, or asset sales. This helps in calculating your goal's success probability."

## Goals Display Page

### Filter Options

**All Goals**
- *Tooltip:* "Show all your financial goals regardless of category"

**Security / Essential / Retirement / Lifestyle / Legacy**
- *Tooltip:* "Filter to show only goals in the [Category] category"

### Goal Card Elements

**Target Amount**
- *Tooltip:* "The total amount needed to achieve this goal"

**Current Amount**
- *Tooltip:* "What you've saved so far toward this goal"

**Progress Bar**
- *Tooltip:* "Visual representation of your progress toward this goal. Green = high importance, Blue = medium importance, Yellow = low importance"

**Complete Percentage**
- *Tooltip:* "The percentage of your target amount you've already saved"

**Remaining Amount**
- *Tooltip:* "How much more you need to save to reach your target"

**Expand Button**
- *Tooltip:* "Show additional details and options for this goal"

### Expanded Goal Details

**Target Date**
- *Tooltip:* "Your deadline for achieving this goal"

**Priority**
- *Tooltip:* "The importance level you've assigned to this goal"

**Monthly Savings**
- *Tooltip:* "Recommended monthly contribution to reach your goal on time"

**Success Probability**
- *Tooltip:* "Estimated likelihood of achieving this goal based on your current plan. Green (>75%) = on track, Yellow (50-75%) = at risk, Red (<50%) = off track"

**Flexibility**
- *Tooltip:* "How adaptable this goal is in terms of timeline and amount"

**Update Progress Form**
- *Tooltip:* "Enter your current saved amount and click Update to refresh your progress"

**Recommended Asset Allocation**
- *Tooltip:* "Suggested investment mix based on your goal's timeframe, importance, and flexibility"

## Parameter Settings Page

### Inflation Parameters

**General Inflation**
- *Tooltip:* "The overall inflation rate used for general calculations. Higher values create more conservative long-term projections."

**Education Inflation**
- *Tooltip:* "Specific inflation rate for education costs, which historically exceed general inflation. Affects education goal calculations."

**Medical Inflation**
- *Tooltip:* "Specific inflation rate for healthcare costs, which typically rise faster than general inflation. Affects retirement and insurance calculations."

### Asset Return Parameters

**Equity Returns**
- *Tooltip:* "Expected annual returns from stock investments. Different risk profiles (conservative, moderate, aggressive) have different expected returns."

**Debt Returns**
- *Tooltip:* "Expected annual returns from fixed-income investments like bonds and deposits. Varies by risk level selected."

**Gold Returns**
- *Tooltip:* "Expected annual returns from gold investments, including physical gold and gold ETFs."

**Real Estate Appreciation**
- *Tooltip:* "Expected annual appreciation rate for real estate investments, excluding rental income."

### Retirement Parameters

**Corpus Multiplier**
- *Tooltip:* "Multiple of annual expenses needed for retirement corpus. Higher values create more conservative retirement plans."

**Life Expectancy**
- *Tooltip:* "Age used for planning the longevity of retirement funds. Consider family history and health factors when adjusting."

**Withdrawal Rate**
- *Tooltip:* "Annual percentage of retirement corpus that can be safely withdrawn. Lower rates create more conservative retirement plans."

### Rules of Thumb

**Emergency Fund Months**
- *Tooltip:* "Recommended months of expenses to keep in your emergency fund. Consider job security and family needs when adjusting."

**Savings Rate**
- *Tooltip:* "Recommended percentage of income to save. Higher values accelerate goal achievement but require stricter budgeting."

**Debt Service Ratio**
- *Tooltip:* "Maximum percentage of income recommended for debt payments. Exceeding this may indicate financial stress."

## Financial Planning Scenario Tutorials

### Getting Started Tutorial

**Emergency Fund Calculator**
- *Help text:* "This calculator helps you determine how much you need in your emergency fund based on your monthly expenses."
- *Tooltip:* "The calculator multiplies your monthly expenses by the recommended number of months to determine your target emergency fund amount."

**Debt Elimination Calculator**
- *Help text:* "This calculator helps you create a plan to eliminate high-interest debt."
- *Tooltip:* "Enter your debts with balances and interest rates to get a prioritized repayment plan that minimizes interest costs."

### Retirement Planning Tutorial

**Retirement Needs Calculator**
- *Help text:* "This calculator helps estimate how much you need to save for retirement."
- *Tooltip:* "Enter your current age, retirement age, and expected annual expenses in retirement to calculate your target retirement corpus."

**Savings Rate Calculator**
- *Help text:* "This calculator determines how much you need to save monthly to reach your retirement goal."
- *Tooltip:* "Based on your retirement target, current savings, and timeline, this calculates the required monthly contribution."

### Education Planning Tutorial

**Education Fund Calculator**
- *Help text:* "This calculator helps plan for education expenses."
- *Tooltip:* "Enter the education type, duration, and expected annual costs to calculate the total amount needed, adjusted for education inflation."

### Home Purchase Tutorial

**Home Affordability Calculator**
- *Help text:* "This calculator helps determine how much home you can afford."
- *Tooltip:* "Based on your income, existing debts, and down payment, this calculates the maximum property value within recommended affordability guidelines."

**Down Payment Calculator**
- *Help text:* "This calculator helps plan your home down payment savings."
- *Tooltip:* "Enter your target property value and desired down payment percentage to calculate your savings goal."