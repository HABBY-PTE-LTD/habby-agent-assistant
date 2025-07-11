#!/bin/bash

# PDF to Markdown Lambda Deployment Script
# This script packages and deploys the Lambda function

set -e

FUNCTION_NAME="pdf2md-converter"
REGION="us-east-1"
RUNTIME="python3.9"
HANDLER="lambda_function.lambda_handler"
TIMEOUT=300
MEMORY_SIZE=3008

echo "🚀 Starting Lambda deployment process..."

# Create deployment package
echo "📦 Creating deployment package..."
rm -rf package
mkdir package

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -t package/

# Copy Lambda function
echo "📄 Copying Lambda function..."
cp lambda_function.py package/

# Create deployment zip
echo "🗜️  Creating deployment zip..."
cd package
zip -r ../lambda-deployment.zip .
cd ..

echo "📊 Package size:"
ls -lh lambda-deployment.zip

# Check if function exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "🔄 Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip \
        --region $REGION
    
    echo "⚙️  Updating function configuration..."
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --region $REGION
else
    echo "🆕 Creating new Lambda function..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role \
        --handler $HANDLER \
        --zip-file fileb://lambda-deployment.zip \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --region $REGION
fi

echo "🧪 Testing deployed function..."
aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload '{"pdf_content":"test"}' \
    --region $REGION \
    response.json

echo "📋 Response:"
cat response.json

echo "✅ Deployment completed successfully!"
echo "🔗 Function ARN: arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME"

# Cleanup
echo "🧹 Cleaning up..."
rm -rf package
rm lambda-deployment.zip
rm response.json

echo "🎉 All done!" 