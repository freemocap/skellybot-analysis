import uuid

from sqlalchemy import Column, Text
from sqlmodel import SQLModel, Field, Relationship

from skellybot_analysis.models.db_join_tables import UserProfileTopicArea, ServerAnalysisTopicArea
from skellybot_analysis.models.user_db_models import UserProfile
from skellybot_analysis.models.ai_analysis_db import ServerObjectAiAnalysis


class TopicArea(SQLModel, table=True):
    """Represents a topic area of interest."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(
        description="The name of this topic area. This should be a single word or hyphenated phrase that describes the topic area. For example, 'machine-learning', 'python', 'oculomotor-control', 'neural-networks', 'computer-vision', etc. Do not include conversational aspects such as 'greetings', 'farewells', 'thanks', etc.")
    category: str = Field(
        description="The general category or field of interest (e.g., 'science', 'technology', 'arts', 'activities', 'health', etc).")
    subject: str = Field(
        description="A more specific subject or area of interest within the category (e.g., 'biology', 'computer science', 'music', 'sports', 'medicine', etc).")
    topic: str = Field(
        description="More specific topic or subfield within the category (e.g., 'neuroscience', 'machine learning',  'classical music', 'basketball', 'cardiology', etc).")
    subtopic: str = Field(
        description="An even more specific subtopic or area of interest within the topic (e.g., 'oculomotor-control', 'neural-networks', 'Baroque music', 'NBA', 'heart surgery', etc).")
    niche: str = Field(
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

    @property
    def as_string(self):
        """
        Convert the TopicArea instance to a string representation.
        """
        return f"{self.name} -> {self.category} -> {self.subject} -> {self.topic} -> {self.subtopic} -> {self.niche}"
