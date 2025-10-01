#!/bin/bash
# Build script for Azure deployment

set -e

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Frontend built successfully to frontend/dist/"
echo "Ready for Azure deployment!"
