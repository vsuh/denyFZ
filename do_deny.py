"""
Скрипт приводит в порядок флаг блокировки регламентных заданий

Скрипт запускается без параметров каждый час из шедулера и
- на тестовом кластере устанавливает флаг блокировки на все ИБ
- на рабочем кластере снимает флаг блокировки со всех ИБ
"""

import pythoncom
import win32com.client
import os
from datetime import datetime
import suhLib

global varz, npp, tm_start, err_text, eml_text, email, login
varz = {'clAuth':('adm','321'), 'agAuth':('adm','321'),'w_cl':'obr-app-11', 't_cl':'OBR-APP-13 '}
npp = 0
tm_start = datetime.now()
ar_prced = []
eml_text = ''

def set_regl_task(test_cluster = True):
    global varz, npp, tm_start, err_text, eml_text, email, login

    err_text = ''
    email = True
    login = True

    def now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " [" + str(npp) + "]"

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

    if test_cluster:
        clAddr = 'OBR-APP-13'
        clAuth = ('adm','321')
        ibAuth = ('admin','kzueirf')
    else:
        clAddr = 'OBR-APP-11'
        clAuth = ('adm','321')
        ibAuth = ('admin','kzueirf')

    pythoncom.CoInitialize()
    V83 = win32com.client.Dispatch("V83.COMConnector")
    Agent = V83.ConnectAgent(clAddr)
    Clsts = Agent.GetClusters()
    for cls in Clsts:
        print(now(), "CLST> ", cls.ClusterName, "/", cls.HostName, "/", cls.MainPort)
        eml_text = eml_text + now() + "<h5>CLST> " + cls.ClusterName + "/" + cls.HostName + "/" + str(cls.MainPort) +'</h5>'
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
                try:
                    prv = '✔' if bse.ScheduledJobsDenied else '✘'
                    atm = '✔' if test_cluster else '✘'
                    ok = setDenialState(bse, WrPrc, test_cluster)
                    # bse.ScheduledJobsDenied = False;
                    # WrPrc.UpdateInfoBase(bse)
                    print(now(), '  BSE>>', cls.HostName.upper()+":"+str(prc.MainPort)+ "/" +bse.Name, prv,'=>',atm,ok)
                    eml_text = eml_text + '<li>'+now() + '  BSE>>' + cls.HostName.upper() + ":" + str(prc.MainPort) + "/<b style='color:navy'>" + bse.Name +'</b> '+ prv + ' => ' + atm +' ('+ ok+')'
                    ar_prced.append(bse.Name.upper()+'@'+cls.ClusterName.upper())
                except BaseException as err:
                    err_text = 'we have problems, Huston' + err
                    print(err_text)
                    eml_text = eml_text + err_text

set_regl_task()
set_regl_task(False)
print('done', (datetime.now() - tm_start).seconds, 'sec.')
eml_text = eml_text + '<p>done ' + str((datetime.now() - tm_start).seconds) + ' sec.</p>'
if err_text:
    suhLib.inform('Setting reglament task enabling flag', err_text, 2)
if email:
    suhLib.inform('Test scheduled task report', eml_text, 1)
if login:
    suhLib.logg(eml_text)
