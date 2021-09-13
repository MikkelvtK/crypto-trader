import time
import os
import datetime as dt

while True:

    if dt.datetime.now().second == 0:
        os.system("datalogger.py")
