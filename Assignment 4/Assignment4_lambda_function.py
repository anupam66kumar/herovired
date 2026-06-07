import json
import boto3
from datetime import datetime, timedelta, timezone

# Initialize the EC2 client globally
ec2 = boto3.client('ec2')

# REPLACE THIS with your actual EBS Volume ID (e.g., 'vol-0abcd1234efgh5678')
VOLUME_ID = 'YOUR_EBS_VOLUME_ID_HERE'

# Set the retention window (Assignment specifies 30 days)
# TIP: Change this to 0 during testing to instantly delete the snapshot you just made!
RETENTION_DAYS = 30

def lambda_handler(event, context):
    try:
        now_utc = datetime.now(timezone.utc)
        print(f"Execution started at: {now_utc}")
        
        # ==========================================
        # STEP 1: CREATE NEW SNAPSHOT
        # ==========================================
        description = f"Automated backup for volume {VOLUME_ID} created on {now_utc.strftime('%Y-%m-%d')}"
        
        print(f"Creating snapshot for volume {VOLUME_ID}...")
        snapshot = ec2.create_snapshot(
            VolumeId=VOLUME_ID,
            Description=description,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {'Key': 'CreatedBy', 'Value': 'LambdaAutomation'},
                        {'Key': 'PurgeAfterDays', 'Value': str(RETENTION_DAYS)}
                    ]
                }
            ]
        )
        
        new_snapshot_id = snapshot['SnapshotId']
        print(f"📸 SUCCESS: Created snapshot '{new_snapshot_id}' for volume '{VOLUME_ID}'.")
        
        # ==========================================
        # STEP 2: FIND AND PURGE OLD SNAPSHOTS
        # ==========================================
        cutoff_date = now_utc - timedelta(days=RETENTION_DAYS)
        print(f"Scanning for snapshots created before: {cutoff_date}")
        
        # Filter to only look at snapshots created by this Lambda function in your account
        # This prevents your script from accidentally looking at public/AWS system snapshots
        snapshot_response = ec2.describe_snapshots(
            OwnerIds=['self'],
            Filters=[
                {'Name': 'tag:CreatedBy', 'Values': ['LambdaAutomation']},
                {'Name': 'volume-id', 'Values': [VOLUME_ID]}
            ]
        )
        
        deleted_snapshots = []
        
        for snap in snapshot_response['Snapshots']:
            snap_id = snap['SnapshotId']
            snap_time = snap['StartTime'] # Timezone-aware UTC datetime object
            
            # Skip the snapshot we literally just created in this execution loop
            if snap_id == new_snapshot_id:
                continue
                
            # Deletion evaluation logic
            if snap_time < cutoff_date:
                print(f"🗑️ MATCH FOUND: Snapshot '{snap_id}' is older than {RETENTION_DAYS} days (Created: {snap_time}). Deleting...")
                ec2.delete_snapshot(SnapshotId=snap_id)
                deleted_snapshots.append(snap_id)
            else:
                print(f"SAFE: Snapshot '{snap_id}' is within retention window (Created: {snap_time}).")
                
        # ==========================================
        # STEP 3: LOG SUMMARY AND RETURN
        # ==========================================
        print("\n--- EBS BACKUP SUMMARY REPORT ---")
        print(f"New Snapshot Created: {new_snapshot_id}")
        print(f"Total Snapshots Purged: {len(deleted_snapshots)}")
        print(f"Deleted Snapshot IDs: {deleted_snapshots}")
        print("---------------------------------\n")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'Success',
                'created_snapshot': new_snapshot_id,
                'deleted_snapshots': deleted_snapshots,
                'retention_days_used': RETENTION_DAYS
            })
        }
        
    except Exception as e:
        print(f"Critical error during execution: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }