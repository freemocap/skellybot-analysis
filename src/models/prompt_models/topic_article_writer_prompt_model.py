from typing import List

from pydantic import BaseModel, Field

WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT = (
    f"\nYou are tasked with writing a Wikipedia article based on your knowledge of a given topic. "
    f"Your response should be structured according to the JSON schema provided, and it should be as accurate and truthful as possible, "
    f"without citing external sources."
)

class WikipediaArticleWriterModel(BaseModel):
    title: str = Field(..., description="The title of the Wikipedia article.")
    lead: str = Field(..., description="A concise (2-4 sentence) introduction that summarizes the most important aspects of the topic.")
    background: str = Field(
        ...,
        description="A brief overview of the topic, including its history, context, and any relevant background information."
    )
    sections: List[dict] = Field(
        default_factory=list,
        description="A list of sections in the article, each containing a heading (denoted by an H2 ## Heading Title) and the associated content (a paragraph of text)."
    )
    conclusion: str = Field(..., description="A concluding paragraph summarizing the key points of the article.")
