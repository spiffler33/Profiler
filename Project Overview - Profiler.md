# Financial Profiler Project Overview

## Project Vision
We are building a sophisticated financial profiler system that captures user financial information through a multi-tiered question approach. The profiler will create comprehensive user profiles combining objective financial data and subjective behavioral preferences to enable personalized financial guidance.

## Core Focus
This project specifically focuses on the **Profiler Engine** component of a larger financial advisory ecosystem. The profiler will:

1. Ask structured questions in a conversational format
2. Capture responses and store them in profile JSON files
3. Progress through multiple question tiers (Core, Next-Level, Behavioral)
4. Track completion of different question categories
5. Eventually feed into an investment recommendation system

## Architecture Components

### 1. Question Flow Engine
- Manages the progression through question tiers
- Determines the next appropriate question based on previous answers
- Tracks completion percentages by category
- Implements a "funnel approach" moving from essential to deeper questions

### 2. Profile Management System
- Creates and updates user profile JSON files
- Maintains versioning for profiles as they evolve
- Tracks progress across question categories
- Ensures data persistence and consistency

### 3. LLM Integration (Future Enhancement)
- Uses Claude and GPT to clarify partial answers
- Analyzes sentiment and detects behavioral biases
- Generates follow-up questions based on previous responses
- Provides conversational context and explanations

### 4. Life Event Updates
- Handles major financial life changes (new job, relocation, etc.)
- Revises profiles based on new circumstances
- Creates new profile versions to track progress over time

## Question Tiers

### Core Tier (Must-Have Questions)
- Essential demographic information (age, employment, dependents, etc.)
- Basic financial parameters (income, expenses, savings)
- Initial risk assessment and financial maturity indicators
- Required for minimal viable profile generation

### Next-Level Tier
- More detailed questions about existing answers
- Contextual follow-ups that qualify or add nuance to core answers
- Category-specific expansions (debt breakdowns, income stability, etc.)
- Helps weigh or adjust the impact of core answers

### Behavioral Tier
- Psychological aspects of financial decision-making
- Scenario-based questions to detect biases (FOMO, overconfidence, etc.)
- Sentiment analysis to gauge emotional responses to markets
- Creates a more complete picture of the user's financial personality

## Technical Implementation
- Python-based backend with Flask web framework
- SQLite database with SQLAlchemy ORM
- JSON storage for profile data
- Modular architecture for easy expansion
- Strong focus on data persistence and consistency

## Success Metrics
- Profile completion rates
- Data consistency and persistence
- Question flow logic accuracy
- Logical progression between question tiers
- User satisfaction with the questioning process

---

**Note**: This document serves as the foundational reference for the Financial Profiler project. All development decisions should align with the vision and architecture outlined here.
