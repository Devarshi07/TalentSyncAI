#!/bin/bash
# Deploy backend to Azure Container Apps
# Prerequisites: az CLI installed, logged in (az login)
#
# Usage: ./deploy-azure.sh
# 
# This script:
# 1. Creates a resource group
# 2. Creates a Container Apps environment
# 3. Builds and deploys the backend Docker image
#
# Cost: ~$0-2/month on consumption plan (scales to zero)

set -e

# ===== Configuration =====
RESOURCE_GROUP="talentsyncai-rg"
LOCATION="eastus"
ENVIRONMENT="talentsyncai-env"
APP_NAME="talentsyncai-api"
IMAGE_NAME="talentsyncai-api"

echo "🔧 Setting up Azure resources..."

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create Container Apps environment
az containerapp env create \
  --name $ENVIRONMENT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Build and deploy from Dockerfile
echo "🐳 Building and deploying container..."
az containerapp up \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT \
  --source ./backend \
  --target-port 5001 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --env-vars \
    DATABASE_URL="$DATABASE_URL" \
    GEMINI_API_KEY="$GEMINI_API_KEY" \
    JWT_SECRET="$JWT_SECRET" \
    GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
    GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
    GOOGLE_REDIRECT_URI="$GOOGLE_REDIRECT_URI" \
    FRONTEND_URL="$FRONTEND_URL" \
    CORS_ORIGINS="$CORS_ORIGINS" \
    RATE_LIMIT_ENABLED="true" \
    DEBUG="false"

# Get the URL
FQDN=$(az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv)

echo ""
echo "✅ Backend deployed!"
echo "🌍 URL: https://$FQDN"
echo ""
echo "Next steps:"
echo "  1. Set VITE_API_URL=https://$FQDN/api in Vercel dashboard"
echo "  2. Update CORS_ORIGINS to include your Vercel frontend URL"
echo "  3. Update GOOGLE_REDIRECT_URI to https://$FQDN/api/auth/google/callback"
