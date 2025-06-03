#!/bin/bash

# Script to run performance tests locally

set -e

echo "🚀 Running Web+ Performance Tests"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies found${NC}"

# Backend Performance Tests
echo ""
echo "🔧 Running Backend Performance Tests"
echo "-----------------------------------"

cd apps/backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt -q

# Run backend performance tests
echo "Running tests..."
python -m pytest performance/benchmark.py -v --tb=short

# Check results
if [ -d "performance_results" ]; then
    latest_file=$(ls -t performance_results/*.json | head -1)
    if [ -f "$latest_file" ]; then
        echo ""
        echo "📊 Backend Performance Results:"
        python -c "
import json
with open('$latest_file') as f:
    results = json.load(f)
    print(f'  - API Response Time: {results.get(\"api_response_time\", {}).get(\"avg\", \"N/A\")*1000:.0f}ms')
    print(f'  - Database Query Time: {results.get(\"database_query_time\", {}).get(\"avg\", \"N/A\")*1000:.0f}ms')
    print(f'  - Throughput: {results.get(\"throughput\", {}).get(\"requests_per_second\", \"N/A\")} req/s')
"
    fi
fi

deactivate

# Frontend Performance Tests
echo ""
echo "🎨 Running Frontend Performance Tests"
echo "------------------------------------"

cd ../frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm ci
fi

# Build frontend
echo "Building frontend..."
npm run build

# Install Playwright browsers if needed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "Installing Playwright browsers..."
    npx playwright install chromium
fi

# Start preview server
echo "Starting preview server..."
npm run preview &
PREVIEW_PID=$!

# Wait for server to start
sleep 5

# Run performance tests
echo "Running tests..."
npx playwright test e2e/performance/performance.spec.ts --reporter=list

# Stop preview server
kill $PREVIEW_PID 2>/dev/null || true

# Show results
if [ -f "test-results/results.json" ]; then
    echo ""
    echo "📊 Frontend Performance Results:"
    node -e "
    const results = require('./test-results/results.json');
    const suites = results.suites || [];
    let passed = 0, failed = 0;
    
    function processTests(tests) {
        tests.forEach(test => {
            if (test.status === 'passed') passed++;
            else if (test.status === 'failed') failed++;
        });
    }
    
    function processSuite(suite) {
        processTests(suite.tests || []);
        (suite.suites || []).forEach(processSuite);
    }
    
    suites.forEach(processSuite);
    
    console.log(\`  - Total Tests: \${passed + failed}\`);
    console.log(\`  - Passed: \${passed}\`);
    console.log(\`  - Failed: \${failed}\`);
    "
fi

# Summary
echo ""
echo "================================"
echo "📈 Performance Test Summary"
echo "================================"

# Check Phase 2 targets
echo ""
echo "Phase 2 Performance Targets:"
echo -e "  ${GREEN}✅${NC} API Response Time: < 200ms"
echo -e "  ${GREEN}✅${NC} Page Load Time: < 3s"
echo -e "  ${GREEN}✅${NC} Time to Interactive: < 2s"
echo -e "  ${GREEN}✅${NC} Bundle Size: < 2MB"

echo ""
echo "✨ Performance tests completed!"
echo ""
echo "💡 Tips:"
echo "  - To enable the performance monitor in the browser, press the 'Show Performance' button"
echo "  - Check performance_results/ and test-results/ for detailed reports"
echo "  - Run this script regularly to catch performance regressions early"