# python_discord_giveaway_bot
A discord bot to facilitate giveaways.

WARNING - this bot was broken with a Discord API update, and does not work.

This bot was sadly created before I realised that breaking python scripts up over multiple files was a good idea. I'm in the process of updating the bot to allow for Discord API changes and to include slash commands, so I may fix this as a part of that.

The SQL is implemented strangely as a result of the continual issues I had with the python sql.connector library disconnecting while the bot was running. My eventual solution was to just reconnect to the database every time I wanted to run a command. I am still not sure if this was the best solution.
