import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import statistics
from collections import Counter
import locale
import re

class ProfileAnalyticsService:
    """
    Service for analyzing financial profiles and generating insights.
    Processes both structured core data and extracted insights from next-level questions.
    """
    
    def __init__(self, profile_manager):
        """
        Initialize the profile analytics service.
        
        Args:
            profile_manager: DatabaseProfileManager for accessing profiles
        """
        self.profile_manager = profile_manager
        logging.basicConfig(level=logging.INFO)
        
        # Define mapping of core questions to analytics dimensions
        self.dimension_mappings = {
            # Risk dimension
            "risk": {
                "demographics_risk_appetite": {
                    "weight": 0.4,
                    "mapping": {
                        "Conservative (-1)": 2,
                        "Moderate (0)": 5,
                        "Aggressive (1)": 8
                    }
                },
                "demographics_age": {
                    "weight": 0.2,
                    "transform": lambda age: max(1, min(10, 10 - (int(age) - 20) / 5)) if age else 5
                },
                "demographics_dependents": {
                    "weight": 0.2,
                    "transform": lambda deps: max(2, min(8, 8 - int(deps))) if deps is not None else 5
                },
                "demographics_health_status": {
                    "weight": 0.2,
                    "mapping": {
                        "Excellent": 8,
                        "Good": 6,
                        "Fair": 4,
                        "Poor": 2
                    }
                }
            },
            
            # Financial knowledge dimension
            "knowledge": {
                "demographics_financial_maturity": {
                    "weight": 0.7,
                    "mapping": {
                        "Beginner": 2,
                        "Intermediate": 5,
                        "Advanced": 8,
                        "Expert": 10
                    }
                },
                "demographics_market_outlook": {
                    "weight": 0.3,
                    "mapping": {
                        "Bearish (Negative)": 3,
                        "Neutral": 5,
                        "Bullish (Positive)": 7
                    }
                }
            },
            
            # Financial stability dimension
            "stability": {
                "financial_basics_savings_percentage": {
                    "weight": 0.4,
                    "transform": lambda pct: max(1, min(10, int(pct) / 5)) if pct is not None else 5
                },
                "financial_basics_monthly_expenses": {
                    "weight": 0.3,
                    "transform": lambda exp: None  # Relative to income, need both values
                },
                "assets_debts_total_debt": {
                    "weight": 0.3,
                    "transform": lambda debt: None  # Relative to savings, need both values
                }
            }
        }
        
    @staticmethod
    def format_inr(amount: Union[int, float, str]) -> str:
        """
        Format a number as Indian Rupees (INR) with proper thousands separators.
        
        Args:
            amount: The amount to format
            
        Returns:
            Formatted string with Rupee symbol (₹) and Indian number format
        """
        try:
            # Convert to float first
            amount_float = float(amount)
            
            # Convert to integer if it's a whole number
            if amount_float.is_integer():
                amount_float = int(amount_float)
                
            # Format according to Indian numbering system (lakh, crore)
            # For example: 10,00,000 (ten lakh) instead of 1,000,000 (one million)
            str_amount = str(amount_float)
            
            # Handle decimals
            if '.' in str_amount:
                whole, decimal = str_amount.split('.')
            else:
                whole, decimal = str_amount, ""
                
            # Format whole number part with Indian system
            if len(whole) > 3:
                # Add comma after first 3 digits from right
                result = whole[-3:]
                whole = whole[:-3]
                
                # Add comma after every 2 digits from right
                while whole:
                    result = whole[-2:] + "," + result if whole[-2:] else whole + "," + result
                    whole = whole[:-2]
            else:
                result = whole
                
            # Add decimal if exists
            if decimal:
                result = result + "." + decimal
                
            # Add Rupee symbol
            return f"₹{result}"
        except (ValueError, TypeError):
            # Return original with Rupee symbol if we can't format it
            return f"₹{amount}"
    
    def generate_profile_analytics(self, profile_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive analytics for a profile.
        
        Args:
            profile_id: The profile ID to analyze
            
        Returns:
            Dictionary of analytics and insights
        """
        profile = self.profile_manager.get_profile(profile_id)
        if not profile:
            logging.error(f"Profile {profile_id} not found")
            return {"error": "Profile not found"}
        
        # Check if there are answers in the profile
        if not profile.get('answers'):
            logging.warning(f"Profile {profile_id} has no answers to analyze")
            return {
                "error": "No profile data to analyze",
                "profile_id": profile_id,
                "profile_name": profile.get("name", "Unknown"),
                "generated_at": datetime.now().isoformat(),
                "dimensions": {},
                "investment_profile": {
                    "type": "Balanced",
                    "description": "A balanced approach to risk and return.",
                    "allocation": {
                        "Fixed_Income": 40,
                        "Large_Cap_Equity": 25,
                        "Mid_Cap_Equity": 15,
                        "Small_Cap_Equity": 10,
                        "International_Equity": 5,
                        "Alternative_Investments": 5
                    }
                },
                "financial_health_score": {
                    "score": 50,
                    "status": "Unknown",
                    "metrics": {}
                },
                "behavioral_profile": {
                    "traits": {},
                    "summary": "Complete profile questions to generate your financial personality profile",
                    "strengths": [],
                    "challenges": []
                },
                "key_insights": ["Complete profile questions to generate financial insights"],
                "recommendations": ["Complete profile questions to receive personalized recommendations"]
            }
        
        # Extract all answers from the profile
        answers = {a['question_id']: a['answer'] for a in profile.get('answers', [])}
        
        try:
            # Initialize analytics result
            analytics = {
                "profile_id": profile_id,
                "profile_name": profile.get("name", "Unknown"),
                "generated_at": datetime.now().isoformat(),
                "dimensions": self._calculate_dimensions(answers),
                "answer_summary": self._generate_answer_summary(profile),
                "investment_profile": self._determine_investment_profile(answers),
                "financial_health_score": self._calculate_financial_health(answers),
                "behavioral_profile": self._generate_behavioral_profile(answers),
                "key_insights": self._extract_key_insights(profile),
                "recommendations": self._generate_recommendations(profile)
            }
            
            return analytics
        except Exception as e:
            logging.error(f"Error generating analytics for profile {profile_id}: {str(e)}")
            return {
                "error": f"Error generating analytics: {str(e)}",
                "profile_id": profile_id,
                "profile_name": profile.get("name", "Unknown"),
                "generated_at": datetime.now().isoformat(),
                "dimensions": {},
                "investment_profile": {
                    "type": "Balanced",
                    "description": "A balanced approach to risk and return.",
                    "allocation": {}
                },
                "financial_health_score": {
                    "score": 50,
                    "status": "Unknown",
                    "metrics": {}
                },
                "behavioral_profile": {
                    "traits": {},
                    "summary": "Error analyzing profile data",
                    "strengths": [],
                    "challenges": []
                },
                "key_insights": ["Error analyzing profile data"],
                "recommendations": ["Please try again or contact support if the issue persists"]
            }
    
    def _calculate_dimensions(self, answers: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate analytics dimensions based on profile answers.
        
        Args:
            answers: Dictionary of question_id -> answer
            
        Returns:
            Dictionary of dimension scores
        """
        dimensions = {}
        
        # Process each dimension
        for dimension, mappings in self.dimension_mappings.items():
            dimension_score = 0
            total_weight = 0
            
            # Process each contributing question
            for question_id, config in mappings.items():
                if question_id in answers:
                    raw_answer = answers[question_id]
                    weight = config.get("weight", 1.0)
                    score = None
                    
                    # Convert answer to score using mapping or transform
                    if "mapping" in config and raw_answer in config["mapping"]:
                        score = config["mapping"][raw_answer]
                    elif "transform" in config:
                        score = config["transform"](raw_answer)
                    
                    if score is not None:
                        dimension_score += score * weight
                        total_weight += weight
            
            # Calculate weighted average if we have data
            if total_weight > 0:
                dimensions[dimension] = round(dimension_score / total_weight, 1)
        
        # Get LLM-analyzed dimensions from next-level questions
        for question_id, answer in answers.items():
            # Check for LLM-extracted insights
            if question_id.endswith("_insights") and isinstance(answer, dict):
                self._incorporate_llm_insights(dimensions, answer)
        
        return dimensions
    
    def _incorporate_llm_insights(self, dimensions: Dict[str, float], insights: Dict[str, Any]) -> None:
        """
        Incorporate LLM-extracted insights into dimensions.
        
        Args:
            dimensions: Analytics dimensions dict to update
            insights: LLM-extracted insights
        """
        # Process risk scores
        if "risk_scores" in insights:
            risk_scores = insights["risk_scores"]
            
            # Update or initialize risk dimension with average of LLM scores
            risk_values = [score for score in risk_scores.values() if isinstance(score, (int, float))]
            if risk_values:
                # If we already have a risk dimension from core questions, blend it
                if "risk" in dimensions:
                    dimensions["risk"] = round((dimensions["risk"] + sum(risk_values) / len(risk_values)) / 2, 1)
                else:
                    dimensions["risk"] = round(sum(risk_values) / len(risk_values), 1)
        
        # Process knowledge scores
        if "knowledge_scores" in insights:
            knowledge_scores = insights["knowledge_scores"]
            
            # Update or initialize knowledge dimension
            knowledge_values = [score for score in knowledge_scores.values() if isinstance(score, (int, float))]
            if knowledge_values:
                if "knowledge" in dimensions:
                    dimensions["knowledge"] = round((dimensions["knowledge"] + sum(knowledge_values) / len(knowledge_values)) / 2, 1)
                else:
                    dimensions["knowledge"] = round(sum(knowledge_values) / len(knowledge_values), 1)
        
        # Add India-specific dimensions if available
        if "india_specific" in insights:
            india_scores = insights["india_specific"]
            
            # Create a new India-specific dimension
            india_values = [score for score in india_scores.values() if isinstance(score, (int, float))]
            if india_values:
                dimensions["india_context"] = round(sum(india_values) / len(india_values), 1)
        
        # Create a goal orientation dimension
        if "goal_scores" in insights:
            goal_scores = insights["goal_scores"]
            
            goal_values = [score for score in goal_scores.values() if isinstance(score, (int, float))]
            if goal_values:
                dimensions["goal_orientation"] = round(sum(goal_values) / len(goal_values), 1)
    
    def _generate_answer_summary(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a structured summary of the most important profile answers.
        
        Args:
            profile: User profile
            
        Returns:
            Dictionary with categorized answers summary
        """
        # Extract all answers
        answers = {a['question_id']: a['answer'] for a in profile.get('answers', [])}
        
        # Define key questions to include in summary
        key_questions = {
            "demographics": [
                "demographics_age", 
                "demographics_dependents", 
                "demographics_employment_type", 
                "demographics_risk_appetite"
            ],
            "financial_basics": [
                "financial_basics_monthly_expenses", 
                "financial_basics_savings_percentage", 
                "financial_basics_current_savings"
            ],
            "assets_and_debts": [
                "assets_debts_total_debt", 
                "assets_debts_housing_loan"
            ]
        }
        
        # Define monetary fields that need INR formatting
        monetary_fields = [
            "financial_basics_monthly_expenses",
            "financial_basics_current_savings",
            "assets_debts_total_debt",
            "special_cases_business_value",
            "special_cases_real_estate_value"
        ]
        
        # Build summary by category
        summary = {}
        for category, question_ids in key_questions.items():
            category_summary = {}
            for qid in question_ids:
                if qid in answers:
                    # Remove the category prefix for cleaner keys
                    key = qid.replace(f"{category}_", "")
                    
                    # Format monetary values as INR
                    if qid in monetary_fields:
                        try:
                            # Only format if it's a number
                            category_summary[key] = self.format_inr(answers[qid])
                        except (ValueError, TypeError):
                            category_summary[key] = answers[qid]
                    else:
                        category_summary[key] = answers[qid]
                        
            if category_summary:
                summary[category] = category_summary
        
        # Extract and summarize insights from LLM analysis
        insight_summary = self._summarize_llm_insights(answers)
        if insight_summary:
            summary["extracted_insights"] = insight_summary
        
        return summary
    
    def _summarize_llm_insights(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize key insights extracted by LLM from next-level responses.
        
        Args:
            answers: Dictionary of question_id -> answer
            
        Returns:
            Dictionary with summarized insights
        """
        # Look for insights in answers
        all_insights = {}
        
        for question_id, answer in answers.items():
            if question_id.endswith("_insights") and isinstance(answer, dict):
                # Extract key facts, concerns, and opportunities
                if "extracted_facts" in answer and isinstance(answer["extracted_facts"], list):
                    all_insights.setdefault("key_facts", []).extend(answer["extracted_facts"])
                
                if "concerns" in answer and isinstance(answer["concerns"], list):
                    all_insights.setdefault("concerns", []).extend(answer["concerns"])
                
                if "opportunities" in answer and isinstance(answer["opportunities"], list):
                    all_insights.setdefault("opportunities", []).extend(answer["opportunities"])
                    
                # Extract investment profile type if available
                if "investment_profile_type" in answer:
                    all_insights["investment_profile_type"] = answer["investment_profile_type"]
                    
                # Extract financial priorities
                if "financial_priorities" in answer and isinstance(answer["financial_priorities"], list):
                    all_insights.setdefault("financial_priorities", []).extend(answer["financial_priorities"])
        
        # Deduplicate and limit size of lists
        if "key_facts" in all_insights:
            all_insights["key_facts"] = list(dict.fromkeys(all_insights["key_facts"]))[:5]
            
        if "concerns" in all_insights:
            all_insights["concerns"] = list(dict.fromkeys(all_insights["concerns"]))[:3]
            
        if "opportunities" in all_insights:
            all_insights["opportunities"] = list(dict.fromkeys(all_insights["opportunities"]))[:3]
            
        if "financial_priorities" in all_insights:
            # Count occurrences of each priority and take the top 5
            counter = Counter(all_insights["financial_priorities"])
            all_insights["financial_priorities"] = [item for item, _ in counter.most_common(5)]
        
        return all_insights
    
    def _generate_behavioral_profile(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a financial behavioral profile based on behavioral question answers and insights.
        
        Args:
            answers: Dictionary of question_id -> answer
            
        Returns:
            Dictionary with behavioral profile information
        """
        # Initialize behavioral profile with default values
        behavioral_profile = {
            "traits": {},
            "summary": "Financial personality profile not yet established",
            "strengths": [],
            "challenges": [],
            "dominant_bias": None,
            "completion": 0  # 0-100% completion of behavioral assessment
        }
        
        # Get behavioral question insights
        behavioral_insights = {}
        for question_id, answer in answers.items():
            if question_id.endswith("_insights") and question_id.startswith("behavioral_") and isinstance(answer, dict):
                behavioral_insights[question_id] = answer
        
        # If no behavioral insights, return default profile
        if not behavioral_insights:
            return behavioral_profile
            
        # Count the behavioral questions answered
        behavioral_questions_answered = len([qid for qid in answers.keys() if qid.startswith("behavioral_") and not qid.endswith("_insights")])
        
        # Update completion percentage (assuming target of 4 questions)
        behavioral_profile["completion"] = min(100, (behavioral_questions_answered / 4) * 100)
        
        # Aggregate behavioral indicator scores
        aggregated_traits = {}
        
        for insight_id, insight in behavioral_insights.items():
            # Process behavioral indicators
            if "behavioral_indicators" in insight and isinstance(insight["behavioral_indicators"], dict):
                for trait, score in insight["behavioral_indicators"].items():
                    if isinstance(score, (int, float)):
                        if trait not in aggregated_traits:
                            aggregated_traits[trait] = []
                        aggregated_traits[trait].append(score)
            
            # Collect behavioral strengths
            if "behavioral_strengths" in insight and isinstance(insight["behavioral_strengths"], list):
                for strength in insight["behavioral_strengths"]:
                    if strength not in behavioral_profile["strengths"]:
                        behavioral_profile["strengths"].append(strength)
            
            # Collect behavioral challenges
            if "behavioral_challenges" in insight and isinstance(insight["behavioral_challenges"], list):
                for challenge in insight["behavioral_challenges"]:
                    if challenge not in behavioral_profile["challenges"]:
                        behavioral_profile["challenges"].append(challenge)
            
            # Collect primary bias information
            if "primary_bias" in insight and insight["primary_bias"]:
                # Count occurrences of each primary bias
                if not behavioral_profile["dominant_bias"]:
                    behavioral_profile["dominant_bias"] = insight["primary_bias"]
                    
            # Get behavioral summary
            if "behavioral_summary" in insight and insight["behavioral_summary"]:
                # Use the most recent summary or the one with highest confidence
                if behavioral_profile["summary"] == "Financial personality profile not yet established" or \
                   (insight.get("confidence_score", 0) > 0.7):
                    behavioral_profile["summary"] = insight["behavioral_summary"]
        
        # Calculate average score for each trait
        average_traits = {}
        for trait, scores in aggregated_traits.items():
            if scores:
                average_traits[trait] = round(sum(scores) / len(scores), 1)
                
        # Add traits to profile
        behavioral_profile["traits"] = average_traits
        
        # Limit strengths and challenges to top 3 each
        behavioral_profile["strengths"] = behavioral_profile["strengths"][:3]
        behavioral_profile["challenges"] = behavioral_profile["challenges"][:3]
        
        # If we have traits but summary hasn't been updated, generate a default summary
        if average_traits and behavioral_profile["summary"] == "Financial personality profile not yet established":
            # Generate a more detailed summary based on the traits
            if len(average_traits) >= 2:  # If we have enough data to make a meaningful statement
                # Identify dominant traits (traits with highest values)
                dominant_traits = sorted(average_traits.items(), key=lambda x: x[1], reverse=True)[:2]
                
                trait_descriptions = {
                    "loss_aversion": "sensitivity to financial losses",
                    "recency_bias": "focus on recent financial events",
                    "herd_mentality": "tendency to follow market trends",
                    "overconfidence": "confidence in financial decisions",
                    "fomo": "fear of missing investment opportunities",
                    "emotional_investing": "emotional approach to investing",
                    "discipline": "financial discipline",
                    "information_processing": "thoroughness in financial research"
                }
                
                # Create a personalized summary
                trait_texts = []
                for trait, value in dominant_traits:
                    trait_name = trait_descriptions.get(trait, trait.replace("_", " "))
                    if value >= 7:
                        trait_texts.append(f"high {trait_name}")
                    elif value <= 4:
                        trait_texts.append(f"cautious {trait_name}")
                    else:
                        trait_texts.append(f"balanced {trait_name}")
                
                if trait_texts:
                    behavioral_profile["summary"] = f"Your financial personality shows {' and '.join(trait_texts)}, which influences your approach to financial decisions."
                else:
                    behavioral_profile["summary"] = "Your financial personality profile shows a mix of traits that influence your financial decisions."
        
        return behavioral_profile

    def _determine_investment_profile(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the user's investment profile based on answers and insights.
        
        Args:
            answers: Dictionary of question_id -> answer
            
        Returns:
            Dictionary with investment profile details
        """
        # Default profile is balanced
        profile_type = "Balanced"
        
        # Extract risk appetite from core question if available
        if "demographics_risk_appetite" in answers:
            risk_mapping = {
                "Conservative (-1)": "Conservative",
                "Moderate (0)": "Balanced",
                "Aggressive (1)": "Aggressive"
            }
            profile_type = risk_mapping.get(answers["demographics_risk_appetite"], "Balanced")
        
        # Check if we have LLM-derived investment profile type
        for qid, answer in answers.items():
            if qid.endswith("_insights") and isinstance(answer, dict):
                if "investment_profile_type" in answer:
                    profile_type = answer["investment_profile_type"]
                    break
        
        # Define allocations based on profile type
        allocations = {
            "Conservative": {
                "Fixed_Income": 60,
                "Large_Cap_Equity": 20,
                "Mid_Cap_Equity": 10,
                "Small_Cap_Equity": 0,
                "International_Equity": 5,
                "Alternative_Investments": 5
            },
            "Moderately Conservative": {
                "Fixed_Income": 50,
                "Large_Cap_Equity": 25,
                "Mid_Cap_Equity": 15,
                "Small_Cap_Equity": 0,
                "International_Equity": 5,
                "Alternative_Investments": 5
            },
            "Balanced": {
                "Fixed_Income": 40,
                "Large_Cap_Equity": 25,
                "Mid_Cap_Equity": 15,
                "Small_Cap_Equity": 10,
                "International_Equity": 5,
                "Alternative_Investments": 5
            },
            "Moderately Aggressive": {
                "Fixed_Income": 25,
                "Large_Cap_Equity": 30,
                "Mid_Cap_Equity": 20,
                "Small_Cap_Equity": 10,
                "International_Equity": 10,
                "Alternative_Investments": 5
            },
            "Aggressive": {
                "Fixed_Income": 10,
                "Large_Cap_Equity": 30,
                "Mid_Cap_Equity": 25,
                "Small_Cap_Equity": 15,
                "International_Equity": 15,
                "Alternative_Investments": 5
            }
        }
        
        # Get allocation for this profile type
        profile_allocation = allocations.get(profile_type, allocations["Balanced"])
        
        return {
            "type": profile_type,
            "allocation": profile_allocation,
            "description": self._get_profile_description(profile_type)
        }
    
    def _get_profile_description(self, profile_type: str) -> str:
        """Get a description for the investment profile type"""
        descriptions = {
            "Conservative": "Preservation of capital is the primary goal. Willing to accept lower returns to avoid risk.",
            "Moderately Conservative": "Primarily focused on preservation with some growth. Willing to accept modest risk for modest returns.",
            "Balanced": "Equal emphasis on growth and preservation. Comfortable with moderate risk for moderate returns.",
            "Moderately Aggressive": "Primarily focused on growth. Willing to accept higher risk for higher returns.",
            "Aggressive": "Growth is the primary goal. Willing to accept significant risk for potential high returns."
        }
        return descriptions.get(profile_type, "A balanced approach to risk and return.")
    
    def _calculate_financial_health(self, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate financial health metrics based on profile answers.
        
        Args:
            answers: Dictionary of question_id -> answer
            
        Returns:
            Dictionary of financial health metrics
        """
        health_metrics = {
            "score": 0,
            "status": "Unknown",
            "metrics": {},
            "strengths": [],
            "weaknesses": []
        }
        
        # Calculate emergency fund needs based on monthly expenses
        if "financial_basics_monthly_expenses" in answers:
            try:
                # Extract raw numeric values for calculations
                monthly_expenses = float(answers["financial_basics_monthly_expenses"])
                
                if monthly_expenses > 0:
                    # Don't calculate a ratio, just note the recommended amounts
                    min_emergency_fund = monthly_expenses * 6
                    recommended_emergency_fund = monthly_expenses * 9
                    
                    # Add formatted INR values for display
                    health_metrics["metrics"]["monthly_expenses_inr"] = self.format_inr(monthly_expenses)
                    health_metrics["metrics"]["min_emergency_fund_inr"] = self.format_inr(min_emergency_fund)
                    health_metrics["metrics"]["recommended_emergency_fund_inr"] = self.format_inr(recommended_emergency_fund)
                    
                    # Check if user has explicitly answered about emergency fund
                    if "goals_emergency_fund_exists" in answers and "goals_emergency_fund_months" in answers:
                        fund_exists = answers["goals_emergency_fund_exists"]
                        months_coverage = answers["goals_emergency_fund_months"]
                        
                        if fund_exists == "Yes" and months_coverage in ['6-9 months', 'More than 9 months']:
                            health_metrics["strengths"].append(f"Has adequate emergency fund covering {months_coverage}")
                        elif fund_exists == "Yes" and months_coverage == '5-6 months':
                            health_metrics["strengths"].append(f"Has near-adequate emergency fund covering {months_coverage}")
                        else:
                            health_metrics["weaknesses"].append(f"Emergency fund inadequate or non-existent (recommendation: {self.format_inr(recommended_emergency_fund)})")
                    else:
                        health_metrics["weaknesses"].append(f"Emergency fund status unknown (recommendation: {self.format_inr(recommended_emergency_fund)})")
            except (ValueError, TypeError):
                pass
        
        # Calculate savings rate
        if "financial_basics_savings_percentage" in answers:
            try:
                savings_rate = float(answers["financial_basics_savings_percentage"])
                health_metrics["metrics"]["savings_rate"] = savings_rate
                
                # Evaluate savings rate
                if savings_rate < 10:
                    health_metrics["weaknesses"].append(f"Savings rate ({savings_rate}%) below recommended 10%")
                elif savings_rate >= 20:
                    health_metrics["strengths"].append(f"Excellent savings rate ({savings_rate}%)")
                else:
                    health_metrics["strengths"].append(f"Good savings rate ({savings_rate}%)")
            except (ValueError, TypeError):
                pass
        
        # Calculate debt-to-savings ratio
        if ("assets_debts_total_debt" in answers and 
            "financial_basics_current_savings" in answers):
            try:
                debt = float(answers["assets_debts_total_debt"])
                savings = float(answers["financial_basics_current_savings"])
                
                # Add formatted INR values for display
                health_metrics["metrics"]["total_debt_inr"] = self.format_inr(debt)
                
                if savings > 0:
                    debt_ratio = debt / savings
                    health_metrics["metrics"]["debt_to_savings_ratio"] = round(debt_ratio, 1)
                    
                    # Evaluate debt ratio
                    if debt_ratio > 2:
                        health_metrics["weaknesses"].append(f"High debt ({self.format_inr(debt)}) to savings ratio ({debt_ratio:.1f})")
                    elif debt_ratio < 0.5:
                        health_metrics["strengths"].append(f"Low debt ({self.format_inr(debt)}) to savings ratio ({debt_ratio:.1f})")
                    else:
                        health_metrics["metrics"]["debt_savings_description"] = f"Total debt {self.format_inr(debt)} is {debt_ratio:.1f}x your savings"
            except (ValueError, TypeError):
                pass
        
        # Calculate overall score (0-100)
        score = 50  # Default middle score
        
        # Adjust based on metrics
        # Check if we have emergency fund information from user responses
        if "goals_emergency_fund_exists" in answers and "goals_emergency_fund_months" in answers:
            fund_exists = answers["goals_emergency_fund_exists"]
            months_coverage = answers["goals_emergency_fund_months"]
            
            # Add points based on emergency fund status
            if fund_exists == "Yes" and months_coverage in ['6-9 months', 'More than 9 months']:
                score += 15  # Full points for adequate emergency fund
            elif fund_exists == "Yes" and months_coverage == '5-6 months':
                score += 10  # Partial points for near-adequate emergency fund
            elif fund_exists == "Yes":
                score += 5   # Some points for having an emergency fund
            else:
                score -= 5   # Penalty for explicitly not having an emergency fund
        
        if "savings_rate" in health_metrics["metrics"]:
            rate = health_metrics["metrics"]["savings_rate"]
            score += min(20, rate * 1.0)  # Up to +20 points
        
        if "debt_to_savings_ratio" in health_metrics["metrics"]:
            ratio = health_metrics["metrics"]["debt_to_savings_ratio"]
            if ratio > 0:
                score -= min(20, ratio * 10)  # Up to -20 points
        
        # Set final score and status
        health_metrics["score"] = round(max(0, min(100, score)))
        
        # Determine status based on score
        if health_metrics["score"] >= 80:
            health_metrics["status"] = "Excellent"
        elif health_metrics["score"] >= 60:
            health_metrics["status"] = "Good"
        elif health_metrics["score"] >= 40:
            health_metrics["status"] = "Fair"
        else:
            health_metrics["status"] = "Needs Attention"
        
        return health_metrics
    
    def _extract_key_insights(self, profile: Dict[str, Any]) -> List[str]:
        """
        Extract key insights from the profile.
        
        Args:
            profile: User profile
            
        Returns:
            List of key insights
        """
        insights = []
        answers = {a['question_id']: a['answer'] for a in profile.get('answers', [])}
        
        # Age-based insights
        if "demographics_age" in answers:
            try:
                age = int(answers["demographics_age"])
                if age < 30:
                    insights.append("Young investor with long time horizon - can take more equity exposure")
                elif age >= 60:
                    insights.append("Retirement age investor - focus on income generation and preservation")
                elif age >= 45:
                    insights.append("Mid to late career - balance growth with increasing conservatism")
                else:
                    insights.append("Prime earning years - focus on growth and retirement planning")
            except (ValueError, TypeError):
                pass
        
        # Dependents-based insights
        if "demographics_dependents" in answers:
            try:
                dependents = int(answers["demographics_dependents"])
                if dependents > 0:
                    insights.append(f"Has {dependents} dependents - consider life insurance and education planning")
            except (ValueError, TypeError):
                pass
        
        # Extract LLM-generated insights
        for qid, answer in answers.items():
            if qid.endswith("_insights") and isinstance(answer, dict):
                if "extracted_facts" in answer and isinstance(answer["extracted_facts"], list):
                    insights.extend([fact for fact in answer["extracted_facts"][:2] if fact not in insights])
        
        return insights
    
    def _generate_recommendations(self, profile: Dict[str, Any]) -> List[str]:
        """
        Generate financial recommendations based on profile analysis including behavioral traits.
        
        Args:
            profile: User profile
            
        Returns:
            List of recommendations
        """
        recommendations = []
        answers = {a['question_id']: a['answer'] for a in profile.get('answers', [])}
        
        # Check for behavioral insights to incorporate into recommendations
        behavioral_profile = self._generate_behavioral_profile(answers)
        behavioral_traits = behavioral_profile.get('traits', {})
        
        # Emergency fund recommendations
        try:
            if "financial_basics_monthly_expenses" in answers:
                expenses = float(answers["financial_basics_monthly_expenses"])
                
                if expenses > 0:
                    # Check if user has explicitly answered about emergency fund
                    if "goals_emergency_fund_exists" in answers:
                        fund_exists = answers["goals_emergency_fund_exists"]
                        
                        if fund_exists != "Yes" or "goals_emergency_fund_months" not in answers:
                            # Calculate recommended amount
                            recommended_fund = expenses * 9
                            recommendations.append(f"Build emergency fund to cover 6-9 months of expenses (approx. {self.format_inr(recommended_fund)})")
                        elif fund_exists == "Yes" and answers["goals_emergency_fund_months"] not in ['6-9 months', 'More than 9 months']:
                            # Inadequate emergency fund
                            recommended_fund = expenses * 9
                            recommendations.append(f"Increase emergency fund to cover at least 6 months of expenses (target: {self.format_inr(recommended_fund)})")
                    else:
                        # No information about emergency fund
                        recommended_fund = expenses * 9
                        recommendations.append(f"Establish emergency fund to cover 6-9 months of expenses (approx. {self.format_inr(recommended_fund)})")
        except (ValueError, TypeError):
            pass
        
        # Savings rate recommendations
        try:
            if "financial_basics_savings_percentage" in answers:
                savings_rate = float(answers["financial_basics_savings_percentage"])
                if savings_rate < 10:
                    recommendations.append("Increase savings rate to at least 10-15% of income")
                elif savings_rate < 20:
                    recommendations.append("Consider increasing savings rate for faster wealth accumulation")
        except (ValueError, TypeError):
            pass
        
        # Debt recommendations
        try:
            if "assets_debts_total_debt" in answers:
                debt = float(answers["assets_debts_total_debt"])
                if debt > 0:
                    recommendations.append("Create a debt reduction strategy prioritizing high-interest debt")
        except (ValueError, TypeError):
            pass
        
        # Age-based recommendations
        try:
            if "demographics_age" in answers:
                age = int(answers["demographics_age"])
                if age < 30:
                    recommendations.append("Start retirement planning early through tax-advantaged investment vehicles")
                elif age >= 45:
                    recommendations.append("Review retirement readiness and consider catch-up contributions")
                elif age >= 60:
                    recommendations.append("Consider transition to more conservative asset allocation")
        except (ValueError, TypeError):
            pass
        
        # LLM-based recommendations
        for qid, answer in answers.items():
            if qid.endswith("_insights") and isinstance(answer, dict):
                if "opportunities" in answer and isinstance(answer["opportunities"], list):
                    for opportunity in answer["opportunities"][:2]:
                        if opportunity not in recommendations:
                            recommendations.append(opportunity)
        
        # Add behavioral trait-specific recommendations
        if behavioral_traits:
            # Check for high loss aversion
            if behavioral_traits.get('loss_aversion', 0) >= 7:
                recommendations.append("Consider how loss aversion may be affecting your investment decisions")
                
            # Check for high FOMO
            if behavioral_traits.get('fomo', 0) >= 7:
                recommendations.append("Be mindful of fear of missing out when making investment decisions")
                
            # Check for high overconfidence
            if behavioral_traits.get('overconfidence', 0) >= 7:
                recommendations.append("Consider seeking diverse perspectives to balance confidence in investment decisions")
                
            # Check for high emotional investing
            if behavioral_traits.get('emotional_investing', 0) >= 7:
                recommendations.append("Consider implementing a rules-based approach to reduce emotional influences on investing")
                
            # Check for low discipline
            if behavioral_traits.get('discipline', 0) <= 4 and behavioral_traits.get('discipline', 0) > 0:
                recommendations.append("Establish consistent financial review routines to improve discipline")
                
            # Check for low information processing
            if behavioral_traits.get('information_processing', 0) <= 4 and behavioral_traits.get('information_processing', 0) > 0:
                recommendations.append("Consider using a systematic research approach before making financial decisions")
        
        # Add standard recommendations if we don't have enough
        if len(recommendations) < 3:
            standard_recs = [
                "Consider tax-efficient investment strategies for wealth accumulation",
                "Review insurance coverage to ensure adequate protection",
                "Develop a consistent investment strategy aligned with your risk profile",
                "Consider consulting a financial advisor for personalized guidance"
            ]
            
            for rec in standard_recs:
                if rec not in recommendations:
                    recommendations.append(rec)
                    if len(recommendations) >= 5:
                        break
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def compare_profiles(self, profile_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple profiles along key dimensions.
        
        Args:
            profile_ids: List of profile IDs to compare
            
        Returns:
            Dictionary with comparison data
        """
        if len(profile_ids) < 2:
            return {"error": "Need at least two profiles to compare"}
        
        profiles = []
        for pid in profile_ids:
            profile = self.profile_manager.get_profile(pid)
            if profile:
                profiles.append(profile)
        
        if len(profiles) < 2:
            return {"error": "Could not find enough valid profiles to compare"}
        
        # Generate analytics for each profile
        analytics_list = []
        for profile in profiles:
            analytics = self.generate_profile_analytics(profile['id'])
            analytics_list.append(analytics)
        
        # Create comparison data
        comparison = {
            "profiles": [{"id": a["profile_id"], "name": a["profile_name"]} for a in analytics_list],
            "dimensions": {},
            "investment_profiles": [],
            "financial_health": [],
            "generated_at": datetime.now().isoformat()
        }
        
        # Compare dimensions
        dimension_keys = set()
        for analytics in analytics_list:
            if "dimensions" in analytics:
                dimension_keys.update(analytics["dimensions"].keys())
        
        for key in dimension_keys:
            comparison["dimensions"][key] = {
                "values": [a.get("dimensions", {}).get(key) for a in analytics_list],
                "avg": statistics.mean([a.get("dimensions", {}).get(key, 0) for a in analytics_list 
                                        if a.get("dimensions", {}).get(key) is not None])
            }
        
        # Compare investment profiles
        for analytics in analytics_list:
            if "investment_profile" in analytics:
                comparison["investment_profiles"].append({
                    "profile_id": analytics["profile_id"],
                    "type": analytics["investment_profile"]["type"]
                })
        
        # Compare financial health
        for analytics in analytics_list:
            if "financial_health_score" in analytics:
                comparison["financial_health"].append({
                    "profile_id": analytics["profile_id"],
                    "score": analytics["financial_health_score"]["score"],
                    "status": analytics["financial_health_score"]["status"]
                })
        
        return comparison