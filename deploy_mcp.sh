#!/bin/bash
# Deployment script for ProteinKart MCP Server

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./deploy_mcp.sh <PROJECT_ID>"
    exit 1
fi

echo "🚀 Deploying ProteinKart MCP Server to GCP: $PROJECT_ID"

# 1. Build and Push
gcloud builds submit --tag "gcr.io/$PROJECT_ID/proteinkart-mcp" --project "$PROJECT_ID"

# 2. Deploy to Cloud Run
gcloud run deploy proteinkart-mcp \
    --image "gcr.io/$PROJECT_ID/proteinkart-mcp" \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --project "$PROJECT_ID"

echo ""
echo "✅ MCP Server Live!"
echo "Students/Agents should use the URL: <SERVICE_URL>/sse"
