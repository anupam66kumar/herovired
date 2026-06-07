## Assignment 1: Automated EC2 Instance Management

### Objective
Automatically manage EC2 instance states (`running` or `stopped`) based on specific resource tags to optimize computing environments.

### Steps Followed
1. **EC2 Tagging:** Annotated two separate `t2.micro` instances with the tag key `Action`. One instance was assigned the value `Auto-Start`, and the other was assigned `Auto-Stop`.
2. **IAM Role Configuration:** Created an IAM execution role for Lambda and attached the `AmazonEC2FullAccess` policy to grant explicit permissions for describing, starting, and stopping EC2 instances.
3. **Lambda Setup:** Provisioned an AWS Lambda function from scratch utilizing the **Python 3.x** runtime, assigned the newly created IAM role, and pasted the execution logic.
4. **Manual Invocation & Verification:** Triggered the Lambda function manually. The function checked the instances via an API filter, moved the running `Auto-Stop` instance into a `Stopping` state, and moved the stopped `Auto-Start` instance into a `Pending` (running) state.

-----------------------------
## Assignment 2: Automated S3 Bucket Cleanup

### Objective
Automate S3 object remediation by finding and removing files older than 30 days from a designated storage bucket.

### Overcoming the S3 Upload Timestamp Constraint
Amazon S3 stamps all new objects with a fresh LastModified time based strictly on when it receives the file, overwriting local computer system file creation dates. To safely test files older than 30 days without waiting, **User-Defined Custom Metadata** (original-created-time) was attached during upload to keep the original historical dates from March 2026.

### Steps Followed
1.  **S3 Bucket Creation:** Provisioned a globally unique bucket named anupam66s3bucket.
2.  **Local Environment Setup:** Initialized an isolated Python virtual environment (venv) to work around OS system package limitations (PEP 668), activated it via source bin/activate, and installed boto3.
3.  **Object Hydration Script:** Executed a local Python script to upload local files (CalculatorPlus.py and GeometryCalculator.py), dynamically extracting their true local system modification times and embedding them into the object headers as metadata.
4.  **Lambda Deployment:** Configured a Lambda function with AmazonS3FullAccess execution permissions. The code pulls the custom metadata header via s3.head\_object, parses it into a UTC object, evaluates it against a 30-day window, and cleans up the bucket.

-----------------------------

## Assignment 4: Automatic EBS Snapshot and Cleanup


### Objective

Automate backup generation for specific Elastic Block Store (EBS) volumes and ensure historical snapshots older than 30 days are automatically removed to optimize cloud storage expenditures.

### Overcoming the Runtime Timestamp Constraint

AWS generates snapshot creation times dynamically at run time. To easily test the backup cycle logic without waiting 30 days, a retention parameter variable configuration (RETENTION\_DAYS = 0) was targeted during the active evaluation to instantly clean up snapshots made during a preceding manual run.

### Steps Followed

1.  **EBS Volume Target Identification:** Opened the EC2 dashboard console, located the active operational storage volume, and recorded its unique identifier string (VOLUME\_ID).
    
2.  **IAM Permissions Mapping:** Created an IAM execution role for Lambda containing permissions (AmazonEC2FullAccess) to create, list, and delete snapshots.
    
3.  **Lambda Function Architecture Setup:** Built a new Lambda function powered by Python 3.x, linked the target execution role, and added specific metadata tracking tags (CreatedBy: LambdaAutomation) during snapshot initialization.
    
4.  **Automated EventBridge Integration:** Configured an Amazon EventBridge schedule rule mapping directly to the function with a rate expression of rate(5 minutes) to establish continuous recurrences.
    
5.  **Validation Testing:** Successfully ran the routine with retention days modified to 0. The execution cycle generated a fresh snapshot, ran an account query for previous snapshots, matched the older entry, and purged it instantly.

-------------------------------------

## Assignment 5: Auto-Tagging EC2 Instances on Launch

### Objective

Enforce cloud resource governance by automatically applying the launch calendar date and organizational tracking keys to any EC2 instance immediately as it initializes.

### Event-Driven Execution Mechanism

Rather than scanning environment assets continuously, this routine relies on an asynchronous event architecture. When an instance moves to a running status, **Amazon EventBridge** intercepts the API event rule notification and passes a payload body directly to Lambda containing the runtime instance-id.

### Steps Followed

1.  **IAM Role Provisioning:** Created a targeted execution role bound to the Lambda service, injecting the AmazonEC2FullAccess authorization parameters to facilitate structural metadata updates on computing assets.
    
2.  **Lambda Function Implementation:** Built an operational serverless endpoint leveraging the **Python 3.x** environment, attaching programmatic parsing paths that isolate the unique string nested at event\['detail'\]\['instance-id'\].
    
3.  **Automated EventBridge Attachment:** Created a standard Event Pattern Rule inside CloudWatch/EventBridge. Configured it to intercept EC2 Instance State-change Notification states filtering specifically for the running state value.
    
4.  **Validation Testing:** Initiated a manual t2.micro instance launch configuration from the EC2 console. After a brief operational propagation delay, audited the asset’s **Tags** pane to verify LaunchDate, Environment, and ManagedBy strings were appended successfully.
