

# Gitlab/Github
Gitlab_URL = '你的Gitlab地址'
Gitlab_USER = "Gitlab用户名"
Gitlab_TOKEN = 'Gitlab Token'
Github_USER = 'Github用户名'
Github_TOKEN = 'Github Token'

# Monitor
Monitor_visibility = ["public", "internal"]
Monitor_user = [Gitlab_USER] # None for all users
Monitor_project_file=".teclab/project.json"
Monitor_projects_file="data/projects.json"

# Clone
Follow_repo = False # 克隆仓库时是否使用仓库的默认地址
Default_description = "No description."
Default_image = "默认图片地址"

# Display
Web_file_path = "web/"

# Mail
mail_host = "smtp.163.com"
mail_user = ""
mail_pass = ""
mail_targets = [""]
mail_name = "TECLAB-项目管理器"

# 项目分析
gpt_model = "gpt-4"
gpt_prompt = """
*** 以下是一个项目的readme文件内容,我需要你根据文本信息,给出你判断出的这个项目的开发进度(百分比,尽可能精确)以及项目状态(分为“构思”、“开发”、“维护”、“归档”、“中止”)，构思是指项目还没有正式开始建设，只有基本的雏形和方案，没有一个阶段目标被完成；开发是指正在编写代码、设计模型或进行实验；维护是指开发已完毕，项目已经运行，平时对项目进行小修小补；归档是指项目已经不再维护；中止是指在开发或构思阶段决定放弃该项目；而开发进度是指”开发的进度“，若为构思，则进度为0；若为维护或归档，则进度为100；若为中止或开发，需要你根据readme中的各种信息来判断项目进行到何种程度.不要输出任何多余的话，直接使用json格式输出，格式如下: {"status": 项目状态,"progress": 开发进度} 不要使用Markdown!!!直接返回json文本!!!***
"""
gpt_authorization_code = ""
gpt_proxies=None