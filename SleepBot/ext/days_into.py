import hikari
import lightbulb
from datetime import *
from time import *

into_2023_channel = await ctx.bot.rest.fetch_channel('1058945983679053853')
day_31_months = (1, 3, 5, 7, 8, 10, 12)
day_30_months = (4, 6, 9, 11)
old_day = 0
into_2023 = 0

while True:
    date = date.today()
    day = int(date.day)
    month = int(date.month)
    year = int(date.year)
    if day != old_day:
        for mon in range(month-1):
            mon += 1
            if mon in day_31_months:
                into_2023 += 31
            elif mon in day_30_months:
                into_2023 += 30
            else:
                if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                    into_2023 += 29
                else:
                    into_2023 += 28
        
    into_2023 += day
    text = (f"{into_2023} days passed in year {year}")
    await into_2023_channel.send(text)

    old_day = day
    into_2023 = 0
    sleep(3600)