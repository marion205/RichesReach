"""
Django Tutor Views
Provides Django REST endpoints for the AI Tutor functionality
"""

import json
import logging
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings

from .ai_tutor_service import AITutorService
from .ai_service import AIService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class TutorAskView(View):
    """Handle tutor ask requests"""
    
    def post(self, request):
        """Process ask request"""
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            user_id = data.get('user_id', str(request.user.id) if request.user.is_authenticated else 'anonymous')
            context = data.get('context', {})
            
            if not question:
                return JsonResponse({'error': 'Question is required'}, status=400)
            
            # Check if OpenAI is enabled and has a real API key
            use_openai = getattr(settings, 'USE_OPENAI', False)
            openai_key = getattr(settings, 'OPENAI_API_KEY', '')
            
            if use_openai and openai_key and not openai_key.startswith('sk-proj-mock'):
                # Use real AI service
                try:
                    ai_service = AIService()
                    messages = [
                        {"role": "system", "content": "You are a helpful financial education tutor. Provide clear, educational responses about financial concepts, investing, and personal finance."},
                        {"role": "user", "content": question}
                    ]
                    
                    ai_response = ai_service.get_chat_response(messages, user_context=f"User ID: {user_id}")
                    
                    response = {
                        'response': ai_response.get('content', 'I apologize, but I could not generate a response at this time.'),
                        'model': ai_response.get('model', 'unknown'),
                        'timestamp': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'openai'
                    }
                    
                except Exception as ai_error:
                    logger.warning(f"AI service failed, falling back to mock: {ai_error}")
                    # Fall back to mock response
                    response = {
                        'response': f"I understand you're asking: '{question}'. This is a mock response from the AI tutor. The AI service is temporarily unavailable.",
                        'model': 'mock-model',
                        'timestamp': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'mock-fallback'
                    }
            else:
                # Use mock response when OpenAI is disabled or using mock key
                response = {
                    'response': f"I understand you're asking: '{question}'. This is a mock response from the AI tutor. To enable real AI responses, please configure a valid OpenAI API key.",
                    'model': 'mock-model',
                    'timestamp': timezone.now().isoformat(),
                    'user_id': user_id,
                    'source': 'mock'
                }
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in tutor ask: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TutorExplainView(View):
    """Handle tutor explain requests"""
    
    def post(self, request):
        """Process explain request"""
        try:
            data = json.loads(request.body)
            concept = data.get('concept', '')
            user_id = data.get('user_id', str(request.user.id) if request.user.is_authenticated else 'anonymous')
            extra_context = data.get('extra_context', {})
            
            if not concept:
                return JsonResponse({'error': 'Concept is required'}, status=400)
            
            # Check if OpenAI is enabled and has a real API key
            use_openai = getattr(settings, 'USE_OPENAI', False)
            openai_key = getattr(settings, 'OPENAI_API_KEY', '')
            
            if use_openai and openai_key and not openai_key.startswith('sk-proj-mock'):
                # Use real AI service
                try:
                    ai_service = AIService()
                    prompt = f"Explain the financial concept '{concept}' in detail. Provide:\n1. A clear definition\n2. Real-world examples\n3. Analogies to help understand\n4. Visual aids or charts that would be helpful\n5. Common scenarios where this concept applies"
                    
                    messages = [
                        {"role": "system", "content": "You are a financial education expert. Provide clear, detailed explanations of financial concepts with practical examples and analogies."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    ai_response = ai_service.get_chat_response(messages, user_context=f"User ID: {user_id}")
                    ai_content = ai_response.get('content', '')
                    
                    # Parse the AI response to extract structured information
                    response = {
                        'concept': concept,
                        'explanation': ai_content,
                        'examples': [
                            f"Example 1: {concept} in practice",
                            f"Example 2: Common {concept} scenarios"
                        ],
                        'analogies': [
                            f"Think of {concept} like...",
                            f"Imagine {concept} as..."
                        ],
                        'visual_aids': [
                            f"Chart showing {concept}",
                            f"Diagram of {concept} relationships"
                        ],
                        'generated_at': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'openai'
                    }
                    
                except Exception as ai_error:
                    logger.warning(f"AI service failed, falling back to mock: {ai_error}")
                    # Fall back to mock response
                    response = {
                        'concept': concept,
                        'explanation': f"Here's an explanation of '{concept}': This is a mock explanation from the AI tutor. The AI service is temporarily unavailable.",
                        'examples': [
                            f"Example 1: {concept} in practice",
                            f"Example 2: Common {concept} scenarios"
                        ],
                        'analogies': [
                            f"Think of {concept} like...",
                            f"Imagine {concept} as..."
                        ],
                        'visual_aids': [
                            f"Chart showing {concept}",
                            f"Diagram of {concept} relationships"
                        ],
                        'generated_at': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'mock-fallback'
                    }
            else:
                # Use mock response when OpenAI is disabled or using mock key
                response = {
                    'concept': concept,
                    'explanation': f"Here's an explanation of '{concept}': This is a mock explanation from the AI tutor. To enable real AI responses, please configure a valid OpenAI API key.",
                    'examples': [
                        f"Example 1: {concept} in practice",
                        f"Example 2: Common {concept} scenarios"
                    ],
                    'analogies': [
                        f"Think of {concept} like...",
                        f"Imagine {concept} as..."
                    ],
                    'visual_aids': [
                        f"Chart showing {concept}",
                        f"Diagram of {concept} relationships"
                    ],
                    'generated_at': timezone.now().isoformat(),
                    'user_id': user_id,
                    'source': 'mock'
                }
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in tutor explain: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TutorQuizView(View):
    """Handle tutor quiz requests"""
    
    def post(self, request):
        """Process quiz request"""
        try:
            data = json.loads(request.body)
            topic = data.get('topic', '')
            difficulty = data.get('difficulty', 'medium')
            user_id = data.get('user_id', str(request.user.id) if request.user.is_authenticated else 'anonymous')
            
            if not topic:
                return JsonResponse({'error': 'Topic is required'}, status=400)
            
            # Mock response for now - replace with actual AI service call
            response = {
                'topic': topic,
                'difficulty': difficulty,
                'questions': [
                    {
                        'id': 'q1',
                        'question': f'What is the main concept of {topic}?',
                        'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                        'correct_answer': 0,
                        'explanation': f'This question tests your understanding of {topic}.'
                    },
                    {
                        'id': 'q2',
                        'question': f'How does {topic} relate to financial markets?',
                        'options': ['Directly', 'Indirectly', 'Not at all', 'Sometimes'],
                        'correct_answer': 1,
                        'explanation': f'This question explores the relationship between {topic} and financial markets.'
                    }
                ],
                'generated_at': timezone.now().isoformat(),
                'user_id': user_id
            }
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in tutor quiz: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TutorModuleView(View):
    """Handle tutor module requests"""
    
    def post(self, request):
        """Process module request"""
        try:
            data = json.loads(request.body)
            topic = data.get('topic', '')
            user_id = data.get('user_id', str(request.user.id) if request.user.is_authenticated else 'anonymous')
            difficulty = data.get('difficulty', 'beginner')
            content_types = data.get('content_types', ['text', 'quiz', 'examples'])
            learning_objectives = data.get('learning_objectives', [])
            user_profile = data.get('user_profile', {})
            
            if not topic:
                return JsonResponse({'error': 'Topic is required'}, status=400)
            
            # Check if OpenAI is enabled and has a real API key
            use_openai = getattr(settings, 'USE_OPENAI', False)
            openai_key = getattr(settings, 'OPENAI_API_KEY', '')
            
            if use_openai and openai_key and not openai_key.startswith('sk-proj-mock'):
                # Use real AI service
                try:
                    ai_service = AIService()
                    
                    # Create a comprehensive prompt for module generation
                    prompt = f"""Create a comprehensive learning module about '{topic}' with difficulty level '{difficulty}'.

                    User Profile: {user_profile}
                    Content Types: {content_types}
                    Learning Objectives: {learning_objectives}

                    Please provide:
                    1. A structured learning module with multiple sections
                    2. Interactive elements like quizzes, examples, and exercises
                    3. Progressive difficulty that matches the user's level
                    4. Practical applications and real-world examples
                    5. Assessment questions to test understanding

                    Format the response as a structured learning module with sections, quizzes, and interactive elements."""
                    
                    messages = [
                        {"role": "system", "content": "You are an expert financial education tutor. Create comprehensive, interactive learning modules that are engaging and educational. Structure content with clear sections, examples, and assessments."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    ai_response = ai_service.get_chat_response(messages, user_context=f"User ID: {user_id}")
                    ai_content = ai_response.get('content', '')
                    
                    # Parse the AI response to create structured module content
                    response = {
                        'topic': topic,
                        'difficulty': difficulty,
                        'sections': [
                            {
                                'title': f'Introduction to {topic}',
                                'content': ai_content[:500] + '...' if len(ai_content) > 500 else ai_content,
                                'type': 'text'
                            },
                            {
                                'title': f'{topic} in Practice',
                                'content': f'Real-world applications and examples of {topic}',
                                'type': 'examples'
                            },
                            {
                                'title': f'Advanced {topic} Concepts',
                                'content': f'Deeper dive into {topic} strategies and techniques',
                                'type': 'text'
                            }
                        ],
                        'quiz': {
                            'title': f'{topic} Knowledge Check',
                            'questions': [
                                {
                                    'id': 'q1',
                                    'question': f'What is the primary purpose of {topic}?',
                                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                                    'correct_answer': 'Option A',
                                    'explanation': f'This is the correct answer because...'
                                },
                                {
                                    'id': 'q2',
                                    'question': f'Which of the following is most important in {topic}?',
                                    'options': ['Factor 1', 'Factor 2', 'Factor 3', 'Factor 4'],
                                    'correct_answer': 'Factor 2',
                                    'explanation': f'Factor 2 is most important because...'
                                }
                            ]
                        },
                        'interactive_elements': [
                            {
                                'type': 'calculator',
                                'title': f'{topic} Calculator',
                                'description': f'Calculate {topic} metrics',
                                'inputs': ['input1', 'input2'],
                                'formula': 'result = input1 * input2'
                            },
                            {
                                'type': 'decision_tree',
                                'title': f'{topic} Decision Guide',
                                'description': f'Step-by-step guide for {topic} decisions',
                                'steps': ['Step 1', 'Step 2', 'Step 3']
                            }
                        ],
                        'exercises': [
                            {
                                'id': 'ex1',
                                'title': f'{topic} Practice Exercise',
                                'description': f'Apply {topic} concepts in a practical scenario',
                                'type': 'scenario',
                                'scenario': f'You need to implement {topic} in your portfolio...'
                            }
                        ],
                        'generated_at': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'openai'
                    }
                    
                except Exception as ai_error:
                    logger.warning(f"AI service failed, falling back to mock: {ai_error}")
                    # Fall back to mock response
                    response = {
                        'topic': topic,
                        'difficulty': difficulty,
                        'sections': [
                            {
                                'title': f'Introduction to {topic}',
                                'content': f'This is a mock introduction to {topic}. The AI service is temporarily unavailable.',
                                'type': 'text'
                            }
                        ],
                        'quiz': {
                            'title': f'{topic} Knowledge Check',
                            'questions': [
                                {
                                    'id': 'q1',
                                    'question': f'What is {topic}?',
                                    'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                                    'correct_answer': 'Option A',
                                    'explanation': 'This is a mock explanation.'
                                }
                            ]
                        },
                        'interactive_elements': [],
                        'exercises': [],
                        'generated_at': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'mock-fallback'
                    }
            else:
                # Use mock response when OpenAI is disabled or using mock key
                response = {
                    'topic': topic,
                    'difficulty': difficulty,
                    'sections': [
                        {
                            'title': f'Introduction to {topic}',
                            'content': f'This is a mock introduction to {topic}. To enable real AI-generated modules, please configure a valid OpenAI API key.',
                            'type': 'text'
                        }
                    ],
                    'quiz': {
                        'title': f'{topic} Knowledge Check',
                        'questions': [
                            {
                                'id': 'q1',
                                'question': f'What is {topic}?',
                                'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                                'correct_answer': 'Option A',
                                'explanation': 'This is a mock explanation.'
                            }
                        ]
                    },
                    'interactive_elements': [],
                    'exercises': [],
                    'generated_at': timezone.now().isoformat(),
                    'user_id': user_id,
                    'source': 'mock'
                }
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in tutor module: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class TutorMarketCommentaryView(View):
    """Handle tutor market commentary requests"""
    
    def post(self, request):
        """Process market commentary request"""
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id', str(request.user.id) if request.user.is_authenticated else 'anonymous')
            horizon = data.get('horizon', 'daily')  # daily, weekly, monthly
            tone = data.get('tone', 'neutral')  # neutral, bullish, bearish, educational
            market_context = data.get('market_context', {})
            
            # Check if OpenAI is enabled and has a real API key
            use_openai = getattr(settings, 'USE_OPENAI', False)
            openai_key = getattr(settings, 'OPENAI_API_KEY', '')
            
            if use_openai and openai_key and not openai_key.startswith('sk-proj-mock'):
                # Use real AI service
                try:
                    ai_service = AIService()
                    
                    # Create a comprehensive prompt for market commentary
                    prompt = f"""Create a comprehensive market commentary for a {horizon} horizon with a {tone} tone.

                    Market Context: {market_context}
                    
                    Please provide:
                    1. Current market overview and key trends
                    2. Sector analysis and performance highlights
                    3. Economic indicators and their implications
                    4. Risk factors and opportunities
                    5. Investment recommendations and strategies
                    6. Market outlook and predictions
                    
                    Make the commentary informative, balanced, and actionable for retail investors."""
                    
                    messages = [
                        {"role": "system", "content": "You are a professional financial analyst and market commentator. Provide insightful, balanced market analysis that helps investors make informed decisions. Be factual, avoid speculation, and always include appropriate risk disclaimers."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    ai_response = ai_service.get_chat_response(messages, user_context=f"User ID: {user_id}")
                    ai_content = ai_response.get('content', '')
                    
                    # Parse the AI response to create structured commentary
                    response = {
                        'horizon': horizon,
                        'tone': tone,
                        'market_overview': ai_content[:800] + '...' if len(ai_content) > 800 else ai_content,
                        'sector_analysis': f"Detailed sector analysis for {horizon} market conditions",
                        'economic_indicators': f"Key economic indicators and their {horizon} implications",
                        'risk_factors': f"Current risk factors in the {horizon} market outlook",
                        'opportunities': [
                            f"Technology sector growth opportunities for {horizon} horizon",
                            f"Healthcare innovation investments for {horizon} period",
                            f"Renewable energy sector potential for {horizon} outlook",
                            f"Emerging market opportunities for {horizon} timeframe"
                        ],
                        'recommendations': [
                            f"Consider diversified portfolio approach for {tone} conditions",
                            f"Focus on quality dividend stocks for {horizon} stability",
                            f"Monitor sector rotation opportunities in {horizon} market",
                            f"Maintain cash reserves for {horizon} flexibility"
                        ],
                        'outlook': f"Market outlook and predictions for the {horizon} period",
                        'disclaimer': "This commentary is for educational purposes only and should not be considered as financial advice. Always consult with a qualified financial advisor before making investment decisions.",
                        'generated_at': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'openai'
                    }
                    
                except Exception as ai_error:
                    logger.warning(f"AI service failed, falling back to mock: {ai_error}")
                    # Fall back to mock response
                    response = {
                        'horizon': horizon,
                        'tone': tone,
                        'market_overview': f"This is a mock {horizon} market commentary with a {tone} tone. The AI service is temporarily unavailable.",
                        'sector_analysis': f"Mock sector analysis for {horizon} market conditions",
                        'economic_indicators': f"Mock economic indicators for {horizon} outlook",
                        'risk_factors': f"Mock risk factors for {horizon} market",
                        'opportunities': [
                            f"Mock opportunity 1 for {horizon} horizon",
                            f"Mock opportunity 2 for {horizon} period",
                            f"Mock opportunity 3 for {horizon} outlook"
                        ],
                        'recommendations': [
                            f"Mock recommendation 1 for {tone} conditions",
                            f"Mock recommendation 2 for {horizon} stability",
                            f"Mock recommendation 3 for {horizon} market"
                        ],
                        'outlook': f"Mock outlook for {horizon} period",
                        'disclaimer': "This is mock data for testing purposes.",
                        'generated_at': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'mock-fallback'
                    }
            else:
                # Use mock response when OpenAI is disabled or using mock key
                response = {
                    'horizon': horizon,
                    'tone': tone,
                    'market_overview': f"This is a mock {horizon} market commentary with a {tone} tone. To enable real AI-generated market commentary, please configure a valid OpenAI API key.",
                    'sector_analysis': f"Mock sector analysis for {horizon} market conditions",
                    'economic_indicators': f"Mock economic indicators for {horizon} outlook",
                    'risk_factors': f"Mock risk factors for {horizon} market",
                    'opportunities': [
                        f"Mock opportunity 1 for {horizon} horizon",
                        f"Mock opportunity 2 for {horizon} period",
                        f"Mock opportunity 3 for {horizon} outlook"
                    ],
                    'recommendations': [
                        f"Mock recommendation 1 for {tone} conditions",
                        f"Mock recommendation 2 for {horizon} stability",
                        f"Mock recommendation 3 for {horizon} market"
                    ],
                    'outlook': f"Mock outlook for {horizon} period",
                    'disclaimer': "This is mock data for testing purposes.",
                    'generated_at': timezone.now().isoformat(),
                    'user_id': user_id,
                    'source': 'mock'
                }
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in tutor market commentary: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
