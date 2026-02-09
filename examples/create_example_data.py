import pandas as pd
import os

def create_comprehensive_spec(output_path):
    # Sheet 1: Compute (EC2)
    ec2_data = [
        {'Name': 'prod-web-01', 'InstanceType': 't3.large', 'AMI': 'ami-0c55b159cbfafe1f0', 'Tags': 'Env=Prod,Role=Web'},
        {'Name': 'prod-api-01', 'InstanceType': 'c5.large', 'AMI': 'ami-0c55b159cbfafe1f0', 'Tags': 'Env=Prod,Role=API'}
    ]

    # Sheet 2: Storage (S3)
    s3_data = [
        {'BucketName': 'prod-data-lake-raw', 'Versioning': 'Enabled', 'Encryption': 'AES256', 'ACL': 'private'},
        {'BucketName': 'prod-data-lake-processed', 'Versioning': 'Enabled', 'Encryption': 'AES256', 'ACL': 'private'}
    ]

    # Sheet 3: Networking (VPC)
    # Testing AI's ability to infer complex structures
    vpc_data = [
        {'CidrBlock': '10.0.0.0/16', 'Name': 'prod-vpc', 'EnableDnsSupport': 'true', 'EnableDnsHostnames': 'true'},
    ]

    # Sheet 4: IAM (Roles) - Testing policy attachment inference
    iam_data = [
        {'RoleName': 'prod-ec2-role', 'AssumeRolePolicy': 'ec2.amazonaws.com', 'ManagedPolicyArns': 'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'}
    ]

    # Sheet 5: Database (RDS)
    rds_data = [
        {'Identifier': 'prod-db', 'Engine': 'mysql', 'EngineVersion': '8.0', 'InstanceClass': 'db.t3.medium', 'AllocatedStorage': 20, 'Username': 'admin'}
    ]

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        pd.DataFrame(ec2_data).to_excel(writer, sheet_name='Compute_Instances', index=False)
        pd.DataFrame(s3_data).to_excel(writer, sheet_name='Storage_Buckets', index=False)
        pd.DataFrame(vpc_data).to_excel(writer, sheet_name='Networking_VPC', index=False)
        pd.DataFrame(iam_data).to_excel(writer, sheet_name='IAM_Roles', index=False)
        pd.DataFrame(rds_data).to_excel(writer, sheet_name='Database_RDS', index=False)

    print(f"Comprehensive specification created at {output_path}")

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), 'comprehensive_infrastructure.xlsx')
    create_comprehensive_spec(output_path)
