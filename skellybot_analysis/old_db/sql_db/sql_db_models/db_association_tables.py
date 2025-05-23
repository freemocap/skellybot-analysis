from sqlmodel import SQLModel, Field


class UserProfileTopicArea(SQLModel, table=True):
    userprofile_id: str = Field(foreign_key="userprofile.id", primary_key=True)
    topicarea_id: str = Field(foreign_key="topicarea.id", primary_key=True)


class ServerAnalysisTopicArea(SQLModel, table=True):
    serverobjectaianalysis_id: str = Field(foreign_key="serverobjectaianalysis.id", primary_key=True)
    topicarea_id: str = Field(foreign_key="topicarea.id", primary_key=True)

class ServerAnalysisContextPrompt(SQLModel, table=True):
    serverobjectaianalysis_id: str = Field(foreign_key="serverobjectaianalysis.id", primary_key=True)
    contextsystemprompt_id: str = Field(foreign_key="contextsystemprompt.id", primary_key=True)

class ThreadContextPrompt(SQLModel, table=True):
    thread_id: str = Field(foreign_key="thread.id", primary_key=True)
    contextsystemprompt_id: str = Field(foreign_key="contextsystemprompt.id", primary_key=True)

class UserServerAnalysis(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    serverobjectaianalysis_id: str = Field(foreign_key="serverobjectaianalysis.id", primary_key=True)