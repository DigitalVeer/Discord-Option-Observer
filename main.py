import os, discord
import datetime as dt

from discord.ext import tasks
from dotenv import load_dotenv

from tda_handler import TDAHandler
from api_handler import APIHandler
from personal_alerts import PersonalAlert
from logging import DEBUG
from string_constants import StringConstants
load_dotenv()

SCOPE =             ["https://spreadsheets.google.com/feeds",
                     'https://www.googleapis.com/auth/spreadsheets',
                     "https://www.googleapis.com/auth/drive.file",
                     "https://www.googleapis.com/auth/drive"]
                     
TOKEN =             os.getenv('DISCORD_TOKEN')
GUILD =             os.getenv('DISCORD_GUILD')
API_KEY=            os.getenv('API_KEY')
SPREADSHEETNAME =   os.getenv('SPREADSHEETNAME')
SHEETNAME =         os.getenv('SHEETNAME')
LEAPSHEETNAME =     os.getenv('LEAPSHEETNAME')
MAIN_CHANNEL =      os.getenv('MAIN_CHANNEL')
FLOW_CHANNEL =      os.getenv('FLOW_CHANNEL')
DEBUG_CHANNEL =     os.getenv('DEBUG_CHANNEL')
DEBUG_SHEET =       os.getenv('DEBUG_SHEET')
PERSONAL_SHEET =    os.getenv('PERSONAL_SHEET')
DEBUG =             os.getenv('DEBUG')

client = discord.Client()

if DEBUG:
    FLOW_CHANNEL    =DEBUG_CHANNEL
    SHEETNAME       =DEBUG_SHEET

Handler = APIHandler(SCOPE, SPREADSHEETNAME, SHEETNAME, "creds.json", API_KEY)
LeapHandler = APIHandler(SCOPE, SPREADSHEETNAME, LEAPSHEETNAME, "creds.json", API_KEY)
PARSE = TDAHandler(apikey=API_KEY)
personalAlert = PersonalAlert(SCOPE, SPREADSHEETNAME, PERSONAL_SHEET, "creds.json", API_KEY)

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    update_morning.start()
    oi_update_intraday.start()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    # ===============[ MISC ]================= #
    if "!validate" in message.content.lower():
        TOS = message.content.split(" ")[-1]
        PARSE.set_new_option(TOS)
        await message.channel.send(("The option you are trying to track is: ", PARSE.OPTION))

    # ===============[ PERSONAL OPTION TRACKING ]================= #
    if "!follow" in message.content.lower():
        personalAlert.update_dataframe()
        TOS = message.content.split(" ")
        generated_message = "Unabled to parse command"
        user = message.author
        if "-" in TOS[1]:
            # List the options the person is following
            if "--list" == TOS[1]:
                generated_message = personalAlert.generate_message_list_of_user_options(user)
            elif "--remove" == TOS[1]:
                if len(TOS) != 3:
                    generated_message = "Provide an option to delete in this format: \n !follow --remove [option name]"
                else:
                    generated_message = personalAlert.delete_option_from_user(user, TOS[2])
            elif "--sort" == TOS[1]:
                personalAlert.sort_user_options(user)
                generated_message = personalAlert.generate_message_list_of_user_options(user)
                generated_message = "Successfully sorted all of your options in alphabetical order\n" + generated_message
            elif "--help" == TOS[1]:
                generated_message = personalAlert.generate_help_message()
        else:
            # The normal flow for someone to follow a option
            generated_message = personalAlert.add_option_to_user(user, TOS[1])
        await message.author.send(generated_message)

    # ===============[ FLOW OI ]================= #
    if "!track" in message.content.lower():
        TOS = message.content.split(" ")
        PARSE.set_new_option(TOS[1])
        OI_PLUS = Handler.find_all_options_with_ticker(PARSE.TICKER)
        Handler.configure_option(TOS[1])
        await message.channel.send(f'{StringConstants.SMALL_HEADER} **{PARSE.TICKER}** {StringConstants.SMALL_HEADER}\n')
        await message.channel.send(f'Now tracking: {PARSE.OPTION} **[{PARSE.TOS}]**\n{StringConstants.LARGE_HEADER*2}')
        if len(OI_PLUS) > 0:
            await message.channel.send(f'For **{PARSE.TICKER}**, you are also tracking these  contracts:\n')
            for OI in chunks(OI_PLUS, 15):
                await message.channel.send(" \n".join(OI)+"\n"+(StringConstants.LARGE_HEADER*2))

    if "!goodentry" in message.content.lower():
        entries = Handler.get_all_below_cost()
        for entry in chunks(entries, 15):
            await message.channel.send(" \n".join(entry))

    if "!volumecheck" in message.content.lower():
        vols = Handler.tuple_volume()
        for vol in chunks(vols, 15):
            await message.channel.send(" \n".join(vol))

    # ===============[ LEAPS ]================= #
    if "!ltrack" in message.content.lower():
        TOS = message.content.split(" ")
        PARSE.set_new_option(TOS[1])
        OI_PLUS = LeapHandler.find_all_options_with_ticker(PARSE.TICKER)
        LeapHandler.configure_option(TOS[1])
        await message.channel.send(f'{StringConstants.SMALL_HEADER} **{PARSE.TICKER}** {StringConstants.SMALL_HEADER}\nNow tracking: {PARSE.OPTION} **[{PARSE.TOS}]**\n{StringConstants.LARGE_HEADER*2}')
        if len(OI_PLUS) > 0:
            await message.channel.send(f'For **{PARSE.TICKER}**, you are also tracking these  contracts:\n')
            for OI in chunks(OI_PLUS, 15):
                await message.channel.send(" \n".join(OI)+"\n"+(StringConstants.LARGE_HEADER*2))

    if "!lgoodentry" in message.content.lower():
        entries = LeapHandler.get_all_below_cost()
        for entry in chunks(entries, 15):
            await message.channel.send(" \n".join(entry))
            
    if "!lvolumecheck" in message.content.lower():
        vols = LeapHandler.tuple_volume()
        for vol in chunks(vols, 15):
            await message.channel.send(" \n".join(vol))

@tasks.loop(minutes=10)
async def update_morning():
    MAIN = client.get_channel(int(FLOW_CHANNEL))
    curr_time = dt.datetime.now()
    if (DEBUG or (curr_time.hour == 7 and (30 <= curr_time.minute < 40))):
        increases, decreases, map_from_option_to_data = Handler.get_morning_updates()

        increased_opt = map_from_option_to_data["increased_option"].keys()
        decreased_opt = map_from_option_to_data["decreased_option"].keys()
        alert_personal_option_changes_map = personalAlert.alert_everyone_map(increased_opt, decreased_opt)

        for user, options in alert_personal_option_changes_map["increased_oi_notification"].items():
            message = personalAlert.build_message(user, options, map_from_option_to_data["increased_option"], increased_oi = True)
            if message:
                user_channel = await client.fetch_user(user)
                await user_channel.send(message)

        for user, options in alert_personal_option_changes_map["decreased_oi_notification"].items():
            message = personalAlert.build_message(user, options, map_from_option_to_data["decreased_option"], increased_oi = False)
            if message:
                user_channel = await client.fetch_user(user)
                await user_channel.send(message)

        await MAIN.send(StringConstants.LARGE_HEADER + "**[ FLOW ]**" + StringConstants.LARGE_HEADER)
        if len(increases) > 0:
            await MAIN.send(StringConstants.OVERNIGHT_INCREASE  + " \n".join(increases) + " \n" )
        else:
            await MAIN.send(StringConstants.OVERNIGHT_NO_INCREASE)
        if len(decreases) > 0:
            await MAIN.send(StringConstants.OVERNIGHT_DECREASE  + " \n".join(decreases) + " \n")
        else:
            await MAIN.send(StringConstants.OVERNIGHT_NO_DECREASE)

        increases, decreases, map_from_option_to_data = LeapHandler.get_morning_updates()
        await MAIN.send(StringConstants.LARGE_HEADER + "**[ FLOW LEAP ]**" + StringConstants.LARGE_HEADER)
        if len(increases) > 0:
            await MAIN.send(StringConstants.OVERNIGHT_INCREASE  + " \n".join(increases) + " \n" )
        else:
            await MAIN.send(StringConstants.OVERNIGHT_NO_INCREASE)
        if len(decreases) > 0:
            await MAIN.send(StringConstants.OVERNIGHT_DECREASE  + " \n".join(decreases) + " \n")
        else:
            await MAIN.send(StringConstants.OVERNIGHT_NO_DECREASE)

        Handler.run_spreadsheet_update(override=False)
        LeapHandler.run_spreadsheet_update(override=False)

@tasks.loop(hours=1)
async def oi_update_intraday():
    MAIN = client.get_channel(int(MAIN_CHANNEL))
    curr_time = dt.datetime.now()
    if (9 <= curr_time.hour < 17 ):
        vols = Handler.get_all_with_volume(10)
        if len(vols) >= 1:
            await MAIN.send(StringConstants.INTRADAY_UPDATE + " \n".join(vols))
        else:
            await MAIN.send(StringConstants.INTRADAY_NO_UPDATE)


client.run(TOKEN)

async def on_error(event, *args, **kwargs):
    with open('err.log', 'a') as f:
        if event == 'on_message':
            f.write(f'Unhandled message: {args[0]}\n')
        else:
            raise discord.DiscordException
