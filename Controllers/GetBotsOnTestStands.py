# gets the path as a parameter and returns a pandas dataframe

import concurrent.futures as cf
import pandas as pd
import datetime
import os
from sqlalchemy import true
from os.path import isfile, join
from Utils.CsvWritter import CsvWritter
from Utils.YesterdayPrefix import YesterdayPrefix



def LoadBotsOnTestStands(currentPath):
    standDic = {}
    with cf.ProcessPoolExecutor() as executor:
        for filenameParallel in os.listdir(currentPath):
            absolutePath = os.path.join(currentPath, filenameParallel)
            currentFileBaseName = os.path.basename(absolutePath)
            if "Client.MM-Test Stand" in currentFileBaseName:
                standDic[currentFileBaseName] = executor.submit(LoadLogsForTestStand, absolutePath)
    executor.shutdown(wait=true)
    for dataFrameName in standDic:
        actualDf = (standDic.get(dataFrameName)).result()
        sortedDf = actualDf.sort_values(by=["FirstDateTime"])
        yesterdayDate = YesterdayPrefix()
        filenameICanLiveWith = dataFrameName[: -(len(dataFrameName) - 23)]
        filePath = "/LOG2/wireless/" + yesterdayDate + "/" + filenameICanLiveWith
        CsvWritter(filePath, sortedDf)



def LoadLogsForTestStand(filenameParallel):
    standDf = pd.DataFrame(columns=["BotNumber", "FirstDateTime", "LastDateTime", "Duration"])        
    longFileName = os.path.basename(filenameParallel)
    fileName = longFileName[: -(len(longFileName) - 23)]
    try:
        countLines = 0
        numberOfLines = 0
        limitPrint = 10000
        with open(filenameParallel, "r") as inputFile:
            numberOfLines = len(inputFile.readlines())
            print("Records in  " + fileName + " = " + str(numberOfLines))
            inputFile.seek(0, 0)
            for currentLine in inputFile:
                countLines += 1
                if limitPrint >= limitPrint:
                    print("Analizing " + fileName + " line No " + str(countLines)+"/"+str(numberOfLines))
                    limitPrint += 10000
                    if limitPrint > numberOfLines:
                        limitPrint = numberOfLines
                dataInRecord = currentLine.split()
                if "Rover" in dataInRecord:
                    if dataInRecord[13] == "Rover":
                        thisDateTime = (((join(dataInRecord[0], dataInRecord[1])).strip()).replace(",", "."))[:-3]
                        firstDateTime = datetime.datetime.strptime(thisDateTime, "%Y-%m-%d/%H:%M:%S.%f")    
                        botOnHand = dataInRecord[14]
                        if botOnHand not in standDf.values:
                            duration = firstDateTime - firstDateTime
                            lastDateTime = firstDateTime
                            standDf.loc[len((standDf.index))] = [botOnHand, firstDateTime, lastDateTime, duration]
                        else:
                            currentIndex = ((standDf.index[standDf["BotNumber"] == botOnHand]).to_list())[0]
                            standDf.at[currentIndex, "LastDateTime"] = firstDateTime
                            previusTime = standDf.at[currentIndex, "FirstDateTime"]
                            standDf.at[currentIndex, "Duration"] = firstDateTime - previusTime
    except Exception as e:
        print(e)
    print("\n")
    return  standDf