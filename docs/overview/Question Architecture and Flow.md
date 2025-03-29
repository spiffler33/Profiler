# Question Architecture & Flow

## Core Question Categories

The core tier consists of essential questions grouped into the following categories:

### 1. Demographics
- **Age**: Impacts risk capacity and investment horizon
- **Employment Type**: Affects income stability and emergency fund requirements
- **Dependents**: Influences insurance needs and protection planning
- **Health Status**: Affects emergency fund sizing and insurance requirements
- **Risk Appetite**: Subjective risk tolerance (-1, 0, 1 scale)
- **Financial Maturity**: Knowledge level and decision-making approach
- **Market Outlook**: Personal view on market conditions
- **Location**: Geographic context for recommendations

### 2. Financial Basics
- **Monthly Expenses**: Foundation for emergency fund calculation
- **Savings Percentage**: Key indicator of financial health
- **Current Savings & Investments**: Starting point for planning

### 3. Assets and Debts
- **Debts**: Total outstanding liabilities
- **Is Housing Loan**: Special flag for housing debt

### 4. Special Cases
- **Business Value**: For business owners
- **Real Estate Value**: For property owners
- **Real Estate Type**: Classification of property holdings

## Next-Level Question Design

Next-level questions provide context and qualification to core answers. They help weigh the impact of initial responses and provide deeper insights.

### Approach:
1. **Contextual Follow-ups**: Ask questions that add nuance to basic data points
2. **Conditional Branching**: Different follow-ups based on initial answers
3. **Timing Strategy**: Can be asked immediately after core questions or in a separate deepening phase

### Examples By Category:

#### Demographics Deepening
- **Dependents**: "You mentioned having X dependents. Could you clarify their relationship to you and how financially dependent they are on your income?"
- **Health Status**: "You indicated your health status is X. Does this affect your ability to work, or require ongoing medical expenses?"
- **Employment**: "As a self-employed person, how stable would you say your income has been over the past 2 years?"

#### Financial Basics Deepening
- **Current Savings**: "Could you share roughly how your current savings are distributed? For example, what percentage is in fixed deposits, equity, or other investments?"
- **Monthly Expenses**: "Of your monthly expenses, approximately what percentage would you consider essential (housing, food, utilities)?"

#### Assets and Debts Deepening
- **Housing Loan**: "Regarding your home loan, how would you rate the sellability of your property if needed? Is it in a high-demand location?"
- **Debts**: "What types of debts do you currently have, and what are their approximate interest rates?"

#### Special Cases Deepening
- **Business Value**: "What percentage of your net worth is tied to your business assets?"
- **Real Estate**: "Do you plan to hold this property long-term or sell it within the next 5 years?"

## Behavioral Questions Tier

Behavioral questions assess psychological aspects of financial decision-making:

### Key Behavioral Areas:
1. **Loss Aversion**: Reaction to market downturns
2. **FOMO (Fear of Missing Out)**: Following market trends
3. **Overconfidence**: Self-assessment of financial knowledge
4. **Social Proof**: Influence of others' financial decisions
5. **Mental Accounting**: How money from different sources is valued
6. **Anchoring Bias**: Attachment to reference points in valuations

### Implementation Strategy:
- Scenario-based questions
- Hypothetical market situations
- Self-assessment of emotional reactions
- Past behavior reflection questions

## Question Flow Logic

### Core Flow Principles:
1. **Category Completion**: Track progress within each question category
2. **Prioritization**: Complete core questions before moving to next-level
3. **Contextual Relevance**: Next-level questions should relate directly to previous answers
4. **Session Awareness**: Remember what was asked previously
5. **Adaptability**: Adjust flow based on time available and user engagement

### Flow Algorithm:
1. Begin with unanswered core questions from Demographics category
2. Once Demographics is complete, move to Financial Basics
3. Complete Assets and Debts questions
4. Address Special Cases questions if applicable
5. For each completed core question, offer relevant next-level follow-ups
6. Once all core and next-level questions reach 80% completion, introduce behavioral questions
7. Periodically prompt for life event updates for existing profiles

## Life Event Update Mechanism

### Triggering Events:
- Job change
- Relocation
- Marriage/Divorce
- Child birth/adoption
- Major asset purchase/sale
- Significant inheritance
- Health status change

### Implementation:
1. Periodic life event check-in prompt for existing users
2. If life event identified, trigger specific question set
3. Create a new profile version to track changes
4. Preserve history for trend analysis
5. Re-evaluate core assumptions based on new information

## Technical Implementation Guidelines

### Question Definition Schema:
```json
{
  "id": "unique_question_id",
  "text": "Question text",
  "type": "core|next_level|behavioral",
  "category": "demographics|financial_basics|assets_and_debts|special_cases",
  "input_type": "text|number|select|slider|radio",
  "options": ["Option1", "Option2"],  // For select/radio types
  "min": 0,  // For number/slider types
  "max": 100,  // For number/slider types
  "required": true,
  "order": 1,  // Display order within category
  "help_text": "Explanation of why we ask this question",
  "depends_on": {  // Conditional display logic
    "question_id": "another_question_id",
    "value": "specific_value"
  },
  "validation": {
    "type": "number|string|boolean",
    "min": 0,
    "max": 100,
    "pattern": "regex_pattern"
  }
}
```

### Answer Storage Schema:
```json
{
  "id": "unique_answer_id",
  "question_id": "question_id",
  "answer": "user's answer",
  "timestamp": "ISO datetime"
}
```

### Flow Management:
- Use a state machine approach for question flow
- Track completion percentages by category
- Implement priority rules for question selection
- Maintain session context between interactions
- Log question and answer history for analysis

---

This document serves as the blueprint for implementing the question architecture and flow logic of the Financial Profiler system.
