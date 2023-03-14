from typing import List, Optional
import datetime

import discord
from discord import ui
from discord.ext import commands
from discord import app_commands

from sqlalchemy import exc
from sqlalchemy import select
from sqlalchemy import delete

import models
from bot import Bot
from bot import Message
from bot import Context
from bot import Interaction


class TagCreator(ui.Modal, title="New Tag"):
    def __init__(self, bot: Bot, tagName: str):
        super().__init__()

        self.bot = bot

        self.tagname.default = tagName

    tagname = ui.TextInput(
        label="Tag name", style=discord.TextStyle.short, max_length=100
    )

    tagcontent = ui.TextInput(
        label="Tag content", style=discord.TextStyle.long, max_length=2000
    )

    async def on_submit(self, interaction: Interaction):
        try:
            async with self.bot.db_session.begin() as session:
                newTag = models.Tag()
                newTag.name = str(self.tagname)
                newTag.content = str(self.tagcontent)
                newTag.server_id = interaction.guild_id  # type: ignore
                newTag.author_id = interaction.user.id

                session.add(newTag)
        except exc.IntegrityError:
            return await interaction.response.send_message(
                "An integrity error occured whilst writing to the database. Does the tag already exist?",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Your tag was created successfully.", ephemeral=True
            )

class TagEditor(ui.Modal, title="Edit Tag"):
    tag_name: str
    def __init__(self, bot: Bot, tag_name: str, current_content: str):
        super().__init__()

        self.bot = bot

        self.tag_name = tag_name

        self.tagcontent.default = current_content

    tagcontent = ui.TextInput(
        label="Tag content", style=discord.TextStyle.long, max_length=2000
    )

    async def on_submit(self, interaction: Interaction):
        try:
            async with self.bot.db_session.begin() as session:
                tag = await session.get(models.Tag, (interaction.guild_id, self.tag_name))
                
                if tag:
                    tag.content = self.tagcontent.value
                else:
                    await session.rollback()
                    return await interaction.response.send_message(
                        "The tag you were editing could not be found. Was it deleted?",
                        ephemeral=True,
                    )
        except exc.IntegrityError:
            return await interaction.response.send_message(
                "An integrity error occured whilst writing to the database. Does the tag already exist?",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Your tag was created successfully.", ephemeral=True
            )


class AutoresponseCreator(ui.Modal, title="New Autoresponse"):
    def __init__(self, bot: Bot, tagName: str):
        super().__init__()

        self.bot = bot

        self.tagname.default = tagName

    tagname = ui.TextInput(
        label="Tag name", style=discord.TextStyle.short, max_length=100
    )

    tagcontent = ui.TextInput(
        label="Tag content", style=discord.TextStyle.long, max_length=2000
    )

    async def on_submit(self, interaction: Interaction):
        try:
            async with self.bot.db_session.begin() as session:
                newTag = models.Tag()
                newTag.name = str(self.tagname)
                newTag.content = str(self.tagcontent)
                newTag.server_id = interaction.guild_id  # type: ignore
                newTag.author_id = interaction.user.id

                session.add(newTag)
        except exc.IntegrityError:
            return await interaction.response.send_message(
                "An integrity error occured whilst writing to the database. Does the tag already exist?",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Your tag was created successfully.", ephemeral=True
            )


async def tag_autocomplete(
    interaction: Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    if not interaction.guild:
        return []

    async with interaction.client.db_session.begin() as session:
        tag_query = (
            select(models.Tag)
            .where(models.Tag.server_id == interaction.guild.id)
            .limit(25)
            .with_hint(models.Tag, "USE INDEX col1_index")
        )
        tags = (await session.execute(tag_query)).scalars().all()

    return [
        app_commands.Choice(name=tag.name, value=tag.name)
        for tag in tags
        if current.lower() in tag.name.lower()
    ]


class Tags(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.describe(tag="The tag to retrieve")
    @commands.guild_only()
    @commands.hybrid_command(name="tag", description="Get a tag!")
    async def tag(self, ctx: Context, tag: str, target: Optional[discord.User] = None):
        if not ctx.guild:
            return

        async with ctx.bot.db_session.begin() as session:
            #tag_query = (
            #    select(models.Tag)
            #    .where(models.Tag.server_id == ctx.guild.id)
            #    .where(models.Tag.name == tag)
            #    .limit(1)
            #    .with_hint(models.Tag, "USE INDEX col1_index")
            #)
            #retrieved_tag = (await session.execute(tag_query)).scalar_one_or_none()
            retrieved_tag = await session.get(models.Tag, (ctx.guild.id, tag))

        if retrieved_tag is None:
            return await ctx.reply("This tag does not exist.", ephemeral=True)

        allowed_mentions = discord.AllowedMentions.none()
        allowed_mentions.replied_user = True

        if target:
            allowed_mentions.users = [target]

        embed = discord.Embed(colour=self.bot.config["EmbedColour"])
        embed.title = retrieved_tag.name

        """tag_author = self.bot.get_user(retrieved_tag.author_id) or await self.bot.fetch_user(retrieved_tag.author_id)

        embed.set_author(
            name="Tag author: " + tag_author.display_name if tag_author else str(retrieved_tag.author_id),
            icon_url=tag_author.display_avatar.url if tag_author else None,
            #url=f"discord://-/users/{retrieved_tag.author_id}"
        )"""

        embed.description = retrieved_tag.content

        embed.set_footer(
            text=f"Requested by {ctx.author} | Last updated",
            icon_url=ctx.author.display_avatar.url
        )

        embed.timestamp = retrieved_tag.time_updated

        return await ctx.reply(
            target.mention,
            embed=embed,
            allowed_mentions=allowed_mentions,
            mention_author=False
        ) if target else await ctx.reply(
            embed=embed,
            allowed_mentions=allowed_mentions
        )

    @tag.autocomplete("tag")  # type: ignore
    async def tagcmd_autocomplete(self, interaction: Interaction, current: str):
        return await tag_autocomplete(interaction, current)

    @app_commands.describe(tag="The tag to create")
    @commands.guild_only()
    @commands.hybrid_command(
        name="tag-create",
        description="Create a tag!",
        default_permissions=discord.Permissions.advanced(),
    )
    async def tag_create(self, ctx: Context, tag: str):
        if not ctx.guild:
            return

        if ctx.interaction is None:
            return await ctx.reply("This command must be run as a slash command.")

        async with ctx.bot.db_session.begin() as session:
            tag_query = (
                select(models.Tag)
                .where(models.Tag.server_id == ctx.guild.id)
                .where(models.Tag.name == tag)
                .limit(1)
                .with_hint(models.Tag, "USE INDEX col1_index")
            )
            retrieved_tag = (await session.execute(tag_query)).scalar_one_or_none()

        if retrieved_tag is not None:
            return await ctx.reply("This tag already exists.", ephemeral=True)

        return await ctx.interaction.response.send_modal(TagCreator(self.bot, tag))

    @app_commands.describe(tag="The tag to create")
    @commands.guild_only()
    @commands.hybrid_command(
        name="tag-delete",
        description="Delete a tag!",
        default_permissions=discord.Permissions.advanced(),
    )
    async def tag_delete(self, ctx: Context, tag: str):
        if not ctx.guild:
            return

        async with ctx.bot.db_session.begin() as session:
            tag_query = (
                delete(models.Tag)
                .where(models.Tag.server_id == ctx.guild.id)
                .where(models.Tag.name == tag)
            )
            result = await session.execute(tag_query)

        if result.rowcount == 0:  # type: ignore
            return await ctx.reply("No tag was found.", ephemeral=True)
        else:
            return await ctx.reply("Tag deleted sucessfully.")

    @tag_delete.autocomplete("tag")  # type: ignore
    async def tagdelcmd_autocomplete(self, interaction: Interaction, current: str):
        return await tag_autocomplete(interaction, current)
    
    @app_commands.describe(tag="The tag to create")
    @commands.guild_only()
    @commands.hybrid_command(
        name="autoresponse-create",
        description="Make the bot annoying! /s",
        default_permissions=discord.Permissions.advanced(),
    )
    async def autoresponse_create(self, ctx: Context, tagname: str):
        pass

        
    @commands.Cog.listener(name="on_message")
    async def autorespond(self, message: Message):
        if not message.guild:
            return
        async with self.bot.db_session.begin() as session:
            autoresponse_query = (
                select(models.Autoresponse)
                .where(models.Autoresponse.server_id == message.guild.id)
                .with_hint(models.Autoresponse, "USE INDEX col1_index")
            )
            autoresponses = (await session.execute(autoresponse_query)).scalars().all()

            for autoresponse in autoresponses:
                if autoresponse.phrase in message.content:
                    await session.refresh(autoresponse, ("tag",))

                    if autoresponse.tag:
                        return await message.reply(content=autoresponse.tag.content)


async def setup(bot: Bot):
    await bot.add_cog(Tags(bot))
