from pydantic import BaseModel, Field, computed_field


class TopicAreaPromptModel(BaseModel):
    name : str = Field(
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
    description: str = Field(
        description="A brief description of this interest, including any relevant background information, key concepts, notable figures, recent developments, and related topics. This should be a concise summary that provides context and depth to the interest")

    @computed_field
    def id(self) -> int:
        """
        Generate a unique ID for the TopicArea instance based on its attributes.
        """
        return hash(self.as_string)

    @computed_field
    def as_string(self) -> str:
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
        description=" 3-6 of most important points of the text, formatted as a newline separated string list")
    detailed_summary: str = Field(
        description="An exhaustively thorough and detailed summary of the major points of this text in markdown bulleted outline format, like `* point 1\n* point 2\n* point 3` etc. Do not include conversational aspects such as 'the human greets the ai' and the 'ai responds with a greeting', only include the main contentful components of the text.")
    topic_areas: list[TopicAreaPromptModel] = Field(
        description="A list of topic areas that describe the content of the text. These will be used to categorize the text within a larger collection of texts. Ignore conversational aspects (such as 'greetings', 'farewells', 'thanks', etc.).  These should almost always be single word, unless the tag is a multi-word phrase that is commonly used as a single tag, in which case it should be hyphenated. For example, 'machine-learning, python, oculomotor-control,neural-networks, computer-vision', but NEVER things like 'computer-vision-conversation', 'computer-vision-questions', etc.")

    @property
    def topic_areas_as_string(self) -> str:
        """
        Convert the list of topic areas to a string representation.
        """
        topic_area_strings = ""
        for topic_area in self.topic_areas:
            topic_area_strings += topic_area.as_string + " \n,"
        return topic_area_strings.strip(", \n")  # Remove trailing comma and newline

class UserProfilePromptModel(BaseModel):
    """Represents a user's profile with interests and recommendations."""
    broad_summary: str = Field(description="An overall summary of the user's interactions, interests, and background. Should include everything we know or can reliably infer about the user. Formatted as a markdown bulleted outline, like `* point 1\n* point 2\n* point 3` etc. DO NOT include conversational aspects such as 'the human greets the ai' and the 'ai responds with a greeting', only include the main contentful components of the text.")
    terse_summary: str = Field(
        description="A short, very terse summary of the user's profile, including their interests and background. This should be a single sentence that captures the essence of the user.")
    interests: list[TopicAreaPromptModel] = Field(description="A list of the user's interests, based on the available information")
    recommendations: list[str] = Field(description="A list of recommended actions, resources, or topics for the user based on the analysis of their interactions. These could be things the user would enjoy, or ways for them to pursue their interests and desired skillsets")




