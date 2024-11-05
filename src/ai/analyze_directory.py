import asyncio
from pathlib import Path
from pprint import pformat
from typing import Type

from src.models.extract_text_data_prompt_model import ExtractedTextData

from pydantic import BaseModel
from src.ai.analyze_text import analyze_text
from src.configure_logging import configure_logging

configure_logging()
import logging

logger = logging.getLogger(__name__)


async def analyze_directory(base_directory: str,
                            output_directory: str,
                            json_schema_model: Type[BaseModel],
                            base_prompt_text: str):
    input_directory_path = Path(base_directory)
    output_directory_path = Path(output_directory)
    output_directory_path.mkdir(parents=True, exist_ok=True)

    if not input_directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {input_directory_path}")
    logger.info(f"Analyzing directory: {input_directory_path}")
    tasks = []

    for file_number, file in enumerate(input_directory_path.rglob('*.md')):
        tasks.append(analyze_markdown_file(base_prompt_text=base_prompt_text,
                                           file_path=file,
                                           input_directory_path=input_directory_path,
                                           json_schema_model=json_schema_model,
                                           output_directory_path=output_directory_path,
                                           ))

    logger.info(f"Starting analysis of {len(tasks)} files in directory: {input_directory_path}")
    await asyncio.gather(*tasks)
    logger.info(f"Analysis complete for directory: {input_directory_path}")


async def analyze_markdown_file(base_prompt_text: str,
                                file_path: Path,
                                input_directory_path: Path,
                                json_schema_model: ExtractedTextData,
                                output_directory_path: Path):
    logger.debug(f"Analyzing file: {file_path}")
    try:
        input_file_text = file_path.read_text(encoding='utf-8')
        file_parent_path = file_path.parent
        output_parent_path = output_directory_path / str(
            file_parent_path.relative_to(input_directory_path / "raw-markdown" / "HMN_Fall24"))
        if "bot-playground" in str(file_parent_path):
            logger.warning(f"Skipping file in bot-playground: {file_path}")
            return
        output_parent_path.mkdir(parents=True, exist_ok=True)
        try:
            constructed_pydantic_model, embedding_response = await analyze_text(input_text=input_file_text,
                                                                                json_schema_model=json_schema_model,
                                                                                base_prompt_text=base_prompt_text)
        except Exception as e:
            logger.error(f"Error analyzing file: {file_path}")
            logger.error(e)
            return
        if not constructed_pydantic_model:
            logger.warning(f"No Pydantic model constructed for file: {file_path}")
            return
        logger.info(f"Constructed Pydantic model:\n\n{constructed_pydantic_model}")

        output_markdown_string = str(constructed_pydantic_model)
        full_output_string = output_markdown_string + "\n\n___\n\n___\n\nOriginal text:\n\n" + input_file_text + "\n\n___\n\n___\n\nEmbedding response:\n\n" + pformat(
            embedding_response, indent=4)
        output_file_name = constructed_pydantic_model.filename
        save_path = output_parent_path / output_file_name

        save_path.write_text(full_output_string, encoding='utf-8')
        logger.info(f"Saved Pydantic model as JSON: {str(save_path)}")
    except Exception as e:
        logger.error(f"Error analyzing file: {file_path}")
        logger.error(e)
        raise


if __name__ == "__main__":
    from src.utilities.load_env_variables import OUTPUT_DIRECTORY

    in_server_name = "HMN_Fall24"
    classbot_prompt_file_name = f"{in_server_name}-prompt.txt"
    classbot_prompt_file_path = str(Path(OUTPUT_DIRECTORY) / classbot_prompt_file_name)

    with open(classbot_prompt_file_path, 'r', encoding='utf-8') as f:
        classbot_prompt = f.read()

    checkpoint_name = "2024-10-28T12-26"
    outer_base_directory = Path(OUTPUT_DIRECTORY) / checkpoint_name
    if not outer_base_directory.exists():
        raise FileNotFoundError(f"Directory not found: {outer_base_directory}")
    asyncio.run(analyze_directory(base_directory=str(outer_base_directory),
                                  output_directory=str(Path(
                                      OUTPUT_DIRECTORY) / f"{in_server_name}-checkpoint-{checkpoint_name}-ai-processed"),
                                  json_schema_model=ExtractedTextData,
                                  base_prompt_text=classbot_prompt))

    logger.info(f"Analysis complete for directory: {OUTPUT_DIRECTORY}")

    print("Done!")
