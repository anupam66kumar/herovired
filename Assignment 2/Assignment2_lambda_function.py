import json
import boto3
from datetime import datetime, timedelta, timezone

s3 = boto3.client('s3')

BUCKET_NAME = 'anupam66s3bucket'
DAYS_THRESHOLD = 30

def lambda_handler(event, context):
    try:
        # 1. Establish precise UTC cutoff time
        now_utc = datetime.now(timezone.utc)
        cutoff_date = now_utc - timedelta(days=DAYS_THRESHOLD)
        
        print(f"Current UTC Time: {now_utc}")
        print(f"Targeting files modified BEFORE: {cutoff_date}")
        
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        deleted_files = []
        
        if 'Contents' not in response:
            print("Bucket is completely empty.")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Bucket is empty', 'deleted_files': []})
            }
            
        for obj in response['Contents']:
            file_key = obj['Key']
            
            # Fetch object metadata
            head_response = s3.head_object(Bucket=BUCKET_NAME, Key=file_key)
            metadata = head_response.get('Metadata', {})
            custom_time_str = metadata.get('original-created-time')
            
            if custom_time_str:
                # Sanitize 'Z' and force absolute timezone-aware UTC parsing
                clean_timestamp = custom_time_str.replace('Z', '+00:00')
                target_time = datetime.fromisoformat(clean_timestamp)
                # Ensure the parsed datetime is explicitly locked to UTC
                if target_time.tzinfo is None:
                    target_time = target_time.replace(tzinfo=timezone.utc)
                print(f"File '{file_key}' metadata string parsed as UTC object: {target_time}")
            else:
                target_time = obj['LastModified'].astimezone(timezone.utc)
                print(f"File '{file_key}' fallback to standard S3 upload UTC time: {target_time}")
            
            # 2. Deletion evaluation
            if target_time < cutoff_date:
                print(f"MATCH FOUND: '{file_key}' is older than {DAYS_THRESHOLD} days. Deleting...")
                s3.delete_object(Bucket=BUCKET_NAME, Key=file_key)
                deleted_files.append(file_key)
            else:
                # This log will tell us exactly why it skipped it
                time_difference = now_utc - target_time
                print(f"SKIPPED: '{file_key}' is only {time_difference.days} days old relative to current execution.")
                
        return {
            'statusCode': 200,
            'deleted_files': deleted_files
        }
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }