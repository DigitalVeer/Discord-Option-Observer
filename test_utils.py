import os, requests
from re import IGNORECASE
from tda_handler import TDAHandler
from api_handler import APIHandler
from dotenv import load_dotenv
from pickle import *
from random import randint
from gspread.utils import *

load_dotenv()
API_KEY=os.getenv('API_KEY')

SCOPE = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
SPREADSHEETNAME = "Flow Dashboard"
SHEETNAME = "Flow OI"
DEBUG=True

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


if DEBUG:
    FLOW_CHANNEL    =DEBUG_CHANNEL
    SHEETNAME       =DEBUG_SHEET

# Handler = APIHandler(SCOPE, SPREADSHEETNAME, SHEETNAME, "creds.json", API_KEY)

TEST_STRINGS = ['.PENN210618C130', ".TME230120C27", ".NLS211015C22.5", ".WDC210716C70", ".FTAI210716C27"]

# x = PrettyTable()
# x.field_names = ["Ticker", "Open Interest", "Volume", "Ratio"]
# x.add_row(["UBER", 1295, 11582, 23])
# x.add_row(["PINS", 95, 661, 52])
# x.add_row(["TECK", 7456, 35223, 78])
# x.add_row(["USFD", 352, 737, 53])
# x.border = False
# mystring = x.get_string()
# print(mystring)
# print(Handler.find_all_options_with_ticker("FTAI"))
# print(Handler.df)
# Handler.configure_option(TEST_STRINGS[-1])
# Handler.run_spreadsheet_update()
# LeapHandler.run_spreadsheet_update()
# PARSE = TDAHandler(apikey=API_KEY)
# Handler = APIHandler(SCOPE, SPREADSHEETNAME, SHEETNAME, "creds.json", API_KEY)
# print(rowcol_to_a1(1, 80))
# print(a1_to_rowcol("CB1"))
# str = rowcol_to_a1(1, len(Handler.get_options()))[:-1]
# print(str)
# Handler.color_all_open_interest()
# print(Handler.test_tuple_volume())
# print(Handler.get_morning_updates())
# PARSE.set_new_option(INPUTSTRING3)
# print(PARSE.OPTION)
# PARSE.input_components_into_api(API_KEY)
# print(PARSE.REQUEST)
# Handler.df  = Handler.df.reindex(sorted(Handler.df.columns), axis=1)
# print(Handler.df)
# Handler.run_spreadsheet_update()
# print(Handler.get_all_below_cost())
# print(Handler.get_all_with_volume())
# PARSE.set_new_option(INPUTSTRING)
# PARSE.input_components_into_api()
# r = requests.get(PARSE.REQUEST)
# print(r.json())
# print(Handler.tuple_volume())

# words=["UBER", "05/21", "CALL"]
# print('{:>8} {:>8} {:>8}'.format(*words))


# Handler.format_open_interest_numbers()
# # Handler.run_spreadsheet_update()
# Handler.format_rows()
# print(PARSE.validate_is_option(INPUTSTRING))
# Handler.format_open_interest_numbers()
# Handler.run_spreadsheet_update()
# print(Handler.df)
# PARSE.set_new_option(INPUTSTRING3)
# print(PARSE.OPTION)
# PARSE.input_components_into_api()
# print(PARSE.get_cost_from_tos())
# print(PARSE.get_open_interest_from_tos())



# REQUESTA = PARSE.REQUEST
# print("REQUEST", REQUESTA)
# # print(PARSE.get_field_from_tos())
# response = requests.get(REQUESTA)
# print(response.json())
# field = PARSE.json_extract(response.json(())


# headers = []
# for opt in Handler.get_options():
#     PARSE.set_new_option(opt)
#     headers.append(PARSE.OPTION)
# Handler.color_all_open_interest()
# print(Handler.track_option(INPUTSTRING))

# print(Handler.is_updated(".AA210521C30"))
# Handler.track_option(INPUTSTRING2)
# print(Handler.df)
# Handler.run_oi_update()
# print(Handler.df)

# Handler.add_open_interest(INPUTSTRING3, 1)
# Handler.add_open_interest(INPUTLONG, 1)
# Handler.add_open_interest(INPUTSTRING3, 1)
# Handler.add_open_interest(INPUTSTRING3, 2)
# Handler.add_open_interest(INPUTSTRING3, 3)
# Handler.add_open_interest(INPUTSTRING3, 4)
# print(Handler.df)

# Handler.sheet.update([headers] + [Handler.df.columns.values.tolist()] + Handler.df.values.tolist())

# print([headers] + [Handler.df.columns.values.tolist()] + Handler.df.values.tolist())


# # print(Handler.find_all_options_with_ticker("UBER"))
# # print([Handler.df.columns.values.tolist()] + Handler.df.values.tolist())
# all_options = Handler.get_options()
# print(all_options)
# Handler.add_open_interest(INPUTSTRING, 52)
# print(Handler.df)
# Handler.add_open_interest(INPUTSTRING2, 5522)
# print(Handler.df)
# Handler.add_open_interest(".LI210917C32", 53)
# # print(Handler.df)

# print([Handler.df.columns.values.tolist()] + Handler.df.values.tolist())

# Handler.sheet.update([Handler.df.columns.values.tolist()] + Handler.df.values.tolist())

# count = 1
# print(all_options)
# for option in all_options:
#     PARSE.set_new_option(Handler.sheet.cell(1, count).value)
#     print(PARSE.TOS)
#     Handler.sheet.update_cell(2, count, PARSE.TOS)
#     count = count + 1
# print(PARSE.TOS)

# print(all_options)
# # print(Handler.df)
# print(Handler.get_dramatic_changes())
# Handler.color_all_open_interest()


