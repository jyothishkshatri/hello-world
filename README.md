# n8n Terraform Automation Workflow

This repository contains a fully automated n8n workflow for managing Terraform infrastructure. It handles:
1.  **Drift Detection:** Identifies existing unmanaged resources and generates `import` blocks.
2.  **Excel Specification:** Parses an Excel file with infrastructure requirements (EC2, S3, SG).
3.  **AI Integration:** Leverages AI (Ollama, Bedrock, Vertex AI) to generate Terraform code.
4.  **Git Integration:** Commits changes to a new branch and creates a Merge Request on GitLab.
5.  **State Management:** Automatically initializes S3 backend and DynamoDB table for state locking.

## Setup

### Prerequisites
-   Docker and Docker Compose
-   AWS Credentials (`~/.aws/credentials`)
-   GitLab Personal Access Token

### Installation
1.  Clone this repository.
2.  Run `docker-compose up -d`.
3.  Import the workflow into n8n.
4.  Configure the `AWS_PROFILE` and other environment variables in `.env`.

### Generating Sample Spec
To generate a sample infrastructure specification file:
```bash
docker-compose run n8n python3 /data/scripts/create_sample_spec.py
```
This will create `infrastructure_spec.xlsx` in the `scripts` directory (mounted locally).

### Usage
-   Send a POST request to the Webhook URL (e.g., `http://localhost:5678/webhook/process-infra`).
-   **Payload (Multipart Form-Data):**
    -   `file`: The `infrastructure_spec.xlsx` file.
    -   `repo_url`: The Git repository URL (e.g., `https://gitlab.com/group/repo.git`).
    -   `branch_name`: The branch to create (e.g., `feature/infra-update-1`).
    -   `project_id`: The GitLab Project ID (integer).

-   The workflow will:
    -   Clone/Pull the repo (injecting credentials automatically).
    -   Check for drift and fix it (creating `generated_imports.tf`).
    -   Generate Terraform code based on the Excel specs (creating `.tf` files).
    -   Commit and push changes to a new branch.
    -   Create a Merge Request for review.

## Configuration
-   **AI Provider:** Configure in `docker-compose.yml` (e.g., `AI_PROVIDER=ollama`).
-   **GitLab:** Configure `GITLAB_URL` and `GITLAB_TOKEN`.
-   **AWS:** Ensure credentials are mounted correctly.

## Scripts Overview
-   `scripts/backend_manager.py`: Initializes S3 backend for Terraform state.
-   `scripts/drift_manager.py`: Runs `terraform plan`, detects unmanaged resources, and generates import blocks.
-   `scripts/infra_generator.py`: Parses Excel and uses AI to generate Terraform HCL.
-   `scripts/git_manager.py`: Handles Git operations (clone, push, MR) with secure authentication.
