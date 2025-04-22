from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import Field, BaseModel
from sqlalchemy import Column, Text
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel, Relationship

from skellybot_analysis.models.base_sql_model import BaseSQLModel
from skellybot_analysis.models.db_association_tables import ServerAnalysisTopicArea, UserProfileTopicArea
from skellybot_analysis.utilities.sanitize_filename import sanitize_name


class TopicArea(BaseSQLModel, table=True):
    """Represents a topic area of interest."""
    name: str = SQLField(
        primary_key=True,
        description="The name of this topic area. This should be a single word or hyphenated phrase that describes the topic area. For example, 'machine-learning', 'python', 'oculomotor-control', 'neural-networks', 'computer-vision', etc. Do not include conversational aspects such as 'greetings', 'farewells', 'thanks', etc.")
    category: str = SQLField(
        primary_key=True,
        description="The general category or field of interest (e.g., 'science', 'technology', 'arts', 'activities', 'health', etc).")
    subject: str = SQLField(
        primary_key=True,
        description="A more specific subject or area of interest within the category (e.g., 'biology', 'computer science', 'music', 'sports', 'medicine', etc).")
    topic: str = SQLField(
        primary_key=True,
        description="More specific topic or subfield within the category (e.g., 'neuroscience', 'machine learning',  'classical music', 'basketball', 'cardiology', etc).")
    subtopic: str = SQLField(
        primary_key=True,
        description="An even more specific subtopic or area of interest within the topic (e.g., 'oculomotor-control', 'neural-networks', 'Baroque music', 'NBA', 'heart surgery', etc).")
    niche: str = SQLField(
        primary_key=True,
        description="A very specific niche or focus area within the subtopic (e.g., 'gaze-stabilization', 'convolutional-neural-networks', 'Bach', 'NBA playoffs', 'pediatric cardiology', etc).")
    description: str = SQLField(sa_column=Column(Text),
                             description="A brief description of this interest, including any relevant background information, key concepts, notable figures, recent developments, and related topics. This should be a concise summary that provides context and depth to the interest")

    user_profiles: list["UserProfile"] = Relationship(
        back_populates="interests",
        link_model=UserProfileTopicArea
    )
    server_analyses: list["ServerObjectAiAnalysis"] = Relationship(
        back_populates="topic_areas",
        link_model=ServerAnalysisTopicArea  # Change this to use ServerAnalysisTopicArea
    )

    @property
    def as_string(self):
        """
        Convert the TopicArea instance to a string representation.
        """
        return f"{self.name} -> {self.category} -> {self.subject} -> {self.topic} -> {self.subtopic} -> {self.niche}"

class TextAnalysisPromptModel(BaseModel):
    title_slug: str = Field(
        description="The a descriptive title of the text, will be used as the H1 header, the filename slug, and the URL slug. It should be short (only a few words) and provide a terse preview of the basic content of the full text, it should include NO colons")
    extremely_short_summary: str = Field(description="An extremely short 6-10 word summary of the text")
    very_short_summary: str = Field(description="A very short one sentence summary of the text")
    short_summary: str = Field(description="A short (2-3 sentence) summary of the text")
    highlights: str = Field(
        description="A list of the 5-10 most important points of the text, formatted as a bulleted list")
    detailed_summary: str = Field(
        description="An exhaustively thorough and detailed summary of the major points of this text in markdown bulleted outline format, like `* point 1\n* point 2\n* point 3` etc. Do not include conversational aspects such as 'the human greets the ai' and the 'ai responds with a greeting', only include the main contentful components of the text.")
    topic_areas: list[TopicArea] = Field(
        description="A list of topic areas that describe the content of the text. These will be used to categorize the text within a larger collection of texts. Ignore conversational aspects (such as 'greetings', 'farewells', 'thanks', etc.).  These should almost always be single word, unless the tag is a multi-word phrase that is commonly used as a single tag, in which case it should be hyphenated. For example, 'machine-learning, python, oculomotor-control,neural-networks, computer-vision', but NEVER things like 'computer-vision-conversation', 'computer-vision-questions', etc.")


class ServerObjectAiAnalysis(BaseSQLModel, table=True):
    """Represents an AI analysis of a server object"""
    context_route: str = SQLField(primary_key=True, index=True)  # `server_id`/`category_id`/`channel_id`/`thread_id`
    context_route_names: str = SQLField(index=True)  # `server_name`/`category_name`/`channel_name`/`thread_name`

    server_id: int = SQLField(foreign_key="server.id")
    category_id: Optional[int] = SQLField(default=None, foreign_key="category.id")
    channel_id: Optional[int] = SQLField(default=None, foreign_key="channel.id")
    thread_id: Optional[int] = SQLField(default=None, foreign_key="thread.id")

    server_name: str
    category_name: Optional[str] = SQLField(default=None)
    channel_name: Optional[str] = SQLField(default=None)
    thread_name: Optional[str] = SQLField(default=None)

    base_text: str = SQLField(description="The text this analysis is based on", sa_column=Column(Text))

    title_slug: str = SQLField(
        description="The a descriptive title of the text, will be used as the H1 header, the filename slug, and the URL slug. It should be short (only a few words) and provide a terse preview of the basic content of the full text, it should include NO colons")
    extremely_short_summary: str = SQLField(description="An extremely short 6-10 word summary of the text")
    very_short_summary: str = SQLField(description="A very short one sentence summary of the text")
    short_summary: str = SQLField(description="A short (2-3 sentence) summary of the text")
    highlights: str = SQLField(
        description="A (comma-separated string) list of the 5-10 most important points of the text, formatted as a bulleted list")
    detailed_summary: str = SQLField(
        description="An exhaustively thorough and detailed summary of the major points of this text in markdown bulleted outline format, like `* point 1\n* point 2\n* point 3` etc. Do not include conversational aspects such as 'the human greets the ai' and the 'ai responds with a greeting', only include the main contentful components of the text.")
    topic_areas: list[TopicArea] = Relationship(
        back_populates="server_analyses",
        link_model=ServerAnalysisTopicArea,
    )
    def save_as_markdown(self, base_folder: str):
        save_path = Path(base_folder) / self.safe_context_route
        save_path.mkdir(parents=True, exist_ok=True)

        with open(str(save_path / f"{self.filename}"), 'w', encoding='utf-8') as f:
            f.write(self.full_text)

    created_at: datetime = SQLField(default_factory=datetime.now)
    @property
    def safe_context_route(self) -> str:
        """
        Return a safe context route for the analysis.
        """
        cr = f"{sanitize_name(self.server_name)}-{self.server_id}/".lower().strip()
        if self.category_id:
            cr += f"{sanitize_name(self.category_name)}-{self.category_id}/".lower().strip()
        if self.channel_id:
            cr += f"{sanitize_name(self.channel_name)}-{self.channel_id}/".lower().strip()
        if self.thread_id:
            cr += f"{sanitize_name(self.thread_name)}-{self.thread_id}/".lower().strip()
        return cr

    @property
    def title(self):
        return self.title_slug.replace("-", " ").title()
    @property
    def filename(self, extension="md"):
        if not extension.startswith("."):
            extension = "." + extension
        return sanitize_name(self.title_slug.lower()) + f"{extension}"


    @property
    def tags(self):
        tag_list = []
        for topic in self.topic_areas:
            tag_list.extend(list(topic.model_dump(exclude={"id", "created_at", "description"}).values()))
        clean_tags = []
        for tag in tag_list:
            tag.strip()
            if not tag.startswith("#"):
                tag = "#" + tag
            tag.replace(" ", "-")
            tag = tag.replace("# ", "#")
            tag = tag.replace("##", "#")
            tag = tag.replace("###", "#")
            if not tag in clean_tags:
                clean_tags.append(tag)
        return clean_tags

    @property
    def topic_areas_string(self):
        topic_areas = []
        for topic in self.topic_areas:
            topic_areas.append(topic.as_string)
        return "\n- ".join(topic_areas)

    @property
    def tags_string(self):
        return ", \n".join(self.tags)

    @property
    def backlinks(self):
        bl = []
        for thing in self.tags:
            thing = f"[[{thing}]]"
            bl.append(thing)
        return "\n".join(bl)


    @property
    def full_text(self):
        return f"""
# {self.title}\n\n
> context route: {self.safe_context_route}\n\n
## Extremely Short Summary\n\n
{self.extremely_short_summary}\n\n
## Highlights\n
{self.highlights}\n\n
## Very Short Summary\n
{self.very_short_summary}\n\n
## Short Summary\n
{self.short_summary}\n\n
## Detailed Summary\n
{self.detailed_summary}\n\n
## Topic Areas\n
{self.topic_areas_string}\n\n
## Tags\n
{self.tags}\n\n

## Backlinks\n
{self.backlinks}\n\n
__
## Full Content Text\n
{self.base_text}\n\n
__
        """

