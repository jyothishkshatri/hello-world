# n8n Terraform Automation Workflow

This repository contains a fully automated n8n workflow for managing Terraform infrastructure. It is designed to be **intelligent, production-ready, and highly scalable**.

## Features

1.  **Universal Drift Detection**:
    -   Uses **AI-driven analysis** to identify drift for *any* AWS resource type.
    -   Automatically generates `import` blocks for unmanaged resources by querying AWS dynamically.
    -   **Secure Execution**: LLM-generated commands are sanitized and executed without shell access to prevent injection attacks.
    -   No hardcoded resource lists—it adapts to what Terraform finds.

2.  **Intelligent Excel Parsing**:
    -   Upload an Excel file with *any* sheet structure.
    -   The system uses AI to analyze the data, infer the correct Terraform resource types (e.g., `aws_instance`, `aws_db_instance`, `aws_lambda_function`), and generate valid HCL code.
    -   Includes a self-correction loop to fix syntax errors automatically.

3.  **Enterprise-Grade Git Integration**:
    -   Supports **Self-Managed GitLab** and GitLab SaaS.
    -   Securely handles authentication (Token Injection).
    -   Automated branching, committing, pushing, and Merge Request creation.

4.  **Backend Management**:
    -   Automatically initializes S3 backend and DynamoDB table for state locking if they don't exist.
    -   Generates `backend.tf` dynamically in the workspace to ensure consistent state management.

## Getting Started

### Prerequisites
-   **Docker & Docker Compose**: Installed on your machine.
-   **AWS Credentials**: Configured in `~/.aws/credentials` (or environment variables).
-   **GitLab Token**: A Personal Access Token with `api` and `write_repository` scopes.
-   **AI Provider**: An account with OpenAI, Anthropic, Bedrock, Vertex AI, OR a local Ollama instance.

### Installation
1.  **Clone this repository**:
    ```bash
    git clone https://gitlab.com/your-group/n8n-terraform-automation.git
    cd n8n-terraform-automation
    ```

2.  **Configure Environment**:
    -   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Edit `.env` to set your preferences.

3.  **Start the System**:
    ```bash
    docker-compose up -d
    ```
    -   Access n8n at `http://localhost:5678`.
    -   Import the `n8n_workflow.json` file into n8n.

### AI Configuration

#### Local Models (Ollama) - *Recommended for Cost/Privacy*
1.  Install Ollama on your host machine (or run via Docker).
2.  Pull a capable model (e.g., `llama3` or `mistral`):
    ```bash
    ollama pull llama3
    ```
3.  In `.env`, set:
    ```ini
    AI_PROVIDER=ollama
    AI_MODEL=llama3
    OLLAMA_BASE_URL=http://host.docker.internal:11434
    ```

#### Cloud Providers (OpenAI, Bedrock, Vertex)
-   **OpenAI**: Set `AI_PROVIDER=openai`, `AI_MODEL=gpt-4`, and provide `OPENAI_API_KEY`.
-   **AWS Bedrock**: Set `AI_PROVIDER=bedrock`, `AI_MODEL=anthropic.claude-3-sonnet-20240229-v1:0`, and ensure your AWS credentials have Bedrock access.

### Usage

1.  **Prepare your Infrastructure Spec**:
    -   Create an Excel file. Each sheet represents a resource type (e.g., `EC2`, `S3`, `Databases`).
    -   Columns should map roughly to Terraform arguments (e.g., `Name`, `InstanceType`, `BucketName`).
    -   *See `examples/` for a comprehensive sample.*

2.  **Trigger the Workflow**:
    -   Send a POST request to the Webhook URL (e.g., `http://localhost:5678/webhook/process-infra`).
    -   **Payload (Multipart Form-Data)**:
        -   `file`: The Excel file.
        -   `repo_url`: The Git repository URL.
        -   `branch_name`: The new branch name.
        -   `project_id`: The GitLab Project ID.

3.  **Review**:
    -   Check GitLab for the new Merge Request.
    -   Review the generated Terraform code and any imported resources.

## Troubleshooting

-   **"Terraform Init Failed"**: Check your AWS credentials and ensure the S3 bucket name in `.env` is globally unique.
-   **"Git Clone Failed"**: Verify your `GITLAB_TOKEN` has permissions and the `repo_url` is correct.
-   **"AI Generation Failed"**: Ensure your AI provider is reachable. For Ollama, check `OLLAMA_BASE_URL`.

## Emergency Procedures

-   **Stop the Workflow**:
    -   In the n8n UI, go to "Executions", find the running workflow, and click "Stop".
    -   Or kill the container: `docker-compose stop n8n`.

-   **Manual Intervention**:
    -   The workspace is mounted at `terraform_workspace`. You can SSH into the container (`docker-compose exec n8n bash`) and inspect the files in `/data/terraform_workspace`.
