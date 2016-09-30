"""
Скрипт приводит в порядок флаг блокировки регламентных заданий

Скрипт запускается без параметров каждый час из шедулера и
- на тестовом кластере устанавливает флаг блокировки на все ИБ
- на рабочем кластере снимает флаг блокировки со всех ИБ
"""

# ☐ В init вызывать собственное исключение при ошибке

import pythoncom
import win32com.client
import os
from datetime import datetime
import suhLib

def version:
    return '1.1.4'

def init():
    global err_text, cfg
    if not os.environ['USERNAME'].lower() in ('tasker', 'goblin'):
        err_text = err_text + '!!! попытка запустить скрипт от неподходящего пользователя провалилась !!!'
        return False
    cfg = suhLib.settings1C()
    return True

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S ")

def set_regl_task(test_cluster = True):
    global tm_start, err_text, eml_text, email, login


    def findIBdecriptionByIBName(ibName, Agent, Cluster):
        ibDescriptions = Agent.GetInfoBases(Cluster)
        for ibd in ibDescriptions:
            if ibd.Name.upper() == ibName.upper():
                return ibd
        return None

    def setDenialState(ib, conn, state):
        if ib.ScheduledJobsDenied == state:
            return 'ok'
        try:
            ib.ScheduledJobsDenied = state
            conn.UpdateInfoBase(ib)
            return 'ok'
        except BaseException as err:
            return 'error'

    clAddr = cfg['tcAddr'] if test_cluster else cfg['wcAddr']
    clAuth = cfg['clAuth']
    ibAuth = cfg['ibAuth']

    pythoncom.CoInitialize()
    V83 = win32com.client.Dispatch("V83.COMConnector")
    Agent = V83.ConnectAgent(clAddr)
    Clsts = Agent.GetClusters()
    for cls in Clsts:
        print(now(), "CLST> ", cls.ClusterName, "/", cls.HostName, "/", cls.MainPort)
        eml_text = eml_text + '\n\r'+now() + "<h5>CLST> " + cls.ClusterName + "/" + cls.HostName + "/" + str(cls.MainPort) +'</h5>'
        Agent.Authenticate(cls, *clAuth)
        Prcss = Agent.GetWorkingProcesses(cls)
        for prc in Prcss:
            if not prc.Running:
                continue
            WrPrc = V83.ConnectWorkingProcess('tcp://' + str(cls.HostName) + ":" + str(prc.MainPort))
            WrPrc.AddAuthentication(*ibAuth)
            Bases = WrPrc.GetInfoBases()
            for bse in Bases:
                if bse.Name.upper()+'@'+cls.ClusterName.upper() in ar_prced:  # base already processed
                    continue
                prv = 'V' if bse.ScheduledJobsDenied else 'X'
                atm = 'V' if test_cluster else 'X'
                ok = setDenialState(bse, WrPrc, test_cluster)
                # bse.ScheduledJobsDenied = False;
                # WrPrc.UpdateInfoBase(bse)
                print(now(), '  BSE>>', cls.HostName.upper()+":"+str(prc.MainPort)+ "/" +bse.Name+'\t', prv,'->',atm,ok)
                eml_text = eml_text +'\n\r'+ '<li>'+now() + '  BSE>>' + cls.HostName.upper() + ":" + str(prc.MainPort) + "/<b style='color:navy'>" + bse.Name.upper() +'</b> '+ prv + ' ➜ ' + atm +' ('+ ok+')'
                ar_prced.append(bse.Name.upper()+'@'+cls.ClusterName.upper())
try:
    tm_start = datetime.now()
    ar_prced = []
    eml_text = ''
    err_text = ''
    email = True
    login = True
    cfg = dict()
    if init():
        set_regl_task()
        set_regl_task(False)
    print('done', (datetime.now() - tm_start).seconds, 'sec.')
except BaseException as err:
    print(err)
    err_text = err_text + now()+'error occured '+str(err)
    eml_text = eml_text +'\n\r'+ err_text
finally:
    eml_text = eml_text + '\n\r'+'<p>done ' + str((datetime.now() - tm_start).seconds) + ' sec.</p>'
    if login:
        suhLib.logg(eml_text, 'c:/1c/cmd/log/LOG.log')
    if err_text:
        print(err_text)
        suhLib.inform('Setting reglament task enabling flag', err_text, 2)
    else:
        if email:
            suhLib.inform('Test scheduled task report', eml_text, 1)

