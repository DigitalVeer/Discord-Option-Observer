from logging import error
import re, requests
from datetime import datetime

class TDAHandler:

    APITEMPLATE = "https://api.tdameritrade.com/v1/marketdata/chains?apikey=A0&symbol=A1&contractType=A2&includeQuotes=TRUE&strategy=SINGLE&strike=A3&fromDate=A4&toDate=A4"
    TRACK_PREFIX="!track"
    COST_DELIMITER="@"
    
    def __init__(self, input=None, apikey=None):
        self.TOS = None
        self.TICKER = None
        self.DAY = None
        self.MONTH = None
        self.YEAR = None
        self.CALLPUT = None
        self.STRIKE = None
        self.FULLDATE = None
        self.OPTION = None
        self.REQUEST = None
        self.JSON = None
        self.APIKey = apikey
        if input is not None:
            self.set_new_option(input)
            
    def set_new_option(self, input):
        if self.determineType(input) == "TOS":
            self.tos_to_components(input)
        else:
            self.tos_to_components(self.option_to_tos(input))
            
    #will add regex validation another time
    def determineType(self, str):
        if (str[0]=='.' and str.count(' ')==0):
            return 'TOS'
        else:
            return 'OPTION'

    def option_to_tos(self, option):
        clean_str = list(
            filter(None,  option
            .replace(self.COST_DELIMITER, " ")
            .replace(self.TRACK_PREFIX, "")
            .split(" "))
        )        
        ticker, date, strike, call_put, *_ = clean_str
        date_fields = date.split("-")
        
        #2021-05-21 is acceptable as well as 05-21 (defaults to current year)
        if (len(date_fields) == 2):
            month, day, = date_fields
            year = datetime.today().year
        else:
            year, month, day, = date_fields
        
        year = str(year).replace("20", ""); tos_str = (f'.{ticker}{year}{month}{day}{call_put[0]}{strike}').upper(); 
        self.TOS = tos_str        
        
        return tos_str

    def tos_to_components(self, tos_str):
        
        components = re.match(r'\.([A-Z]+)(\d\d)(\d\d)(\d\d)([CP])([\d\.]+)',tos_str).groups()
        TICKER, YEAR, MONTH, DAY, CALLPUT, STRIKE = components
        
        YEAR = "20" + YEAR
        CALLPUT = 'CALL' if CALLPUT == 'C' else 'PUT'
        FULL_DATE=f"{YEAR}-{MONTH}-{DAY}"

        self.TOS =          tos_str    
        self.OPTION =       f"{TICKER} {FULL_DATE} {STRIKE} {CALLPUT}"
        self.TICKER =       TICKER
        self.YEAR =         YEAR
        self.MONTH =        MONTH
        self.DAY =          DAY
        self.FULLDATE =     FULL_DATE
        self.CALLPUT =      CALLPUT
        self.STRIKE =       STRIKE
        
        
    def input_components_into_api(self, apikey=None):
        API_HANDLE =    (
                        self.APITEMPLATE
                        .replace("A0", self.APIKey or apikey)
                        .replace("A1", self.TICKER)
                        .replace("A2", self.CALLPUT)
                        .replace("A3", self.STRIKE)
                        .replace("A4", self.FULLDATE)
                        )
        self.REQUEST = API_HANDLE
        
    #Credit: https://hackersandslackers.com/extract-data-from-complex-json-python/
    def json_extract(self, key):
        arr = []
        def extract(obj, arr, key):
            if isinstance(obj, dict):
                  for k, v in obj.items():
                     if isinstance(v, (dict, list)):
                         extract(v, arr, key)
                     elif k == key:
                        arr.append(v)
            elif isinstance(obj, list):
                 for item in obj:
                     extract(item, arr, key)
            return arr

        values = extract(self.JSON, arr, key)
        return values
    
    def get_fields_from_tos(self, field, tos_str=None, apikey=None):
        self.tos_to_components(tos_str or self.TOS)
        self.input_components_into_api(apikey or self.APIKey)
        
        response = requests.get(self.REQUEST)
        self.JSON = response.json()
        field = self.json_extract(field)
        return field
    
    def get_cost_from_tos(self, tos_str=None, apikey=None):
        print(self.OPTION)
        fields = self.get_fields_from_tos("mark", tos_str, apikey)
        cost = fields[-1]
        return cost
    
    def get_volume_from_tos(self, tos_str=None, apikey=None):
        print(self.OPTION)
        fields = self.get_fields_from_tos("totalVolume", tos_str, apikey)
        cost = fields[-1]
        return cost
    
    def get_open_interest_from_tos(self, tos_str=None, apikey=None):
        attempts = 0
        while True:
            attempts = attempts + 1
            fields = self.get_fields_from_tos("openInterest", tos_str, apikey)
            if fields:
                openInterest = fields[0]
                return openInterest
            if attempts > 5:
                error("Could not get OI!")
    
    

    def validate_is_option(self, tos_str=None, apikey=None):
        fields = self.get_fields_from_tos("status", tos_str, apikey)
        print(fields[0])