#!/bin/bash

echo "🚀 Starting TutorAI Application"
echo "==============================="

# Kill any existing backend processes
echo "🛑 Stopping any existing backend processes..."
pkill -f "python3 main.py" 2>/dev/null || true
sleep 2

# Start fresh backend
echo "🚀 Starting backend server..."
source venv/bin/activate
cd backend/app
python3 main.py &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ Backend started successfully"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start"
        exit 1
    fi
done

# Start Streamlit app
echo "🎓 Starting TutorAI application..."
echo "✨ Features:"
echo "   • ✅ Practice Questions with dropdown answers"
echo "   • ✅ AI Assistant chat about video content"
echo "   • ✅ YouTube URL and manual transcript support"
echo "   • ✅ Multi-language support"
echo "   • ✅ Export functionality"
echo ""
echo "🌐 Opening in browser at http://localhost:8501"
echo "🛑 Press Ctrl+C to stop"

streamlit run app.py --server.port 8501 --server.address localhost
