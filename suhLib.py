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
import os

global logfile

def settings1C():
    env = os.environ
    _cf = {'wcAddr' : env['C1.clstr']
        , 'tcAddr'  : env['C1.clstrTST']
        , 'ibAuth'  : (env['C1.IBadmin'], env['C1.IBpasswd'])
        , 'clAuth'  : (env['C1.clstAdmin'], env['C1.clstPasswd'])
        }
    return _cf

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

def _logfile_handler(_log_file_name):
    # _log_file_name = 'c:/1c/cmd/log/FZ.deny'
    try:
        return open(_log_file_name, mode='a', encoding='UTF-8')
    except FileNotFoundError:
        return sys.stdout

def logg(text, lf_name='LOG.LOG'):
    _log = _logfile_handler(lf_name)
    _log.write(re.sub(r'\<[^>]*\>', '', text)+'\n')

# ***************************************************************************
if __name__ == '__main__':
    inform('Пример отправки','Вам пришло это письмо из-за того, что библиотека suhLib.py была запущена как самостоятельный скрипт<br><b>Не отвечайте на это письмо!!!!</b> TEXT ',5)

