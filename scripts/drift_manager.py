import json
import subprocess
import boto3
import os
import sys

def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(e.stderr)
        return None

def check_s3_exists(bucket_name, region):
    s3 = boto3.client('s3', region_name=region)
    try:
        s3.head_bucket(Bucket=bucket_name)
        return True
    except:
        return False

def check_ec2_exists(name_tag, region):
    try:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [name_tag]},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
            ]
        )
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                return instance.get('InstanceId')
    except Exception as e:
        print(f"Error checking EC2 existence: {e}")
    return None

def check_sg_exists(group_name, vpc_id, region):
    try:
        ec2 = boto3.client('ec2', region_name=region)
        filters = [{'Name': 'group-name', 'Values': [group_name]}]
        if vpc_id:
            filters.append({'Name': 'vpc-id', 'Values': [vpc_id]})

        response = ec2.describe_security_groups(Filters=filters)
        if response.get('SecurityGroups'):
            return response['SecurityGroups'][0]['GroupId']
    except Exception as e:
        print(f"Error checking SG existence: {e}")
    return None

def analyze_drift(tf_dir, region):
    print("Initializing Terraform...")
    if not run_command(['terraform', 'init'], cwd=tf_dir):
        print("Terraform init failed.")
        return

    print("Running Terraform Plan...")
    plan_file = os.path.join(tf_dir, 'tfplan')
    if not run_command(['terraform', 'plan', '-out=tfplan'], cwd=tf_dir):
        print("Terraform plan failed.")
        return

    json_output = run_command(['terraform', 'show', '-json', 'tfplan'], cwd=tf_dir)
    if not json_output:
        print("Failed to generate plan JSON.")
        return

    try:
        plan = json.loads(json_output)
    except json.JSONDecodeError as e:
        print(f"Failed to parse plan JSON: {e}")
        return

    resource_changes = plan.get('resource_changes', [])

    imports = []

    for change in resource_changes:
        actions = change.get('change', {}).get('actions', [])
        if 'create' in actions:
            resource_type = change['type']
            resource_addr = change['address']
            resource_config = change.get('change', {}).get('after', {})

            print(f"Checking potential drift for {resource_addr}...")

            resource_id = None

            if resource_type == 'aws_s3_bucket':
                bucket_name = resource_config.get('bucket')
                if bucket_name and check_s3_exists(bucket_name, region):
                    resource_id = bucket_name

            elif resource_type == 'aws_instance':
                tags = resource_config.get('tags', {})
                name_tag = tags.get('Name')
                if name_tag:
                    resource_id = check_ec2_exists(name_tag, region)

            elif resource_type == 'aws_security_group':
                group_name = resource_config.get('name')
                vpc_id = resource_config.get('vpc_id')
                if group_name:
                    resource_id = check_sg_exists(group_name, vpc_id, region)

            if resource_id:
                print(f"Found existing resource for {resource_addr}: {resource_id}")
                imports.append(f'import {{\n  to = {resource_addr}\n  id = "{resource_id}"\n}}\n')

    if imports:
        import_file = os.path.join(tf_dir, 'generated_imports.tf')
        with open(import_file, 'w') as f:
            f.writelines(imports)
        print(f"Generated {len(imports)} import blocks in {import_file}")
    else:
        print("No drift detected or no matching existing resources found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python drift_manager.py <terraform_dir>")
        sys.exit(1)

    tf_dir = sys.argv[1]
    region = os.environ.get('AWS_REGION', 'us-east-1')
    analyze_drift(tf_dir, region)
