import boto3
import os
import sys

def init_backend(bucket_name, table_name, region):
    s3 = boto3.client('s3', region_name=region)
    dynamodb = boto3.client('dynamodb', region_name=region)

    # Check/Create S3 Bucket
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} exists.")
    except Exception as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            print(f"Creating bucket {bucket_name}...")
            if region == 'us-east-1':
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            # Enable versioning
            s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            # Enable encryption
            s3.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]
                }
            )
        else:
            print(f"Error checking bucket: {e}")
            sys.exit(1)

    # Check/Create DynamoDB Table
    try:
        dynamodb.describe_table(TableName=table_name)
        print(f"Table {table_name} exists.")
    except dynamodb.exceptions.ResourceNotFoundException:
        print(f"Creating table {table_name}...")
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'LockID', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'LockID', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
    except Exception as e:
        print(f"Error checking table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    bucket = os.environ.get('TF_STATE_BUCKET')
    table = os.environ.get('TF_STATE_TABLE')
    region = os.environ.get('AWS_REGION', 'us-east-1')

    if not bucket or not table:
        print("Error: TF_STATE_BUCKET and TF_STATE_TABLE env vars must be set.")
        sys.exit(1)

    init_backend(bucket, table, region)

    # Generate backend.tf in the workspace if provided
    # The workflow calls this script. The workspace path should be passed as an argument or we default to /data/terraform_workspace
    workspace_path = '/data/terraform_workspace'
    if len(sys.argv) > 1:
        workspace_path = sys.argv[1]

    if os.path.exists(workspace_path):
        backend_config = f"""
terraform {{
  backend "s3" {{
    bucket         = "{bucket}"
    key            = "terraform.tfstate"
    region         = "{region}"
    dynamodb_table = "{table}"
    encrypt        = true
  }}
}}
"""
        backend_file = os.path.join(workspace_path, 'backend.tf')
        with open(backend_file, 'w') as f:
            f.write(backend_config)
        print(f"Generated backend.tf at {backend_file}")
    else:
        print(f"Workspace path {workspace_path} does not exist. Skipping backend.tf generation.")
