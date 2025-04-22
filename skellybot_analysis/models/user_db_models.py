from typing import Optional

from sqlalchemy import Column, JSON, Text
from sqlmodel import Field, Relationship

from skellybot_analysis.models.ai_analysis_db import TopicArea
from skellybot_analysis.models.base_sql_model import BaseSQLModel
from skellybot_analysis.models.db_association_tables import UserProfileTopicArea
from skellybot_analysis.models.server_db_models import  UserThread, Message, Thread


class User(BaseSQLModel, table=True):
    """Represents a  user."""
    is_bot: bool

    # Relationships
    messages: list[Message] = Relationship(back_populates="author")
    threads: list[Thread] = Relationship(
        back_populates="users",
        link_model=UserThread
    )
    profile: Optional["UserProfile"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )


class UserProfile(BaseSQLModel, table=True):
    """Represents a user's profile with interests and recommendations."""
    user_id: int = Field(foreign_key="user.id")
    broad_summary: str = Field(sa_column=Column(Text),
                               description="An overall summary of the user's interactions, interests, and background. Should include everything we know or can reliably infer about the user.")
    terse_summary: str = Field(
        description="A short, very terse summary of the user's profile, including their interests and background. This should be a single sentence that captures the essence of the user.")
    recommendations: list[str] = Field(default=[], sa_column=Column(JSON),
                                       description="A list of recommended actions, resources, or topics for the user based on the analysis of their interactions. These could be things the user would enjoy, or ways for the to pursue their interests and desired skillsets")

    # Relationships
    user: User = Relationship(back_populates="profile")
    interests: list[TopicArea] = Relationship(
        back_populates="user_profiles",
        link_model=UserProfileTopicArea,
    )



