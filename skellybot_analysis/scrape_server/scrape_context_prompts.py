import logging

import discord

from skellybot_analysis.models.dataframe_handler import DataframeHandler
from skellybot_analysis.models.server_models import ContextPromptModel
from skellybot_analysis.scrape_server.scrape_thread import get_channel_threads
from skellybot_analysis.scrape_server.scrape_utils import get_prompts_from_channel

logger = logging.getLogger(__name__)


async def grab_context_prompts(df_handler: DataframeHandler,
                               target_server: discord.Guild,
                               text_channels: list[discord.TextChannel]) -> None:
    server_prompt = await get_server_prompt(df_handler=df_handler,
                                            target_server=target_server,
                                            text_channels=text_channels)
    category_prompt_messages = await get_category_prompts(server_prompt=server_prompt,
                                                          df_handler=df_handler,
                                                          target_server=target_server,
                                                          text_channels=text_channels)
    _ = await get_channel_prompts(df_handler=df_handler,
                                  text_channels=text_channels,
                                  server_prompt=server_prompt,
                                  category_prompt_messages=category_prompt_messages)


async def get_channel_prompts(df_handler: DataframeHandler,
                              text_channels: list[discord.TextChannel],
                              server_prompt: str,
                              category_prompt_messages: dict[int, str]) -> dict[int, str]:
    channel_prompts: dict[int, str] = {}
    for channel in text_channels:
        if isinstance(channel, discord.CategoryChannel) or not isinstance(channel, discord.TextChannel):
            continue

        channel_threads = await get_channel_threads(channel=channel)
        if not channel_threads:
            logger.info(f"No chat threads found in: {channel.name} (ID: {channel.id}) - skipping")
            continue
        base_prompt = category_prompt_messages.get(channel.category_id, server_prompt)
        channel_prompts[channel.id] = base_prompt + "\n".join(await get_prompts_from_channel(channel=channel))
        if channel.category:
            context_id = hash((channel.guild.id, channel.category.id, channel.id))
        else:
            context_id = hash((channel.guild.id, channel.id))
        df_handler.store(
            primary_id=context_id,
            entity=ContextPromptModel(context_id=context_id,
                                      server_id=channel.guild.id,
                                      server_name=channel.guild.name,
                                      category_id=channel.id,
                                      category_name=channel.name,
                                      channel_id=channel.id,
                                      channel_name=channel.name,
                                      prompt_text=channel_prompts[channel.id]
                                      ))
        logger.info(f"✅ Added channel system prompt for channel: {channel.name} (ID: {channel.id})")

    return channel_prompts


async def get_category_prompts(server_prompt: str,
                               df_handler: DataframeHandler,
                               target_server: discord.Guild,
                               text_channels: list[discord.TextChannel]) -> dict[int, str]:
    category_prompt_messages: dict[int, str] = {}
    for potential_category in text_channels:
        # discord's "everything is a channel" philosophy is ¯\_(ツ)_/¯
        if isinstance(potential_category, discord.CategoryChannel):
            category_prompt_messages[potential_category.id] = ""

    for channel in text_channels:
        if not channel.category_id or channel.category_id not in category_prompt_messages:
            continue

        # TODO - should match whatever regex we're using in `skellybot` proper
        if "bot" in channel.name or "prompt" in channel.name or "instructions" in channel.name:
            logger.info(f"Extracting category-level prompts for category: {channel.name}")
            category_prompt_messages[channel.category_id] = server_prompt + "\n".join(
                await get_prompts_from_channel(channel=channel))
            context_id = hash((channel.guild.id, channel.category_id))
            df_handler.store(primary_id=context_id,
                          entity=ContextPromptModel(context_id=context_id,
                                                    server_id=target_server.id,
                                                    server_name=target_server.name,
                                                    category_id=channel.category.id if channel.category else None,
                                                    category_name=channel.category.name if channel.category else None,
                                                    prompt_text=category_prompt_messages[channel.category_id]
                                                    ))
            logger.info(
                f"✅ Added category system prompt for category: {channel.category.name} (ID: {channel.category.id})")
    return category_prompt_messages


async def get_server_prompt(df_handler: DataframeHandler,
                            target_server: discord.Guild,
                            text_channels: list[discord.TextChannel]) -> str:
    server_prompt = ""
    context_id = hash(target_server.id)
    for channel in text_channels:
        if channel.category:
            continue
        if "bot" in channel.name or "prompt" in channel.name or "instructions" in channel.name:
            logger.info(f"Extracting server-level prompts from channel: {channel.name}")
            server_prompt += "\n".join(await get_prompts_from_channel(channel=channel))
    if server_prompt:
        df_handler.store(primary_id=context_id,
                      entity=ContextPromptModel(context_id=context_id,
                                                server_id=target_server.id,
                                                server_name=target_server.name,
                                                prompt_text=server_prompt
                                                )
                      )
        logger.info(f"✅ Added server-level system prompt")
    return server_prompt
