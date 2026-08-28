#!/bin/bash
# Sahayak Live — Start Script
# Starts both the backend and frontend in one command

echo "🎓 Starting Sahayak Live..."

# Check .env
if [ ! -f backend/classroom/.env ]; then
    echo "⚠️  No .env found. Copying from .env.example..."
    cp backend/classroom/.env.example backend/classroom/.env
    echo "📝 Please edit backend/classroom/.env and add your API keys."
    echo "   At least one of GROQ_API_KEY or MISTRAL_API_KEY is required."
    exit 1
fi

# Start backend
echo "🧠 Starting multi-agent backend on port 8001..."
cd backend/classroom
python3 -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload &
BACKEND_PID=$!
cd ../..

# Wait for backend
sleep 3
if curl -s http://127.0.0.1:8001/api/health | grep -q '"ok"'; then
    echo "✅ Backend running"
else
    echo "❌ Backend failed to start. Check backend/classroom/ requirements."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🖥️  Starting frontend on port 9002..."
npm run dev &
FRONTEND_PID=$!

# Wait for frontend
sleep 5
echo ""
echo "🎉 Sahayak Live is running!"
echo ""
echo "   Frontend:  http://localhost:9002"
echo "   Backend:   http://127.0.0.1:8001"
echo "   API docs:  http://127.0.0.1:8001/docs"
echo ""
echo "   Go to http://localhost:9002/classroom to start a live class."
echo ""
echo "   Press Ctrl+C to stop both servers."

# Cleanup on exit
trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
