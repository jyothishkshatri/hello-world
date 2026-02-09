import os
import sys
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.llms import Ollama
from langchain_community.chat_models import ChatOllama
from langchain_aws import ChatBedrock
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI

class InfrastructureGenerator:
    def __init__(self, provider='ollama', model_name='llama3'):
        self.provider = provider
        self.model_name = model_name
        self.llm = self._get_llm()

    def _get_llm(self):
        if self.provider == 'ollama':
            base_url = os.environ.get('OLLAMA_BASE_URL', 'http://host.docker.internal:11434')
            return ChatOllama(model=self.model_name, base_url=base_url)
        elif self.provider == 'bedrock':
            return ChatBedrock(model_id=self.model_name, region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        elif self.provider == 'vertex':
            return ChatVertexAI(model_name=self.model_name)
        elif self.provider == 'openai':
            return ChatOpenAI(model_name=self.model_name)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def load_spec(self, excel_path):
        xls = pd.ExcelFile(excel_path)
        specs = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            specs[sheet_name] = df.to_dict(orient='records')
        return specs

    def analyze_sheet_content(self, sheet_name, data):
        """Asks the LLM to understand what Terraform resources this sheet represents."""
        print(f"Analyzing sheet: {sheet_name}...")
        prompt = PromptTemplate(
            input_variables=["sheet_name", "data_sample"],
            template="""
            Analyze the following data from an Excel sheet named "{sheet_name}".

            Data Sample (first few rows):
            {data_sample}

            Identify the most likely AWS Terraform resource type(s) that this data represents (e.g., aws_instance, aws_s3_bucket, aws_iam_role).
            Return ONLY the Terraform resource type name(s), separated by commas if multiple. Do not include any explanation.
            """
        )

        # Take a sample to avoid token limits
        sample = str(data[:3])
        chain = prompt | self.llm
        response = chain.invoke({"sheet_name": sheet_name, "data_sample": sample})
        resource_types = response.content.strip()
        print(f"Identified resource types for {sheet_name}: {resource_types}")
        return resource_types

    def generate_terraform(self, specs):
        generated_code = {}

        for sheet_name, resource_list in specs.items():
            if not resource_list:
                continue

            # Step 1: Analyze structure
            resource_types = self.analyze_sheet_content(sheet_name, resource_list)

            # Step 2: Generate Code
            print(f"Generating Terraform code for {sheet_name} ({resource_types})...")

            prompt_template = PromptTemplate(
                input_variables=["resource_types", "spec"],
                template="""
                You are an expert Terraform developer.
                Based on the data below, generate valid Terraform HCL code for the resource type(s): {resource_types}.

                The data comes from a sheet representing these resources. Each row should correspond to a resource block, unless the data suggests otherwise (e.g., rules for a security group).

                Specification Data:
                {spec}

                Instructions:
                1. Use the column headers as a guide for arguments. Infer mapping intelligently (e.g., "Name" -> "tags = {{ Name = ... }}").
                2. Do not include provider configuration.
                3. Output ONLY the Terraform HCL code. No markdown, no explanations.
                4. Ensure valid HCL syntax.
                """
            )

            chain = prompt_template | self.llm
            response = chain.invoke({"resource_types": resource_types, "spec": str(resource_list)})

            raw_code = response.content.replace("```hcl", "").replace("```terraform", "").replace("```", "").strip()

            # Step 3: Review Code (Self-Correction)
            print(f"Reviewing generated code for {sheet_name}...")
            review_prompt = PromptTemplate(
                input_variables=["code"],
                template="""
                Review the following Terraform code for syntax errors or hallucinations.
                If it is valid, output it exactly as is.
                If there are errors (e.g., invalid arguments for the resource type), fix them and output the corrected code.

                Code to Review:
                {code}

                Output ONLY the final valid HCL code.
                """
            )
            review_chain = review_prompt | self.llm
            reviewed_response = review_chain.invoke({"code": raw_code})
            final_code = reviewed_response.content.replace("```hcl", "").replace("```terraform", "").replace("```", "").strip()

            generated_code[sheet_name] = final_code

        return generated_code

    def save_code(self, code_dict, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for sheet_name, code in code_dict.items():
            # Sanitize filename
            filename = "".join([c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')]).strip().lower().replace(" ", "_")
            filepath = os.path.join(output_dir, f"{filename}.tf")
            with open(filepath, 'w') as f:
                f.write(code)
            print(f"Saved {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python infra_generator.py <excel_path> <output_dir>")
        sys.exit(1)

    excel_path = sys.argv[1]
    output_dir = sys.argv[2]

    provider = os.environ.get('AI_PROVIDER', 'ollama')
    model = os.environ.get('AI_MODEL', 'llama3')

    print(f"Using AI Provider: {provider}, Model: {model}")

    try:
        generator = InfrastructureGenerator(provider, model)
        specs = generator.load_spec(excel_path)
        code = generator.generate_terraform(specs)
        generator.save_code(code, output_dir)
    except Exception as e:
        print(f"Error generating infrastructure: {e}")
        sys.exit(1)
