from pydantic import BaseModel, computed_field, Field

from skellybot_analysis.models.context_route_model import ContextRoute
from skellybot_analysis.models.prompt_models import TopicAreaPromptModel
from skellybot_analysis.models.server_models import DataframeModel, CategoryId
from skellybot_analysis.utilities.sanitize_filename import sanitize_name


class TopicAreaModel(BaseModel):
    name: str
    category: str
    subject: str
    topic: str
    subtopic: str
    niche: str
    description: str

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

class AiThreadAnalysisModel(DataframeModel):
    server_id: int
    server_name: str
    category_id: CategoryId | None = -1
    category_name: str | None = "none"
    channel_id: int
    channel_name: str
    thread_id: int
    thread_name: str
    base_text: str
    analysis_prompt: str
    title_slug: str
    extremely_short_summary: str
    very_short_summary: str
    short_summary: str
    highlights: str
    detailed_summary: str
    topic_areas: list[TopicAreaModel] = Field(default_factory=list)

    @classmethod
    def df_filename(cls) -> str:
        return "ai_thread_analyses.csv"

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
            topic_areas += f"{topic.as_string}\n\n"
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
    def context_route(self):
        return ContextRoute(
            server_id=self.server_id,
            server_name=self.server_name,
            category_id=self.category_id,
            category_name=self.category_name,
            channel_id=self.channel_id,
            channel_name=self.channel_name,
        )
    @property
    def full_text(self):
        return f"""
    # {self.title}\n\n
    > Context Route
    > {self.context_route.as_formatted_text}\n\n
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
