# Comprehensive Infrastructure Example

This directory contains a complete example to test the n8n Terraform Automation Workflow. It demonstrates how to handle various AWS resources (EC2, S3, VPC, IAM, RDS) and validates the AI's ability to interpret generic Excel data.

## Contents

1.  `create_example_data.py`: A Python script to generate a `comprehensive_infrastructure.xlsx` file. This file contains multiple sheets with different resource types to test the system's "intelligence".
2.  `main.tf`: A starter Terraform file representing an existing state (partial).

## Step-by-Step Test Guide

### 1. Generate the Test Data
Run the script to create the Excel file:
```bash
python3 create_example_data.py
```
This will create `comprehensive_infrastructure.xlsx` in this directory.

### 2. Configure the Environment
Ensure your `.env` file (in the root directory) has:
-   `AI_PROVIDER` set (e.g., `ollama`, `openai`, or `bedrock`).
-   Valid AWS credentials mounted via Docker.
-   `GITLAB_URL` and `GITLAB_TOKEN` set.

### 3. Run the Workflow
Send a POST request to your n8n webhook (e.g., `http://localhost:5678/webhook/process-infra`) with the following form-data:

-   `file`: (Upload `comprehensive_infrastructure.xlsx`)
-   `repo_url`: Your target GitLab repository URL (e.g., `https://gitlab.com/my-group/infra-test.git`).
-   `branch_name`: `feature/test-comprehensive-01`
-   `project_id`: Your GitLab Project ID.

### 4. What to Expect

1.  **Repo Clone**: The system clones your repo.
2.  **Drift Check**:
    -   The system runs `terraform plan`.
    -   It sees the new resources defined in the Excel sheet (which the AI generates code for).
    -   It checks if any of these resources *already exist* in your AWS account using AI-generated CLI commands.
    -   If found, it generates `import` blocks in `generated_imports.tf`.
3.  **Code Generation**:
    -   The AI analyzes each sheet in the Excel file (`Compute_Instances`, `Storage_Buckets`, etc.).
    -   It identifies them as `aws_instance`, `aws_s3_bucket`, etc.
    -   It generates valid Terraform HCL files (e.g., `compute_instances.tf`, `storage_buckets.tf`).
    -   It self-corrects any syntax errors.
4.  **Commit & MR**:
    -   The new `.tf` files and `generated_imports.tf` are committed.
    -   A Merge Request is created on GitLab.

### 5. Verification
-   Go to your GitLab Merge Request.
-   Verify that the Terraform code looks correct and follows the specs in the Excel file.
-   Check if `generated_imports.tf` contains import blocks for any resources that happened to already exist.
