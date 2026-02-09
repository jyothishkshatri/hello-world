import pandas as pd
import os

def create_sample_spec(output_path):
    # Sample data for EC2
    ec2_data = [
        {'Name': 'web-server', 'InstanceType': 't3.micro', 'AMI': 'ami-0c55b159cbfafe1f0', 'Tags': 'Env=Dev,Role=Web'},
        {'Name': 'db-server', 'InstanceType': 't3.medium', 'AMI': 'ami-0c55b159cbfafe1f0', 'Tags': 'Env=Dev,Role=DB'}
    ]

    # Sample data for S3
    s3_data = [
        {'BucketName': 'my-app-logs', 'Versioning': 'Enabled', 'Encryption': 'AES256'},
        {'BucketName': 'my-app-assets', 'Versioning': 'Disabled', 'Encryption': 'AES256'}
    ]

    # Sample data for Security Groups
    sg_data = [
        {'GroupName': 'web-sg', 'Description': 'Allow HTTP/HTTPS', 'Inbound': '80,443', 'Outbound': 'All'},
        {'GroupName': 'db-sg', 'Description': 'Allow MySQL', 'Inbound': '3306', 'Outbound': 'All'}
    ]

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        pd.DataFrame(ec2_data).to_excel(writer, sheet_name='EC2', index=False)
        pd.DataFrame(s3_data).to_excel(writer, sheet_name='S3', index=False)
        pd.DataFrame(sg_data).to_excel(writer, sheet_name='SecurityGroups', index=False)

    print(f"Sample specification created at {output_path}")

if __name__ == "__main__":
    # Save to the same directory as the script so it's accessible via the volume mount
    output_path = os.path.join(os.path.dirname(__file__), 'infrastructure_spec.xlsx')
    create_sample_spec(output_path)
