#!/bin/bash

# Start Web+ Application (Frontend and Backend)
# This script launches both the frontend and backend services.

# Define colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Web+ Application...${NC}"

# Set up environment variables
export PATH=$PATH:$HOME/.local/bin

# Check for running processes and stop them
echo -e "${BLUE}Checking for existing processes...${NC}"
pkill -f "npm run dev" || true
pkill -f "python.*run_backend.py" || true

# Start backend service
echo -e "${BLUE}Starting backend service...${NC}"
cd $(dirname "$0")
python3 scripts/run_backend.py &
BACKEND_PID=$!
echo -e "${GREEN}Backend started with PID ${BACKEND_PID}${NC}"

# Wait for backend to initialize
echo "Waiting for backend to initialize (5 seconds)..."
sleep 5

# Start frontend service
echo -e "${BLUE}Starting frontend service...${NC}"
cd $(dirname "$0")/apps/frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started with PID ${FRONTEND_PID}${NC}"

echo -e "${GREEN}Services started successfully!${NC}"
echo -e "${GREEN}Frontend URL: http://localhost:5173${NC}"
echo -e "${GREEN}Backend URL: http://localhost:8000${NC}"
echo -e "${GREEN}API Documentation: http://localhost:8000/docs${NC}"
echo ""
echo -e "${RED}Press Ctrl+C to stop all services${NC}"

# Wait for user to press Ctrl+C
trap "echo -e '${RED}Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" INT
wait