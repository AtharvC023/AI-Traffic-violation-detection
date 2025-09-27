provider "aws" {
  region = "us-east-1"
}

# S3 Bucket for violations
resource "aws_s3_bucket" "violations" {
  bucket = "traffic-violations-bucket"
}

# DynamoDB Table
resource "aws_dynamodb_table" "violations" {
  name           = "traffic-violations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "violation_id"

  attribute {
    name = "violation_id"
    type = "S"
  }
}

# Kinesis Video Stream
resource "aws_kinesis_video_stream" "camera_feed" {
  name                    = "traffic-camera-1"
  data_retention_in_hours = 24
}

# ECS Fargate Cluster
resource "aws_ecs_cluster" "processor" {
  name = "traffic-processor"
}