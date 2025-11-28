from langchain_core.prompts import PromptTemplate


template = PromptTemplate(
    input_variables=["playwright_results", ],
    template="""You are an expert QA assistant. 
    Your have two jobs, First is to find only the relevant elements which are hoverable or perform Popup at click from the playwright_results and 
    Second is to create a Gherkin style test case for the question based on the playwright_results provided.
    {playwright_results}"""
)
