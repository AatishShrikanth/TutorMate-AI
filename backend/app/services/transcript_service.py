import re
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional, Tuple

# Patch the session globally once
#session = requests.Session()
#session.verify = False
# TranscriptApi._TranscriptApi__session = session

class TranscriptService:
    def __init__(self):
        pass
    
    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(youtube_url))
            if match:
                return match.group(1)
        return None
    
    def get_transcript(self, youtube_url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get transcript from YouTube URL
        Returns: (transcript_text, error_message)
        """
        try:
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                return None, "Invalid YouTube URL format"
            
            # Try to get transcript - using the correct API method
            import requests
            from youtube_transcript_api._api import TranscriptApi

            TranscriptApi._TranscriptApi__session = requests.Session()
            TranscriptApi._TranscriptApi__session.verify = False
            api = YouTubeTranscriptApi()
            transcript_result = api.fetch(video_id)
            
            # Format transcript as plain text - accessing the text attribute
            transcript_text = " ".join([snippet.text for snippet in transcript_result])
            
            # Clean up the text
            transcript_text = self.clean_transcript(transcript_text)
            
            return transcript_text, None
            
        except Exception as e:
            error_msg = f"Failed to extract transcript: {str(e)}"
            return None, error_msg
    
    def clean_transcript(self, text: str) -> str:
        """Clean and format transcript text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common transcript artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove [Music], [Applause], etc.
        text = re.sub(r'\(.*?\)', '', text)  # Remove (inaudible), etc.
        
        # Clean up punctuation
        text = text.strip()
        
        return text
    
    def validate_transcript(self, transcript: str) -> bool:
        """Validate if transcript has sufficient content"""
        if not transcript or len(transcript.strip()) < 50:
            return False
        return True
