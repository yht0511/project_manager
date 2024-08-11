import json
import os
import time
import shutil
import repo
import web
from settings import *
import utils


web.run()
utils.send_email(f"[已启动]",f"项目管理器已启动.")
while True:
    print("开始收集项目")
    ps=repo.get_monitored_project()
    print(f"收集项目完成，共有{len(ps)}个受监测项目")
    for p in ps:
        print(f"检查项目 {p}")
        project=repo.get_project_info(p)
        if repo.check_sync(project):
            utils.send_email(f"[更新中] {p}",f"检测到项目{p}存在更新,正在同步仓库到Github.\n项目信息:\n{json.dumps(project,ensure_ascii=False,indent=4)}")
            print(f"更新项目 {p}")
            repo.sync_git(project)
            utils.send_email(f"[更新完毕] {p}",f"检测到项目{p}存在更新,已同步仓库到Github.\n项目信息:\n{json.dumps(project,ensure_ascii=False,indent=4)}")
            print("更新完毕.")
        repo.update_data(project)
        print("项目信息已保存")
    time.sleep(60)


