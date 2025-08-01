from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from enum import Enum

class LanguageEnum(str, Enum):
    ENGLISH = "english"
    SPANISH = "spanish"
    FRENCH = "french"
    GERMAN = "german"
    HINDI = "hindi"

class TranscriptRequest(BaseModel):
    youtube_url: Optional[HttpUrl] = None
    transcript_text: Optional[str] = None
    target_language: LanguageEnum = LanguageEnum.ENGLISH

class ActionStep(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_time: Optional[str] = None
    completed: bool = False

class PracticeQuestion(BaseModel):
    question_id: int
    question: str
    question_type: str  # "multiple_choice", "true_false", "short_answer"
    options: Optional[List[str]] = None  # For multiple choice questions
    correct_answer: str
    explanation: str
    difficulty: str  # "easy", "medium", "hard"
    topic: str

class TutorialSummary(BaseModel):
    title: str
    short_summary: str
    detailed_summary: str
    duration: Optional[str] = None
    difficulty_level: str
    key_topics: List[str]

class ProcessedTutorial(BaseModel):
    summary: TutorialSummary
    action_steps: List[ActionStep]
    practice_questions: List[PracticeQuestion] = []
    original_language: str
    target_language: str
    processing_time: float
    original_transcript: Optional[str] = None  # Store for AI chat context

class ExportRequest(BaseModel):
    tutorial_data: ProcessedTutorial
    export_format: str = "markdown"  # markdown, pdf, json

class ChatRequest(BaseModel):
    tutorial_data: dict  # Changed from ProcessedTutorial to dict for flexibility
    user_message: str
    chat_history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    response: str
    timestamp: float
