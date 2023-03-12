from typing import List
import discord
from discord.ext import commands
from discord import app_commands

from sqlalchemy import select
from sqlalchemy import delete

import models
from bot import Bot
from bot import Message
from bot import Context
from bot import Interaction

async def tag_autocomplete(
    interaction: Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:

    if not interaction.guild:
        return []

    async with interaction.client.db_session.begin() as session:
        tag_query = select(models.Tag).where(models.Tag.server_id == interaction.guild.id).limit(25).with_hint(models.Tag, 'USE INDEX col1_index')
        tags = (await session.execute(tag_query)).scalars().all()

    return [
        app_commands.Choice(name=tag.name, value=tag.name)
        for tag in tags if current.lower() in tag.name.lower()
    ]

class Tags(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.describe(tag='The tag to retrieve')
    @commands.guild_only()
    @commands.hybrid_command(name="tag", description="Get a tag!")
    async def tag(self, ctx: Context, tag: str):
        if not ctx.guild:
            return

        async with ctx.bot.db_session.begin() as session:
            tag_query = select(models.Tag).where(models.Tag.server_id == ctx.guild.id).limit(1).with_hint(models.Tag, 'USE INDEX col1_index')
            retrieved_tag = (await session.execute(tag_query)).scalar_one_or_none()

        if retrieved_tag is None:
            return await ctx.reply("This tag does not exist.", ephemeral=True)

        return await ctx.reply(retrieved_tag.content)

    @tag.autocomplete('tag') # type: ignore
    async def tagcmd_autocomplete(self, interaction: Interaction, current: str):
        return await tag_autocomplete(interaction, current)
        

    @app_commands.describe(tag='The tag to create')
    @commands.guild_only()
    @commands.hybrid_command(
        name="tag-create",
        description="Create a tag!",
        default_permissions=discord.Permissions.advanced()
    )
    async def tag_create(self, ctx: Context, tag: str):
        if not ctx.guild:
            return
        return await ctx.reply("Not implemented yet", ephemeral=True)

    @app_commands.describe(tag='The tag to create')
    @commands.guild_only()
    @commands.hybrid_command(
        name="tag-delete",
        description="Delete a tag!",
        default_permissions=discord.Permissions.advanced()
    )
    async def tag_delete(self, ctx: Context, tag: str):
        if not ctx.guild:
            return
        
        async with ctx.bot.db_session.begin() as session:
            tag_query = delete(models.Tag).where(models.Tag.server_id == ctx.guild.id)
            result = await session.execute(tag_query)

        if result.rowcount == 0:
            return await ctx.reply("No tag was found.", ephemeral=True)
        else:
            return await ctx.reply("Tag deleted sucessfully.")

    @tag_delete.autocomplete('tag') # type: ignore
    async def tagdelcmd_autocomplete(self, interaction: Interaction, current: str):
        return await tag_autocomplete(interaction, current)

    @commands.Cog.listener(name="on_message")
    async def autorespond(self, message: Message):
        if not message.guild:
            return
        async with self.bot.db_session.begin() as session:
            autoresponse_query = select(models.Autoresponse).where(models.Autoresponse.server_id == message.guild.id).with_hint(models.Autoresponse, 'USE INDEX col1_index')
            autoresponses = (await session.execute(autoresponse_query)).scalars().all()

            for autoresponse in autoresponses:
                if autoresponse.phrase in message.content:
                    await session.refresh(autoresponse, ("tag",))

                    if autoresponse.tag:
                        return await message.reply(content=autoresponse.tag.content)

        
        

async def setup(bot: Bot):
    await bot.add_cog(Tags(bot))