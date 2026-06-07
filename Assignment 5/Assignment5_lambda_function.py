import json
import boto3
from datetime import datetime, timezone

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    try:
        # Extract metadata identifiers from incoming EventBridge payload
        instance_id = event.get('detail', {}).get('instance-id')
        current_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        if not instance_id:
            print("Error: Target instance-id missing from structural event body.")
            return {'statusCode': 400, 'body': json.dumps('Missing parameters.')}
            
        print(f"Auto-tagging triggered for Instance ID: {instance_id}")
        
        # Inject resource tags into the isolated instance
        ec2.create_tags(
            Resources=[instance_id],
            Tags=[
                {'Key': 'LaunchDate', 'Value': current_date},
                {'Key': 'Environment', 'Value': 'Automated-Lab'},
                {'Key': 'ManagedBy', 'Value': 'LambdaAutoTag'}
            ]
        )
        print(f"Successfully tagged instance {instance_id} with date {current_date}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'Success',
                'tagged_instance': instance_id,
                'applied_date': current_date
            })
        }
    except Exception as e:
        print(f"Critical execution error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps(str(e))}