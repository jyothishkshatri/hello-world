import json
import subprocess
import boto3
import os
import sys
import shlex
from langchain.prompts import PromptTemplate
from langchain.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_aws import ChatBedrock
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI

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

def get_llm():
    provider = os.environ.get('AI_PROVIDER', 'ollama')
    model_name = os.environ.get('AI_MODEL', 'llama3')

    if provider == 'ollama':
        base_url = os.environ.get('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
        return ChatOllama(model=model_name, base_url=base_url)
    elif provider == 'bedrock':
        return ChatBedrock(model_id=model_name, region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    elif provider == 'vertex':
        return ChatVertexAI(model_name=model_name)
    elif provider == 'openai':
        return ChatOpenAI(model_name=model_name)
    else:
        return ChatOllama(model='llama3', base_url='http://host.docker.internal:11434')

def check_resource_exists_with_ai(resource_type, config, region):
    """
    Uses AI to determine how to check if a resource exists using aws cli or python boto3.
    """
    llm = get_llm()

    # Simplification: Ask LLM for a CLI command that returns the ID if found, or empty if not.
    # We'll ask for a specific AWS CLI command.

    prompt = PromptTemplate(
        input_variables=["resource_type", "config", "region"],
        template="""
        I need to check if an AWS resource of type "{resource_type}" already exists in region "{region}".
        The Terraform configuration for this resource has these attributes:
        {config}

        Generate a valid AWS CLI command that:
        1. Uses filters based on the attributes (like tags 'Name', or specific names/identifiers) to find this resource.
        2. Outputs ONLY the Resource ID (e.g., instance-id, bucket-name, arn) if found.
        3. Outputs nothing or fails gracefully if not found.
        4. Uses --query and --output text to ensure clean output.
        5. Does not use any pipe (|) or shell redirect characters.

        Example for aws_instance with Name tag 'web':
        aws ec2 describe-instances --filters "Name=tag:Name,Values=web" "Name=instance-state-name,Values=running" --query "Reservations[].Instances[].InstanceId" --output text --region {region}

        Return ONLY the command string. No markdown, no explanations.
        """
    )

    chain = prompt | llm

    # Extract meaningful identifiers to pass to prompt to keep it focused
    # We prioritize 'tags', 'name', 'id', 'bucket', 'arn'
    filtered_config = {k: v for k, v in config.items() if k in ['tags', 'name', 'bucket', 'id', 'arn', 'vpc_id', 'cidr_block']}

    response = chain.invoke({"resource_type": resource_type, "config": str(filtered_config), "region": region})
    command_str = response.content.strip().replace("```bash", "").replace("```", "").strip()

    print(f"Generated check command for {resource_type}: {command_str}")

    # Security Check: Ensure command starts with 'aws' and has no dangerous characters
    if not command_str.startswith('aws '):
        print(f"Security: Command rejected because it does not start with 'aws': {command_str}")
        return None

    if any(char in command_str for char in [';', '|', '&', '$', '`', '>', '<']):
        print(f"Security: Command rejected because it contains potentially dangerous characters: {command_str}")
        return None

    # Execute the command
    try:
        # Use shlex.split to parse the command string into a list of arguments
        # This prevents shell injection vulnerabilities
        cmd_args = shlex.split(command_str)

        result = subprocess.run(
            cmd_args,
            shell=False, # Secure execution
            check=False, # Don't raise exception on non-zero exit (e.g., not found)
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        resource_id = result.stdout.strip()
        if resource_id and resource_id != "None":
            return resource_id
    except Exception as e:
        print(f"Error executing AI command: {e}")

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

            # Use AI to find the resource ID
            resource_id = check_resource_exists_with_ai(resource_type, resource_config, region)

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
