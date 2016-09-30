# coding=utf-8
# Copyright (c) 2016 VSCraft. All rights ...

"""
Модуль для общих процедур

Функция inform отправляет извещения на э-почту мне
"""
import smtplib
from email.headerregistry import Address
# from email.message import EmailMessage
from email.mime.text import MIMEText
from email.utils import make_msgid
import re

global logfile

def _setEmergencyTitle(l):
    if l<1:
        return 'INFO'
    elif l==1:
        return 'NOTE'
    elif l==2:
        return 'WARN'
    elif l==3:
        return 'ERRR'
    elif l==4:
        return 'CRIT'
    elif l>4:
        return 'PZTZ'

def inform(s='', t='', l=0):
    """ Отправляет текст автору

    модуль принимает на вход тему(s), текст сообщения(t) и уровень важности(l) отправляет его
    электронной почтой мне.
    Уровень важности: от 0-инфо до 5-ппц
    >>>inform('hi there!', 'the disaster happen', 4)
    """
    nrm_list=['sukhikh@moscollector.ru']
    srz_list=['79636755975@sms.beemail.ru']
    msg = MIMEText(t, 'html')
    sbj = [ _setEmergencyTitle(l),':',s]
    sutr = " ".join(sbj)
    msg['Subject'] = sutr
    msg['From'] = 'fodo-svc@moscollector.ru'
    msg['To'] = ";".join(nrm_list) if l<4 else ";".join(nrm_list+srz_list)
    msg.set_charset='utf-8'
   # msg.set_type='text/html'
    msg.set_content=t+" TOT!"
    with smtplib.SMTP('mail') as sm:
        sm.send_message(msg)
        sm.quit()

def _logfilename():
    return 'c:/1c/cmd/log/FZ.deny'

def logg(text):
    _log = open(_logfilename(), 'a')
    print(re.sub(r'\<[^>]*\>', '', text), file=_log)

# ***************************************************************************
if __name__ == '__main__':
    inform('Пример отправки','<b>Не отвечайте на это письмо!!!!</b> TEXT ',5)
