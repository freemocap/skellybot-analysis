from pydantic import computed_field

from skellybot_analysis.data_models.context_route_model import ContextRoute
from skellybot_analysis.data_models.server_models import DataframeModel, CategoryId
from skellybot_analysis.utilities.sanitize_filename import sanitize_name


class AiThreadAnalysisModel(DataframeModel):
    server_id: int
    server_name: str
    category_id: CategoryId | None = -1
    category_name: str | None = "none"
    channel_id: int
    channel_name: str
    thread_id: int
    thread_name: str
    jump_url: str # url to the thread in the server
    thread_owner_id: int # the human user who owns the thread (human user with most messages in the thread, b/c no easier way to determine this atm)
    base_text: str
    analysis_prompt: str
    title_slug: str
    extremely_short_summary: str
    very_short_summary: str
    short_summary: str
    highlights: str
    detailed_summary: str
    topic_areas: str

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
    def tags(self) -> list[str]:
        tags = self.topic_areas.split(" -> ")
        split_tags = []
        for tag in tags:
            split_tags.extend(tag.split(','))
        clean_tags = []
        for tag in tags:
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
    @property
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
    {self.topic_areas}\n\n
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
