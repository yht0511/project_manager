import shutil
import os
import stat
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
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
    message = MIMEText(message, 'plain', 'utf-8')
    message['From'] = formataddr((settings.mail_name, settings.mail_user))
    message['To'] = formataddr(("管理员", settings.mail_targets[0]))
    message['Subject'] = Header(subject, 'utf-8')
    
    for i in range(3):
        try:
            smtpObj = smtplib.SMTP(settings.mail_host, 587)
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