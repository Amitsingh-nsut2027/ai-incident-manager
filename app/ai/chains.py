"""Example LangChain chains (Phase 12).

Demonstrates the two patterns every agent will use:
  1. A text chain:  prompt | model | output-parser   (LCEL pipe syntax)
  2. A structured chain: model.with_structured_output(PydanticModel)
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.ai.models import get_chat_model


# --- 1. A simple text chain --------------------------------------------------
def build_explanation_chain():
    """A chain that explains a log line in plain English (returns a string)."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert SRE. Explain clearly and concisely."),
            ("user", "Explain what this log line means:\n\n{log_line}"),
        ]
    )
    model = get_chat_model()
    # LCEL: data flows prompt -> model -> parser (string out).
    return prompt | model | StrOutputParser()


# --- 2. A structured-output chain -------------------------------------------
class SeverityVerdict(BaseModel):
    """Schema the LLM must fill — validated automatically (Phase 5 + 11 + 12)."""

    severity: int = Field(ge=1, le=4, description="1=critical .. 4=minor")
    reason: str = Field(description="short justification")


def build_severity_chain():
    """A chain that classifies a log's severity into a validated Pydantic object."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an SRE triaging incidents. Assign a severity 1-4."),
            ("user", "Classify the severity of this log:\n\n{log_line}"),
        ]
    )
    # with_structured_output forces + validates the output against SeverityVerdict.
    model = get_chat_model().with_structured_output(SeverityVerdict)
    return prompt | model
