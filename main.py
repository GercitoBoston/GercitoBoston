import os.path
import subprocess
import pandas as pd
import gzip
import datetime
import pathlib
import re
from datetime import timedelta
from pathlib import Path
from IPython.display import display
from os import system
from os import listdir
from os.path import isfile, join
from pandasql import sqldf


menu_options = {
    1: 'Get AP-BOT connection Matrix',
    2: 'Get BI AP Master',
    3: 'Get BI Bot Master',
    4: 'Check AP Usage',
    5: 'DiscoReport',
    6: 'Get Roaming by BOT',
    7: 'Get Roaming from AP',
    8: 'Exit',
}


# define our clear function
def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


def GetApBotConnectionMatrix():
    global name
    # today_date = datetime.date.today()
    today_date = datetime.datetime(2022, 4, 30)
    yesterday = today_date - timedelta(days=1)
    yesterday_prefix = yesterday.strftime("%Y%m%d")
    eventsFound = 0
    apSeenEvent = 0
    currentRecordNo = 0
    name = ""
    master_wireless_path = Path("/logs/wireless/" + yesterday_prefix + "/master_wireless.log.gz")
    a_file = gzip.open(master_wireless_path)
    # ApUsageDf = pd.DataFrame(
    #     columns=["SiteId", "Date", "ApName", "ApMac", "Chanel", "Connections", "Clients", "Percent"])
    RssiLogEntryDf = pd.DataFrame(columns=["currentDate", "SerialNumber", "botType", "currentLocation",
                                           "BrgMac", "ApMac", "RSSI", "SNR", "chanel"])
    # brgApCountDf = pd.DataFrame(columns=["bridge", "ap", "countBriAp"])
    df = pd.DataFrame(columns=["roamTimeAp", "bridgeMac", "fromAp", "toAp"])
    with a_file as master_logs:
        for log in master_logs:
            currentRecordNo += 1
            log = log.rstrip()
            if b"<501065>" in log and b"Client" in log and b"moved from AP" in log:
                eventsFound += 1
                df = LoadRoamEvent(df, log)
            elif "RSSI log entry" in log.decode('utf-8'):
                apSeenEvent += 1
                RssiLogEntryDf = LoadApUsage(log, RssiLogEntryDf)
            print("current record %d Bot - AP correlation %d AP seen events %d" % (currentRecordNo, eventsFound,
                                                                                   apSeenEvent), end="\r")
    df["bridgeMac"] = df["bridgeMac"].str.upper()
    sortedDf = df.sort_values(by=["bridgeMac", "fromAp"])
    filePath = "eventsOfInterest.csv"
    filePath2 = "ApUsage.csv"
    if os.path.exists(filePath):
        os.remove(filePath)
    sortedDf.to_csv(filePath, encoding='utf-8')
    if os.path.exists(filePath2):
        os.remove(filePath2)
    RssiLogEntryDf.to_csv(filePath2, encoding='utf-8')
    display(df)


def LoadApUsage(log, RssiLogEntryDf):
    logInstanceListData = log.split()
    currentDate = ParseTime(logInstanceListData)
    brgBotLoc = (logInstanceListData[2].decode('utf-8')).split(".")
    SerialNumber = brgBotLoc[0]
    botType = brgBotLoc[1]
    currentLocation = brgBotLoc[2]
    BrgMac = ((logInstanceListData[4]).decode('utf-8'))[:-1]
    # if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", BrgMac.lower()):
    #     BrgMac = "NULL"
    ApMac = ((logInstanceListData[9]).decode('utf-8'))[3:]
    # if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", ApMac.lower()):
    #     ApMac = "NULL"
    RSSI = int(((logInstanceListData[10]).decode('utf-8'))[5:])
    SNR = int(((logInstanceListData[11]).decode('utf-8'))[5:-1])
    chanel = ((logInstanceListData[12]).decode('utf-8'))[8:]
    RssiLogEntryTempDf = pd.DataFrame({"currentDate": [currentDate],
                                       "SerialNumber": [SerialNumber],
                                       "botType": [botType],
                                       "currentLocation": [currentLocation],
                                       "BrgMac": [BrgMac],
                                       "ApMac": [ApMac],
                                       "RSSI": [RSSI],
                                       "SNR": [SNR],
                                       "chanel": [chanel]})
    RssiLogEntryDf = pd.concat([RssiLogEntryDf, RssiLogEntryTempDf], ignore_index=True)

    return RssiLogEntryDf


def LoadRoamEvent(df, log):
    logInstanceListData = log.split()
    roamTimeAp = ParseTime(logInstanceListData)
    bridgeMac = logInstanceListData[10].decode('utf-8')
    fromAp = logInstanceListData[14].decode('utf-8')
    toAp = logInstanceListData[17].decode('utf-8')
    df0 = pd.DataFrame({"roamTimeAp": [roamTimeAp],
                        "bridgeMac": [bridgeMac],
                        "fromAp": [fromAp],
                        "toAp": [toAp]})
    df = pd.concat([df, df0], ignore_index=True)
    return df


def CheckApUsage():
    sqlQuery = lambda q: sqldf(q, globals())
    print(sqlQuery("SELECT * FROM RssiLogEntryDf"))


def createCsvFile(param, botDF):
    sortedDf = param.sort_values(by=["InterestingEventTime"])
    filePath = botDF + ".csv"
    if os.path.exists(filePath):
        os.remove(filePath)
    sortedDf.to_csv(filePath, encoding='utf-8')


def DiscoReport():
    # today_date = datetime.date.today()
    today_date = datetime.datetime(2022, 4, 30)
    yesterday = today_date - timedelta(days=1)
    yesterday_prefix = yesterday.strftime("%Y-%m-%d")
    socketErrorDirectoryPath = Path("/mnt/nas/SRE01/RoverServices/" + yesterday_prefix + "/")
    # socketErrorDirectoryPath = Path("/mnt/nas/SRE01/RoverServices/" + "QuickTest" + "/")
    botHeartsDictionary ={}
    dfColumns = ["InterestingEventTime", "EventDescription", "currentThreadID", "BotNumber"]
    heartbeatDf = pd.DataFrame(columns=["InterestingEventTime", "EventDescription", "currentThreadID", "BotNumber"])
    botOnHand = 0
    for filename in os.listdir(socketErrorDirectoryPath):
        currentFile = os.path.join(socketErrorDirectoryPath, filename)
        if os.path.isfile(currentFile):
            baseFileName = os.path.basename(currentFile)
            fileExtension = pathlib.Path(baseFileName).suffix
            if "Client.Engine_" in baseFileName:
                with open(currentFile, "r") as inputFile:
                    for currentLine in inputFile:
                        dataInRecord = currentLine.split()
                        if dataInRecord[8] == "Rover":
                            botOnHand = dataInRecord[9]
                            size = len(dataInRecord)
                            seed = 11;
                        else:
                            botOnHand = dataInRecord[14]
                            size = len(dataInRecord)
                            seed = 22;
                        dynamicDf = ("Bot" + str(botOnHand))
                        thisDateTime = (((join(dataInRecord[0], dataInRecord[1])).strip()).replace(",", "."))[:-3]
                        eventTime = datetime.datetime.strptime(thisDateTime, "%Y-%m-%d/%H:%M:%S.%f")
                        description = ""
                        while seed < size:
                            description = description + " " + dataInRecord[seed]
                            seed += 1
                        currentThread = (dataInRecord[4])[:-1]
                        if ("Bot" + botOnHand) not in botHeartsDictionary:
                            newDic = {"InterestingEventTime":[eventTime], "EventDescription":[description],
                                      "currentThreadID":[currentThread], "BotNumber":[botOnHand]}
                            botHeartsDictionary[dynamicDf] = pd.DataFrame(newDic)
                        else:
                            (botHeartsDictionary[dynamicDf]).loc[len((botHeartsDictionary[dynamicDf]).index)] = \
                                [eventTime, description, currentThread, botOnHand]
                        print("Event found for " + botOnHand + " i.e. " + description, end="\r")
    for botDF in botHeartsDictionary:
        createCsvFile(botHeartsDictionary.get(botDF), botDF)


def ParseTime(logInstanceListData):
    dtAp = ((logInstanceListData[0].decode('utf-8')).replace('T', ' '))[:-6]
    roamTimeAp = datetime.datetime.strptime(dtAp, "%Y-%m-%d %H:%M:%S.%f")
    return roamTimeAp


def GetRoamingFrequencyByBOT():
    df1 = pd.read_csv("eventsOfInterest.csv")
    dfF = df1["bridgeMac"].value_counts()
    dfF.to_csv("FrequencyByBOT.csv", encoding='utf-8')
    display(dfF)


def RoamedFromApFrequency():
    df1 = pd.read_csv("eventsOfInterest.csv")
    dfF = df1["fromAp"].value_counts()
    dfF.to_csv("FrequencyByFromAp.csv", encoding='utf-8')
    display(dfF)


def print_menu():
    for key in menu_options.keys():
        print(key, '--', menu_options[key])


def GetArubaWlcInventory():
    try:
        with open('get_aruba_wlc_inventory.sh', 'rb') as file:
            script = file.read()
        subprocess.call(script, shell=True)
        print("SYMBETH4_BI_APMaster DONE")
    except Exception as e:
        print("I knew it")


def GetBotBrgSafInventory():
    try:
        with open('get_bot_brg_saf_inventory.sh', 'rb') as file:
            script = file.read()
        subprocess.call(script, shell=True)
        print("SYMBETH4_BI_BotMaster DONE")
    except Exception as e:
        print("I knew it")


if __name__ == '__main__':
    while True:
        print_menu()
        option = ''
        try:
            option = int(input('Enter your choice: '))
        except:
            print('Wrong input. Please enter a number ...')

        if option == 1:
            GetApBotConnectionMatrix()
        elif option == 2:
            GetArubaWlcInventory()
        elif option == 3:
            GetBotBrgSafInventory()
        elif option == 4:
            CheckApUsage()
        elif option == 5:
            DiscoReport()
        elif option == 6:
            GetRoamingFrequencyByBOT()
        elif option == 7:
            RoamedFromApFrequency()
        elif option == 8:
            print('Thanks')
            exit()
        else:
            print('Invalid option. Please enter a number between 1 and 4.')
