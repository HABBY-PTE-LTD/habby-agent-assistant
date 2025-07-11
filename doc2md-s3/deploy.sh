#!/bin/bash

# doc2md-s3 Lambda Deployment Script
# Deploys the doc2md-s3 Lambda function with all dependencies

set -e

FUNCTION_NAME="doc2md-s3"
REGION="us-east-1"
RUNTIME="python3.9"
HANDLER="lambda_function.lambda_handler"
TIMEOUT=900  # 15 minutes
MEMORY_SIZE=10240  # 10GB for processing large documents
DESCRIPTION="PDF to Markdown converter using Docling and S3 storage"

echo "🚀 Starting doc2md-s3 Lambda deployment..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Create deployment package
echo "📦 Creating deployment package..."
rm -rf package
mkdir package

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -t package/ --quiet

# Copy Lambda function and modules
echo "📄 Copying Lambda function and modules..."
cp lambda_function.py package/
cp s3_handler.py package/
cp docling_processor.py package/
cp markdown_optimizer.py package/
cp metadata_analyzer.py package/

# Create deployment zip
echo "🗜️  Creating deployment zip..."
cd package
zip -r ../lambda-deployment.zip . -q
cd ..

echo "📊 Package information:"
ls -lh lambda-deployment.zip
echo "Package size: $(du -h lambda-deployment.zip | cut -f1)"

# Check package size (Lambda limit is 250MB unzipped, 50MB zipped)
PACKAGE_SIZE=$(stat -f%z lambda-deployment.zip)
if [ $PACKAGE_SIZE -gt 52428800 ]; then  # 50MB in bytes
    echo "⚠️  Warning: Package size exceeds 50MB. Consider using Lambda Layers."
fi

# Check if IAM role exists
ROLE_NAME="doc2md-s3-execution-role"
ROLE_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/$ROLE_NAME"

echo "🔍 Checking IAM role..."
if ! aws iam get-role --role-name $ROLE_NAME > /dev/null 2>&1; then
    echo "🆕 Creating IAM role..."
    
    # Create trust policy
    cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create execution policy
    cat > execution-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::*",
        "arn:aws:s3:::*/*"
      ]
    }
  ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file://trust-policy.json \
        --description "Execution role for doc2md-s3 Lambda function"

    # Attach policies
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

    aws iam put-role-policy \
        --role-name $ROLE_NAME \
        --policy-name S3AccessPolicy \
        --policy-document file://execution-policy.json

    # Wait for role to be available
    echo "⏳ Waiting for IAM role to be available..."
    sleep 10

    # Cleanup policy files
    rm trust-policy.json execution-policy.json
else
    echo "✅ IAM role already exists"
fi

# Check if function exists
echo "🔍 Checking if Lambda function exists..."
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > /dev/null 2>&1; then
    echo "🔄 Updating existing Lambda function..."
    
    # Update function code
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip \
        --region $REGION \
        --output text

    # Update function configuration
    aws lambda update-function-configuration \
        --function-name $FUNCTION_NAME \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --region $REGION \
        --output text

    echo "✅ Function updated successfully"
else
    echo "🆕 Creating new Lambda function..."
    
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://lambda-deployment.zip \
        --timeout $TIMEOUT \
        --memory-size $MEMORY_SIZE \
        --description "$DESCRIPTION" \
        --region $REGION \
        --output text

    echo "✅ Function created successfully"
fi

# Test function with a simple event
echo "🧪 Testing deployed function..."
cat > test-event.json << EOF
{
  "source_bucket": "test-bucket",
  "source_key": "test.pdf",
  "output_bucket": "test-bucket",
  "output_key": "test.md"
}
EOF

aws lambda invoke \
    --function-name $FUNCTION_NAME \
    --payload file://test-event.json \
    --region $REGION \
    response.json > /dev/null

echo "📋 Test response:"
cat response.json | jq '.'

# Get function info
echo "📊 Function information:"
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.{FunctionName:FunctionName,Runtime:Runtime,MemorySize:MemorySize,Timeout:Timeout,LastModified:LastModified}' --output table

echo "✅ Deployment completed successfully!"
echo "🔗 Function ARN: $(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.FunctionArn' --output text)"

# Cleanup
echo "🧹 Cleaning up..."
rm -rf package
rm lambda-deployment.zip
rm test-event.json
rm response.json

echo "🎉 All done!"
echo ""
echo "📝 Usage example:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"source_bucket\":\"my-bucket\",\"source_key\":\"document.pdf\",\"output_bucket\":\"my-bucket\",\"output_key\":\"document.md\"}' response.json" 