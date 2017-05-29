"""
Скрипт приводит в порядок флаг блокировки регламентных заданий

Скрипт запускается без параметров каждый час из шедулера и
- на тестовом кластере устанавливает флаг блокировки на все ИБ
- на рабочем кластере снимает флаг блокировки со всех ИБ
"""

# ☐ В init вызывать собственное исключение при ошибке
# ✔ Сделать протоколирование работы в файл @done (May 29th 2017, 13:33)

import pythoncom
import win32com.client
import os, sys
import logging
import inspect
from datetime import datetime
import suhLib

log = logging.getLogger('FZ_flags_Control')
log.setLevel(logging.DEBUG)
fh = logging.FileHandler('log\\Regl.log' if os.path.exists(os.fspath('.\\log')) else 'LOG.LOG')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
log.addHandler(fh)
log.addHandler(ch)

def version():
    return '1.2.1'

def init():
    global err_text, cfg
    log.critical(os.path.basename('####### '+sys.argv[0])+' выполняется. Протокол пишется в '+log.handlers[0].baseFilename)
    if not os.environ['USERNAME'].lower() in ('tasker', 'goblin'):
        err_text = err_text + '!!! попытка запустить скрипт от неподходящего пользователя провалилась !!!'
        log.error('!!! попытка запустить скрипт от неподходящего пользователя провалилась !!! line: '+str(inspect.currentframe().f_lineno))
        return False
    cfg = suhLib.settings1C()
    return True

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S ")

def set_regl_task(test_cluster=True):
    global tm_start, err_text, eml_text, email, login


    def findIBdecriptionByIBName(ibName, Agent, Cluster):
        ibDescriptions = Agent.GetInfoBases(Cluster)
        for ibd in ibDescriptions:
            if ibd.Name.upper() == ibName.upper():
                return ibd
        return None

    def setDenialState(ib, conn, state):
        if ib.ScheduledJobsDenied == state:
            log.info('Флаг запрета регламентных заданий для ИБ '+ib+' не изменен ('+state+')')
            return 'ok'
        try:
            ib.ScheduledJobsDenied = state
            conn.UpdateInfoBase(ib)
            log.info('Флаг запрета регламентных заданий переустановлен для ИБ '+ib+' в значение '+state)
            return 'ok'
        except BaseException as err:
            log.error('Не удалось выставить для ИБ '+ib+' флаг запрета РЗ в значение '+state)
            err_text =+'Не удалось выставить для ИБ '+ib+' флаг запрета РЗ в значение '+state
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
            WrPrc = V83.ConnectWorkingProcess('tcp://' + str(prc.HostName) + ":" + str(prc.MainPort))
            WrPrc.AddAuthentication(*ibAuth)
            Bases = WrPrc.GetInfoBases()
            for bse in Bases:
                if bse.Name.upper()+'@'+cls.ClusterName.upper() in ar_prced:
                    continue
                prv = 'V' if bse.ScheduledJobsDenied else 'X'
                atm = 'V' if test_cluster else 'X'
                ok = setDenialState(bse, WrPrc, test_cluster)
                log.info('  BSE>>'+ cls.HostName.upper()+":"+str(prc.MainPort)+ "/" +bse.Name+'\t'+ prv+ ' -> '+ atm+' '+ok)
                eml_text = eml_text +'\n\r'+ '<li>'+now() + '  BSE>>'+ cls.HostName.upper() + ":" + str(prc.MainPort)+ "/<b style='color:navy'>" + bse.Name.upper()+'</b> '+ prv + ' ➜ ' + atm +' ('+ ok+')'
                ar_prced.append(bse.Name.upper()+'@'+cls.ClusterName.upper())
try:
    tm_start = datetime.now()
    ar_prced = []
    eml_text = ''
    err_text = ''
    email = False
    login = True
    cfg = dict()
    if init():
        set_regl_task()
        set_regl_task(False)
    print('done', (datetime.now() - tm_start).seconds, 'sec.')
except BaseException as err:
    err_text =+ now()+'error occured '+str(err)
finally:
    if err_text:
        print(err_text)
        suhLib.inform('Setting reglament task enabling flag', err_text, 2)
        if email:
            suhLib.inform('Test scheduled task report', eml_text, 1)

