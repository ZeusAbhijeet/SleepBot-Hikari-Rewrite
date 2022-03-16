from datetime import datetime
import hikari
import lightbulb
import Utils
import motor.motor_asyncio

from pymongo import MongoClient
from lightbulb import commands, context
from random import randint

coin_plugin = lightbulb.Plugin("Coins")

with open("./Secrets/mongourl") as f:
	MongoURL = f.read().strip()

cluster = motor.motor_asyncio.AsyncIOMotorClient(MongoURL)
db = cluster.bluelearn
coinsdata = db.coins

async def AddToCoinsDatabase(user : hikari.User, coins : int) -> None:
	UserCoinsData = await coinsdata.find_one({"user_ID" : str(user.id)})
	if UserCoinsData:
		CoinBalance = int(UserCoinsData['points']) + coins
		await coinsdata.update_one(
			{'user_ID' : str(user.id)},
			{'$set' : {'points' : CoinBalance}}
		)
	else:
		CoinBalance = coins
		await coinsdata.insert_one(
			{
				'user_ID' : str(user.id),
				'points' : CoinBalance
			}
		)

async def FetchCoinsFromDatabase(user : hikari.User) -> int:
	UserCoinsData = await coinsdata.find_one({"user_ID" : str(user.id)})
	if UserCoinsData:
		TargetCoins = UserCoinsData['points']
	else:
		TargetCoins = 0
		await coinsdata.insert_one(
			{
				'user_ID' : str(user.id),
				'points' : TargetCoins
			}
		)
	return TargetCoins

@coin_plugin.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("user", "The user[s] to give the coins to", type = hikari.User, modifier = commands.OptionModifier.GREEDY, required = True)
@lightbulb.option("amount", "The amount of coins to give", type = int, required = True)
@lightbulb.command("givecoins", "Gives the mentioned user[s] the given amount of coins", hidden = True)
@lightbulb.implements(commands.PrefixCommand)
async def givecoinscmd(ctx : context.Context) -> None:
	target = ctx.options.user
	coins = ctx.options.amount
	memberlist = []

	try:
		for t in target:
			memberlist.append(ctx.get_guild().get_member(t))
	except:
		return await ctx.respond(":warning: One of the user[s] does not seem to exist. Check the arguments passed again")
	for m in memberlist:
		await AddToCoinsDatabase(m, coins)
		await ctx.respond(f"Successfully gave {coins} coins to {m.mention}!")
	
@coin_plugin.command
@lightbulb.option("user", "The user to check the coin balance of.", type = hikari.User, required = False)
@lightbulb.command(name = "coins", description = "Check your coins balance.", aliases = ['points', 'coin', 'point', 'blc'], auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def coinscmd(ctx : context.Context) -> None:
	target = ctx.options.user if ctx.options.user is not None else ctx.user
	target = ctx.get_guild().get_member(target)

	coins = await FetchCoinsFromDatabase(target)

	await ctx.respond(embed = hikari.Embed(
		title = f"User {target.display_name}'s Coin balance",
		description = f"{target.mention} has {coins} coins in their balance.",
		colour = randint(0, 0xffffff),
		timestamp = datetime.now().astimezone()
	))

@coin_plugin.command
@lightbulb.command(name = "BL Coins Balance", description = "Check your coins balance.", auto_defer = True)
@lightbulb.implements(commands.UserCommand)
async def coinscmd(ctx : context.Context) -> None:
	target = ctx.get_guild().get_member(ctx.options.target)

	coins = await FetchCoinsFromDatabase(target)

	await ctx.respond(embed = hikari.Embed(
		title = f"User {target.display_name}'s Coin balance",
		description = f"{target.mention} has {coins} coins in their balance.",
		colour = randint(0, 0xffffff),
		timestamp = datetime.now().astimezone()
	))

@coin_plugin.command
@lightbulb.command(name = "coins_leaderboard", description = "Show the top 100 members with highest number of coins", aliases = ['coinslb', 'coinlb', 'cointop', 'coinstop'], auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def coinslbcmd(ctx : context.Context) -> None:
	total_coins = coinsdata.find({}).sort("points", -1).limit(115)
	top_20 = 1
	"""
	embed = hikari.Embed(
		title= "Coins Leaderboard",
		colour = randint(0, 0xffffff),
		timestamp = datetime.now().astimezone()
	)
	"""
	rank_pag = lightbulb.utils.EmbedPaginator(max_lines = 10)

	@rank_pag.embed_factory()
	def build_embed(page_index, page_content) -> hikari.Embed:
		return hikari.Embed(
			title = "Coins Leaderboard",
			description = f"Here are the top 100 members.\n\n {page_content}",
			colour = 0x76ffa1 
		).set_footer(f"Page {page_index}/10")

	async for user in total_coins:
		try:
			member = ctx.get_guild().get_member(int(user['user_ID']))
		except:
			continue
		if member == None:
			continue
		"""
		embed.add_field(
			name = f"{top_20} : {member.display_name}",
			value = f"{user['points']}",
			inline = True
		)
		"""
		rank_pag.add_line(f"**{top_20}. {member}**\t•\tBLC {user['points']}" if ctx.author.id != member.id else f"**-> {top_20}. {member} <-**\t•\tBLC {user['points']}")

		top_20 += 1
		if top_20 > 100:
			break
	
	navigator = lightbulb.utils.ButtonNavigator(rank_pag.build_pages(), timeout = 60)
	await navigator.run(ctx)

	#await ctx.respond(embed = embed)

@coin_plugin.listener(event = hikari.MessageCreateEvent)
async def on_message_create(event : hikari.MessageCreateEvent) -> None:
	if not await Utils.is_point_chnl(event.channel_id):
		return
	if event.author.is_bot:
		return
	if randint(0, 175) == 0:
		emoji = '🎖'
		await event.app.rest.add_reaction(event.channel_id, event.message_id, emoji)
		await AddToCoinsDatabase(event.author, 10)

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(coin_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(coin_plugin)
