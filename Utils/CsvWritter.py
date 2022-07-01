import os
from pathlib import Path

def CsvWritter(fileWithPath, actualDataFrame):
    filePath = Path(fileWithPath + ".csv")
    targetDirectory = os.path.dirname(filePath)
    if not os.path.exists(targetDirectory):
        os.makedirs(targetDirectory)
    if os.path.exists(filePath):
        os.remove(filePath)
    actualDataFrame.to_csv(filePath, encoding='utf-8')