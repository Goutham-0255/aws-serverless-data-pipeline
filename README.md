# AWS Serverless Event-Driven Data Pipeline

An enterprise-grade, fully serverless data processing pipeline built on AWS. This architecture automatically detects raw data uploads, queues the events for processing, transforms the data using Python, stores the processed output, and sends an automated email alert upon successful completion.

## 🏗️ Architecture Overview

This project implements a decoupled, event-driven architecture using the following AWS services:

1. **Amazon S3 (Raw Landing Zone):** Triggers an event notification the moment a new CSV file is uploaded.
2. **Amazon SQS (Message Queue):** Buffers the S3 event notifications, ensuring no events are dropped or lost before processing.
3. **AWS Lambda (Compute):** A Python-based serverless function that polls the SQS queue, downloads the raw file from S3, applies data transformation logic, and uploads the final result.
4. **Amazon S3 (Processed Zone):** Stores the final, transformed data files.
5. **Amazon SNS (Notification):** Publishes a success alert to subscribed email addresses.
6. **AWS IAM (Security):** Enforces least-privilege access, allowing Lambda to interact only with specific S3 buckets, SQS, SNS, and CloudWatch.

## 🚀 Event Flow

`User Upload` ➡️ `S3 (Raw)` ➡️ `SQS Queue` ➡️ `Lambda Processor` ➡️ `S3 (Processed)` ➕ `SNS (Email Alert)`

---

## 🛠️ Prerequisites
* AWS Account
* AWS CLI installed and authenticated (`aws configure`)
* Python 3.x
* IAM User with CLI access

## ⚙️ Deployment & Setup Instructions

### 1. Storage & Queuing
* Create two S3 buckets: one for raw data (e.g., `sales-raw`) and one for processed data (e.g., `sales-processed`).
* Create an SQS Queue named `file-processing-queue`.
* Update the SQS Access Policy to explicitly allow the S3 Raw bucket to send messages (`sqs:SendMessage`).

### 2. Notifications
* Create an SNS Topic named `PipelineAlerts`.
* Subscribe your email address to the topic and click the confirmation link sent to your inbox.

### 3. Compute (Lambda)
* Create a Python Lambda function named `DataPipelineProcessor`.
* Attach the SQS queue as a trigger for the Lambda function.
* Update the Lambda execution IAM Role to include permissions for:
  * `AmazonS3FullAccess` (or scoped bucket access)
  * `AmazonSQSFullAccess`
  * `AmazonSNSFullAccess`
  * `AWSLambdaBasicExecutionRole` (for CloudWatch logs)

### 4. Event Routing
* Configure an Event Notification on the Raw S3 bucket to route all `s3:ObjectCreated:*` events to your SQS queue. 
* *Note: This can be applied via the console or via the CLI using a `notification.json` file.*

---

## 💻 Code Deployment

To deploy updates to the Lambda function directly from your local terminal, use the following commands:

```bash
# 1. Compress the Python script
zip function.zip lambda_function.py

# 2. Push the updated code to AWS Lambda
aws lambda update-function-code \
    --function-name DataPipelineProcessor \
    --zip-file fileb://function.zip \
    --no-cli-pager
