import json
import logging
from pprint import pprint
from typing import List, Dict

from pydantic import BaseModel, Field

from src.ai.openai_constants import OPENAI_CLIENT
from src.models.server_data_model import ServerData

TAG_CONDENSOR_TASK_DESCRIPTION = (
    f"\n You are an currently analyzing server data extracted from student conversations in "
    f"the course discord server. Your task is to condense the #tags extracted from the first "
    f"round of AI analysis, and condensing them down into a smaller list of more general #tags "
    f"You should provide your response in the form of a JSON mapping of the more generalized "
    f"#tags you will come up with to the original, more specific #tag-values \n Take the "
    f"provided list of tags and produce a condensed list of tags that are a more concise way"
    f" to cover the topics currently described by the original tag list. The mapping should be a JSON formatted "
    f"dictionary key/value pair, where the pair is the extracted condensed tag covering a "
    f"more generalized topic and the values are a list of the more specific tags from the "
    f"original list that are covered by the condensed tag. In short, this represents a one "
    f"layer heirarchy of tags. For example, we might use a condensed tag of "
    f"'#anterior-cruciate-ligament to cover the tags '#acl-repair', '#acl-tear', "
    f"'#acl-surgery', etc. All tags should always be in #lower-kabob-case.")

logger = logging.getLogger(__name__)


from typing import List

from pydantic import BaseModel, Field
from src.utilities.sanitize_filename import sanitize_name


class TagMappingModel(BaseModel):
    class TagMapping(BaseModel):
        condensed_tag: str = Field(description="The condensed tag that covers a more general topic")
        original_tags: List[str] = Field(description="A list of the more specific tags that are covered by the condensed tag")

    tag_condensor_mappings: List[TagMapping] = Field(description="A list of the mappings from the original tags to the condensed tags")


async def run_second_round_ai_analysis(server_data: ServerData):
    system_prompt_og = server_data.server_system_prompt
    system_prompt = system_prompt_og.split("CLASS BOT SERVER INSTRUCTIONS")[0]

    system_prompt += f"\n\n{TAG_CONDENSOR_TASK_DESCRIPTION}"

    original_tags = []
    for thing in server_data.get_all_things():
        if hasattr(thing, "ai_analysis") and hasattr(thing.ai_analysis, "tags_list"):
            original_tags.extend(thing.ai_analysis.tags_list)

    user_input_prompt = f"\n\n The original (uncondensed) tags are: \n \n {original_tags} \n\n This list contains {len(original_tags)} so the condensed list should be about {len(original_tags) // 2} tags long."

    response = await OPENAI_CLIENT.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_input_prompt
            }
        ],
        response_format=TagMappingModel
    )
    output = TagMappingModel(**json.loads(response.choices[0].message.content))

    pprint(output.model_dump())
    return output


if __name__ == "__main__":
    from src.utilities.get_most_recent_server_data import get_server_data
    import asyncio

    server_data, server_data_json_path = get_server_data()

    asyncio.run(run_second_round_ai_analysis(server_data))
    print("Done!")
