#!/bin/bash
echo "🎓 Starting SAPA-LPDP Web Server..."
export PORT=${PORT:-8080}
export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-"kodingdeepdive0826-9569"}

echo "---------------------------------------------------------"
echo "🚀 Server running on http://0.0.0.0:$PORT"
echo "💡 To view in Google Cloud Shell:"
echo "   1. Click 'Web Preview' icon in top right of Cloud Shell"
echo "   2. Click 'Preview on port $PORT'"
echo "---------------------------------------------------------"

python3 app.py
