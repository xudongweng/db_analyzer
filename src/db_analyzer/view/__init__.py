from django.conf import settings

settings.SCHEDULER.start()
tb_ds = settings.SQL_CONNECTION.query('select count(1) from information_schema.TABLES where TABLE_NAME in '
                         '(\'apscheduler_jobs_history\',\'apscheduler_jobs_info\')')

if tb_ds is not None:
    if tb_ds[0][0] < 2:
        settings.LOGGER.error('请先运行jobs_base.sql创建apscheduler_jobs_history和apscheduler_jobs_info表')
        exit()
    else:
        jb_ds = settings.SQL_CONNECTION.query('select count(1)  from apscheduler_jobs aj left join apscheduler_jobs_info jb \
                                  on aj.id =jb.apscheduler_jobs_id where jb.apscheduler_jobs_id is \
                                  null')  # 检查apscheduler_jobs表中的任务在apscheduler_jobs_info表中是否存在
        if jb_ds is not None:
            if jb_ds[0][0] > 0:
                settings.LOGGER.info('apscheduler_jobs_info与apscheduler_jobs表中数据不匹配，需要进行修正。')
                settings.FLAG_FIX = 1
        else:
            exit()
else:
    exit()
