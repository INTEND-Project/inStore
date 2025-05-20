import os

import dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """Question: {question}

Answer: Let's think step by step."""

prompt = ChatPromptTemplate.from_template(template)

dotenv.load_dotenv()
headers = {"Authorization": f"Bearer {os.environ.get('NT_BEARER_TOKEN')}"}

model = OllamaLLM(
    model="meta-llama/Llama-3.3-70B-Instruct", base_url="http://10.60.26.10/ollama", client_kwargs={"headers": headers}
)

chain = prompt | model

chain.invoke({"question": "What is LangChain?"})
