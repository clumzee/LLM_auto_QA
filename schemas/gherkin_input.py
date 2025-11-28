from pydantic import BaseModel

class GherkinInput(BaseModel):
    url: str