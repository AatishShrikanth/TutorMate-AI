import streamlit as st
import requests
import json
import time
from typing import Dict, Any, Optional

# Page config
st.set_page_config(
    page_title="TutorMate AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    /* Page background with sunset gradient */
    .stApp {
        background: #ffffff;
        background-attachment: fixed;
    }
    
    /* Main content area with semi-transparent white background */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #ff6b35 0%, #f7931e 50%, #ff1744 100%);
        color: white;
        margin: -2rem -2rem 2rem -2rem;
        border-radius: 15px 15px 0 0;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
    }
    
    .main-header h1 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
    }
    
    .summary-section {
        background: rgba(255, 255, 255, 0.8);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #ff5722;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .step-container {
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid rgba(255, 87, 34, 0.2);
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .completed-step {
        background: rgba(76, 175, 80, 0.1);
        border-color: #4caf50;
    }
    .question-container {
        background: rgba(255, 255, 255, 0.9);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 87, 34, 0.2);
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .correct-answer {
        background: rgba(76, 175, 80, 0.1);
        border-color: #4caf50;
        color: #2e7d32;
    }
    .incorrect-answer {
        background: rgba(244, 67, 54, 0.1);
        border-color: #f44336;
        color: #c62828;
    }
    .chat-container {
        background: rgba(255, 255, 255, 0.8);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        max-height: 400px;
        overflow-y: auto;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .user-message {
        background: #ff5722;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: right;
    }
    .ai-message {
        background: rgba(255, 255, 255, 0.9);
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 87, 34, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #ff5722, #ff9a00);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 87, 34, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'tutorial_data' not in st.session_state:
    st.session_state.tutorial_data = None
if 'completed_steps' not in st.session_state:
    st.session_state.completed_steps = set()
if 'question_answers' not in st.session_state:
    st.session_state.question_answers = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_input' not in st.session_state:
    st.session_state.chat_input = ""

def call_api(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make API call to backend"""
    try:
        response = requests.post(
            f"http://localhost:8000{endpoint}",
            json=data,
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        st.error("Make sure the backend server is running on http://localhost:8000")
        return None

def process_tutorial(youtube_url: str = None, transcript_text: str = None, target_language: str = "english"):
    """Process tutorial using the backend API"""
    data = {
        "target_language": target_language
    }
    
    if youtube_url:
        data["youtube_url"] = youtube_url
    elif transcript_text:
        data["transcript_text"] = transcript_text
    else:
        st.error("Please provide either a YouTube URL or transcript text")
        return None
    
    return call_api("/api/process-tutorial", data)

def chat_with_ai_simple(user_message: str, tutorial_data: Dict[str, Any]) -> Optional[str]:
    """Send chat message to AI assistant - fixed version"""
    try:
        # Send the full tutorial_data as received from the API
        # The backend expects a ProcessedTutorial object, not a simplified dict
        data = {
            "tutorial_data": tutorial_data,  # Send full tutorial data
            "user_message": user_message,
            "chat_history": []  # Empty to prevent recursion
        }
        
        response = call_api("/api/chat", data)
        if response:
            return response.get('response', '')
        return None
        
    except Exception as e:
        st.error(f"Chat error: {str(e)}")
        return None

def render_practice_questions(questions):
    """Render practice questions with dropdown answers"""
    st.subheader("🧠 Practice Questions")
    
    if not questions:
        st.info("No practice questions available for this tutorial.")
        return
    
    for question in questions:
        question_id = question['question_id']
        
        with st.container():
            st.markdown(f"""
            <div class="question-container">
                <h4>Question {question_id}</h4>
                <p><strong>{question['question']}</strong></p>
                <p><small>📚 Topic: {question['topic']} | 🎯 Difficulty: {question['difficulty'].title()}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Handle different question types
            if question['question_type'] == 'multiple_choice':
                options = question.get('options', [])
                if options:
                    selected_answer = st.selectbox(
                        f"Select your answer for Question {question_id}:",
                        options=["Select an answer..."] + options,
                        key=f"q_{question_id}",
                        index=0
                    )
                    
                    if st.button(f"Show Answer & Explanation", key=f"show_{question_id}"):
                        if selected_answer != "Select an answer...":
                            st.session_state.question_answers[question_id] = selected_answer
                        
                        if question_id in st.session_state.question_answers:
                            user_answer = st.session_state.question_answers[question_id]
                            correct_answer = question['correct_answer']
                            
                            if user_answer == correct_answer:
                                st.success(f"✅ Correct! Your answer: {user_answer}")
                            else:
                                st.error(f"❌ Incorrect. Your answer: {user_answer} | Correct answer: {correct_answer}")
                            
                            st.info(f"💡 **Explanation:** {question['explanation']}")
                        else:
                            st.warning("Please select an answer first!")
            
            elif question['question_type'] == 'true_false':
                selected_answer = st.radio(
                    f"Question {question_id}:",
                    options=["True", "False"],
                    key=f"tf_{question_id}",
                    index=None
                )
                
                if st.button(f"Show Answer & Explanation", key=f"show_tf_{question_id}"):
                    if selected_answer:
                        st.session_state.question_answers[question_id] = selected_answer
                        correct_answer = question['correct_answer']
                        
                        if selected_answer == correct_answer:
                            st.success(f"✅ Correct! The answer is {correct_answer}")
                        else:
                            st.error(f"❌ Incorrect. The correct answer is {correct_answer}")
                        
                        st.info(f"💡 **Explanation:** {question['explanation']}")
                    else:
                        st.warning("Please select True or False first!")
            
            elif question['question_type'] == 'short_answer':
                user_answer = st.text_area(
                    f"Your answer for Question {question_id}:",
                    key=f"sa_{question_id}",
                    height=100
                )
                
                if st.button(f"Show Sample Answer & Explanation", key=f"show_sa_{question_id}"):
                    if user_answer.strip():
                        st.session_state.question_answers[question_id] = user_answer
                        st.info(f"📝 **Your Answer:** {user_answer}")
                    
                    st.success(f"✅ **Sample Answer:** {question['correct_answer']}")
                    st.info(f"💡 **Explanation:** {question['explanation']}")
            
            st.markdown("---")

def render_ai_chat_working(tutorial_data):
    """Render AI chat interface - working version"""
    st.subheader("🤖 AI Tutor Assistant")
    st.write("Ask me anything about this tutorial! I can help explain concepts, clarify steps, or answer questions about the content.")
    
    # Limit chat history
    if len(st.session_state.chat_history) > 6:
        st.session_state.chat_history = st.session_state.chat_history[-6:]
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f'<div class="user-message">You: {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-message">🤖 AI Tutor: {message["content"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input using columns for better layout
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask a question:",
            placeholder="e.g., 'Can you explain step 3 in more detail?'",
            key="chat_input_field",
            label_visibility="collapsed"
        )
    
    with col2:
        send_clicked = st.button("Send 💬", key="send_chat", use_container_width=True)
    
    with col3:
        clear_clicked = st.button("Clear", key="clear_chat", use_container_width=True)
    
    # Handle send button click
    if send_clicked and user_input.strip():
        # Check for duplicates
        recent_questions = [msg['content'].lower().strip() for msg in st.session_state.chat_history if msg['role'] == 'user']
        
        if user_input.lower().strip() not in recent_questions[-2:]:
            # Add user message
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Get AI response
            with st.spinner("🤖 AI Tutor is thinking..."):
                ai_response = chat_with_ai_simple(user_input, tutorial_data)
                
                if ai_response:
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': ai_response
                    })
                    st.success("✅ Response received!")
                else:
                    st.error("❌ Sorry, I couldn't process your question. Please try again.")
            
            # Clear the input field by rerunning
            st.rerun()
        else:
            st.warning("⚠️ You just asked this question. Try asking something different!")
    
    # Handle clear button click
    if clear_clicked:
        st.session_state.chat_history = []
        st.success("🗑️ Chat history cleared!")
        st.rerun()
    
    # Quick question buttons
    st.write("**💡 Quick Questions:**")
    
    col_q1, col_q2, col_q3 = st.columns(3)
    
    with col_q1:
        if st.button("📋 Summarize", key="quick_summary"):
            question = "Can you summarize the key points from this tutorial?"
            st.session_state.chat_history.append({'role': 'user', 'content': question})
            
            with st.spinner("🤖 AI Tutor is thinking..."):
                ai_response = chat_with_ai_simple(question, tutorial_data)
                if ai_response:
                    st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                    st.rerun()
    
    with col_q2:
        if st.button("❓ Hardest part?", key="quick_hard"):
            question = "What is the most challenging part of this tutorial?"
            st.session_state.chat_history.append({'role': 'user', 'content': question})
            
            with st.spinner("🤖 AI Tutor is thinking..."):
                ai_response = chat_with_ai_simple(question, tutorial_data)
                if ai_response:
                    st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                    st.rerun()
    
    with col_q3:
        if st.button("🔧 Prerequisites?", key="quick_prereq"):
            question = "What prerequisites do I need for this tutorial?"
            st.session_state.chat_history.append({'role': 'user', 'content': question})
            
            with st.spinner("🤖 AI Tutor is thinking..."):
                ai_response = chat_with_ai_simple(question, tutorial_data)
                if ai_response:
                    st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                    st.rerun()

def export_tutorial(tutorial_data: Dict[str, Any], format_type: str = "markdown"):
    """Export tutorial data"""
    data = {
        "tutorial_data": tutorial_data,
        "export_format": format_type
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/export",
            json=data,
            timeout=30
        )
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Export Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Export Connection Error: {str(e)}")
        return None

# Main App
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 TutorMate AI</h1>
        <p>Turn any tutorial into your personalized, step-by-step action plan</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        languages = {
            "english": "🇺🇸 English",
            "spanish": "🇪🇸 Spanish", 
            "french": "🇫🇷 French",
            "german": "🇩🇪 German",
            "hindi": "🇮🇳 Hindi"
        }
        
        target_language = st.selectbox(
            "Output Language",
            options=list(languages.keys()),
            format_func=lambda x: languages[x],
            index=0
        )
        
        st.markdown("---")
        
        if st.button("🚀 Quick Test", help="Test with AWS VPC tutorial"):
            with st.spinner("🤖 Processing tutorial... This may take 10-30 seconds"):
                result = process_tutorial(
                    youtube_url="https://www.youtube.com/watch?v=Ed09ReWRQXc", 
                    target_language=target_language
                )
                if result:
                    st.session_state.tutorial_data = result
                    st.session_state.chat_history = []
                    st.rerun()
        
        if st.button("🔄 Start New Tutorial", type="secondary"):
            st.session_state.tutorial_data = None
            st.session_state.completed_steps = set()
            st.session_state.question_answers = {}
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("---")
        st.info("💡 Make sure backend is running:\n\n`cd backend/app && python3 main.py`")

    # Main content area
    if st.session_state.tutorial_data is None:
        # Input form
        st.header("📝 Input Tutorial")
        
        input_type = st.radio(
            "Choose input method:",
            ["YouTube URL", "Manual Transcript"],
            horizontal=True
        )
        
        if input_type == "YouTube URL":
            youtube_url = st.text_input(
                "YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                help="Paste any YouTube tutorial URL here"
            )
            
            st.markdown("**💡 Example:**")
            if st.button("📺 AWS VPC Monitoring Tutorial", key="example1"):
                youtube_url = "https://www.youtube.com/watch?v=Ed09ReWRQXc"
            
            if st.button("🚀 Generate Action Plan", type="primary", disabled=not youtube_url):
                with st.spinner("🤖 Processing tutorial... This may take 10-30 seconds"):
                    result = process_tutorial(youtube_url=youtube_url, target_language=target_language)
                    if result:
                        st.session_state.tutorial_data = result
                        st.session_state.chat_history = []
                        st.rerun()
        
        else:  # Manual Transcript
            transcript_text = st.text_area(
                "Tutorial Transcript",
                placeholder="Paste your tutorial transcript here...",
                height=200,
                help="Paste the full transcript of your tutorial"
            )
            
            if st.button("🚀 Generate Action Plan", type="primary", disabled=not transcript_text):
                with st.spinner("🤖 Processing tutorial... This may take 10-30 seconds"):
                    result = process_tutorial(transcript_text=transcript_text, target_language=target_language)
                    if result:
                        st.session_state.tutorial_data = result
                        st.session_state.chat_history = []
                        st.rerun()
    
    else:
        # Display results
        tutorial = st.session_state.tutorial_data
        
        # Header with tutorial info
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title(tutorial['summary']['title'])
            
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("⏱️ Duration", tutorial['summary'].get('duration', 'Not specified'))
            with col_b:
                st.metric("📊 Difficulty", tutorial['summary']['difficulty_level'])
            with col_c:
                st.metric("🌐 Language", tutorial['target_language'].title())
            with col_d:
                st.metric("⚡ Processing", f"{tutorial['processing_time']:.1f}s")
        
        with col2:
            if st.button("📄 Export Markdown", type="secondary"):
                exported_content = export_tutorial(tutorial, "markdown")
                if exported_content:
                    st.download_button(
                        label="⬇️ Download Markdown",
                        data=exported_content,
                        file_name=f"{tutorial['summary']['title'].replace(' ', '_')}.md",
                        mime="text/markdown"
                    )
        
        # Progress tracking
        total_steps = len(tutorial['action_steps'])
        completed_count = len(st.session_state.completed_steps)
        progress = completed_count / total_steps if total_steps > 0 else 0
        
        st.subheader(f"📈 Progress: {completed_count}/{total_steps} steps ({progress:.0%})")
        st.progress(progress)
        
        # Tabs for content
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary & Details", "✅ Action Steps", "🧠 Practice Questions", "🤖 AI Tutor"])
        
        with tab1:
            st.subheader("🎯 Quick Overview")
            st.markdown(f"""
            <div class="summary-section">
                {tutorial['summary']['short_summary']}
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("📖 Detailed Summary")
            detailed_summary = tutorial['summary']['detailed_summary']
            if not detailed_summary.startswith('•') and not detailed_summary.startswith('-'):
                sentences = [s.strip() for s in detailed_summary.split('.') if s.strip()]
                detailed_summary = '\n'.join([f"• {sentence}." for sentence in sentences if sentence])
            
            st.markdown(f"""
            <div class="summary-section">
                {detailed_summary.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("🔑 Key Topics Covered")
            topics = tutorial['summary']['key_topics']
            if topics:
                num_cols = min(len(topics), 3)
                topic_cols = st.columns(num_cols)
                for i, topic in enumerate(topics):
                    with topic_cols[i % num_cols]:
                        st.info(f"🏷️ {topic}")
            
            st.subheader("📊 Tutorial Statistics")
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.write(f"**Total Steps:** {total_steps}")
                st.write(f"**Estimated Total Time:** {tutorial['summary'].get('duration', 'Not specified')}")
                st.write(f"**Practice Questions:** {len(tutorial.get('practice_questions', []))}")
            with stat_col2:
                st.write(f"**Difficulty Level:** {tutorial['summary']['difficulty_level']}")
                st.write(f"**Target Language:** {tutorial['target_language'].title()}")
        
        with tab2:
            st.subheader("📝 Your Personalized Action Plan")
            
            for i, step in enumerate(tutorial['action_steps']):
                step_num = step['step_number']
                is_completed = step_num in st.session_state.completed_steps
                
                with st.container():
                    col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
                    
                    with col1:
                        completed = st.checkbox(
                            "Done", 
                            key=f"step_{step_num}", 
                            value=is_completed,
                            help="Mark as completed"
                        )
                        if completed != is_completed:
                            if completed:
                                st.session_state.completed_steps.add(step_num)
                            else:
                                st.session_state.completed_steps.discard(step_num)
                            st.rerun()
                    
                    with col2:
                        if is_completed:
                            st.markdown(f"### ~~Step {step_num}: {step['title']}~~ ✅")
                        else:
                            st.markdown(f"### Step {step_num}: {step['title']}")
                    
                    with col3:
                        if step.get('estimated_time'):
                            st.markdown(f"**⏱️ {step['estimated_time']}**")
                    
                    if is_completed:
                        st.success("✅ Completed!")
                        with st.expander("View details"):
                            st.write(step['description'])
                    else:
                        st.write(step['description'])
                        st.info("⏳ Click the checkbox when completed")
                    
                    st.markdown("---")
        
        with tab3:
            render_practice_questions(tutorial.get('practice_questions', []))
        
        with tab4:
            render_ai_chat_working(tutorial)
    
    # Footer removed for cleaner look

if __name__ == "__main__":
    main()
