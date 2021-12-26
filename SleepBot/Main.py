from bot import bot
import os

if __name__ == "__main__":
	if os.name != "nt":
		import uvloop

		uvloop.install()
	
	bot.run()
