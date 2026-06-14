import json
import boto3
import urllib.parse
import uuid

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

# --- CONFIGURATION (UPDATE THIS LINE) ---
DESTINATION_BUCKET = 'goutham-processed-data'
DYNAMODB_TABLE = 'FileProcessingLogs'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-2:568521409124:PipelineAlerts'


def lambda_handler(event, context):
    table = dynamodb.Table(DYNAMODB_TABLE)

    # Loop through all messages received from SQS
    for record in event['Records']:

        # 1. Parse the SQS message body to find the hidden S3 event
        sqs_body = json.loads(record['body'])

        # S3 occasionally sends a 'TestEvent', we want to ignore that safely
        if 'Event' in sqs_body and sqs_body['Event'] == 's3:TestEvent':
            continue

        for s3_record in sqs_body.get('Records', []):
            source_bucket = s3_record['s3']['bucket']['name']
            file_key = urllib.parse.unquote_plus(
                s3_record['s3']['object']['key'], encoding='utf-8')

            try:
                # 2. Download the raw file from the S3 Landing Bucket
                print(f"Downloading {file_key} from {source_bucket}...")
                response = s3.get_object(Bucket=source_bucket, Key=file_key)
                file_content = response['Body'].read().decode('utf-8')

                # 3. Process the Data (Proof of concept: Count rows and convert to uppercase)
                rows = file_content.split('\n')
                row_count = len([row for row in rows if row.strip()])
                processed_content = file_content.upper()

                # 4. Save the clean/processed file to Destination Bucket
                processed_key = f"processed_{file_key}"
                s3.put_object(Bucket=DESTINATION_BUCKET,
                              Key=processed_key, Body=processed_content)

                # 5. Write an audit log to DynamoDB
                log_id = str(uuid.uuid4())
                table.put_item(
                    Item={
                        'FileID': log_id,
                        'OriginalFileName': file_key,
                        'RowCount': row_count,
                        'Status': 'SUCCESS'
                    }
                )

                # 6. Send the Email Alert via SNS
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject="Pipeline Success: File Processed",
                    Message=f"Success! The file '{file_key}' was processed.\nTotal Rows: {row_count}\nSaved to: {DESTINATION_BUCKET} as '{processed_key}'."
                )

                print(f"Successfully finished processing {file_key}")

            except Exception as e:
                print(f"Error processing {file_key}: {str(e)}")
                raise e

    return {
        'statusCode': 200,
        'body': json.dumps('Pipeline execution complete!')
    }
