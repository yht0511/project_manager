import hashlib
import json
import shutil
import os
import stat
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import json
import requests
import settings

def delete_folder(file_path):
    # 删除文件夹
    while 1:
        if not os.path.exists(file_path):
            break
        try:
            shutil.rmtree(file_path)
        except PermissionError as e:
            err_file_path = str(e).split("\'", 2)[1]
            if os.path.exists(err_file_path):
                os.chmod(err_file_path, stat.S_IWUSR)
    return True


def send_email(subject,message):
    message+="\n[本消息由自动化程序发送]\n天创实验室(TECLAB)"
    
    message = MIMEText(message, 'plain', 'utf-8')
    message['From'] = formataddr((settings.mail_name, settings.mail_user))
    message['To'] = formataddr(("管理员", settings.mail_targets[0]))
    message['Subject'] = Header(subject, 'utf-8')
    
    for i in range(3):
        try:
            smtpObj = smtplib.SMTP(settings.mail_host, 587,timeout=10)
            smtpObj.starttls()
            smtpObj.login(settings.mail_user,settings.mail_pass)  
            smtpObj.sendmail(settings.mail_user, settings.mail_targets, message.as_string())
            print("邮件发送成功")
            return True
        except Exception as e:
            print(e)
    print("Error: 无法发送邮件")
    return False

def check_website_status(url):
    try:
        return requests.get(url).status_code==200
    except:
        return False
    
    
def ask_ai_for_progress(text):
    # 使用AI分析进度
    # 检查md5是否存在
    md5=hashlib.md5(text.encode()).hexdigest()
    if os.path.exists(f'cache/ai/{md5}.json'):
        data=json.loads(open(f'cache/ai/{md5}.json','r',encoding="utf-8").read())
    else:
        data=json.loads(get_chat_gpt_response(text))
        f=open(f'cache/ai/{md5}.json','w',encoding='utf-8')
        f.write(json.dumps(data))
        f.close()
    return data["progress"],data["status"]
    
def get_chat_gpt_response(prompt,system_prompt=settings.gpt_prompt,model=settings.gpt_model):
    url = "https://api.gptgod.online/v1/chat/completions"
    headers = {
        "Authorization": settings.gpt_authorization_code,
        "Content-Type": "application/json"
    }
    prompt=system_prompt+prompt
    data = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}]+[{"role": "user", "content": prompt}]
    }
    while True:
        try:
            print("请求ChatGPT:")
            response = requests.post(url, headers=headers, json=data,proxies=settings.gpt_proxies)
            break
        except Exception as e:
            print("Error: AI请求失败")
            print(e)
            print("重试中...")
    res=response.json()
    print(res)
    return res['choices'][0]['message']['content']


if not os.path.exists("cache/"):
    os.mkdir("cache/")
if not os.path.exists("cache/ai/"):
    os.mkdir("cache/ai/")