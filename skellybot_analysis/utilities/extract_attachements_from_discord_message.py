import aiohttp
import discord


async def extract_attachments_from_discord_message(attachments: list[discord.Attachment] | None) -> list[str]:
    """
    Extract the text from a discord attachment.
    """
    attachment_texts = []
    if not attachments:
        return attachment_texts

    for attachment in attachments:
        if attachment.content_type and 'text' in attachment.content_type:
            attachment_string = f"START [{attachment.filename}]({attachment.url})"
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        try:
                            attachment_string += await resp.text()
                        except UnicodeDecodeError:
                            attachment_string += await resp.text(errors='replace')
            attachment_string += f" END [{attachment.filename}]({attachment.url})"
            attachment_texts.append(attachment_string)
    return attachment_texts
