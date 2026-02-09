terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Example of an existing resource that is managed
resource "aws_s3_bucket" "existing_bucket" {
  bucket = "my-existing-app-bucket"

  tags = {
    Name        = "My existing bucket"
    Environment = "Dev"
  }
}

# This resource exists in AWS (assume manual creation) but is missing from state
# drift_manager.py should detect this if we add a resource block for it in the new code
# For the sake of this example, we assume the user adds a resource block for 'legacy-server'
# in the new code generated from Excel, and the tool will find it exists and import it.
