import boto3
import json
import os
import time
from typing import Dict, Any, Optional, List
from models.schemas import TutorialSummary, ActionStep, ProcessedTutorial, PracticeQuestion, ChatResponse

class AIService:
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-runtime')
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0')
        self.current_transcript = ""  # Store current transcript for fallback questions
    
    def process_tutorial(self, transcript: str, target_language: str = "english") -> ProcessedTutorial:
        """
        Process tutorial transcript using Claude Haiku
        Returns complete processed tutorial data including practice questions
        """
        # Store transcript for fallback questions
        self.current_transcript = transcript
        
        # First get the main tutorial processing
        main_prompt = self._create_processing_prompt(transcript, target_language)
        
        try:
            main_response = self._call_claude(main_prompt)
            tutorial_data = self._parse_claude_response(main_response, target_language)
            
            # Always generate practice questions for any input
            print("Generating practice questions...")
            try:
                questions_prompt = self._create_questions_prompt(transcript, target_language)
                questions_response = self._call_claude(questions_prompt)
                practice_questions = self._parse_questions_response(questions_response)
                print(f"Generated {len(practice_questions)} practice questions")
            except Exception as e:
                print(f"Failed to generate practice questions: {str(e)}")
                practice_questions = self._create_content_based_fallback_questions()
            
            # Add practice questions and original transcript to tutorial data
            tutorial_data.practice_questions = practice_questions
            tutorial_data.original_transcript = transcript
            
            return tutorial_data
            
        except Exception as e:
            print(f"Error in process_tutorial: {str(e)}")
            # Create fallback tutorial data
            return self._create_fallback_tutorial(transcript, target_language, str(e))
    
    def chat_about_tutorial(self, tutorial_data: dict, user_message: str, chat_history: List[dict] = None) -> ChatResponse:
        """
        Handle chat questions about the tutorial content
        Only keeps the last user question for context, no full history
        """
        # Only use the last question from history for minimal context
        last_context = ""
        if chat_history and len(chat_history) >= 2:
            # Get the last user question and AI response
            last_user = None
            last_ai = None
            for msg in reversed(chat_history):
                if msg.get('role') == 'user' and last_user is None:
                    last_user = msg.get('content', '')
                elif msg.get('role') == 'assistant' and last_ai is None and last_user:
                    last_ai = msg.get('content', '')
                    break
            
            if last_user and last_ai:
                last_context = f"\nPrevious question: {last_user}\nPrevious answer: {last_ai[:200]}...\n"
        
        chat_prompt = self._create_chat_prompt_from_dict(tutorial_data, user_message, last_context)
        
        try:
            response = self._call_claude(chat_prompt)
            return ChatResponse(
                response=response,
                timestamp=time.time()
            )
        except Exception as e:
            raise Exception(f"Chat processing failed: {str(e)}")
    
    def _create_chat_prompt_from_dict(self, tutorial_data: dict, user_message: str, last_context: str) -> str:
        """Create prompt for chat about tutorial from dict data"""
        
        # Extract data safely from dict
        summary = tutorial_data.get('summary', {})
        title = summary.get('title', 'Tutorial')
        detailed_summary = summary.get('detailed_summary', '')
        key_topics = summary.get('key_topics', [])
        action_steps = tutorial_data.get('action_steps', [])
        target_language = tutorial_data.get('target_language', 'english')
        original_transcript = tutorial_data.get('original_transcript', '')
        
        # Build action steps text
        action_steps_text = ""
        for step in action_steps:
            step_num = step.get('step_number', 1)
            step_title = step.get('title', '')
            step_desc = step.get('description', '')
            action_steps_text += f"{step_num}. {step_title}: {step_desc}\n"
        
        return f"""
You are a helpful AI tutor assistant. You have access to a tutorial that the user has been studying. Answer their questions based on the tutorial content.

TUTORIAL INFORMATION:
Title: {title}
Summary: {detailed_summary}
Key Topics: {', '.join(key_topics)}

ORIGINAL TRANSCRIPT:
{original_transcript or "Transcript not available"}

ACTION STEPS:
{action_steps_text}

{last_context}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. Answer based ONLY on the tutorial content provided above
2. If the question is about something not covered in the tutorial, politely say so and offer to help with what is covered
3. Be conversational and helpful, but provide UNIQUE responses each time
4. If asked about specific topics, refer to the relevant parts of the tutorial
5. If asked to explain concepts, use examples from the tutorial when possible
6. Keep responses concise but informative (2-3 paragraphs maximum)
7. Use the target language: {target_language}
8. IMPORTANT: Provide fresh, varied responses - avoid repeating the same information in the same way
9. If this seems like a repeated question, acknowledge it and offer a different perspective or additional details

Please provide a helpful, unique response:
"""
    
    def _create_processing_prompt(self, transcript: str, target_language: str) -> str:
        """Create comprehensive prompt for Claude to process the tutorial"""
        return f"""
You are an expert tutorial analyzer. Please process this tutorial transcript and provide a structured response.

TRANSCRIPT:
{transcript}

INSTRUCTIONS:
1. Analyze the tutorial and create a comprehensive summary
2. Extract actionable learning steps as a checklist
3. For the detailed summary, provide it as a single string with bullet points separated by newlines
4. If target language is not English, translate all content to {target_language}
5. Maintain technical terms appropriately

Please respond with a JSON object in this exact format:
{{
    "title": "Tutorial title (inferred from content)",
    "short_summary": "2-3 sentence overview",
    "detailed_summary": "• Key concept 1 explained\\n• Key concept 2 explained\\n• Key concept 3 explained\\n• Important details and takeaways",
    "duration": "Estimated completion time",
    "difficulty_level": "Beginner/Intermediate/Advanced",
    "key_topics": ["topic1", "topic2", "topic3"],
    "action_steps": [
        {{
            "step_number": 1,
            "title": "Step title",
            "description": "Detailed description of what to do",
            "estimated_time": "5-10 minutes"
        }}
    ]
}}

TARGET LANGUAGE: {target_language}
Ensure all text content is in {target_language} if it's not English.
IMPORTANT: 
- The detailed_summary must be a single string value, not an object or array
- Use \\n to separate bullet points within the string
- Each bullet point should start with •
"""

    def _create_questions_prompt(self, transcript: str, target_language: str) -> str:
        """Create prompt for generating practice questions"""
        return f"""
You are an expert educator. Based on this tutorial transcript, create practice questions to test understanding of the SPECIFIC CONTENT.

TRANSCRIPT:
{transcript}

CRITICAL INSTRUCTIONS:
1. Read the transcript carefully and create questions about the ACTUAL CONTENT discussed
2. Questions must be based on specific topics, concepts, or steps mentioned in the transcript
3. Create 5-6 practice questions covering key concepts from the tutorial
4. Include a mix of question types: multiple choice, true/false, and short answer
5. Make questions practical and test real understanding of the content
6. Provide clear explanations for answers
7. If target language is not English, translate all content to {target_language}
8. ALWAYS generate questions regardless of transcript length
9. Return ONLY valid JSON - no markdown, no extra text, no control characters

RESPONSE FORMAT - Return ONLY this JSON structure:
{{
    "questions": [
        {{
            "question_id": 1,
            "question": "Based on the transcript, what is [specific concept mentioned]?",
            "question_type": "multiple_choice",
            "options": ["Option A from content", "Option B from content", "Option C from content", "Option D from content"],
            "correct_answer": "Option A from content",
            "explanation": "This is correct because the transcript specifically mentions...",
            "difficulty": "easy",
            "topic": "Specific topic from transcript"
        }},
        {{
            "question_id": 2,
            "question": "True or False: The transcript mentions [specific detail]",
            "question_type": "true_false",
            "options": ["True", "False"],
            "correct_answer": "True",
            "explanation": "This is true because the tutorial specifically covers...",
            "difficulty": "medium",
            "topic": "Specific topic from transcript"
        }},
        {{
            "question_id": 3,
            "question": "According to the tutorial, how would you [specific process mentioned]?",
            "question_type": "short_answer",
            "options": null,
            "correct_answer": "Based on the transcript, you would [specific steps mentioned]",
            "explanation": "The tutorial outlines these specific steps...",
            "difficulty": "hard",
            "topic": "Specific topic from transcript"
        }}
    ]
}}

TARGET LANGUAGE: {target_language}
IMPORTANT: 
- Base ALL questions on the actual transcript content
- Use specific details, terms, and concepts from the transcript
- Do not use generic questions
- Return only clean JSON without any markdown formatting
- Ensure all strings are properly escaped
"""

    def _create_chat_prompt(self, tutorial_data: ProcessedTutorial, user_message: str, last_context: str) -> str:
        """Create prompt for chat about tutorial with minimal context"""
        
        return f"""
You are a helpful AI tutor assistant. You have access to a tutorial that the user has been studying. Answer their questions based on the tutorial content.

TUTORIAL INFORMATION:
Title: {tutorial_data.summary.title}
Summary: {tutorial_data.summary.detailed_summary}
Key Topics: {', '.join(tutorial_data.summary.key_topics)}

ORIGINAL TRANSCRIPT:
{tutorial_data.original_transcript or "Transcript not available"}

ACTION STEPS:
{chr(10).join([f"{step.step_number}. {step.title}: {step.description}" for step in tutorial_data.action_steps])}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. Answer based ONLY on the tutorial content provided above
2. If the question is about something not covered in the tutorial, politely say so and offer to help with what is covered
3. Be conversational and helpful, but provide UNIQUE responses each time
4. If asked about specific topics, refer to the relevant parts of the tutorial
5. If asked to explain concepts, use examples from the tutorial when possible
6. Keep responses concise but informative (2-3 paragraphs maximum)
7. Use the target language: {tutorial_data.target_language}
8. IMPORTANT: Provide fresh, varied responses - avoid repeating the same information in the same way
9. If this seems like a repeated question, acknowledge it and offer a different perspective or additional details

Please provide a helpful, unique response:
"""
    
    def _call_claude(self, prompt: str) -> str:
        """Make API call to Claude via Bedrock"""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    def _parse_claude_response(self, response: str, target_language: str) -> ProcessedTutorial:
        """Parse Claude's JSON response into ProcessedTutorial model"""
        try:
            # Extract JSON from response (Claude sometimes adds extra text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            data = json.loads(json_str)
            
            # Ensure detailed_summary is a string
            detailed_summary = data.get('detailed_summary', '')
            if isinstance(detailed_summary, dict):
                # If it's a dict, try to extract meaningful content
                detailed_summary = str(detailed_summary)
            elif isinstance(detailed_summary, list):
                # If it's a list, join the items
                detailed_summary = '\n'.join([f"• {item}" for item in detailed_summary])
            elif not isinstance(detailed_summary, str):
                detailed_summary = str(detailed_summary)
            
            # Create TutorialSummary
            summary = TutorialSummary(
                title=str(data.get('title', 'Tutorial')),
                short_summary=str(data.get('short_summary', '')),
                detailed_summary=detailed_summary,
                duration=data.get('duration'),
                difficulty_level=str(data.get('difficulty_level', 'Intermediate')),
                key_topics=data.get('key_topics', []) if isinstance(data.get('key_topics'), list) else []
            )
            
            # Create ActionSteps
            action_steps = []
            for step_data in data.get('action_steps', []):
                step = ActionStep(
                    step_number=int(step_data.get('step_number', 1)),
                    title=str(step_data.get('title', '')),
                    description=str(step_data.get('description', '')),
                    estimated_time=step_data.get('estimated_time'),
                    completed=False
                )
                action_steps.append(step)
            
            return ProcessedTutorial(
                summary=summary,
                action_steps=action_steps,
                practice_questions=[],  # Will be populated separately
                original_language="english",  # Assuming input is English
                target_language=target_language,
                processing_time=0.0  # Will be calculated in the API endpoint
            )
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            print(f"Response content: {response[:500]}...")
            raise Exception(f"Failed to parse AI response: {str(e)}")
        except Exception as e:
            print(f"General parsing error: {str(e)}")
            print(f"Response content: {response[:500]}...")
            raise Exception(f"Error processing AI response: {str(e)}")
    
    def _parse_questions_response(self, response: str) -> List[PracticeQuestion]:
        """Parse Claude's questions response into PracticeQuestion models"""
        try:
            # Clean the response first - remove control characters and fix common issues
            cleaned_response = self._clean_json_response(response)
            
            # Extract JSON from response
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                print("No JSON found in questions response")
                return self._create_content_based_fallback_questions()
            
            json_str = cleaned_response[json_start:json_end]
            
            data = json.loads(json_str)
            
            practice_questions = []
            for q_data in data.get('questions', []):
                question = PracticeQuestion(
                    question_id=int(q_data.get('question_id', 1)),
                    question=str(q_data.get('question', '')),
                    question_type=str(q_data.get('question_type', 'multiple_choice')),
                    options=q_data.get('options') if q_data.get('options') else None,
                    correct_answer=str(q_data.get('correct_answer', '')),
                    explanation=str(q_data.get('explanation', '')),
                    difficulty=str(q_data.get('difficulty', 'medium')),
                    topic=str(q_data.get('topic', 'General'))
                )
                practice_questions.append(question)
            
            if not practice_questions:
                print("No questions found in parsed response")
                return self._create_content_based_fallback_questions()
            
            return practice_questions
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error in questions: {str(e)}")
            print(f"Cleaned response sample: {response[:300]}...")
            return self._create_content_based_fallback_questions()
        except Exception as e:
            print(f"Error processing questions response: {str(e)}")
            return self._create_content_based_fallback_questions()
    
    def _clean_json_response(self, response: str) -> str:
        """Clean JSON response by removing control characters and fixing common issues"""
        import re
        
        # Remove markdown code blocks first
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        # Remove control characters (except newlines and tabs)
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
        
        # Fix common JSON issues - be more careful with newlines
        # Only escape newlines that are inside JSON strings, not structural newlines
        lines = cleaned.split('\n')
        cleaned_lines = []
        in_string = False
        
        for line in lines:
            if line.strip():  # Skip empty lines
                # Simple heuristic: if line contains JSON structure, keep it
                if any(char in line for char in ['{', '}', '[', ']', ':', ',']):
                    cleaned_lines.append(line)
                else:
                    # This might be content inside a string, escape it
                    cleaned_lines.append(line.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'))
        
        cleaned = '\n'.join(cleaned_lines)
        
        return cleaned.strip()
    
    def _create_content_based_fallback_questions(self) -> List[PracticeQuestion]:
        """Create fallback questions that are more content-aware"""
        # Try to extract some basic info from the transcript
        transcript = self.current_transcript.lower()
        
        # Extract potential topics/keywords
        common_tech_terms = ['python', 'javascript', 'aws', 'cloud', 'database', 'api', 'web', 'server', 'network', 'security', 'data', 'machine learning', 'ai', 'docker', 'kubernetes', 'react', 'node', 'sql', 'html', 'css']
        found_topics = [term for term in common_tech_terms if term in transcript]
        
        # Get first few sentences for context
        sentences = self.current_transcript.split('.')[:3]
        context = '. '.join(sentences).strip()
        
        questions = []
        
        # Question 1: About main topic
        if found_topics:
            main_topic = found_topics[0].title()
            questions.append(PracticeQuestion(
                question_id=1,
                question=f"Based on the tutorial content, what is the main focus regarding {main_topic}?",
                question_type="short_answer",
                options=None,
                correct_answer=f"The tutorial focuses on {main_topic} concepts and their practical application",
                explanation=f"The tutorial content specifically mentions {main_topic} and related concepts",
                difficulty="easy",
                topic=main_topic
            ))
        else:
            questions.append(PracticeQuestion(
                question_id=1,
                question="What is the main topic or subject covered in this tutorial?",
                question_type="short_answer",
                options=None,
                correct_answer="The main topic discussed in the tutorial content",
                explanation="Review the tutorial title and key concepts to identify the primary subject matter",
                difficulty="easy",
                topic="Main Topic"
            ))
        
        # Question 2: True/False about content
        questions.append(PracticeQuestion(
            question_id=2,
            question="True or False: This tutorial provides practical, actionable information",
            question_type="true_false",
            options=["True", "False"],
            correct_answer="True",
            explanation="The tutorial content is designed to provide practical guidance and actionable steps",
            difficulty="easy",
            topic="Tutorial Structure"
        ))
        
        # Question 3: Multiple choice about approach
        if found_topics:
            topic = found_topics[0].title()
            questions.append(PracticeQuestion(
                question_id=3,
                question=f"According to the tutorial, what is the best approach to learning {topic}?",
                question_type="multiple_choice",
                options=[
                    "Follow the step-by-step process outlined",
                    "Skip directly to advanced topics",
                    "Ignore the foundational concepts",
                    "Only read without practicing"
                ],
                correct_answer="Follow the step-by-step process outlined",
                explanation=f"The tutorial emphasizes following a structured approach to learning {topic}",
                difficulty="medium",
                topic=topic
            ))
        else:
            questions.append(PracticeQuestion(
                question_id=3,
                question="What would be the first step you should take after studying this tutorial?",
                question_type="multiple_choice",
                options=[
                    "Review and understand the key concepts",
                    "Ignore the content completely", 
                    "Start with the most advanced topics",
                    "Skip all practice exercises"
                ],
                correct_answer="Review and understand the key concepts",
                explanation="The best approach after any tutorial is to review and understand the key concepts before moving forward",
                difficulty="medium",
                topic="Learning Strategy"
            ))
        
        return questions
    
    def _create_fallback_questions(self) -> List[PracticeQuestion]:
        """Create fallback questions when parsing fails"""
        return [
            PracticeQuestion(
                question_id=1,
                question="What was the main topic of this tutorial?",
                question_type="short_answer",
                options=None,
                correct_answer="Based on the tutorial content",
                explanation="Reflect on the key concepts discussed in the tutorial",
                difficulty="easy",
                topic="General"
            ),
            PracticeQuestion(
                question_id=2,
                question="True or False: This tutorial provided actionable steps",
                question_type="true_false",
                options=["True", "False"],
                correct_answer="True",
                explanation="The tutorial was processed into actionable steps",
                difficulty="easy",
                topic="General"
            )
        ]
    
    def _create_fallback_tutorial(self, transcript: str, target_language: str, error_msg: str) -> ProcessedTutorial:
        """Create fallback tutorial when AI processing fails"""
        # Extract basic info from transcript
        words = transcript.split()
        title = f"Tutorial ({len(words)} words)"
        
        # Create basic summary
        summary = TutorialSummary(
            title=title,
            short_summary="This tutorial covers various topics. Processing encountered some issues, but basic structure has been created.",
            detailed_summary="• Tutorial content was processed with limited AI analysis\n• Manual review may be needed for optimal results\n• Key concepts may need additional clarification",
            duration="Variable",
            difficulty_level="Intermediate",
            key_topics=["General Tutorial Content"]
        )
        
        # Create basic action steps
        action_steps = [
            ActionStep(
                step_number=1,
                title="Review Tutorial Content",
                description="Go through the original tutorial content to understand the main concepts.",
                estimated_time="10-15 minutes",
                completed=False
            ),
            ActionStep(
                step_number=2,
                title="Practice Key Concepts",
                description="Apply the concepts learned from the tutorial in practical exercises.",
                estimated_time="20-30 minutes",
                completed=False
            )
        ]
        
        return ProcessedTutorial(
            summary=summary,
            action_steps=action_steps,
            practice_questions=self._create_fallback_questions(),
            original_language="english",
            target_language=target_language,
            processing_time=0.0,
            original_transcript=transcript
        )
