from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, Text, JSON
from sqlmodel import Relationship, Field
from pydantic import computed_field

from skellybot_analysis.db.db_models.db_base_sql_model import BaseSQLModel
from skellybot_analysis.models.context_route_model import ContextRoute
from skellybot_analysis.db.db_models.db_association_tables import ServerAnalysisTopicArea, UserProfileTopicArea
from skellybot_analysis.models.prompt_models import TopicAreaPromptModel
from skellybot_analysis.db.db_models.db_server_models import User
from skellybot_analysis.utilities.sanitize_filename import sanitize_name


class TopicArea(BaseSQLModel, table=True):
    """Represents a topic area of interest."""
    name: str = Field(
        primary_key=True,
        description="The name of this topic area. This should be a single word or hyphenated phrase that describes the topic area. For example, 'machine-learning', 'python', 'oculomotor-control', 'neural-networks', 'computer-vision', etc. Do not include conversational aspects such as 'greetings', 'farewells', 'thanks', etc.")
    category: str = Field(
        primary_key=True,
        description="The general category or field of interest (e.g., 'science', 'technology', 'arts', 'activities', 'health', etc).")
    subject: str = Field(
        primary_key=True,
        description="A more specific subject or area of interest within the category (e.g., 'biology', 'computer science', 'music', 'sports', 'medicine', etc).")
    topic: str = Field(
        primary_key=True,
        description="More specific topic or subfield within the category (e.g., 'neuroscience', 'machine learning',  'classical music', 'basketball', 'cardiology', etc).")
    subtopic: str = Field(
        primary_key=True,
        description="An even more specific subtopic or area of interest within the topic (e.g., 'oculomotor-control', 'neural-networks', 'Baroque music', 'NBA', 'heart surgery', etc).")
    niche: str = Field(
        primary_key=True,
        description="A very specific niche or focus area within the subtopic (e.g., 'gaze-stabilization', 'convolutional-neural-networks', 'Bach', 'NBA playoffs', 'pediatric cardiology', etc).")
    description: str = Field(sa_column=Column(Text),
                             description="A brief description of this interest, including any relevant background information, key concepts, notable figures, recent developments, and related topics. This should be a concise summary that provides context and depth to the interest")

    user_profiles: list["UserProfile"] = Relationship(
        back_populates="interests",
        link_model=UserProfileTopicArea
    )
    server_analyses: list["ServerObjectAiAnalysis"] = Relationship(
        back_populates="topic_areas",
        link_model=ServerAnalysisTopicArea  # Change this to use ServerAnalysisTopicArea
    )

    @computed_field
    def as_string(self) -> str:
        """
        Convert the TopicArea instance to a string representation.
        """
        return f"{self.name} -> {self.category} -> {self.subject} -> {self.topic} -> {self.subtopic} -> {self.niche}"

    @classmethod
    def from_prompt_model(cls, topic: TopicAreaPromptModel):
        """
        Create a TopicArea instance from a TopicAreaPromptModel instance.
        """
        return cls.get_create_or_update(
            db_id=hash((topic.name, topic.category, topic.subject, topic.topic, topic.subtopic, topic.niche)),
            name=topic.name,
            category=topic.category,
            subject=topic.subject,
            topic=topic.topic,
            subtopic=topic.subtopic,
            niche=topic.niche,
            description=topic.description
        )


class ServerObjectAiAnalysis(BaseSQLModel, table=True):
    """Represents an AI analysis of a server object"""
    context_route_ids: str = Field(index=True)  # `server_id`/`category_id`/`channel_id`/`thread_id`
    context_route_names: str = Field(index=True)  # `server_name`/`category_name`/`channel_name`/`thread_name`

    server_id: str = Field(index=True)
    server_name: str

    category_id: Optional[int] = Field(default=None, index=True)
    category_name: Optional[str] = Field(default=None)
    channel_id: Optional[int] = Field(default=None,  index=True)
    channel_name: Optional[str] = Field(default=None)
    thread_id: Optional[int] = Field(default=None,   index=True, foreign_key="thread.id")
    thread_name: Optional[str] = Field(default=None)
    thread_owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    # thread_owner_name: Optional[str] = Field(default=None, foreign_key="user.name")

    base_text: str = Field(description="The text this analysis is based on", sa_column=Column(Text))
    analysis_prompt: str = Field(description="The prompt used to generate this analysis (includes base_text)", sa_column=Column(Text))

    title_slug: str = Field(
        description="The a descriptive title of the text, will be used as the H1 header, the filename slug, and the URL slug. It should be short (only a few words) and provide a terse preview of the basic content of the full text, it should include NO colons")
    extremely_short_summary: str = Field(description="An extremely short 6-10 word summary of the text")
    very_short_summary: str = Field(description="A very short one sentence summary of the text")
    short_summary: str = Field(description="A short (2-3 sentence) summary of the text")
    highlights: str = Field(
        description="A (comma-separated string) list of the 5-10 most important points of the text, formatted as a bulleted list")
    detailed_summary: str = Field(
        description="An exhaustively thorough and detailed summary of the major points of this text in markdown bulleted outline format, like `* point 1\n* point 2\n* point 3` etc. Do not include conversational aspects such as 'the human greets the ai' and the 'ai responds with a greeting', only include the main contentful components of the text.")
    topic_areas: list[TopicArea] = Relationship(
        back_populates="server_analyses",
        link_model=ServerAnalysisTopicArea,
    )



    def save_as_markdown(self, base_folder: str):
        save_path = Path(base_folder) / self.context_route.safe_context_route
        save_path.mkdir(parents=True, exist_ok=True)

        with open(str(save_path / f"{self.filename}"), 'w', encoding='utf-8') as f:
            f.write(self.full_text)

    created_at: datetime = Field(default_factory=datetime.now)
    @property
    def context_route(self) -> ContextRoute:
        """
        Return a ContextRoute object representing the context of this analysis.
        """
        return ContextRoute(
            server_id=self.server_id,
            server_name=self.server_name,
            category_id=self.category_id,
            category_name=self.category_name,
            channel_id=self.channel_id,
            channel_name=self.channel_name,
        )

    @computed_field
    def title(self) -> str:
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
        topic_areas = ""
        for topic in self.topic_areas:
            topic_areas+=f"{topic.as_string}\n\n"
        return topic_areas

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

    @computed_field
    def full_text_no_base_text(self) -> str:
        return self.full_text.split("## Full Content Text")[0]

    @property
    def full_text(self):
        return f"""
# {self.title}\n\n
> Context Route
> (names): {self.context_route.names}\n\n
> (ids): {self.context_route.ids}\n\n
## Topic Areas\n
{self.topic_areas_string}\n\n
## Tags\n
{self.tags_string}\n\n
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

## Backlinks\n
{self.backlinks}\n\n
__
## Full Content Text\n
{self.base_text}\n\n
__
        """




class UserProfile(BaseSQLModel, table=True):
    """Represents a user's profile with interests and recommendations."""
    user_id: str = Field(foreign_key="user.id")
    broad_summary: str = Field(sa_column=Column(Text),
                               description="An overall summary of the user's interactions, interests, and background. Should include everything we know or can reliably infer about the user.")
    terse_summary: str = Field(
        description="A short, very terse summary of the user's profile, including their interests and background. This should be a single sentence that captures the essence of the user.")
    recommendations: list[str] = Field(default=[], sa_column=Column(JSON),
                                       description="A list of recommended actions, resources, or topics for the user based on the analysis of their interactions. These could be things the user would enjoy, or ways for the to pursue their interests and desired skillsets")

    # Relationships
    user: User = Relationship(back_populates="profile")
    interests: list["TopicArea"] = Relationship(
        back_populates="user_profiles",
        link_model=UserProfileTopicArea,
    )


