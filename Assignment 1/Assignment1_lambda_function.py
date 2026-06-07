import json
import boto3

# Initialize the EC2 client globally to leverage connection reuse across invocations
ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    try:
        # 1. Fetch instances that match our specific assignment tag keys and values
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Action',
                    'Values': ['Auto-Stop', 'Auto-Start']
                }
            ]
        )
        
        auto_stop_instances = []
        auto_start_instances = []
        
        # 2. Parse through the reservations and instances to separate IDs by tag value
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                tags = instance.get('Tags', [])
                
                # Double-check the tag key-value mapping to match assignment logic
                for tag in tags:
                    if tag['Key'] == 'Action':
                        if tag['Value'] == 'Auto-Stop':
                            auto_stop_instances.append(instance_id)
                        elif tag['Value'] == 'Auto-Start':
                            auto_start_instances.append(instance_id)

        # 3. Log what the script found to CloudWatch Logs
        print(f"Targeting for STOP command: {auto_stop_instances}")
        print(f"Targeting for START command: {auto_start_instances}")

        # Dictionary to keep track of actions for the final Lambda response output
        summary = {
            'stopped_instances': [],
            'started_instances': []
        }

        # 4. Execute stop command if target instances exist
        if auto_stop_instances:
            ec2.stop_instances(InstanceIds=auto_stop_instances)
            print(f"Successfully sent STOP command to: {auto_stop_instances}")
            summary['stopped_instances'] = auto_stop_instances
        else:
            print("No running instances found matching tag -> Action: Auto-Stop")

        # 5. Execute start command if target instances exist
        if auto_start_instances:
            ec2.start_instances(InstanceIds=auto_start_instances)
            print(f"Successfully sent START command to: {auto_start_instances}")
            summary['started_instances'] = auto_start_instances
        else:
            print("No stopped instances found matching tag -> Action: Auto-Start")
            
        # 6. Return standard structured HTTP response for Lambda logs/execution output
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'Success',
                'message': 'Automation processes handled successfully.',
                'actions_summary': summary
            })
        }

    except Exception as e:
        # Error handling block to capture configuration errors or permission denials
        print(f"An unexpected execution error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'Failure',
                'error': str(e)
            })
        }