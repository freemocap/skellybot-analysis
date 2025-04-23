from sqlmodel import SQLModel, Field


class UserProfileTopicArea(SQLModel, table=True):
    userprofile_id: int = Field(foreign_key="userprofile.id", primary_key=True)
    topicarea_id: str = Field(foreign_key="topicarea.id", primary_key=True)


class ServerAnalysisTopicArea(SQLModel, table=True):
    serverobjectaianalysis_context_route: str = Field(foreign_key="serverobjectaianalysis.id", primary_key=True)
    topicarea_id: str = Field(foreign_key="topicarea.id", primary_key=True)
