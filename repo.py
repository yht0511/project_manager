import json
import git.remote
import gitlab
import requests
from settings import *
import datetime
import time
import os
import git
from github import Github
from github import Auth
import utils

# 临时文件夹
if not os.path.exists("tmp/"):
    os.mkdir("tmp/")
# 数据文件夹
if not os.path.exists("data/"):
    os.mkdir("data/")
# 读取Data
if os.path.exists(Monitor_projects_file):
    with open(Monitor_projects_file, "r") as f:
        Data = json.load(f)
else:
    Data = []

def save_data():
    with open(Monitor_projects_file, "w") as f:
        json.dump(Data, f, indent=4)
def get_data(name):
    for data in Data:
        if data["name"]==name:
            return data
    return None

# 取消git安全目录检查
os.system("git config --global --add safe.directory \"*\"")
# 取消ssl验证
os.system("git config --global http.sslVerify false")

# 登录
gl = gitlab.Gitlab(Gitlab_URL, private_token=Gitlab_TOKEN,ssl_verify=False)
gh = Github(auth=Auth.Token(Github_TOKEN))

def check_project():
    print(f"开始检查项目...")

    # 清空tmp文件夹
    for file in os.listdir("tmp/"):
        utils.delete_folder("tmp/"+file)

    projects=gl.projects.list(all=True)

    monitored_projects = []

    # 筛选项目
    for project in projects:
        if project.visibility in Monitor_visibility:
            if not Monitor_user or project.namespace['path'] in Monitor_user:
                monitored_projects.append(project)

    # 获取项目信息
    projects=[]
    for project in monitored_projects:
        # 检查项目是否有项目信息文件
        try:
            project.files.get(file_path=Monitor_project_file,ref='main')
        except gitlab.exceptions.GitlabGetError:
            continue
        pj=json.loads(project.files.raw(file_path=Monitor_project_file).decode('utf-8'))
        pj["name"]=project.name if not "name" in pj else pj["name"]
        pj["description"]=pj["description"] if "description" in pj and pj["description"] else (project.description if project.description else Default_description)
        pj["repo"]=project.http_url_to_repo
        pj["github_repo"]=get_gh_url(pj) if "github_repo" not in pj else pj["github_repo"]
        pj["namespace"]=project.namespace['name']
        pj["username"]=project.namespace['path']
        # 转换时间格式
        pj["created_time"]=datetime.datetime.strptime(project.created_at, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
        pj["last_activity"]=datetime.datetime.strptime(project.last_activity_at, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
        # 获取项目的commit
        commits=project.commits.list(all=True)
        pj["commits"]=[{"title":commit.title, "created_time":datetime.datetime.strptime(commit.created_at.split("+")[0], "%Y-%m-%dT%H:%M:%S.%f").timestamp()} for commit in commits]
        # 更新项目Github信息
        pj.update(get_repo_info_github(pj["name"]))
        projects.append(pj)
        # 如果有网站,检测服务状态
        if "website" in pj:
            pj["service_status"] = "Live" if check_website_status(pj["website"]) else "Down"
        # 图片
        pj["image"] = Default_image if "image" not in pj else pj["image"]

    print(f"共有{len(projects)}个受监测项目")
    # 更新项目
    for project in projects:
        if get_data(project["name"]) and get_data(project["name"])["last_activity"]==project["last_activity"] and get_data(project["name"])["commits"]==project["commits"] and get_data(project["name"])["description"]==project["description"]:
            # 不需要更新
            pass 
        else:
            # 更新
            print(f"更新项目{project['name']}")
            utils.send_email(f"[更新中] 项目{project['name']}", f"项目{project['name']}存在更新,正在同步至Github.")
            update_git(project)
            utils.send_email(f"[更新完成] 项目{project['name']}", f"项目{project['name']}已同步至Github.")
        # 更新项目信息
        if get_data(project["name"]):
            Data.remove(get_data(project["name"]))
        Data.append(project)
        save_data()
    
    print(f"完成.")
    
def update_git(project):
    git.Repo.clone_from(get_gl_url(project),"tmp/"+project["name"],allow_unsafe_protocols=True,allow_unsafe_options=True,)
    repo=git.Repo("tmp/"+project["name"])
    # 检测Github上是否存在该项目,不存在则创建
    try:
        repo_gh=gh.get_repo(Github_USER+"/"+transform_name(project["name"]))
    except:
        print(f"创建Github项目...")
        gh.get_user().create_repo(transform_name(project["name"]), description=project["description"], private=False)
        repo_gh=gh.get_repo(Github_USER+"/"+transform_name(project["name"]))
    repo_gh.edit(description=project["description"])
    # 强制推送
    if "github-auto" not in [remote.name for remote in repo.remotes]:
        repo.create_remote("github-auto", repo_gh.clone_url)
    print(f"推送Github项目...")
    while True:
        try:
            repo.remote("github-auto").push("*", force=True,allow_unsafe_options=True,allow_unsafe_protocols=True)
            
            break
        except Exception as e:
            print(f"推送Github项目失败:\n{e}\n重试中...")
            time.sleep(1)
    print(f"OK.")


def get_repo_info_github(name):
    try:
        repo=gh.get_repo(Github_USER+"/"+transform_name(name))
    except:
        return {}
    repo=gh.get_repo(Github_USER+"/"+transform_name(name))
    return {
        "stars":repo.stargazers_count,
        "forks":repo.forks_count,
        "issues":repo.open_issues_count,
        "watchers":repo.subscribers_count,
    }

def get_gl_url(project):
    if Follow_repo:
        return project["repo"]
    else:
        return "https://"+Gitlab_USER+":"+Gitlab_TOKEN+"@"+Gitlab_URL.split("https://")[1]+"/"+project["username"]+"/"+transform_name(project["name"])

def get_gh_url(project):
    return "https://github.com"+"/"+Github_USER+"/"+transform_name(project["name"])

def transform_name(name):
    return name.replace(" ", "-").lower()

def check_website_status(url):
    try:
        return requests.get(url).status_code==200
    except:
        return False