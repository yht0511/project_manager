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



def init():
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
    # 取消git安全目录检查
    os.system("git config --global --add safe.directory \"*\"")
    # 取消ssl验证
    os.system("git config --global http.sslVerify false")
    return Data


def save_data():
    global Data
    with open(Monitor_projects_file, "w") as f:
        json.dump(Data, f, indent=4)
        
def get_data(name):
    global Data
    for data in Data:
        if data["name"]==name:
            return data
    return None

def get_monitored_project():

    # 清空tmp文件夹
    for file in os.listdir("tmp/"):
        utils.delete_folder("tmp/"+file)

    projects=gl.projects.list(all=True)

    monitored_projects = []

    # 筛选项目
    for project in projects:
        if project.visibility in Monitor_visibility:
            if not Monitor_user or project.namespace['path'] in Monitor_user:
                # 要求有Monitor_project_file文件
                try:
                    project.files.get(file_path=Monitor_project_file,ref='main')
                except gitlab.exceptions.GitlabGetError:
                    continue
                monitored_projects.append(project.name)

    return monitored_projects

def get_project_by_name(name):
    projects=gl.projects.list(all=True)
    for project in projects:
        if project.name==name:
            return project
    return None

def get_project_info(project_name):
    # 获取项目信息
    # Gitlab
    repo_gl=get_project_by_name(project_name)
    # Github
    repo_info_gh=get_repo_info_github(project_name)
    # project文件
    project_file_info=json.loads(repo_gl.files.raw(file_path=Monitor_project_file).decode('utf-8'))
    # 合并
    project=project_file_info # 项目信息
    project["name"]=repo_gl.name if not "name" in project else project["name"] # 若文件指定，则使用文件中的name
    project["description"]=project["description"] if "description" in project and project["description"] else (repo_gl.description if repo_gl.description else Default_description) # 若文件指定，则使用文件中的description；否则使用Gitlab中的description；若Gitlab中也没有，则使用默认值
    project["repo"]=repo_gl.http_url_to_repo # Gitlab仓库地址
    project["github_repo"]=get_gh_url(project) if "github_repo" not in project else project["github_repo"] # Github仓库地址; 若文件指定，则使用文件中的github_repo
    project["namespace"]=repo_gl.namespace['name'] # 项目所属组织
    project["username"]=repo_gl.namespace['path'] # 项目所属用户
    project["image"] = Default_image if "image" not in project else project["image"] # 项目图片; 若文件指定，则使用文件中的image
    project["readme"] = "README.md" if "readme" not in project else project["readme"] # 项目README; 若文件指定，则使用文件中的readme
    # 转换时间格式
    project["created_time"]=datetime.datetime.strptime(repo_gl.created_at, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()  # 项目创建时间
    project["last_activity"]=datetime.datetime.strptime(repo_gl.last_activity_at, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()  # 项目最后活动时间
    # 获取项目的commit
    commits=repo_gl.commits.list(all=True)
    project["commits"]=[{"title":commit.title, "created_time":datetime.datetime.strptime(commit.created_at.split("+")[0], "%Y-%m-%dT%H:%M:%S.%f").timestamp()} for commit in commits]
    # 更新项目Github信息
    project.update(repo_info_gh)
    # 如果有网站,检测服务状态
    if "website" in project:
        project["service_status"] = "Live" if utils.check_website_status(project["website"]) else "Down"
    # 自动分析进度
    if "project_manager" in project and project["project_manager"]["auto_analyze_progress"]: # 允许自动分析进度
        text=False
        try:
            text=repo_gl.files.raw(file_path=project["readme"]).decode('utf-8')
        except Exception as e:
            print(f"Error: {project['name']}没有README.md")
        if text:
            project["progress"],project["status"]=utils.ask_ai_for_progress(text)
    return project

def check_sync(project):
    if "project_manager" in project and "sync" in project["project_manager"] and not project["project_manager"]["sync"]:
        return False
    if get_data(project["name"]) and get_data(project["name"])["last_activity"]==project["last_activity"] and get_data(project["name"])["commits"]==project["commits"] and get_data(project["name"])["description"]==project["description"]:
        # 不需要更新
        return False
    else:
        return True

def update_data(project):
    global Data
    # 更新项目信息
    if get_data(project["name"]):
        Data.remove(get_data(project["name"]))
    Data.append(project)
    save_data()

def sync_git(project):
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

# 登录
gl = gitlab.Gitlab(Gitlab_URL, private_token=Gitlab_TOKEN,ssl_verify=False)
gh = Github(auth=Auth.Token(Github_TOKEN))
Data = init()