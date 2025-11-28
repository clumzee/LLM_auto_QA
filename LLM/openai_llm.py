from langchain_openai import ChatOpenAI
from schemas import GeneratedTestScenarios
from core.config import settings

model = ChatOpenAI(temperature=0.3, model_name="gpt-4", api_key=settings.OPENAI_API_KEY)
model = model.with_structured_output(GeneratedTestScenarios)





