from fastapi import APIRouter
from utilities import run_gherkin
from LLM import model, template
from schemas import GherkinInput

router = APIRouter()

@router.post("")
def generate_gherkin(body: GherkinInput):

    playwright_results = run_gherkin(body.url)

    prompt = template.format(playwright_results=playwright_results)
    final_results = model.invoke(prompt)

    return {"results": final_results}