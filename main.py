import discord, os, random, mysql.connector, re, asyncio, random
from discord import app_commands
from discord.utils import get
from dotenv import load_dotenv
from datetime import datetime

#load in the password from an external file
load_dotenv()

#settings up intentions because discord hates bot devs
intents = discord.Intents.default()

intents.reactions = True
intents.members = True
password = ""

#defining and setting up bot
client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

#logging in to bot and database
@client.event
async def on_ready():
    await tree.sync()
    print('We have logged in as {0.user}'.format(client))
    global password
    password = input("Please enter the database password: ")
    await checkLoop()

#check if a user running a command has admin privileges
def is_admin():
    def predicate(interaction : discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            return True
    return app_commands.check(predicate)


#create giveaway command (requires admin permissions on server)
@tree.command(name='create_giveaway', description = "Create a giveaway.")
@is_admin()
async def createGiveaway(ctx, g_duration: str, g_channel: str, g_prize: str, g_winners: int):
    await ctx.response.send_message("Giveaway created.")
    print(gChannel)
    gChannel = gChannel[2:len(gChannel)-1]
    print(gChannel)
    print(gDuration)
    message="**There is a giveaway starting for**: "+gPrize+"!\n\nThis will be ending at "+gDuration+" GMT. React with <:Diamond:973968029803241482> to this message to enter the giveaway."
    giveawayMessage = await ctx.guild.get_channel(int(gChannel)).send(message)
    await giveawayMessage.add_reaction(client.get_emoji(973968029803241482))
    sql = "INSERT INTO GiveAways (ServerID, EndTime, NumberOfWinners, prize, finished, MessageID, ChannelID) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (str(ctx.guild.id), gDuration, gWinners, gPrize, False, giveawayMessage.id, gChannel)
    print(giveawayMessage.id)
    attemptValSQL(sql, val)

#@createGiveaway.error
#async def giveaway_error(interaction : discord.Interaction, error):
#    await interaction.response.send_message("You do not have the required permissions")

#sets the server specific roles to have boosted chances in the giveaway. Saves them to db.
@tree.command(name="set_boost_role", description="Set the role to boost")
@is_admin()
async def setBoostRole(ctx, rolename: str, boost: float):
    role = int(re.sub('[^0-9]','',str(rolename)))
    print(role)
    sql = "INSERT INTO BoostRoles (RoleID, ServerID, Boost) VALUES (%s, %s, %s)"
    val = (role, ctx.guild.id, boost)
    attemptValSQL(sql, val)

@setBoostRole.error
async def giveaway_error(interaction : discord.Interaction, error):
    await interaction.response.send_message("You do not have the required permissions")


#saves the server to the db for future reference`
@client.event
async def on_guild_join(guild):
    print(guild.id)
    sql = "INSERT INTO servers (ServerID) VALUES (%s)"
    val = [str(guild.id)]
    attemptValSQL(sql, val)

#checks for valid entry reactions.
@client.event
async def on_reaction_add(reaction, user):
    if user.id != client.user.id:
        sql = "SELECT MessageID FROM GiveAways WHERE ServerID=(%s) AND FINISHED=0"
        val = [reaction.message.guild.id]
        results = attemptValSQL(sql, val, returnResults=True)
        pResults = []
        for i in results:
            res = re.sub('[^0-9]','',str(i))
            pResults.append(int(res))
            print(int(res))
        print("Reaction Message ID: " + str(reaction.message.id))
        if reaction.message.id in pResults:
            sql = "SELECT * FROM users WHERE UserID=%s"
            val = [user.id]
            print(user.id)
            userExists=attemptValSQL(sql, val, returnResults=True)
            print(userExists)
            if userExists == []:
                sql = "INSERT INTO users (UserID) VALUES (%s)"
                val = [user.id]
                attemptValSQL(sql, val)
            sql = "SELECT GiveAwayID FROM GiveAways WHERE MessageID=%s"
            val = [reaction.message.id]
            gIDs = attemptValSQL(sql, val, returnResults=True)
            gID = gIDs[0]
            gID = re.sub('[^0-9]','',str(gID))
            sql = "INSERT INTO participants (GiveAwayID, UserID, participating) VALUES (%s, %s, %s)"
            val = (gID, user.id, True)
            attemptValSQL(sql, val)

def attemptValSQL(sql, val, returnResults=False):
    global password
    db = mysql.connector.connect(
            host="localhost",
            user="root",
            password=password,
            database="GiveAways"
            )
    cursor = db.cursor()
    cursor.execute(sql, val)
    if returnResults:
        results = cursor.fetchall()
        db.commit()
        return results
    db.commit()

async def checkLoop():
    sql = "SELECT * FROM GiveAways WHERE finished=%s"
    val = [False]
    while True:
        ongoing = attemptValSQL(sql, val, returnResults = True)
        print(ongoing)
        for i in ongoing:
            if i[2] < datetime.now():
                winners = selectWinners(i[0], i[1], i[3])
                print("checked")
                await sendWinners(winners)
                sql1 = "UPDATE GiveAways set finished=1 WHERE GiveAwayID=%s"
                val1=[i[0]]
                attemptValSQL(sql1, val1)
        await asyncio.sleep(60)

async def sendWinners(winners):
    sql = "SELECT ServerID, ChannelID, prize FROM GiveAways WHERE GiveAwayID=%s"
    val = [winners[0][1]]
    results = attemptValSQL(sql, val, returnResults=True)
    print(winners)
    print(results)
    if len(winners) == 1:
        message = "<@"+str(winners[0][2])+"> has won " + results[0][2] +"!"
    else:
        message = "The winners of the "+results[0][2]+" are:"
        for i in winners:
            message = message + "\n<@"+str(i[2])+">"
    await client.get_guild(int(results[0][0])).get_channel(int(results[0][1])).send(message)

def selectWinners(gID, sID, numOfWinners):
    print(gID)
    sql = "SELECT * FROM participants WHERE GiveAwayID=%s AND participating=%s"
    val=[gID, True]
    participants = attemptValSQL(sql, val, returnResults = True)
    server = client.get_guild(int(sID))
    print(participants)
    for i in participants:
        if server.get_member(int(i[2])) is None:
            sql = "UPDATE participants set participating=0 WHERE UserID=%s AND GiveAwayID=%s"
            vals = [i[2], gID]
            attemptValSQL(sql, vals)
            print("inactive person")
            print(i[2])
    sql = "SELECT RoleID, Boost FROM BoostRoles WHERE ServerID=%s"
    val = [sID]
    boostRoles = attemptValSQL(sql, val, returnResults = True)
    print(sID)
    winners = []
    for i in range(numOfWinners):
        pBoosts = []
        selection = 0
        for i in participants:
            selection = selection + 100
            for j in boostRoles:
                print(int(i[2]))
                userRoles = server.get_member(int(i[2])).roles
                if server.get_role(j[0]) in userRoles:
                    selection = selection + (100 * (j[2]-1))
            pBoosts.append(selection)
        chosen = random.randint(0, selection)
        counter = 0
        for i in pBoosts:
            if chosen <= i:
                winner = counter
            else:
                counter = counter + 1
        print(counter)
        print(participants)
        winners.append(participants[counter])
        sql = "UPDATE participants set winner=1 WHERE participantID=%s"
        val = [participants[counter][0]]
        participants.pop(counter)
    return winners

@client.event
async def on_reaction_remove(reaction, user):
	sql = "UPDATE participants set participating=%s WHERE UserID=%s"
	val = (False, user.id)
	attemptValSQL(sql, val)

client.run(os.getenv('DISCORD_TOKEN'))
