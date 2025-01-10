from typing import List
from pydantic import BaseModel, Field

WIKIPEDIA_STYLE_ARTICLE_WRITER_PROMPT = (
    f"\nYou are tasked with writing a Wikipedia article based on your knowledge of a given topic. "
    f"Your response should be structured according to the JSON schema provided, and it should be as accurate and truthful as possible. "
)
class SubsectionModel(BaseModel):
    subheading: str = Field(
        description="The subheading for the subsection, providing a clear and concise title for the content that follows."
    )
    content: str = Field(
        description="The content of the subsection, presented as a  paragraph (or short series of paragraphs) that provide detailed information on the topic under the subheading."
    )

class SectionModel(BaseModel):
    heading: str = Field(
        description="The main heading for the section, denoting the primary topic or aspect being discussed."
    )
    content: str = Field(
        description="The main body of the section, providing an overview of the content covered in the section."
    )
    subsections: List[SubsectionModel] = Field(
        default_factory=list,
        description="A list of one to three subsections within the section, each with a subheading and associated content."
    )


class WikipediaStyleArticleWriterModel(BaseModel):
    title: str = Field(description="The title of the Wikipedia article.")
    short_description: str = Field(
        description="A brief description of the topic, typically 1 sentences long, providing an overview of the subject matter."
    )
    lead: str = Field(
        description="A concise introduction that summarizes the most important aspects of the topic."
    )
    sections: List[SectionModel] = Field(
        default_factory=list,
        description=("A list of 1-3 sections in the article, each containing a heading and a list of subsections.")
    )
    see_also: List[str] = Field(
        default_factory=list,
        description="A list of related topics that readers might find useful if they want to learn more about the subject."
    )
    conclusion: str = Field(
        description="A concluding paragraph summarizing the key points of the article."
    )

    def to_string(self) -> str:
        """
        Format contents into a markdown formatted text document
        """
        text = f"# {self.title}\n\n"
        text += f"{self.short_description}\n\n"
        text += f"## Introduction\n\n{self.lead}\n\n"
        for section in self.sections:
            text += f"## {section.heading}\n\n"
            for subsection in section.subsections:
                text += f"### {subsection.subheading}\n\n{subsection.content}\n\n"
        text += "## Conclusion\n\n"
        text += f"{self.conclusion}\n\n"
        text += "## See Also\n\n"
        for topic in self.see_also:
            text += f"- {topic}\n"
        return text
