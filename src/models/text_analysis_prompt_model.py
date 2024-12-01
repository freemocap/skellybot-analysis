from typing import List

from pydantic import BaseModel, Field

from src.models.data_models.xyz_data_model import XYZData
from src.utilities.sanitize_filename import sanitize_name

class TagModel(BaseModel):
    name: str
    id: str
    embedding: List[float] | None = None
    tsne_xyz: XYZData | None = None

    @classmethod
    def from_tag(cls, tag_name: str):
        if not tag_name.startswith("#"):
            tag_name = "#" + tag_name
        return cls(name=tag_name, id=tag_name.replace("#", "tag-"))

    def as_text(self) -> str:
        return self.name.replace('#', '').replace('-', ' ')


class TextAnalysisPromptModel(BaseModel):
    title_slug: str = Field(
        description="The a descriptive title of the text, will be used as the H1 header, the filename slug, and the URL slug. It should be short (only a few words) and provide a terse preview of the basic content of the full text, it should include NO colons")
    extremely_short_summary: str = Field(description="An extremely short 6-10 word summary of the text")
    very_short_summary: str = Field(description="A very short one sentence summary of the text")
    short_summary: str = Field(description="A short (2-3 sentence) summary of the text")
    highlights: str | List[str] = Field(
        description="A list of the 5-10 most important points of the text, formatted as a bulleted list")
    detailed_summary: str = Field(
        description="An exhaustively thorough and detailed summary of the major points of this text in markdown bulleted outline format, like `* point 1\n* point 2\n* point 3` etc. Do not include conversational aspects such as 'the human greets the ai' and the 'ai responds with a greeting', only include the main contentful components of the text.")
    tags: str = Field(
        description="A list of tags that describe the content of the text, formatted as comma separated #lower-kabob-case. These should be like topic tags that can be used to categorize the text within a larger collection of texts. Ignore conversational aspects (such as '#greetings', '#farewells', '#thanks', etc.).  These should almost always be single word, unless the tag is a multi-word phrase that is commonly used as a single tag, in which case it should be hyphenated. For example, '#machine-learning, #python, #oculomotor-control,#neural-networks, #computer-vision', but NEVER things like '#computer-vision-conversation', '#computer-vision-questions', etc.")
    relevant: bool = Field(description="A boolean flag that indicates whether the content of this text is relevant to the course,"
                                       " or whether it is off topic or incomplete (i.e. a conversation that is mostly just greetings, "
                                       "or a text that is just a list of questions, etc.)")

    @property
    def title(self):
        return self.title_slug.replace("-", " ").title()

    @property
    def tags_list(self):
        tags_list = self.tags.split(",")
        clean_tags = []
        for tag in tags_list:
            tag.strip()
            if not tag.startswith("#"):
                tag = "#" + tag
            tag.replace(" ", "-")
            tag = tag.replace("# ", "#")
            tag = tag.replace("##", "#")
            tag = tag.replace("###", "#")
            clean_tags.append(tag)
        return clean_tags

    @property
    def tags_string(self):
        return "\n".join(self.tags_list)

    @property
    def backlinks(self):
        bl = []
        for thing in self.tags_list:
            thing = thing.replace("#", "").strip().replace(" ", "-")
            thing = f"[{thing}]"
            bl.append(thing)
        return "\n".join(bl)

    @property
    def filename(self, extension="md"):
        if not extension.startswith("."):
            extension = "." + extension
        return sanitize_name(self.title_slug.lower()) + f"{extension}"

    @property
    def highlights_as_string(self):
        if isinstance(self.highlights, list):
            return "\n".join(self.highlights)
        elif isinstance(self.highlights, str):
            return self.highlights
        else:
            return ""

    @classmethod
    def as_description_schema(cls):
        json_prompt = ['{\n']

        for name, field in cls.model_fields.items():
            field_info = cls.model_fields[name]
            description = field_info.description or ""
            json_prompt.append(f'"{name}": ({field_info.annotation}) // {description},')

        json_prompt[-1] = json_prompt[-1][:-1]  # Remove the trailing comma
        json_prompt.append("\n}")
        return "\n".join(json_prompt)

    def to_string(self):
        return self.__str__()



    def __str__(self):
        tags = "\n".join(self.tags.split(","))
        return f"""
# {self.title}\n\n
## Extremely Short Summary\n\n
{self.extremely_short_summary}\n\n
## Highlights\n
{self.highlights_as_string}\n\n
## Very Short Summary\n
{self.very_short_summary}\n\n
## Short Summary\n
{self.short_summary}\n\n
## Detailed Summary\n
{self.detailed_summary}\n\n
## Tags\n
{self.tags_string}\n\n
## Backlinks\n
{self.backlinks}\n\n
        """


if __name__ == "__main__":
    print(TextAnalysisPromptModel.as_description_schema())
