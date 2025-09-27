# AWS Deployment Guide

## Step-by-Step Deployment Plan

### Phase 1: Infrastructure Setup
1. **Install AWS CLI and Terraform**
   ```bash
   aws configure
   terraform init
   terraform plan
   terraform apply
   ```

2. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name traffic-processor
   ```

### Phase 2: Container Deployment
3. **Build and Push Docker Image**
   ```bash
   docker build -t traffic-processor ./docker
   docker tag traffic-processor:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/traffic-processor:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/traffic-processor:latest
   ```

### Phase 3: Service Configuration
4. **Deploy Fargate Service**
5. **Configure Kinesis Video Streams**
6. **Set up API Gateway for dashboard**

### Phase 4: Frontend Deployment
7. **Deploy React dashboard with Amplify**
8. **Configure CloudFront distribution**

## Cost Estimation (Monthly)
- Kinesis Video Streams: $10-50
- Fargate: $20-100
- S3 Storage: $5-20
- DynamoDB: $5-25
- **Total: $40-195/month**

## Security Best Practices
- Use IAM roles, not access keys
- Enable CloudTrail logging
- Encrypt S3 buckets
- Use VPC for Fargate tasks