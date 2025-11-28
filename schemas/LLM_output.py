from typing import List, Optional, Text
from pydantic import BaseModel, Field, HttpUrl, constr

NonEmptyStr = constr(strip_whitespace=True, min_length=1)

class PopupScenario(BaseModel):
    """
    Represents a popup/modal interaction discovered on the page.
    """
    base_url: HttpUrl = Field(..., description="Page URL where popup interaction occurs.")
    trigger_element_label: Optional[str] = Field( # ignore warning
        ..., description="Label of the element that triggers the popup (e.g. 'Learn More')."
    )
    popup_title: Optional[str] = Field( # ignore warning
        ..., description="Heading/title of the popup/modal."
    )
    popup_action_button: Optional[str] = Field(
        ..., description="Button inside popup that redirects or closes it."
    )
    expected_redirect_url: Optional[HttpUrl] = Field(
        None, description="Target URL after clicking the popup action button (if applicable)."
    )

    ImplementationFlow: Text = Field(description="Step-by-step flow to implement the Click interaction test.")



class HoverScenario(BaseModel):
    """
    Represents a hover-based interaction (dropdown, tooltip, etc.)
    """
    base_url: HttpUrl = Field(..., description="Page URL where hover happened.")
    hover_element_label: NonEmptyStr = Field(
        ..., description="Visible text/aria-label/title of the hoverable element."
    )
    revealed_element_label: NonEmptyStr = Field(
        ..., description="Element revealed due to hover (usually a clickable link)."
    )
    expected_redirect_url: Optional[HttpUrl] = Field(
        None, description="Expected URL after clicking the revealed element (if it is clickable)."
    )

    ImplementationFlow: Text = Field(description="Step-by-step flow to implement the hover interaction test.")



class GeneratedTestScenarios(BaseModel):
    """
    Final LLM output containing both types of tests.
    """
    popups: List[PopupScenario] = Field(
        default_factory=list,
        description="List of all popup interactions discovered."
    )
    hovers: List[HoverScenario] = Field(
        default_factory=list,
        description="List of all hover-based interactions discovered."
    )

