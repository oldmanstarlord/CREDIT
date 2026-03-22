"""
GenAI chatbot service: Context-aware assistant powered by OpenAI GPT-4o or Claude.

Helps users understand their credit score, loan terms, and next steps.
Works with SHAP explanations to translate model outputs to plain language.
"""

from typing import Dict, List, Optional, Tuple
import logging
import json
from datetime import datetime
import importlib

logger = logging.getLogger(__name__)


class ChatbotService:
    """
    Conversational assistant for credit application portal.
    
    Capabilities:
    - Explain credit scores and what factors affect them
    - Answer questions about loan application process
    - Provide next steps and ways to improve credit eligibility
    - Plain-English explanations of SHAP model factors
    
    Constraints:
    - Cannot make or override loan decisions
    - Cannot access other users' data
    - Cannot provide specific legal/financial advice
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: Optional[str] = None,
        site_url: Optional[str] = None,
        app_name: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ):
        """
        Initialize chatbot.
        
        Args:
            api_key: Provider API key from environment
            model: Model name ('gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo', etc.)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.fallback_models = [m for m in (fallback_models or []) if m and m.strip()]
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = None
        self._openai_mode = None
        self.last_model_used: Optional[str] = None
        self.used_fallback_response: bool = False
        
        if api_key:
            try:
                try:
                    openai_pkg = importlib.import_module("openai")
                    OpenAI = getattr(openai_pkg, "OpenAI")

                    client_kwargs = {"api_key": api_key}
                    if base_url:
                        client_kwargs["base_url"] = base_url

                    # OpenRouter supports app attribution headers.
                    if base_url and "openrouter.ai" in base_url:
                        default_headers = {}
                        if site_url:
                            default_headers["HTTP-Referer"] = site_url
                        if app_name:
                            default_headers["X-Title"] = app_name
                        if default_headers:
                            client_kwargs["default_headers"] = default_headers

                    self.client = OpenAI(**client_kwargs)
                    self._openai_mode = "v1"
                except Exception:
                    openai = importlib.import_module("openai")
                    openai.api_key = api_key
                    if base_url:
                        openai.base_url = base_url
                    self.client = openai
                    self._openai_mode = "legacy"
                logger.info(f"LLM client initialized (model: {model})")
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
        else:
            logger.warning("No LLM API key provided - chatbot will use fallback responses")
    
    def generate_system_prompt(self, user_context: Dict) -> str:
        """
        Generate system prompt with user-specific context.
        
        Args:
            user_context: {
                'user_category': str,
                'credit_score': int,
                'application_status': str,
                'top_positive_factors': List[str],
                'top_negative_factors': List[str]
            }
        
        Returns:
            System prompt for chatbot
        """
        return f"""You are a helpful loan assistance chatbot for Barclays Credit Intelligence Platform.

Your role is to help users understand their credit application, loan terms, and credit score in simple language.

User Context:
- Category: {user_context.get('user_category', 'Unknown')}
- Current Credit Score: {user_context.get('credit_score', 'N/A')} / 850
- Application Status: {user_context.get('application_status', 'Submitted')}

Top Factors Helping Your Score: {', '.join(user_context.get('top_positive_factors', ['None yet']))}
Top Factors Limiting Your Score: {', '.join(user_context.get('top_negative_factors', ['None yet']))}

Guidelines:
1. **Explain things simply** - use language appropriate for users with limited financial literacy
2. **Be empathetic** - many users applying here face financial hardship
3. **Never promise a specific decision** - you cannot approve/reject loans
4. **Explain SHAP factors in practical terms** - translate model factors to plain language
5. **Encourage improvement** - suggest concrete steps to improve their score
6. **Redirect politely** - if asked about other topics, stay focused on credit/loans
7. **Use their language** - respond in English or Hindi as the user uses
8. **Be honest** - if something is unclear, say so rather than guessing

When explaining a SHAP factor, follow this pattern:
"Your [factor name] score is [value], which is [above/below] average for [category]. This means [practical interpretation]. 
To improve, you could [specific suggestion]."

Examples:
- "Your income consistency score is 0.71, which is above average for gig workers. This means your earnings are relatively stable, which helps your score. To improve it further, try to maintain steady work patterns."
- "Your credit history shows late payments, which significantly lowers your score. You could improve by ensuring all payments go through on time over the next 3-6 months."

When a user seems distressed about their decision, offer:
"I understand this might be disappointing. Your score reflects where you are today, but credit is not permanent. Focus on [specific improvements], and you can reapply in 3-6 months with a stronger profile."
"""
    
    def chat(self, user_message: str, user_context: Dict, 
            conversation_history: List[Dict] = None) -> Tuple[str, List[Dict]]:
        """
        Process user message and generate response.
        
        Args:
            user_message: User's message
            user_context: User's credit application context
            conversation_history: Previous messages [{role, content}, ...]
        
        Returns:
            (response_text, updated_conversation_history)
        """
        if conversation_history is None:
            conversation_history = []
        
        # Add user message to history
        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        self.last_model_used = None
        self.used_fallback_response = False
        
        if not self.client:
            self.used_fallback_response = True
            return self._fallback_response(user_message, user_context), conversation_history
        
        try:
            system_prompt = self.generate_system_prompt(user_context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                *conversation_history
            ]

            candidate_models = [self.model, *self.fallback_models]
            # Keep order and remove duplicates.
            candidate_models = list(dict.fromkeys(candidate_models))

            assistant_message = ""
            total_tokens = None
            last_error = None

            for model_name in candidate_models:
                try:
                    if self._openai_mode == "v1":
                        response = self.client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            temperature=self.temperature,
                            max_tokens=self.max_tokens,
                            top_p=0.9,
                        )
                        assistant_message = (response.choices[0].message.content or "").strip()
                        total_tokens = getattr(response.usage, "total_tokens", None)
                    else:
                        response = self.client.ChatCompletion.create(
                            model=model_name,
                            messages=messages,
                            temperature=self.temperature,
                            max_tokens=self.max_tokens,
                            top_p=0.9,
                        )
                        assistant_message = (response.choices[0].message.content or "").strip()
                        usage = getattr(response, "usage", None)
                        total_tokens = getattr(usage, "total_tokens", None) if usage else None

                    self.last_model_used = model_name
                    break
                except Exception as model_error:
                    last_error = model_error
                    logger.warning(f"LLM call failed for model {model_name}: {model_error}")

            if not self.last_model_used:
                raise last_error or RuntimeError("No LLM model succeeded")
            
            # Add assistant response to history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Keep last 10 exchanges only (20 messages) to manage token usage
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            logger.info(f"Chat response generated (tokens: {total_tokens})")
            
            return assistant_message, conversation_history
        
        except Exception as e:
            logger.error(f"Error calling LLM provider: {e}")
            self.used_fallback_response = True
            fallback = self._fallback_response(user_message, user_context)
            conversation_history.append({
                "role": "assistant",
                "content": fallback
            })
            return fallback, conversation_history
    
    def _fallback_response(self, user_message: str, user_context: Dict) -> str:
        """
        Generate fallback response without OpenAI (for testing or API failures).
        
        Uses rule-based responses based on keywords.
        """
        user_msg_lower = user_message.lower()
        
        # Credit score questions
        if any(keyword in user_msg_lower for keyword in 
               ['credit score', 'score', 'how is my score', 'why is my score']):
            score = user_context.get('credit_score', 500)
            if score < 500:
                return ("Your credit score is currently quite low. This is because you're new to formal credit, "
                       "or you may have had some missed payments in the past. The good news is that credit is not permanent. "
                       "By making your next payments on time and building a positive track record, you can improve your score "
                       "significantly over 6-12 months. Our system takes alternative data (like bill payments and UPI transactions) "
                       "into account, so even without traditional credit history, you can qualify for loans.")
            elif score < 650:
                return (f"Your credit score is {score}, which is in the medium-risk range. This reflects a mix of positive signals "
                       "(like your category stability) and some concerns (like any missed payments or high debt). "
                       "Focus on on-time payments for the next 3 months, and you should see improvement.")
            else:
                return (f"Your credit score of {score} is solid! This reflects your strong repayment history or good income stability. "
                       "You should be in good position for loan approval or better terms.")
        
        # Income/earnings questions
        if any(keyword in user_msg_lower for keyword in 
               ['income', 'earnings', 'how much can i borrow', 'loan amount', 'afford']):
            return ("Your eligible loan amount depends on your income and how much you can afford to repay each month. "
                   "Typically, we approve loans where the monthly payment is no more than 30-40% of your income. "
                   "For example, if you earn ₹30,000/month, a loan with ₹9,000-12,000 EMI would be sustainable. "
                   "You'll see the loan recommendation after we process your application!")
        
        # Next steps / timeline
        if any(keyword in user_msg_lower for keyword in 
               ['how long', 'timeline', 'when', 'next', 'what happens', 'what comes next']):
            return ("Here's what happens next: (1) We verify your identity and documents, (2) Our AI analyzes your financial stability, "
                   "(3) A person on our team reviews your profile, (4) You'll receive a decision within 24-48 hours. The majority of "
                   "applications are processed within 48 hours, though some may need additional review. You'll get email and SMS updates!")
        
        # Improving score
        if any(keyword in user_msg_lower for keyword in 
               ['improve', 'better', 'increase', 'how to', 'increase score']):
            return ("Here are the top ways to improve your credit eligibility: (1) **Make payments on time** - Set reminders for all payments, "
                   "(2) **Reduce debt** - If you have existing loans, try to pay down the balance, (3) **Keep income stable** - Show consistent "
                   "earnings over time, (4) **Link your bank account** - This helps us verify your income and spending patterns, "
                   "(5) **Use UPI payments** - Regular digital transactions show financial responsibility, (6) **Build nominee support** - "
                   "If applicable, have an income guarantor improves your chances. Improvements are usually visible within 3-6 months!")
        
        # Default/generic response
        return ("I'm here to help with questions about your credit application, score, and next steps. Feel free to ask me about: "
               "- Why your credit score is what it is, - What factors are affecting your eligibility, - How to improve your score, "
               "- The application timeline, - What 'loan terms' mean. What would you like to know?")
    
    def explain_shap_factor_simple(self, factor_name: str, shap_value: float,
                                  feature_value: float, user_category: str) -> str:
        """
        Convert a SHAP explanation to plain English using fallback logic.
        
        Args:
            factor_name: Name of the feature (e.g., 'income_stability')
            shap_value: SHAP value (contribution to prediction)
            feature_value: Actual feature value for this applicant
            user_category: User's category (for context)
        
        Returns:
            Plain-English explanation
        """
        explanations = {
            'income_stability': {
                'negative': f"Your income shows high variability - it changes significantly month to month. For {user_category}s, "
                           f"this is common but makes it riskier to lend. Tip: Build 3-6 months of consistent income history.",
                'positive': f"Your income is stable and predictable. This is great - it means we can count on regular payments from you."
            },
            'repayment_capacity': {
                'negative': "Your monthly payment obligations are high relative to your income. We'd need to keep loan size small. "
                           "Tip: Pay down existing debts first, then reapply.",
                'positive': "You have good capacity to take on a loan payment relative to your income. This works in your favor!"
            },
            'transaction_consistency': {
                'negative': "Your bank and UPI transactions are irregular. We can't see a clear pattern of where your money goes. "
                           "Tip: Use your bank account for more daily transactions to build a clearer picture.",
                'positive': "Your transaction history shows healthy, regular patterns. We can see you manage money well."
            },
            'days_employed': {
                'negative': "You've been in your current job/work for a short time. We prefer to see 6+ months stability. "
                           "Tip: Reapply after you've been in your role longer.",
                'positive': "You have solid employment history, which reduces our risk."
            },
            'existing_defaults': {
                'negative': "Our records show you've missed payments before. But don't worry - if it was a while ago and you've "
                           "recovered, we can still work with you. Show consistent good behavior for 3-6 months.",
                'positive': "You have a clean payment history - no red flags. Great!"
            }
        }
        
        direction = 'positive' if shap_value > 0 else 'negative'
        return explanations.get(factor_name, {}).get(direction, 
                                                     f"{factor_name}: {shap_value:+.2f} impact on your score")
    
    def suggest_next_actions(self, user_context: Dict) -> List[str]:
        """
        Generate personalized next actions based on user's profile.
        
        Returns:
            Prioritized list of actionable steps
        """
        actions = []
        credit_score = user_context.get('credit_score', 500)
        status = user_context.get('application_status', 'submitted')
        category = user_context.get('user_category', 'unknown')
        
        # Score-based actions
        if credit_score < 500:
            actions.append("Your score is low right now. Focus on on-time payments for the next 3 months to rebuild.")
        elif credit_score < 650:
            actions.append("Your score is medium - getting closer! Keep payments on time for 2 more months.")
        else:
            actions.append("Your score is solid. You should be eligible for approval or better interest rates.")
        
        #Category-specific actions
        if category == 'farmer':
            actions.append("Document your harvest season income to strengthen your profile for next application.")
        elif category == 'gig_worker':
            actions.append("Link your Ola/Zomato/Uber account to help us verify your platform income directly.")
        elif category == 'msme_owner':
            actions.append("If GST registered, upload your last 3 months of GST returns to boost credibility.")
        elif category == 'homemaker':
            actions.append("Ensure your spouse/guardian's income documents are clear and verifiable.")
        
        # Status-based actions
        if status == 'submitted':
            actions.append("Your application is being reviewed. You'll get an update within 24-48 hours.")
        elif status == 'rejected':
            actions.append("Your application was not approved this time. Address the feedback and reapply in 3 months.")
        elif status == 'approved':
            actions.append("Congratulations! Check your email for next steps and loan agreement details.")
        
        return actions
