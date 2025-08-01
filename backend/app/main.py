from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import time
import os

from models.schemas import TranscriptRequest, ProcessedTutorial, ExportRequest, ChatRequest, ChatResponse
from services.transcript_service import TranscriptService
from services.ai_service import AIService
from services.export_service import ExportService
from utils.helpers import validate_youtube_url

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="TutorMate AI API",
    description="Turn any tutorial into your personalized, step-by-step action plan",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8501", "http://127.0.0.1:8501"],  # React dev server and Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
transcript_service = TranscriptService()
ai_service = AIService()
export_service = ExportService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "TutorMate AI API is running!",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.post("/api/process-tutorial", response_model=ProcessedTutorial)
async def process_tutorial(request: TranscriptRequest):
    """
    Main endpoint to process a tutorial from YouTube URL or transcript text
    """
    start_time = time.time()
    
    try:
        # Get transcript text
        if request.youtube_url:
            if not validate_youtube_url(str(request.youtube_url)):
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")
            
            transcript_text, error = transcript_service.get_transcript(str(request.youtube_url))
            if error:
                raise HTTPException(status_code=400, detail=error)
                
        elif request.transcript_text:
            transcript_text = request.transcript_text
        else:
            raise HTTPException(status_code=400, detail="Either youtube_url or transcript_text must be provided")
        
        # Validate transcript
        if not transcript_service.validate_transcript(transcript_text):
            raise HTTPException(status_code=400, detail="Transcript is too short or invalid")
        
        # Process with AI (now includes practice questions)
        processed_tutorial = ai_service.process_tutorial(
            transcript=transcript_text,
            target_language=request.target_language.value
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        processed_tutorial.processing_time = processing_time
        
        return processed_tutorial
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_about_tutorial(request: ChatRequest):
    """
    Chat endpoint for AI assistant to answer questions about the tutorial
    """
    try:
        response = ai_service.chat_about_tutorial(
            tutorial_data=request.tutorial_data,
            user_message=request.user_message,
            chat_history=request.chat_history or []
        )
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/api/export")
async def export_tutorial(request: ExportRequest):
    """
    Export processed tutorial in different formats
    """
    try:
        if request.export_format.lower() == "markdown":
            content = export_service.export_to_markdown(request.tutorial_data)
            media_type = "text/markdown"
            filename = f"{request.tutorial_data.summary.title.replace(' ', '_')}.md"
            
        elif request.export_format.lower() == "json":
            content = export_service.export_to_json(request.tutorial_data)
            media_type = "application/json"
            filename = f"{request.tutorial_data.summary.title.replace(' ', '_')}.json"
            
        elif request.export_format.lower() == "checklist":
            content = export_service.export_to_checklist(request.tutorial_data)
            media_type = "text/plain"
            filename = f"{request.tutorial_data.summary.title.replace(' ', '_')}_checklist.txt"
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test AWS Bedrock connection
        test_response = ai_service._call_claude("Hello, respond with 'OK'")
        bedrock_status = "healthy" if "OK" in test_response else "unhealthy"
    except:
        bedrock_status = "unhealthy"
    
    return {
        "api_status": "healthy",
        "bedrock_status": bedrock_status,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
