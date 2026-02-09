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
            # Assumes Ollama is running on host or accessible via URL
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

    def generate_terraform(self, specs):
        generated_code = {}

        prompt_template = PromptTemplate(
            input_variables=["resource_type", "spec"],
            template="""
            You are an expert Terraform developer. generate valid Terraform HCL code for the following {resource_type} resources based on the specification below.
            Do not include provider configuration. Only include resource blocks.
            Ensure best practices, such as using variables where appropriate, but for this task, hardcoding values from the spec is acceptable if variables are not provided.

            Specification:
            {spec}

            Output only the Terraform code. Do not include markdown backticks or explanations.
            """
        )

        for resource_type, resource_list in specs.items():
            print(f"Generating code for {resource_type}...")
            if not resource_list:
                continue

            # Convert list of dicts to string for prompt
            spec_str = str(resource_list)

            chain = prompt_template | self.llm
            response = chain.invoke({"resource_type": resource_type, "spec": spec_str})

            # clean response if it contains markdown code blocks
            code = response.content
            code = code.replace("```hcl", "").replace("```terraform", "").replace("```", "").strip()

            generated_code[resource_type] = code

        return generated_code

    def save_code(self, code_dict, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for resource_type, code in code_dict.items():
            filename = f"{resource_type.lower()}.tf"
            filepath = os.path.join(output_dir, filename)
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

    generator = InfrastructureGenerator(provider, model)
    specs = generator.load_spec(excel_path)
    code = generator.generate_terraform(specs)
    generator.save_code(code, output_dir)
