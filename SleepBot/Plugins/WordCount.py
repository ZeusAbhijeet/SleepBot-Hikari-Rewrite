import hikari
import lightbulb
import random
import sqlite3

from lightbulb.command_handler import Bot

class WordCount(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@lightbulb.listener(hikari.MessageCreateEvent)
	async def on_message_create(self, event : hikari.MessageCreateEvent) -> None:
		if event.author_id == 494834222771732481:
			if event.message.content.lower().find('drop') != -1:
				conn = sqlite3.connect('Database.db')
				c = conn.cursor()
				c.execute("CREATE TABLE IF NOT EXISTS drop_count (db_ID INTEGER PRIMARY KEY AUTOINCREMENT, count INTEGER NOT NULL);")
				drop_count = c.execute("SELECT count FROM drop_count;").fetchone()
				if not drop_count:
					drop_count = 1
					c.execute(f"INSERT INTO drop_count VALUES (NULL, {drop_count});")
				else:
					drop_count = drop_count[0]
					drop_count += 1
					c.execute(f"UPDATE drop_count SET count = {drop_count} WHERE db_ID = 1;")
				conn.commit()
				conn.close()
				await self.bot.rest.create_message(
					channel = event.channel_id,
					embed = hikari.Embed(
						title = f"Viraj's Drop Count",
						description = f"{event.author.mention} has mentioned dropping {drop_count} times.",
						colour = random.randint(0, 0xffffff)
					).set_footer(
						text = "smh bro just stop"
					)
				)

def load(bot : Bot):
	bot.add_plugin(WordCount(bot))
	print("Plugin WordCount has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("WordCount")
