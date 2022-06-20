from fileinput import filename
import os.path
import subprocess
import pandas as pd
import gzip
import datetime
import pathlib
import concurrent.futures as cf
import logging
import enlighten
import math
import numpy as np
import time
import threading
import re
import linecache
from flask import Flask
from flask_restful import Resource, Api, reqparse
from datetime import timedelta
from pathlib import Path
from IPython.display import display
from os import system
from os import listdir
from os.path import isfile, join
from pandasql import sqldf
from sqlalchemy import true

from Classes.ConnectionMatrix import ConnectionMatrix

logger_format = '%(asctime)s:%(threadName)s:%(message)s'
logging.basicConfig(format=logger_format, level=logging.INFO, datefmt="%H:%M:%S")
manager = enlighten.get_manager()
progressDictionary = {}
global filesDic
app = Flask(__name__)
api = Api(app)



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




def GetApBotConnectionMatrix():
    # today_date = datetime.date.today()
    today_date = datetime.datetime(2022, 4, 30)
    yesterday = today_date - timedelta(days=1)
    yesterday_prefix = yesterday.strftime("%Y%m%d")
    master_wireless_path = Path("/logs/wireless/" + yesterday_prefix + "/master_wireless.log.gz")
    eventsFound = 0
    apSeenEvent = 0
    currentRecordNo = 0
    linesJobsDic = {}
    startLine = 1
    nextLine = 1000000
    groupOFLinesDf = pd.DataFrame(columns=["StartLine", "EndLine"])
    numberOfLines = sum(1 for i in gzip.open(master_wireless_path, 'rb'))
    while nextLine < numberOfLines:
        groupOFLinesDf.loc[len(groupOFLinesDf.index)] = [startLine, nextLine]
        startLine = nextLine + 1
        nextLine = nextLine + 1000000
    groupOFLinesDf.loc[len(groupOFLinesDf.index)] = [startLine, numberOfLines]
    with cf.ProcessPoolExecutor() as executorMaster:
        for lineGroupParallel in groupOFLinesDf.itertuples():
            startFrom = lineGroupParallel[1]
            endAt = lineGroupParallel[2]
            lineGroup = "from"+str(startFrom)+"to"+str(endAt)
            linesJobsDic[lineGroup] = executorMaster.submit(LoadMasterLogs, startFrom, endAt, master_wireless_path)
    executorMaster.shutdown(wait=true)
    
    # ApUsageDf = pd.DataFrame(
    #     columns=["SiteId", "Date", "ApName", "ApMac", "Chanel", "Connections", "Clients", "Percent"])
    RssiLogEntryDf = pd.DataFrame(columns=["currentDate", "SerialNumber", "botType", "currentLocation",
                                           "BrgMac", "ApMac", "RSSI", "SNR", "chanel"])
    # brgApCountDf = pd.DataFrame(columns=["bridge", "ap", "countBriAp"])
    # df = pd.DataFrame(columns=["roamTimeAp", "bridgeMac", "fromAp", "toAp"])
    # with currentFile as master_logs:
    #     for log in master_logs:
    #         currentRecordNo += 1
    #         log = log.rstrip()
    #         if b"<501065>" in log and b"Client" in log and b"moved from AP" in log:
    #             eventsFound += 1
    #             df = LoadRoamEvent(df, log)
    #         elif "RSSI log entry" in log.decode('utf-8'):
    #             apSeenEvent += 1
    #             RssiLogEntryDf = LoadApUsage(log, RssiLogEntryDf)
    #         print("current record %d Bot - AP correlation %d AP seen events %d" % (currentRecordNo, eventsFound,
    #                                                                                apSeenEvent), end="\r")
    # df["bridgeMac"] = df["bridgeMac"].str.upper()
    # sortedDf = df.sort_values(by=["bridgeMac", "fromAp"])
    # filePath = "eventsOfInterest.csv"
    # filePath2 = "ApUsage.csv"
    # if os.path.exists(filePath):
    #     os.remove(filePath)
    # sortedDf.to_csv(filePath, encoding='utf-8')
    # if os.path.exists(filePath2):
    #     os.remove(filePath2)
    # RssiLogEntryDf.to_csv(filePath2, encoding='utf-8')
    # display(df)


def LoadMasterLogs(startFrom, endAt, master_wireless_path):
    # RssiLogEntryDf = pd.DataFrame(columns=["currentDate", "SerialNumber", "botType", "currentLocation",
    #                                        "BrgMac", "ApMac", "RSSI", "SNR", "chanel"])
    Roamdf = pd.DataFrame(columns=["roamTimeAp", "bridgeMac", "fromAp", "toAp"])
    with gzip.open(master_wireless_path) as currentFile:
        while startFrom <= endAt:
            log = linecache.getline(currentFile, startFrom)
            log = log.rstrip()
            if b"<501065>" in log and b"Client" in log and b"moved from AP" in log:
                LoadRoamEvent(Roamdf, log)
            startFrom += 1


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
    df.loc[len(df.index)] = [roamTimeAp, bridgeMac, fromAp, toAp]
    return df


def CheckApUsage():
    sqlQuery = lambda q: sqldf(q, globals())
    print(sqlQuery("SELECT * FROM RssiLogEntryDf"))


def createCsvFile(param, botDF):
    filePath = botDF + ".csv"
    if os.path.exists(filePath):
        os.remove(filePath)
    param.to_csv(filePath, encoding='utf-8')


def DiscoReport():
    # today_date = datetime.date.today()
    today_date = datetime.datetime(2022, 4, 30)
    yesterday = today_date - timedelta(days=1)
    yesterday_prefix = yesterday.strftime("%Y-%m-%d")
    socketErrorDirectoryPath = Path("/mnt/nas/SRE01/RoverServices/" + yesterday_prefix)
    # socketErrorDirectoryPath = Path("/mnt/nas/SRE01/RoverServices/JustForTesting")
    botHeartsDictionary = {}
    filesJobsDic = {}
    with cf.ProcessPoolExecutor() as executor:
        for filenameParallel in os.listdir(socketErrorDirectoryPath):
            currentFileBaseName = os.path.basename(filenameParallel)
            filesJobsDic[currentFileBaseName] = executor.submit(LoadEngineLogs, filenameParallel, socketErrorDirectoryPath)
    executor.shutdown(wait=true)
    for dic in filesJobsDic:
        cosa = filesJobsDic.get(dic)
        cosa2 = cosa.result()
        dataFR = cosa2.get(dic)
        try:
            if dataFR != None:
                for botDic in dataFR:
                    oraDf = dataFR.get(botDic)
                    if botDic in botHeartsDictionary.keys():
                        botHeartsDictionary[botDic] = pd.concat([botHeartsDictionary.get(botDic), oraDf],
                                                                ignore_index=True)
                    else:
                        botHeartsDictionary[botDic] = oraDf
        except Exception as e:
            print(e)
    manager.stop()
    if "BotSocketErrors" in botHeartsDictionary.keys():
        disconnectCandidates = botHeartsDictionary.get("BotSocketErrors")
        filterDisconnectsDf = disconnectCandidates.loc[(disconnectCandidates["DiscoType"] == "disconnect")]
        filterFlickerDf = disconnectCandidates.loc[(disconnectCandidates["DiscoType"] == "flicker")]
        filterRestartDf = disconnectCandidates.loc[(disconnectCandidates["DiscoType"] == "restart")]
        frames = [filterDisconnectsDf, filterFlickerDf, filterRestartDf]
        finalDisconnectReport = pd.concat(frames)
        botHeartsDictionary["FilteredDisco"] = filterDisconnectsDf
        botHeartsDictionary["FilteredFlicker"] = filterFlickerDf
        botHeartsDictionary["FilteredRestart"] = filterRestartDf
        for currentIndex in (finalDisconnectReport).index:
            currentBot = finalDisconnectReport["AffectedBot"][currentIndex]
            botsHealth = botHeartsDictionary[currentBot]
            aliveMask = (botsHealth["EventTime"] > finalDisconnectReport["EventTime"][currentIndex]) & (botsHealth["EventTime"] < finalDisconnectReport["EndTime"][currentIndex]) & (botsHealth["Health"] == "healthy")
            evidenceDf = botsHealth.loc[aliveMask]
            aliveMask2 = (botsHealth["EventTime"] < finalDisconnectReport["EventTime"][currentIndex]) & (botsHealth["LastHealthyMoment"] > finalDisconnectReport["EndTime"][currentIndex]) & (botsHealth["Health"] == "healthy")
            evidenceDf2 = botsHealth.loc[aliveMask2]
            aliveMask3 = (botsHealth["EventTime"] < finalDisconnectReport["EventTime"][currentIndex]) & (botsHealth["LastHealthyMoment"] > finalDisconnectReport["EventTime"][currentIndex]) & (botsHealth["Health"] == "arrhythmia")
            evidenceDf3 = botsHealth.loc[aliveMask3]
            if len(evidenceDf) > 0 or len(evidenceDf2) > 0:
                finalDisconnectReport.at[currentIndex, "IsWireless"] = "Not Wireless"
            elif len(evidenceDf3) > 0:
                finalDisconnectReport.at[currentIndex, "IsWireless"] = "Is Wireless"

        botHeartsDictionary["DiscoReport"+yesterday_prefix] = finalDisconnectReport
            
    for botDF in botHeartsDictionary:
        botToSort = botHeartsDictionary.get(botDF)
        if(botDF == "BotSocketErrors" or botDF == "FilteredDisco" or botDF == "DiscoReport"+yesterday_prefix):
            sortedBot = botToSort.sort_values(by=["DiscoType", "AffectedBot", "EventTime"])
        else:
            sortedBot = botToSort.sort_values(by=["EventTime"])
        createCsvFile(sortedBot, botDF)


def LoadEngineLogs(filename, socketErrorDirectoryPath):
    filesDic = {}
    currentFile = os.path.join(socketErrorDirectoryPath, filename)
    if os.path.isfile(currentFile):
        baseFileName = os.path.basename(currentFile)
        fileExtension = pathlib.Path(baseFileName).suffix
        if "Client.Engine_" in baseFileName and fileExtension != ".txt":
            print("processing file ",fileExtension)
            filesDic[baseFileName] = BotHeartHealth(currentFile)

        if "Rover" in baseFileName and "Comms" in baseFileName and fileExtension == ".txt":
            print("processing file ",baseFileName)
            filesDic[baseFileName] = SocketErrors(currentFile)
    return filesDic


def BotHeartHealth(currentFile):
    multyThreadDictionary = {}
    pulse = 2
    health = "Healthy"
    rhythmTime = 2
    description = ""
    lastHealthyMoment = datetime.datetime.now()
    numberOfLines = sum(1 for i in open(currentFile, 'rb'))
    baseFileName = os.path.basename(currentFile)
    currentLineNo = 0
    fileExtension = pathlib.Path(baseFileName).suffix
    progressDictionary[baseFileName] = manager.counter(total=numberOfLines, desc="File " + fileExtension, unit="ticks", color="red")
    try:
        with open(currentFile, "r") as inputFile:
            for currentLine in inputFile:
                currentLineNo += 1
                dataInRecord = currentLine.split()
                if dataInRecord[8] == "Rover":
                    botOnHand = dataInRecord[9]
                else:
                    botOnHand = dataInRecord[14]
                dynamicDf = ("BOT" + str(botOnHand))
                if dynamicDf not in multyThreadDictionary:
                    if dataInRecord[8] == "Rover":
                        botOnHand = dataInRecord[9]
                        size = len(dataInRecord)
                        seed = 11
                    else:
                        size = len(dataInRecord)
                        seed = 22
                    thisDateTime = (((join(dataInRecord[0], dataInRecord[1])).strip()).replace(",", "."))[:-3]
                    eventTime = datetime.datetime.strptime(thisDateTime, "%Y-%m-%d/%H:%M:%S.%f")
                    currentThread = (dataInRecord[4])[:-1]
                    while seed < size:
                        description = description + " " + dataInRecord[seed]
                        seed += 1
                    lastHealthyMoment = eventTime
                    health = "healthy"
                    newDic = {"EventTime": [eventTime], "LastHealthyMoment": lastHealthyMoment,
                            "EventDescription": [description], "currentThreadID": [currentThread],
                            "BotNumber": [botOnHand], "RhythmTime": [rhythmTime], "Health": [health]}
                    multyThreadDictionary[dynamicDf] = pd.DataFrame(newDic)
                else:
                    lastHealthyMoment = (multyThreadDictionary[dynamicDf])['LastHealthyMoment'].iloc[-1]
                    currentPulse = round((eventTime - lastHealthyMoment).total_seconds())
                    if currentPulse > rhythmTime:
                        description = ""
                        while seed < size:
                            description = description + " " + dataInRecord[seed]
                            seed += 1
                        health = "arrhythmia"
                        lastHealthyMoment = (multyThreadDictionary[dynamicDf])['LastHealthyMoment'].iloc[-1]
                        (multyThreadDictionary[dynamicDf]).loc[len((multyThreadDictionary[dynamicDf]).index)] = \
                            [lastHealthyMoment, eventTime, description, currentThread, botOnHand, rhythmTime, health]
                    elif currentPulse <= rhythmTime:
                        lastHealth = (multyThreadDictionary[dynamicDf])['Health'].iloc[-1]
                        if lastHealth == "healthy":
                            lastIndex = (len((multyThreadDictionary[dynamicDf]).index)) - 1
                            (multyThreadDictionary[dynamicDf]).at[lastIndex, "LastHealthyMoment"] = eventTime
                        else:
                            health = "healthy"
                            description = ""
                            while seed < size:
                                description = description + " " + dataInRecord[seed]
                                seed += 1
                            lastHealthyMoment = eventTime
                            (multyThreadDictionary[dynamicDf]).loc[len((multyThreadDictionary[dynamicDf]).index)] = \
                                [eventTime, lastHealthyMoment, description, currentThread, botOnHand, rhythmTime, health]
                    # else:
                    #     lastIndex = (len((multyThreadDictionary[dynamicDf]).index)) - 1
                    #     lastHealth = (multyThreadDictionary[dynamicDf])['Health'].iloc[-1]
                    #     if lastHealth != "healthy":
                    #         health = "healthy"
                    #         description = ""
                    #         while seed < size:
                    #             description = description + " " + dataInRecord[seed]
                    #             seed += 1
                    #         lastHealthyMoment = eventTime
                    #         (multyThreadDictionary[dynamicDf]).loc[len((multyThreadDictionary[dynamicDf]).index)] = \
                    #             [eventTime, lastHealthyMoment, description, currentThread, botOnHand, rhythmTime, health]
                    #     else:
                    #         (multyThreadDictionary[dynamicDf]).at[lastIndex, "LastHealthyMoment"] = eventTime
                    #         (multyThreadDictionary[dynamicDf]).at[lastIndex, "Health"] = "healthy"
                # percentage = str(round((currentLineNo * 100) / numberOfLines))
                # print("complite file " + fileExtension + " " + percentage + "%\n")
                (progressDictionary[baseFileName]).update()
    except Exception as e:
        print(e)
    print("complite file " + fileExtension + "\n")
    return  multyThreadDictionary


def SocketErrors(currentFile):
    multyThreadDictionary = {}
    suspiciousEventsFound = 0
    socketErrorFound = 0
    numberOfLines = sum(1 for i in open(currentFile, 'rb'))
    baseFileName = os.path.basename(currentFile)
    discoType = "TBD"
    isWireless = "TBD"
    currentLineNo = 0
    progressDictionary[baseFileName] = manager.counter(total=numberOfLines, desc="File " + baseFileName, unit="ticks", color="blue")
    try:
        with open(currentFile, "r") as inputFile:
            eventsBetween = 0
            for currentLine in inputFile:
                (progressDictionary[baseFileName]).update()
                if "OnReceive SocketError" in currentLine:
                    socketErrorFound = 1
                    eventsBetween += 1
                    suspiciousEventsFound += 1
                    dataInRecord = currentLine.split()
                    thisDateTime = (((join(dataInRecord[0], dataInRecord[1])).strip()).replace(",", "."))[:-3]
                    startTime = datetime.datetime.strptime(thisDateTime, "%Y-%m-%d/%H:%M:%S.%f")
                    disconnectThread = (dataInRecord[4])[:-1]
                    logType = dataInRecord[6]
                    affectedBot = (dataInRecord[8])[1:-1]
                    dynamicDfName = "SocketErrorFor" + affectedBot
                    typeOfError = dataInRecord[15]
                elif "Connecting -> Connected : Established" in currentLine:
                    dataInRecord = currentLine.split()
                    thisDateTime = (((join(dataInRecord[0], dataInRecord[1])).strip()).replace(",", "."))[:-3]
                    endTime = datetime.datetime.strptime(thisDateTime, "%Y-%m-%d/%H:%M:%S.%f")
                    reconnectThread = (dataInRecord[4])[:-1]
                    if socketErrorFound:
                        lenOfDisco = endTime - startTime
                        totalSeconds = lenOfDisco.total_seconds()
                        # if totalSeconds < 5:
                        #     discoType = "Connecting"
                        if 5 <= totalSeconds <= 25:
                            discoType = "flicker"
                        elif 25 < totalSeconds <= 60:
                            discoType = "disconnect"
                        elif totalSeconds > 60:
                            discoType = "restart"

                    else:
                        totalSeconds = 0
                        discoType = "Orphan Connection Established"
                        affectedBot = (dataInRecord[8])[1:-1]
                        startTime = endTime
                        disconnectThread = reconnectThread
                        logType = dataInRecord[6]
                        typeOfError = "none"
                    LoadDf(affectedBot, multyThreadDictionary, discoType, isWireless, disconnectThread, endTime, eventsBetween, logType,
                        reconnectThread, startTime, totalSeconds, typeOfError)
                    # print("disco found for " + affectedBot, end="\r")
                    eventsBetween = 0
                    socketErrorFound = 0
                else:
                    if eventsBetween > 0:
                        eventsBetween += 1
    except Exception as e:
        print(e)
    if socketErrorFound:
        endTime = startTime
        eventsBetween = 0
        reconnectThread = 0
        totalSeconds = 0
        typeOfError = "Unknown"
        discoType = "Orphan error"
        LoadDf(affectedBot, multyThreadDictionary, discoType, isWireless, disconnectThread, endTime, eventsBetween, logType,
               reconnectThread, startTime, totalSeconds, typeOfError)
    # botHeartsDictionary["BotSocketErrors"] = botHeartsDictionary["BotSocketErrors"].sort_values(by=["AffectedBot",
    #                                                                                                "StartTime"])
    return multyThreadDictionary


def LoadDf(affectedBot, botHeartsDictionary, discoType, isWireless, disconnectThread, endTime, eventsBetween, logType,
           reconnectThread, startTime, totalSeconds, typeOfError):
    if "BotSocketErrors" not in botHeartsDictionary:
        newDic = {"AffectedBot": [affectedBot], "EventTime": [startTime],
                  "DisconnectThread": [disconnectThread], "LogType": [logType],
                  "TypeOfError": [typeOfError], "EndTime": [endTime], "ReconnectThread": [reconnectThread],
                  "LenOfDisco": [totalSeconds], "DiscoType": [discoType], "IsWireless": isWireless, "EventsBetween": eventsBetween}
        botHeartsDictionary["BotSocketErrors"] = pd.DataFrame(newDic)
    else:
        (botHeartsDictionary["BotSocketErrors"]).loc[len((botHeartsDictionary["BotSocketErrors"]).index)] \
            = [affectedBot, startTime, disconnectThread, logType, typeOfError, endTime, reconnectThread,
               totalSeconds, discoType, isWireless, eventsBetween]


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
        # app.run()  # run our Flask app
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
