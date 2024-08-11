import os
import time
import shutil
import repo
import web
from settings import *


web.run()
while True:
    print("Checking projects...")
    try:
        repo.check_project()
    except Exception as e:
        print("Checking Error.")
        print(e)
    time.sleep(60)


