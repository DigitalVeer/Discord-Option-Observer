from logging import error, warn
import gspread, datetime, re, time
from gspread.utils import rowcol_to_a1, a1_to_rowcol
from gspread_formatting.batch_update_requests import format_cell_range, set_column_width
from gspread_formatting.functions import get_user_entered_format
from gspread_formatting import batch_updater
from oauth2client.service_account import ServiceAccountCredentials

from pandas.core import api
from tda_handler import TDAHandler
from gspread_formatting import *
import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 500)


class APIHandler:
    def __init__(self, scope, projectName, sheetName, credfile, APIKey):
        self.projectName = projectName
        self.sheetName = sheetName
        self.scope = scope
        self.spreadSheet = None
        self.creds = None
        self.sheet = None
        self.client = None
        self.df = None
        self.parser = TDAHandler()
        self.APIKey = APIKey
        self.appended = False
        self.batch = None
        self.morning = None

        self.buildCredentials(credfile)
        self.generateSpreadSheetService()
        self.set_pandas_dataframe()


    def buildCredentials(self, credfile):
       self.creds = ServiceAccountCredentials.from_json_keyfile_name(credfile, self.scope)
       self.client = gspread.authorize(self.creds)

    def generateSpreadSheetService(self):
        self.spreadSheet = self.client.open(self.projectName)
        self.sheet = self.spreadSheet.worksheet(self.sheetName)

    def get_options(self):
        return list(self.df.columns.values)

    def find_all_options_with_ticker(self, ticker):
        options = []
        tos_lst = self.get_options()
        for opt in tos_lst:
            self.parser.set_new_option(opt)
            if self.parser.TICKER.lower() == ticker.lower():
                opt_data = self.get_option_data(opt)
                COST=(opt_data["COST"]).replace("COST:", "")
                options.append(f'**{opt_data["OPTIONSTR"]}** | Tracked: **{opt_data["FLOWDATE"]}** | Original Cost: **{COST}**')
        return options

    def option_exists(self, option):
        self.parser.set_new_option(option)
        tos = self.parser.TOS
        return tos in self.get_options()

    def get_option_data(self, opt):
        if not self.option_exists(opt):
            error('Option does not exist.')
        self.parser.set_new_option(opt)
        data = self.df[self.parser.TOS]
        data=list(filter(None, data.values))

        OPTION_STR = self.parser.OPTION
        TOS = self.parser.TOS
        FLOWDATE = data[0].split()[-1]
        COST = data[1]
        OI = [str(x).replace(",", "").split()[-1] for x in data[2:]]
        DATES = [str(x).replace(",", "").split()[0] for x in data[2:]]

        return {
            "OPTIONSTR" : OPTION_STR,
            "TOS": TOS,
            "FLOWDATE": FLOWDATE,
            "COST": COST,
            "OI": OI,
            "DATES": DATES
        }

    def get_option_oi(self, opt):
        return self.get_option_data(opt)["OI"]

    def get_option_cost(self, opt):
        return self.get_option_data(opt)["COST"]

    def add_new_option(self, opt, cost, flow_date):
        self.parser.set_new_option(opt)
        value_array = [f'FLOW DATE: {flow_date}', f'COST: {cost}']
        self.df.insert(0,
                       self.parser.TOS,
                       value_array + [""] * (self.df.shape[0] - len(value_array))
                       )
        print("Added to Pandas DF: ", self.parser.TOS)

    def add_open_interest(self, opt, oi):

        if not self.option_exists(opt):
            error('Option does not exist.')
            return

        self.parser.set_new_option(opt)
        num_rows = self.df.shape[0]

        data = self.df[self.parser.TOS]
        data = list(filter(None, data.values))

        #If there is more OI than the table allows, expand the table
        if (len(data) + 1 >= num_rows):
            self.df = self.df.append(pd.Series(), ignore_index=True)
            self.df = self.df.replace(np.nan, '', regex=True)
            self.df[self.parser.TOS][len(data)] = f'{datetime.date.today().month}/{datetime.date.today().day} - {oi}'
            self.appended = True
        else:
            if self.appended:
                self.df[self.parser.TOS][len(data)] = f'{datetime.date.today().month}/{datetime.date.today().day} - {oi}'
            else:
                self.df[self.parser.TOS][len(data) + 1] = f'{datetime.date.today().month}/{datetime.date.today().day} - {oi}'



    def format_rows(self):
        self.batch = batch_updater(self.sheet.spreadsheet)
        TOPROW = CellFormat(
            borders=Borders(bottom=Border("SOLID_THICK", color=Color(1, 0.6, 0))),
            horizontalAlignment="LEFT",
            textFormat=TextFormat(fontFamily="Roboto", fontSize=9, foregroundColor=Color(0, 1, 1))
        )
        TOSROW = CellFormat(
            horizontalAlignment="LEFT",
            textFormat=TextFormat(fontFamily="Roboto", fontSize=10, foregroundColor=Color(1, 1, 0), bold=True)
        )
        COSTROW = CellFormat(
            borders=Borders(bottom=Border("SOLID_THICK", color=Color(1, 0.6, 0))),
            horizontalAlignment="LEFT",
            textFormat=TextFormat(fontFamily="Roboto", fontSize=10, foregroundColor=Color(1, 0, 1), bold=True)
        )
        # print(get_user_entered_format(self.sheet, "A4"))
        self.batch.format_cell_range(self.sheet, '1:1', TOPROW)
        self.batch.format_cell_range(self.sheet, '2:2', TOSROW)
        self.batch.format_cell_range(self.sheet, '4:4', COSTROW)

    def get_morning_updates(self):
        increases = []
        decreases = []
        map_from_option_to_data = {}
        map_from_option_to_data["increased_option"] = {}
        map_from_option_to_data["decreased_option"] = {}
        for opt in self.get_options():
            self.parser.set_new_option(opt)
            last_oi = int(self.get_last_oi(opt))
            curr_oi = int(self.parser.get_open_interest_from_tos(apikey=self.APIKey))
            change_percent = int(((float(curr_oi)-last_oi)/last_oi)*100)
            if change_percent > 5:
                    message = f'**{self.parser.TICKER}** {self.parser.MONTH}/{self.parser.DAY}/{self.parser.YEAR[2:]} {self.parser.STRIKE} {self.parser.CALLPUT} | OI increased **{last_oi}** -> **{curr_oi}** | Change: **{change_percent}**%'
                    increases.append(message)
                    if opt not in map_from_option_to_data["increased_option"]:
                        map_from_option_to_data["increased_option"][opt] = {}
                    map_from_option_to_data["increased_option"][opt]["message"] = message

            elif change_percent < -5:
                    message = f'**{self.parser.TICKER}** {self.parser.MONTH}/{self.parser.DAY}/{self.parser.YEAR[2:]} {self.parser.STRIKE} {self.parser.CALLPUT} | OI decreased **{last_oi}** -> **{curr_oi}** | Change: **{change_percent}%**'
                    decreases.append(message)
                    if opt not in map_from_option_to_data["decreased_option"]:
                        map_from_option_to_data["decreased_option"][opt] = {}
                    map_from_option_to_data["decreased_option"][opt]["message"] = message
        return increases, decreases, map_from_option_to_data


    def get_dramatic_changes(self):
        row_count = self.df.shape[0]
        col_count = self.get_options()
        increases = []; decreases = []
        prior_val = None

        for col in range(0, len(col_count)):
            prior_val = None
            for row in range(3, row_count):
                curr_val = str(self.df[col_count[col]][row])
                if curr_val is None or curr_val == '' or curr_val.isspace():
                    continue
                curr_val = int(curr_val.replace(",", "").split(" ")[-1])
                if prior_val is None:
                    prior_val = curr_val
                    continue
                if prior_val == 0:
                    prior_val = 1
                change_percent = ((float(curr_val)-prior_val)/prior_val)*100
                if change_percent > 10:
                    increases.append(rowcol_to_a1(row + 2, col + 1))
                elif change_percent < -10:
                    decreases.append(rowcol_to_a1(row + 2, col + 1))
                prior_val = curr_val
        return (increases, decreases)

    def format_open_interest_numbers(self):
        self.df = self.df.replace({"-" :" - "}, regex=True)
        self.df = self.df.replace({'\s{2,}' :" "}, regex=True)
        self.df = self.df.replace({"," :""}, regex=True)

    def color_all_open_interest(self):
        self.format_rows()
        increase = CellFormat(textFormat=TextFormat(fontFamily="Roboto", fontSize=10, foregroundColor=Color(0, 1, 0)))
        decrease = CellFormat(textFormat=TextFormat(fontFamily="Roboto", fontSize=10, foregroundColor=Color(1, 0, 0)))
        white = CellFormat(textFormat=TextFormat(fontFamily="Roboto", fontSize=10, foregroundColor=Color(1, 1, 1)))
        self.batch.format_cell_range(self.sheet, "A5:ZZ1000", white)
        self.batch.set_column_width(self.sheet, 'A:ZZ', 165)
        increases, decreases = self.get_dramatic_changes()
        for green_cell in increases:
            self.batch.format_cell_range(self.sheet, green_cell, increase)
        for red_cell in decreases:
            self.batch.format_cell_range(self.sheet, red_cell, decrease)
        self.batch.execute()

    def set_pandas_dataframe(self):
        dataframe = pd.DataFrame(self.sheet.get_all_records())
        new_header = dataframe.iloc[0]
        dataframe = dataframe[1:]
        dataframe.columns = new_header
        self.df = dataframe
        print("Pandas Dataframe Generation [COMPLETED] : ", self.sheetName)

    def get_headers(self):
        headers = []
        for opt in self.get_options():
            self.parser.set_new_option(opt)
            headers.append(self.parser.OPTION)
        return headers

    def update_sheet(self):
        self.format_open_interest_numbers()
        headers = self.get_headers()
        self.sheet.update([headers] + [self.df.columns.values.tolist()] + self.df.values.tolist())

    def get_last_update(self, opt):
        return self.get_option_data(opt)["DATES"][-1]

    def get_last_oi(self, opt):
        return self.get_option_data(opt)["OI"][-1]

    def is_updated(self, opt):
        last_update = self.get_last_update(opt)
        return f'{datetime.date.today().month}/{datetime.date.today().day}' == last_update


    def get_current_day(self):
        return f'{datetime.date.today().month}/{datetime.date.today().day}'

    def track_option(self, opt, cost=None):
        self.parser.set_new_option(opt)
        print(self.parser.OPTION)
        day = self.get_current_day()
        if self.option_exists(opt):
            if not self.is_updated(opt):
                OI = self.parser.get_open_interest_from_tos(apikey=self.APIKey)
                print("OI :", OI)
                self.add_open_interest(opt, OI)
        else:
            if cost:
                self.add_new_option(opt, cost, day)
            else:
                cost = self.parser.get_cost_from_tos(apikey=self.APIKey)
                self.add_new_option(opt, cost, day)
                print("Cost: ", cost)
            OI = self.parser.get_open_interest_from_tos(apikey=self.APIKey)
            print("OI: ", OI)
            self.add_open_interest(opt, OI)
        print("--==--"*5)

    def run_oi_update(self):
        opts = self.get_options()
        for opt in opts:
            self.track_option(opt)

    def is_week(self):
        wk_day = datetime.datetime.today().weekday()
        return wk_day < 5

    def run_spreadsheet_update(self, override=False):
        self.set_pandas_dataframe()
        if self.is_week() or override:
            self.run_oi_update()
            self.format_open_interest_numbers()
            self.update_sheet()
            self.set_pandas_dataframe()
            self.color_all_open_interest()
            print("Completed update.")
            self.appended = False
        else:
            print("Weekend.")

    def configure_option(self, opt):
        self.set_pandas_dataframe()
        self.track_option(opt)
        self.update_sheet()
        self.run_spreadsheet_update(override=True)


    def get_all_below_cost(self):
        below_entry = []
        for opt in self.get_options():
            self.parser.set_new_option(opt)
            flow_cost = self.get_option_cost(opt)
            flow_cost = float(flow_cost.replace("COST:", ""))
            curr_cost = float(self.parser.get_cost_from_tos(opt, apikey = self.APIKey))
            print(opt, curr_cost, flow_cost)
            change_percent = ((curr_cost-flow_cost)/flow_cost)*100
            if (curr_cost < flow_cost):
                below_entry.append(f'{self.parser.OPTION} | Initial Cost: **{flow_cost}** | Current Cost: **{curr_cost}** | Approximately **{int(change_percent)*-1}%** from initial price')
        return below_entry


    def get_all_with_volume(self, thres):
        notable_volume = []
        for opt in self.get_options():
            self.parser.set_new_option(opt)
            curr_volume = self.parser.get_volume_from_tos(opt, apikey = self.APIKey)
            open_interest = self.get_option_oi(opt)[-1]
            ratio = ((float(curr_volume) / float(open_interest)) * 100)
            if ratio > thres:
                tup = f'**{self.parser.TICKER}** {self.parser.STRIKE} {self.parser.CALLPUT} {self.parser.MONTH}/{self.parser.DAY}/{self.parser.YEAR[2:]} {self.parser.STRIKE} {self.parser.CALLPUT} | **{curr_volume}** volume | **{open_interest}** OI | **{int((float(curr_volume) / float(open_interest)) * 100)}%** ratio.'
                notable_volume.append(tup)
                notable_volume = sorted(notable_volume, key=lambda x:x[:4])
        return notable_volume

    def tuple_volume(self):
        notable_volume = []
        for opt in self.get_options():
            self.parser.set_new_option(opt)
            curr_volume = self.parser.get_volume_from_tos(opt, apikey = self.APIKey)
            open_interest = self.get_option_oi(opt)[-1]
            tup = f'**{self.parser.TICKER}** {self.parser.MONTH}/{self.parser.DAY}/{self.parser.YEAR[2:]} {self.parser.STRIKE} {self.parser.CALLPUT} | **{curr_volume}** volume | **{open_interest}** OI | **{int((float(curr_volume) / float(open_interest)) * 100)}%** ratio.'
            notable_volume.append(tup)
            notable_volume = sorted(notable_volume, key=lambda x:x[:4])
        return notable_volume
