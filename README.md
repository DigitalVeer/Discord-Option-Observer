# DOO - Discord Option Observer

<h4 align="center">An Open Interest Tracker built on top of <a href="https://discordpy.readthedocs.io/en/stable/" target="_blank">DiscordPy</a>.</h4>

<p align="center">
  <a href="https://badge.fury.io/py/discord">
    <img src="https://badge.fury.io/py/discord.svg"
         alt="Gitter">
  </a>
</p>

`DOO` lets you easily create and manage a personalized database of market derivatives, such as calls and puts, and automatically track their daily open interest at the end of each day. This system pulls its market data from the TDAmeritrade API and uses Google Sheets to create a dashboard that users can easily view.

![output-onlinegiftools (1)](https://user-images.githubusercontent.com/8453348/139714463-4b7b2cca-5f42-4eed-b3c7-e3c1a95b9a7d.gif)


`DOO` automatically updates your Spreadsheet at the beginning of each day, or whenever you make new changes.

![spreadsheet3](https://user-images.githubusercontent.com/8453348/139717859-a4a14e8b-757b-467c-b707-b48cb667a5e7.gif)


## Features

* Automated - Track once, watch forever
  - DOO will automatically update open interest counts every day
* Real Time Updates
* Easily hostable on AWS  
* Personalized Watchlists
* Supports Calls & Puts
* Integrates Globally
* DM Responses
* Completely Free
  - Market data is very expensive. DOO allows the individual to have a little more power in their hand.
* Mobile Friendly

## How To Use

To run this application, you'll need to edit the .env file with the proper authentication. The following fields are important to understand:

```
API_KEY          - This is your API key for TDA Ameritrade
DISCORD_TOKEN    - This is your authorization token to host bots on your channel. Each user has a unique one.
DISCORD_GUILD    - This is the name of your Discord Channel.
MAIN_CHANNEL     - This is the iD of your Discord channel where you want DOO to post real time updates.
FLOW_CHANNEL     - This is the iD of your Discord channel where you want DOO to post overnight change updates.
SPREADSHEETNAME  - This is the name of your Google Spreadsheet
SHEETNAME        - This is the name of the tab of your Spreadsheet you want all information stored
PERSONAL_SHEET   - This is another tab where the bot will store users private watchlists
LEAPSHEETNAME    - Optional, you can create a seperate spreadsheet for tracking LEAPS and DOO will understand.
DEBUG=FALSE      - Only required if you want to edit the spreadsheet w/o making permanent changes
DEBUG_SHEET      - Optional, only required if DEBUG=TRUE. Creates a clone spreadsheet for development and testing.
DEBUG_CHANNEL    - If you want a seperate channel private to you for debugging, you can put it here.
```

A TDAmeritrade Authentication token can be created for free [here](https://developer.tdameritrade.com/apis)

Once you edit the .env files with your proper tokens, you can simply run the application with

```
py3 main.py
```
