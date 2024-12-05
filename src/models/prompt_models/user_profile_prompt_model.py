from typing import List
from pydantic import BaseModel, Field

class InterestModel(BaseModel):
    category: str = Field(description="The general category or field of interest (e.g., 'science', 'technology', 'arts', 'sports', 'medicine', etc).")
    topics: List[str] = Field(description="A list of specific topics within the category that the user is or maybe interested in.")

class InteractionSummaryModel(BaseModel):
    conversation_id: str = Field(description="A unique identifier for the conversation.")
    main_points: List[str] = Field(description="A list of the main points or topics discussed in this conversation.")
    relevance_score: float = Field(description="A score indicating the relevance of this conversation to the user's interests, between 0 and 1.")

class UserProfilePromptModel(BaseModel):
    user_id: str = Field(description="A unique identifier for the user.")
    short_bio: str = Field(description="A short biography of the user, including relevant background information, if known. If this is not possible to determine from the provided information, simply say 'No information available'.")
    interests: List[InterestModel] = Field(description="A list of the user's interests, categorized and detailed by specific topics, if known or can be inferred. If this is not possible to determine from the provided information, simply say 'No information available'.")
    interaction_summaries: List[InteractionSummaryModel] = Field(description="A list of summaries for each interaction with the AI chatbot.")
    overall_summary: str = Field(description="An overall summary of the user's interactions, interests, and background.")
    recommendations: List[str] = Field(description="A list of recommended actions, resources, or topics for the user based on the analysis of their interactions.")
    tags: str = Field(
        description="A list of tags that describe the user's interests, formatted as comma separated #lower-kabob-case. These should be like topic tags that can be used to categorize the text within a larger collection of texts. Ignore conversational aspects (such as '#greetings', '#farewells', '#thanks', etc.).  These should almost always be single word, unless the tag is a multi-word phrase that is commonly used as a single tag, in which case it should be hyphenated. For example, '#machine-learning, #python, #oculomotor-control,#neural-networks, #computer-vision', but NEVER things like '#computer-vision-conversation', '#computer-vision-questions', etc.")

    @property
    def tags_list(self) -> List[str]:
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

    def to_string(self) -> str:
        text = f"## Student ID: {self.user_id}\n\n"
        text += f"### Short Bio\n\n{self.short_bio}\n\n"
        text += "### Interests\n\n"
        for interest in self.interests:
            text += f"- {interest.category}: {', '.join(interest.topics)}\n"
        text += "\n### Interaction Summaries\n\n"
        for summary in self.interaction_summaries:
            text += f"- Conversation ID: {summary.conversation_id}\n  Main Points: {', '.join(summary.main_points)}\n  Relevance Score: {summary.relevance_score}\n\n"
        text += f"### Overall Summary\n\n{self.overall_summary}\n\n"
        text += "### Recommendations\n\n"
        for recommendation in self.recommendations:
            text += f"- {recommendation}\n"
        text += "\n### Tags\n\n"
        text += "\n- ".join(self.tags_list)

        return text
