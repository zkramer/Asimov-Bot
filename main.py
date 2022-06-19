import os
import discord
import random
from discord.ext import commands
import mysql.connector
from mysql.connector import connect, Error
from discord.ext.commands import CommandNotFound
from datetime import datetime, date
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
mysql_user = os.getenv('MYSQL_USER')
mysql_password = os.getenv('MYSQL_PASS')
db = os.getenv('MYSQL_DB')
host = os.getenv('MYSQL_HOST')
discord_role = os.getenv('DISCORD_ROLE')
#Handles command prefix and setup for games running on multiple channels and servers simultaneously

client = commands.Bot(command_prefix="!asimov ", help_command=None)
myConnection = mysql.connector.connect(host=host, user=mysql_user, passwd=mysql_password, db=db)



#TODO: Add Notes, Query Notes, Query Historical Archives, Add Credits, Exchange Credits, Loan Credits(?), Query Items, Generate Items, Purchase Items, Query Sessions, Date Stuff

#Print Help Message
async def helpmsg(ctx):
    #TODO: Create help message
    await ctx.message.delete()
    embed1 = discord.Embed()
    embed1.title = "Help"
    embed1.description = "A.S.I.M.O.V. is currently in development. Please try the help menu later."
    await ctx.send(embed=embed1)

@client.command()
async def help(ctx):
    await helpmsg(ctx)

@client.event
#Incorrect Command Error Handling
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await helpmsg(ctx)
    raise error

@client.command()
#Schedule a new game session
async def schedule(ctx, *, arg):
    role = discord.utils.get(ctx.guild.roles, name=discord_role)
    if role in ctx.author.roles:
        first_args = arg.split(';')
        if first_args.len() < 7:
            await ctx.send("Missing Arguments, please try again!")
        else:
            await ctx.message.delete()
            if first_args.len() > 6 and first_args[6].startswith("<@"):
                p4 = first_args[6]
            elif first_args.len() > 6:
                mission = first_args[6]
                p4 = "Null"
            if first_args.len() > 7 and first_args[7].startswith("<@"):
                p5 = first_args[7]
                mission = first_args[8]
            elif first_args.len() > 7:
                mission = first_args[7]
                p5 = "Null"
            else:
                p5 = "Null"
            try:
                sql = "INSERT INTO sessions(Date, Start, End, Player1, Player2, Player3, Player4, Player5, Completed, Mission, Running) " \
                      "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = (first_args[0], first_args[1], first_args[2], "<@"+first_args[3]+">", "<@"+first_args[4]+">", "<@"+first_args[5]+">", "<@"+p4+">", "<@"+p5+">", "No", mission, "No")
                curr = myConnection.cursor()
                curr.execute(sql, val)
                myConnection.commit()
                curr.execute("SELECT * FROM sessions order by id desc limit 1")
                sess = curr.fetchone()
                sess_id = sess[0]
                for x in range(3, 6):
                    val = (sess_id, "<@"+first_args[x]+">")
                    query = "UPDATE characters SET Sessions = %s where Player = %s"
                    curr.execute(query, val)
                    myConnection.commit()
                if p4 != "Null":
                    val = (sess_id, "<@" + p4 + ">")
                    query = "UPDATE characters SET Sessions = %s where Player = %s"
                    curr.execute(query, val)
                    myConnection.commit()
                if p5 != "Null":
                    val = (sess_id, "<@" + p5 + ">")
                    query = "UPDATE characters SET Sessions = %s where Player = %s"
                    curr.execute(query, val)
                    myConnection.commit()
                embed1 = discord.Embed()
                embed1.title = "Session " + sess_id + " Created!"
                if p4 != "Null":
                    if p5 != "Null":
                        embed1.description = "Session Date: " + first_args[0] + "\n " \
                                    "Session Start Time: " + first_args[1] + " EST \n" \
                                    "Session End Time: " + first_args[2] + "EST \n" \
                                    "Players: " + first_args[3] + " " + first_args[4] + " " + first_args[5] + " " + p4 + " " +p5 + "\n" \
                                    "Mission: " + mission
                    else:
                        embed1.description = "Session Date: " + first_args[0] + "\n " \
                                    "Session Start Time: " + first_args[1] + " EST \n" \
                                    "Session End Time: " + first_args[2] + "EST \n" \
                                    "Players: " + first_args[3] + " " + first_args[4] + " " + first_args[5] + " " + p4 + "\n" \
                                    "Mission: " + mission
                else:
                    embed1.description = "Session Date: " + first_args[0] + "\n " \
                                                                            "Session Start Time: " + first_args[1] + " EST \n" \
                                                                                                                     "Session End Time: " + \
                                         first_args[2] + "EST \n" \
                                                         "Players: " + first_args[3] + " " + first_args[4] + " " + first_args[
                                             5] + "\n" \
                                                             "Mission: " + mission
                await ctx.send(embed=embed1)
            except Error as e:
                print(e)
    else:
        await ctx.send("You do not have permission to schedule a game session!")

@client.command()
#Start a scheduled game session
async def start(ctx, sess_id: int = 0):
    await ctx.message.delete()
    curr = myConnection.cursor()
    role = discord.utils.get(ctx.guild.roles, name=discord_role)
    if role in ctx.author.roles:
        query = "SELECT * FROM sessions WHERE id = %s"
        val = str(sess_id)
        curr.execute(query, val)
        session = curr.fetchall()
        if session[9] == "Yes" or session[11] == "Yes":
            await ctx.send("This session is already running or has already been completed!")
        else:
            query = "Update sessions set Running = Yes where id = %s"
            curr.execute(query, val)
            myConnection.commit()
            for player in session:
                if player.beginswith("<@"):
                    val = str(player)
                    query = "Update characters set In_Session = Yes where Sessions = %s"
                    curr.execute(query, val)
                    myConnection.commit()
            await ctx.send("Session " + str(sess_id) + " has begun! Good Luck Explorers!!")
    else:
        await ctx.send("You do not have permission to begin a game session!")

@client.command()
#End a  running game session
async def end(ctx, sess_id: int = 0, credits: int = 0):
    #TODO: Delete post in channel after voting completes
    await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name=discord_role)
    if role in ctx.author.roles:
        curr = myConnection.cursor()
        query = "SELECT * FROM sessions WHERE id = %s"
        val = str(sess_id)
        curr.execute(query, val)
        session = curr.fetchall()
        if session[9] == "Yes" or session[11] == "No":
            await ctx.send("This session is not running or has already been completed!")
        else:
            query = "Update sessions set Running = No where id = %s"
            curr.execute(query, val)
            myConnection.commit()
            query = "Update sessions set Completed = Yes where id = %s"
            curr.execute(query, val)
            myConnection.commit()
            players = []
            for player in session:
                if player.beginswith("<@"):
                    players.append(player)
            reports = []
            authors = []
            for player in players:
                await ctx.send_message(player, "Please Provide your Report for this Expedition here!")
                def check(m):
                    return m.author == player and m.guild is None
                reports.append(client.wait_for('message', check=check))
                authors.append(player)
            await ctx.send("Here are the reports!")
            i = 1
            posted = []
            embed = discord.Embed()
            embed.title = "Expeditionary Reports for Session " + str(sess_id)
            for report in reports:
                if i == 1:
                    num = "A"
                elif i == 2:
                    num = "B"
                elif i == 3:
                    num = "C"
                elif i == 4:
                    num = "D"
                else:
                    num = "E"
                embed.description = embed.description + "Report " + num + ": \n" + str(report) + "\n\n"
                i += 1
            embed.description = embed.description + "Please vote for the Report you want Added to the Historical Archive!"
            msg = await ctx.send(embed=embed)
            if reports.len() == 5:
                await msg.add_reaction("{regional_indicator_a}")
                await msg.add_reaction("{regional_indicator_b}")
                await msg.add_reaction("{regional_indicator_c}")
                await msg.add_reaction("{regional_indicator_d}")
                await msg.add_reaction("{regional_indicator_e}")
            elif reports.len() == 4:
                await msg.add_reaction("{regional_indicator_a}")
                await msg.add_reaction("{regional_indicator_b}")
                await msg.add_reaction("{regional_indicator_c}")
                await msg.add_reaction("{regional_indicator_d}")
            else:
                await msg.add_reaction("{regional_indicator_a}")
                await msg.add_reaction("{regional_indicator_b}")
                await msg.add_reaction("{regional_indicator_c}")
            a_count = 0
            b_count = 0
            c_count = 0
            d_count = 0
            e_count = 0
            def check(m):
                return m.id == msg.id
            while (a_count < 5 and b_count < 5 and c_count < 5 and d_count < 5 and e_count < 5):
                await client.wait_for('reaction_add', check=check)
                reactions = msg.reactions.cache
                a_count = reactions.get.count('{regional_indicator_a}')
                b_count = reactions.get.count('{regional_indicator_b}')
                c_count = reactions.get.count('{regional_indicator_c}')
                d_count = reactions.get.count('{regional_indicator_d}')
                e_count = reactions.get.count('{regional_indicator_e}')
                if a_count >= 5:
                    winner = "A"
                    i = 0
                elif b_count >= 5:
                    winner = "B"
                    i = 1
                elif c_count >= 5:
                    winner = "C"
                    i = 2
                elif d_count >= 5:
                    winner = "D"
                    i = 3
                elif e_count >= 5:
                    winner = "E"
                    i = 4
            embed = discord.Embed()
            today = date.today()
            val = (credits, str(sess_id))
            query = "Update characters set Credits + %s where Sessions = %s"
            curr.execute(query, val)
            myConnection.commit()
            val = str(sess_id)
            query = "Update characters set In_Session = No where Sessions = %s"
            curr.execute(query, val)
            myConnection.commit()
            query = "SELECT * FROM characters WHERE Player = %s"
            val = str(authors[i])
            curr.execute(query, val)
            sessions = curr.fetchall()
            if sessions[7] == "Yes":
                await ctx.send_message(authors[i], "Your report has been added to the Historical Archive but you've already earned bonus credits this week!")
            else:
                val = (credits, str(authors[i]))
                query = "Update characters set Credits + %s where Player = %s"
                curr.execute(query, val)
                myConnection.commit()
                val = str(authors[i])
                query = "Update characters set Bonus_Credits_Earned = Yes where Player = %s"
                curr.execute(query, val)
                myConnection.commit()
                await ctx.send_message(authors[i],
                                       "Your report has been added to the Historical Archive and you've been awarded " + str(credits) + " Bonus Credits!! You will not be able to earn additional Bonus Credits this week.")
            dated = today.strftime("%Y-%#m-%#d")
            sql = "INSERT INTO historical_archive(Author, Date, Contents) " \
                  "VALUES(%s, %s, %s)"
            val = (str(authors[i]), dated, str(reports[i]))
            curr = myConnection.cursor()
            curr.execute(sql, val)
            myConnection.commit()
            embed.title = "Report " + winner + " has been added to the Historical Archives!"
            embed.description = str(reports[i])
            await ctx.send(embed=embed)
            await ctx.send("Session " + str(sess_id) + " has been completed!")
    else:
        await ctx.send("You do not have permission to end a game session!")

@client.command()
#Add a character
async def new_character(ctx, player, character, credits):
    await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name=discord_role)
    if role in ctx.author.roles:
        sql = "INSERT INTO characters(Player, Character_Name, Credits) " \
              "VALUES(%s, %s, %s)"
        val = ("<@" + player + ">", character, credits)
        curr = myConnection.cursor()
        curr.execute(sql, val)
        myConnection.commit()
        await ctx.send("Character: " + character + " has been created for player: <@" + player + ">!!")
    else:
        await ctx.send("You do not have permission to create a new character!")