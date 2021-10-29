import gspread, os
from oauth2client.service_account import ServiceAccountCredentials
from TDAHandler import TDAHandler
import pandas as pd

API_KEY     = os.getenv('API_KEY')
PARSE       = TDAHandler(apikey=API_KEY)

class PersonalAlert:
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
        self.nameRow = None

        self.buildCredentials(credfile)
        self.generateSpreadSheetService()
        self.update_dataframe()

    def buildCredentials(self, credfile):
       self.creds = ServiceAccountCredentials.from_json_keyfile_name(credfile, self.scope)
       self.client = gspread.authorize(self.creds)

    def generateSpreadSheetService(self):
        print("Connected to " + self.sheetName)
        self.spreadSheet = self.client.open(self.projectName)
        self.sheet = self.spreadSheet.worksheet(self.sheetName)

    def update_dataframe(self):
        dataframe = pd.DataFrame(self.sheet.get_all_records())
        new_header = dataframe.iloc[0]
        self.nameRow = dataframe.columns
        dataframe = dataframe[1:]
        new_header = [str(x) for x in new_header]
        dataframe.columns = new_header
        self.df = dataframe


    def build_user_map_to_personal_options(self):
        """Builds a map from User id to a list of options the user is tracking
        Example: "1234567" -> [.UBER210604C100, ....]
        """
        user_map = {}
        columns = self.df.iteritems()
        for (colName, colContents) in columns:
            user_map[str(colName)] = list(colContents)
        self.user_map = user_map
        return user_map


    def get_user_map_to_personal_options(self):
        return self.build_user_map_to_personal_options()


    def alert_everyone_map(self, increased_oi_alerts, decreased_oi_alerts):
        """
            Builds a map for discord bot to handle information:
            Given increased_oi_alerts: [.UBER210604C100] and decreased_oi_alerts = [.UBER210604P20]
            and that user "1234567" has .UBER210604C100 in sheet
            and user "09876" has .UBER210604P20
                Returns: {
                increased_oi_notification: {
                    "1234567" : [".UBER210604C100"]
                    },
                    decreased_oi_notification: {
                    "09876" : [.UBER210604P20]
                    }
                }
        """
        oi_notifications = {}
        oi_notifications["increased_oi_notification"] = {}
        oi_notifications["decreased_oi_notification"] = {}
        users = self.get_user_map_to_personal_options()
        increased_oi_alerts = set(increased_oi_alerts)
        decreased_oi_alerts = set(decreased_oi_alerts)
        for (userId, options) in users.items():
             options_set = set(options)

             intersected_increased_options = increased_oi_alerts.intersection(options_set)
             if len(intersected_increased_options) > 0:
                 oi_notifications["increased_oi_notification"][userId] = []
             for option in intersected_increased_options:
                 oi_notifications["increased_oi_notification"][userId].append(option)

             intersected_decreased_options = decreased_oi_alerts.intersection(options_set)
             if len(intersected_decreased_options) > 0:
                 oi_notifications["decreased_oi_notification"][userId] = []
             for option in intersected_decreased_options:
                 oi_notifications["decreased_oi_notification"][userId].append(option)

        return oi_notifications

    def build_message(self, user, options, map_from_option_to_data, increased_oi):
        """
        Params: user: string (userId), options: List[string] (list of options the user has dramatically changed),
        map_from_option_to_message: dict
        Returns: string to be sent back to the user
        """
        message_list = []
        if map_from_option_to_data == None:
            return None 
        else:
            for option in options:
                message_list.append(map_from_option_to_data[option]["message"])

        if increased_oi:
            return "Your following options saw at least a 10\% increase overnight: \n"  + " \n".join(message_list) + " \n"
        else:
            return "Your following options saw at least a 10\% decrease overnight: \n"  + " \n".join(message_list) + " \n"

    def add_option_to_user(self,user, option):
        user_id = str(user.id)
        print("User in sheet: "+ str(self.user_in_sheet(user_id)))

        PARSE.set_new_option(option)
        message = "Failed"
        if self.user_in_sheet(user_id):
            message = self.add_option_to_user_column(user_id, option)
        else:
            message = self.add_user_and_column_to_sheet(str(user), user_id, option)
        self.update_sheet()
        return message

    def update_sheet(self):
        self.sheet.update(([list(self.nameRow)] + [self.df.columns.values.tolist()] + self.df.values.tolist()))

    def user_in_sheet(self, user_id):
        return user_id in list(self.df.head(1))

    def add_option_to_user_column(self, user_id, option):
        '''adds option to user column'''
        # Checks if the option exists for the user
        if self.df[user_id].str.contains(option).any():
            return "Option is already being tracked for user"
        number_of_options_tracked = self.number_options_tracked_by_user(user_id)
        if number_of_options_tracked < self.get_number_of_rows():
            self.df[user_id][number_of_options_tracked+1] = option
            return "Successfully followed " + PARSE.OPTION
        index_of_user_column = self.df.columns.get_loc(user_id)
        # if index is 0, then it will create a row like [(option_name),...,...]
        row_to_add_to_df = [option if n == index_of_user_column else "" for n in range(len(self.df.columns))]
        # Adds row to dataframe
        self.df.loc[len(self.df.index)+1] = row_to_add_to_df
        return "Successfully followed " + PARSE.OPTION

    def sort_user_options(self, user):
        user_id = str(user.id)
        if user_id not in self.df:
            print("User does not exist in database")
            return
        list_of_user_options = [str(option) for option in list(self.df[user_id])]
        list_of_user_options.sort()
        self.df[user_id] = list_of_user_options
        self.update_sheet()

    def add_user_and_column_to_sheet(self, username, user_id, option):
        username = pd.Index([username])
        self.nameRow= self.nameRow.append(username)
        number_of_rows = self.get_number_of_rows()
        # Builds a column list like [(option_name),...,...]
        new_user_column = [option if n == 0 else "" for n in range(number_of_rows)]
        self.df[user_id] = new_user_column
        return "Successfully added new user and " + PARSE.OPTION

    def number_options_tracked_by_user(self, user_id):
        number_of_options = 0
        for element in list(self.df[user_id]):
            if element == '':
                return number_of_options
            number_of_options += 1
        return number_of_options

    def get_number_of_rows(self):
        return len(self.df.index)

    def generate_message_list_of_user_options(self, user):
        users_map = self.get_user_map_to_personal_options()
        user_options = users_map[str(user.id)]
        combined_string_of_options = ""
        for option in user_options:
            combined_string_of_options += f'{option}\n'
        return "Here are the list of options you are following: \n" + combined_string_of_options

    def delete_option_from_user(self, user, option):
        PARSE.set_new_option(option)
        user_id = str(user.id)
        user_column = self.df[user_id]
        if option not in list(user_column):
            return "Option is not being followed by you"
        new_generated_list = [x if x !=option else "" for x in user_column]
        # ["a", "", "b"] -> ["a", "b", ""]
        new_generated_list.sort(key=bool, reverse=True)
        self.df[user_id] = new_generated_list
        self.update_sheet()
        return "Successfully removed: " + PARSE.OPTION

    def generate_help_message(self):
        return """Here are the list of commands for !follow :
    !follow [Option]
        ex: !follow .UBER210604C90
        Tracks Option to your discord account

    !follow --list
        Lists options you are currently tracking

    !follow --sort
        Sorts the options you are currently tracking in alphabetical order

    !follow --remove [Option]
        ex: !follow --remove .UBER210604C90
        Removes the option you are tracking

    !follow --help
        Generates help message for the available commands
    """