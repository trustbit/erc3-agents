"""Simple completion model for basic Q&A without reasoning steps"""

from pydantic import BaseModel
from openai import OpenAI
from config import default_config

client = OpenAI(
    timeout=60.0,
    max_retries=3,
)


class Number_Answer(BaseModel):
    """Answer with a number"""
    answer: int


class String_Answer(BaseModel):
    """Answer with a string"""
    answer: str


class Bool_Answer(BaseModel):
    """Answer with a boolean"""
    answer: bool


def dumb_completion(question: str, response_format):
    """
    Get a simple answer to a question using structured output.

    Args:
        question: The question to answer
        response_format: Pydantic model class (Number_Answer, String_Answer, or Bool_Answer)

    Returns:
        Parsed response object with .answer attribute
    """
    model_id = default_config.dumb_model_id or default_config.model_id
    completion = client.beta.chat.completions.parse(
        model=model_id,
        messages=[
            {"role": "user", "content": question}
        ],
        response_format=response_format,
    )
    return completion.choices[0].message.parsed
