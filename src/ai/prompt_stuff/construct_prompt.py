import logging
from typing import Union, Type

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)




def construct_json_prompt(pydantic_model: Type[BaseModel]) -> str:
    """
    Constructs a prompt for JSON mode from a Pydantic model.

    Args:
    model (BaseModel): The Pydantic model to construct the prompt from.

    Returns:
    str: The constructed prompt.
    """

    json_prompt = ['{\n']

    for name, field in pydantic_model.model_fields.items():
        field_info = pydantic_model.model_fields[name]
        description = field_info.description or ""
        json_prompt.append(f'"{name}": ({field_info.annotation}) // {description},')

    json_prompt[-1] = json_prompt[-1][:-1]  # Remove the trailing comma
    json_prompt.append("\n}")
    return "\n".join(json_prompt)


if __name__ == "__main__":
    # Example usage with a simple Pydantic model
    class ExampleModel(BaseModel):
        name: str = Field(..., description="The name of the person.")
        age: Union[float, int] = Field(..., description="The age of the person")
        is_student: bool = Field(..., description="Whether the person is a student or not.")
        hobbies: list[str] = Field(None, description="A list of the person's hobbies.")
        characteristics: dict[str, str] = Field(None,
                                                description="A dictionary of the person's characteristics. Keys are the characteristic names, values are the characteristic values.")


    # Construct the prompt
    prompt = construct_json_prompt(ExampleModel)
    print(prompt)
