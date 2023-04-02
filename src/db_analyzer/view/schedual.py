import platform
from apscheduler.triggers.cron import CronTrigger
from django.shortcuts import render
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED, EVENT_JOB_EXECUTED
from datetime import datetime
from django.http import HttpResponseRedirect
import uuid
import time
from django.utils.http import urlquote
from db_analyzer.model.second_model import Second_Model
from django.conf import settings
import re

P_sec_min = r'^([0-5]\d|\d)(,[0-5]\d|,\d)*$|^([0-5]\d|\d)\/([0-5]\d|\d)$|^\*(\/([0-5]\d|\d))?$'  # 0-59 a,b,c a/b */a
P_hour = r'^([0-1]\d|[2][0-3]|\d)(,\d|,[0-1]\d|,[2][0-3])*$|^([0-1]\d|[2][0-3]|\d)\/([0-1]\d|[2][0-3]|\d)$|^\*(\/([0-1]\d|[2][0-3]|\d))?$'  # 0-23 a,b,c a/b */a
P_day = r'^([1-2]\d|[0]?[1-9]|3[0-1])(,[1-2]\d|,[0]?[1-9]|,3[0-1])*$|^([1-2]\d|[0]?[1-9]|3[0-1])\/([1-2]\d|[0]?[1-9]|3[0-1])$|^\*(\/([1-2]\d|[0]?[1-9]|3[0-1]))?$|^[l][a][s][t]$'  # 1-31 a,b,c a/b */a last
P_week = r'^([1-4]\d|[0]?[1-9]|5[0-3])(,[1-4]\d|,[0]?[1-9]|,5[0-3])*$|^([1-4]\d|[0]?[1-9]|5[0-3])\/([1-4]\d|[0]?[1-9]|5[0-3])$|^\*(\/([1-4]\d|[0]?[1-9]|5[0-3]))?$'  # 1-53 a,b,c a/b */a
P_day_of_week = r'^([0]?[0-6])(,[0]?[0-6])*$|^([0]?[0-6])\/([0]?[0-6])$|^\*(\/([0]?[0-6]))?$'  # 0-6 a,b,c a/b */a
P_month = r'^([1][0-2]|[0]?[1-9])(,[1][0-2]|,[0]?[1-9])*$|^([1][0-2]|[0]?[1-9])\/([1][0-2]|[0]?[1-9])$|^\*(\/([1][0-2]|[0]?[1-9]))?$'  # 1-12 a,b,c a/b */a
P_year = r'^20[2-9][\d]$|^\*$'


def mysql_job(**options):
    settings.SCHEDULER.remove_listener(job_listener)
    settings.SCHEDULER.add_listener(job_listener, EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_EXECUTED)
    settings.LOGGER.debug(str(options))
    if settings.FLAG_FIX == 1:  # FLAG_FIX为1，说明apscheduler_jobs表中任务在apscheduler_jobs_info表中不存在。
        jb_ds_1 = settings.SQL_CONNECTION.query(
            'select count(1) from apscheduler_jobs_info where apscheduler_jobs_id=\'' + options['job_id'] + '\'')
        if jb_ds_1[0][0] == 0:
            settings.LOGGER.info(options['job_id'] + '没有在apscheduler_jobs表中，需要进行修正。')
            ins_str = 'insert into apscheduler_jobs_info(apscheduler_jobs_id,deploy_host,db_type,remote_host,db_name,' \
                      'table_name,check_type,cron,limit_row) values(\'' + options['job_id'] + '\',\'' + \
                      platform.node() + '\',' + options['db_type'] + ', \'' + options['remote_host'] + '\',\'' + \
                      options['db_name'] + '\',\'' + options['table_name'] + '\',' + options['check_type'] + ',\'' + \
                      options['cron_str'] + '\',' + options['limit_row'] + ')'
            settings.LOGGER.debug(ins_str)
            settings.SQL_CONNECTION.execute(ins_str)
            jb_ds_2 = settings.SQL_CONNECTION.query('select count(1)  from apscheduler_jobs aj left join apscheduler_jobs_info jb \
                                       on aj.id =jb.apscheduler_jobs_id where jb.apscheduler_jobs_id is \
                                       null')  # 检查apscheduler_jobs表中的任务在apscheduler_jobs_info表中是否存在
            if jb_ds_2[0][0] > 0:
                settings.FLAG_FIX = 1
            else:
                settings.LOGGER.info('apscheduler_jobs表已全部修正。')
                settings.FLAG_FIX = 0

    # task_id = str(random.randrange(1000, 9999))  # 随机分配任务id，用于区分同一次任务
    start_time = datetime.now()
    ins_str = 'insert into apscheduler_jobs_history set apscheduler_jobs_id=\'' + options['job_id'] + '\', ' + \
              'start_time=\'' + str(start_time) + '\''
    settings.LOGGER.debug(ins_str)
    aps_id = settings.SQL_CONNECTION.execute(ins_str)  # 任务启动时间写入数据库
    settings.LOGGER.debug('last_id:' + str(aps_id))
    last_id = aps_id
    '''----------------------------------------------------------------------------------------------------'''
    # 进行数据库检查部分
    #from db_analyzer.model.mysql_check_id_card import MySQL_Model
    #mycon = MySQL_Model(options['remote_host'], options['username'], options['password'], 3306)
    #if options['check_type'] == '2':
    #    mycon.mysql_check_id_card(options['limit_row'])  # 身份证检查
    #elif options['check_type'] == '3':
    #    mycon.mysql_check_primary_key()  # 无主键检查
    '''----------------------------------------------------------------------------------------------------'''
    end_time = datetime.now()
    sm = Second_Model()
    settings.LOGGER.info('used_time(' + str(sm.sec_to_time((end_time - start_time).seconds)) + ')')
    upt_str = 'update apscheduler_jobs_history set end_time =\'' + str(end_time) + '\',used_time=\'' + \
              str(sm.sec_to_time((end_time - start_time).seconds)) + '\' where id=' + str(last_id)
    settings.LOGGER.debug(upt_str)
    settings.SQL_CONNECTION.execute(upt_str)  # 任务结束时间写入数据库


def job_listener(event):
    job = settings.SCHEDULER.get_job(event.job_id)
    if not event.exception:
        settings.LOGGER.info(
            'job_id:' + event.job_id + ',job_name:' + job.name + ',code:' + str(event.code) + ',trigger:' +
            str(job.trigger) + ',run_time:' + str(event.scheduled_run_time))
    else:
        settings.LOGGER.error(
            'job_id:' + event.job_id + ',job_name:' + job.name + ',code:' + str(event.code) + ',trigger:' +
            str(job.trigger) + ',run_time:' + str(event.scheduled_run_time) + ',exception:' + str(event.exception) +
            ',traceback:' + str(event.traceback))


def index(request):
    return HttpResponseRedirect('./schedual/')


def sched_idx(request):
    ctx = {}
    err_msg = ''
    if request.POST:

        if 'add_job' in request.POST:
            if settings.SCHEDULER.state == 1:
                return HttpResponseRedirect('./add/')
            else:
                err_msg = '，请先定时启动服务。'

        elif 'search_job' in request.POST:
            if settings.SCHEDULER.state == 1:
                return HttpResponseRedirect('./search/')
            else:
                err_msg = '，请先定时启动服务。'

    if settings.SCHEDULER.state == 0:
        ctx['rlt_message'] = '定时服务已关闭' + err_msg
    elif settings.SCHEDULER.state == 1:
        ctx['rlt_message'] = '定时服务已启动' + err_msg

    return render(request, 'scheduals.html', ctx)


def sched_add(request):
    ctx = {'remote_host': 'localhost', 'username': 'root', 'port': 3306, 'limit_row': 1}

    if request.POST:
        if 'back_index' in request.POST:  # 返回首页
            return HttpResponseRedirect('../')
        ctx['db_type'] = request.POST['db_type']
        ctx['remote_host'] = request.POST['remote_host']
        ctx['username'] = request.POST['username']
        ctx['password'] = request.POST['password']
        ctx['port'] = request.POST['port']
        ctx['db_name'] = request.POST['db_name']
        ctx['table_name'] = request.POST['table_name']
        ctx['check_type'] = request.POST['check_type']
        ctx['cron_str'] = request.POST['cron_str']
        ctx['limit_row'] = request.POST['limit_row']

        if ctx['check_type'] == '1':
            ctx['rlt_message'] = '检查类型手机号尚待开发。'
            return render(request, 'sched_add.html', ctx)

        if len(ctx['remote_host']) == 0:
            ctx['rlt_message'] = '远程主机不能为空。'
            return render(request, 'sched_add.html', ctx)

        if len(ctx['username']) == 0:
            ctx['rlt_message'] = '用户名不能为空。'
            return render(request, 'sched_add.html', ctx)

        if len(ctx['port']) == 0:
            ctx['rlt_message'] = '端口不能为空。'
            return render(request, 'sched_add.html', ctx)

        if len(ctx['remote_host'].replace(' ', '').replace('\n', '')) < len(ctx['remote_host']):
            ctx['rlt_message'] = '远程主机不能包含空格或tab。'
            return render(request, 'sched_add.html', ctx)

        if len(ctx['username'].replace(' ', '').replace('\n', '')) < len(ctx['username']):
            ctx['rlt_message'] = '用户名不能包含空格或tab。'
            return render(request, 'sched_add.html', ctx)

        if len(ctx['port'].replace(' ', '').replace('\n', '')) < len(ctx['port']):
            ctx['rlt_message'] = '端口不能包含空格或tab。'
            return render(request, 'sched_add.html', ctx)

        # 检查数据库是否连通
        mysql_mutil_url = 'mysql+pymysql://' + ctx['username'] + ':' + urlquote(str(ctx['password'])) + '@' + \
                          ctx['remote_host'] + ':' + str(ctx['port'])
        settings.CON_TEST.reset_url(mysql_mutil_url)
        if settings.CON_TEST.con_test() is None:
            ctx['rlt_message'] = ctx['remote_host'] + '连接失败。'
            return render(request, 'sched_add.html', ctx)

        # 检查是否存在相同任务
        same_srt = 'select apscheduler_jobs_id from aps.apscheduler_jobs_info aji inner join aps.apscheduler_jobs aj ' \
                   'on aji.apscheduler_jobs_id = aj.id  where aji.remote_host=\'' + ctx['remote_host'] + \
                   '\'  and aji.db_name=\'' + ctx['db_name'] + '\' and aji.table_name =\'' + \
                   ctx['table_name'] + '\' and aji.db_type=' + ctx['db_type'] + ' and aji.check_type =' + ctx[
                       'check_type']

        settings.LOGGER.debug(same_srt)
        same_ds = settings.SQL_CONNECTION.query(same_srt)
        if same_ds is not None:
            if len(same_ds) > 0:
                ctx['rlt_message'] = 'job id: ' + same_ds[0][0] + ' 已存在相同的任务。'
                return render(request, 'sched_add.html', ctx)

        # 定时拆分检查
        cron_list = ctx['cron_str'].split()
        if len(cron_list) == 8:

            if not len(re.findall(re.compile(P_sec_min, re.S), cron_list[0])):
                ctx['rlt_message'] = 'cron 秒 格式填写有错误(取值范围：00-59 格式：* a,b,c a/b */a)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)
            if not len(re.findall(re.compile(P_sec_min, re.S), cron_list[1])):
                ctx['rlt_message'] = 'cron 分 格式填写有错误(取值范围：00-59 格式：* a,b,c a/b */a)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)
            if not len(re.findall(re.compile(P_hour, re.S), cron_list[2])):
                ctx['rlt_message'] = 'cron 时 格式填写有错误(取值范围：00-23 格式：* a,b,c a/b */a)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)
            if not len(re.findall(re.compile(P_day, re.S), cron_list[3])):
                ctx['rlt_message'] = 'cron 日 格式填写有错误(取值范围：01-31 格式：* a,b,c a/b */a last)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)
            if not len(re.findall(re.compile(P_day_of_week, re.S), cron_list[4])):
                ctx['rlt_message'] = 'cron 星期 格式填写有错误(取值范围：0-6,0为周一 格式：* a,b,c a/b */a)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)
            if not len(re.findall(re.compile(P_week, re.S), cron_list[5])):
                ctx['rlt_message'] = 'cron 日 格式填写有错误(取值范围：01-53 格式：* a,b,c a/b */a)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)
            if not len(re.findall(re.compile(P_month, re.S), cron_list[6])):
                ctx['rlt_message'] = 'cron 月 格式填写有错误(取值范围：01-12 格式：* a,b,c a/b */a)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)
            if not len(re.findall(re.compile(P_year, re.S), cron_list[7])):
                ctx['rlt_message'] = 'cron 年 格式填写有错误(取值范围：2020-2099 格式：* a,b,c a/b */a)。' + request.POST['cron_str']
                return render(request, 'sched_add.html', ctx)

            # 生成job_id
            get_timestamp_uuid = str(uuid.uuid1()).replace('-', '')[0:15]
            ctx['job_id'] = get_timestamp_uuid

            settings.SCHEDULER.add_job(mysql_job, 'cron', kwargs=ctx, year=cron_list[7],
                                       week=cron_list[6], day_of_week=cron_list[5], month=cron_list[4],
                                       day=cron_list[3], hour=cron_list[2], minute=cron_list[1],
                                       second=cron_list[0], id=get_timestamp_uuid)
            ins_str = 'insert into apscheduler_jobs_info(apscheduler_jobs_id,deploy_host,db_type,remote_host,db_name,' \
                      'table_name,check_type,cron,limit_row) values(\'' + ctx['job_id'] + '\',\'' + platform.node() + \
                      '\',\'' + ctx['db_type'] + '\',\'' + ctx['remote_host'] + '\',\'' + ctx['db_name'] + '\',\'' + \
                      ctx['table_name'] + '\',\'' + ctx['check_type'] + '\',\'' + ctx['cron_str'] + '\',' + \
                      ctx['limit_row'] + ')'
            settings.LOGGER.debug(ins_str)
            settings.SQL_CONNECTION.execute(ins_str)  # 写入任务基础表
            msg = '任务添加成功。' + str(ctx)

            ctx.clear()  # 添加成功后，清除所有信息。
            ctx = {'remote_host': 'localhost', 'username': 'root', 'port': 3306, 'limit_row': 1}
        else:
            msg = 'cron长度填写有误。'
        ctx['rlt_message'] = msg
    return render(request, 'sched_add.html', ctx)


def sched_del(request):
    ctx = {}
    if request.POST:
        if 'back_search' in request.POST:  # 返回查询页
            return HttpResponseRedirect('../search/')
        if request.POST['job_id']:
            if settings.SCHEDULER.get_job(request.POST['job_id']) is not None:  # 判断是否存在job_id
                settings.SCHEDULER.remove_job(request.POST['job_id'])
            qry_str = 'select count(1) from apscheduler_jobs where id=\'' + request.POST[
                'job_id'] + '\''  # 检查apscheduler_jobs自生成表是否还存在该job_id，以保证任务job_id已成功删除。
            settings.LOGGER.debug(qry_str)
            job_id = settings.SQL_CONNECTION.query(qry_str)
            if job_id is not None:  # 如果未删除apscheduler_jobs的job_id，则不继续删除后续表中记录。
                if job_id[0][0] == 1:
                    ctx['rlt_message'] = 'job_id:' + request.POST['job_id'] + ' 未成功删除。'
            # 不论是否因为某种原因导致apscheduler_jobs
            del_body = 'delete from apscheduler_jobs_history where apscheduler_jobs_id=\'' + \
                       request.POST['job_id'] + '\''
            del_head = 'delete from apscheduler_jobs_info where apscheduler_jobs_id=\'' + \
                       request.POST['job_id'] + '\''
            settings.LOGGER.debug(del_body)
            settings.SQL_CONNECTION.execute(del_body)
            settings.LOGGER.debug(del_head)
            settings.SQL_CONNECTION.execute(del_head)
            ctx['rlt_message'] = request.POST['job_id'] + ' 任务已成功删除'
            return render(request, 'sched_del.html', ctx)

        else:
            ctx['rlt_message'] = 'job_id不能为空'
    return render(request, 'sched_del.html', ctx)


def sched_search(request):
    ctx = {}
    if request.POST:
        settings.LOGGER.debug(settings.SCHEDULER.print_jobs())
        if 'back_search' not in request.POST:
            if 'back_index' in request.POST:  # 返回首页
                return HttpResponseRedirect('../')

            # if settings.SCHEDULER.get_job(request.POST['job_id']) is not None:
            # 展示单个任务详细执行历史记录
            # print(settings.SCHEDULER.get_job(request.POST['job_id']))
            body_qry = 'select id,apscheduler_jobs_id,date_format(start_time,\'%Y-%m-%d %H:%i:%s\') \
                start_time,date_format(end_time,\'%Y-%m-%d %H:%i:%s\') end_time,used_time from \
                apscheduler_jobs_history where apscheduler_jobs_id = \'' + request.POST['job_id'] + '\'' + \
                       'order by id desc limit 100'
            settings.LOGGER.debug(body_qry)
            body_ds = settings.SQL_CONNECTION.query(body_qry)
            if body_ds is not None:
                settings.LOGGER.debug(str(body_ds))
                ctx = {'rlt_job_history': body_ds}
            return render(request, 'sched_job_history.html', ctx)

    # 展示所有任务
    head_qry = 'select jb.apscheduler_jobs_id,jb.deploy_host,CASE WHEN jb.db_type = 1 then \'MySQL\' ELSE ' \
               '\'Oracle\' END as db_type,jb.remote_host,jb.db_name,jb.table_name,case when jb.check_type = 1 then ' \
               '\'Tel\' when jb.check_type = 2 then \'ID\' when jb.check_type = 3 then \'NPK\' END, \
               jb.cron,jb.limit_row, ifnull(FROM_UNIXTIME(aj.next_run_time, \'%Y-%m-%d ' \
               '%H:%i:%s\'),\'00:00:00\') as next_run_time,CASE WHEN aj.id is null and aj.next_run_time is null \
               then \'OVER\' WHEN aj.id is not null and aj.next_run_time is null then \'PAUSED\' ELSE ' \
               '\'RUNNING\' END as run_state,date_format(create_time,\'%Y-%m-%d %H:%i:%s\'),CASE WHEN \
               aj.id is null and aj.next_run_time is null then  ' \
               '\'disabled\' WHEN aj.id is not null and aj.next_run_time is null then \'\' ELSE ' \
               '\'\' END as btn_state from ' \
               'apscheduler_jobs_info jb left join ' \
               'apscheduler_jobs aj on jb.apscheduler_jobs_id = aj.id order by jb.check_type,create_time'
    settings.LOGGER.debug(head_qry)
    head_ds = settings.SQL_CONNECTION.query(head_qry)
    if head_ds is not None:
        settings.LOGGER.debug(str(head_ds))
        ctx = {'rlt_job_list': head_ds}

    return render(request, 'sched_search.html', ctx)


def sched_resume_stop(request):
    ctx = {}
    if request.POST:
        if 'back_search' in request.POST:  # 返回查询页
            return HttpResponseRedirect('../search/')
        if request.POST['job_id']:
            if settings.SCHEDULER.get_job(request.POST['job_id']) is not None:
                nt_qry = 'SELECT next_run_time from apscheduler_jobs where id=\'' + request.POST['job_id'] + '\''
                settings.LOGGER.debug(nt_qry)
                nt_ds = settings.SQL_CONNECTION.query(nt_qry)
                if nt_ds is not None:
                    job = settings.SCHEDULER.get_job(request.POST['job_id'])
                    settings.LOGGER.debug(str(nt_ds))
                    nt_val = nt_ds[0][0]
                    if nt_val is None:
                        job.resume()
                        ctx['rlt_message'] = request.POST['job_id'] + ' 任务已恢复运行'
                    else:
                        job.pause()
                        ctx['rlt_message'] = request.POST['job_id'] + ' 任务已停止运行'
                return render(request, 'sched_resume_stop.html', ctx)
            else:
                ctx['rlt_message'] = 'job_id:' + request.POST['job_id'] + ' 不存在'
                return render(request, 'sched_resume_stop.html', ctx)
        else:
            ctx['rlt_message'] = 'job_id不能为空'
    return render(request, 'sched_resume_stop.html', ctx)


def sched_go_run(request):
    ctx = {}
    if request.POST:
        ctx['job_id'] = request.POST['job_id']
        if settings.SCHEDULER.get_job(request.POST['job_id']) is not None:
            cron_qry = 'SELECT apscheduler_jobs_id,cron FROM apscheduler_jobs_info WHERE apscheduler_jobs_id=\'' + \
                       request.POST['job_id'] + '\''
            settings.LOGGER.debug(cron_qry)
            cron_ds = settings.SQL_CONNECTION.query(cron_qry)
            if cron_ds is not None:
                if len(cron_ds) == 1:
                    job = settings.SCHEDULER.get_job(request.POST['job_id'])
                    job.pause()
                    t = time.strftime("%Y %m %d %H %M %S", time.localtime(int(time.time()) + 30)).split()
                    job.modify(
                        trigger=CronTrigger(year='*', week='*', day_of_week='*', month=str(t[1]),
                                            day=str(t[2]), hour=str(t[3]),
                                            minute=str(t[4]), second=str(t[5])))
                    upt_str = 'update apscheduler_jobs_info set cron=\'' + str(t[5]) + ' ' + str(t[4]) + \
                              ' ' + str(t[3]) + ' ' + str(t[2]) + ' ' + str(t[1]) + \
                              ' * * *\' where apscheduler_jobs_id=\'' + ctx['job_id'] + '\''
                    settings.LOGGER.debug(upt_str)
                    settings.SQL_CONNECTION.execute(upt_str)
                    job.resume()

    return HttpResponseRedirect('../search/')


def sched_cron_reset(request):
    ctx = {}
    if request.POST:
        if 'back_search' in request.POST:  # 返回查询页
            return HttpResponseRedirect('../search/')
        ctx['job_id'] = request.POST['job_id']
        ctx['cron_str'] = request.POST['cron_str']
        if settings.SCHEDULER.get_job(request.POST['job_id']) is not None:

            cron_qry = 'SELECT apscheduler_jobs_id,cron FROM apscheduler_jobs_info WHERE apscheduler_jobs_id=\'' + \
                       request.POST['job_id'] + '\' and cron=\'' + ctx['cron_str'] + '\''
            settings.LOGGER.debug(cron_qry)
            cron_ds = settings.SQL_CONNECTION.query(cron_qry)
            if cron_ds is not None:
                if len(cron_ds) == 0:
                    # 定时拆分检查
                    cron_list = ctx['cron_str'].split()
                    if len(cron_list) == 8:

                        if not len(re.findall(re.compile(P_sec_min, re.S), cron_list[0])):
                            ctx['rlt_message'] = 'cron 秒 格式填写有错误(取值范围：00-59 格式：* a,b,c a/b */a)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)
                        if not len(re.findall(re.compile(P_sec_min, re.S), cron_list[1])):
                            ctx['rlt_message'] = 'cron 分 格式填写有错误(取值范围：00-59 格式：* a,b,c a/b */a)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)
                        if not len(re.findall(re.compile(P_hour, re.S), cron_list[2])):
                            ctx['rlt_message'] = 'cron 时 格式填写有错误(取值范围：00-23 格式：* a,b,c a/b */a)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)
                        if not len(re.findall(re.compile(P_day, re.S), cron_list[3])):
                            ctx['rlt_message'] = 'cron 日 格式填写有错误(取值范围：01-31 格式：* a,b,c a/b */a last)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)
                        if not len(re.findall(re.compile(P_day_of_week, re.S), cron_list[4])):
                            ctx['rlt_message'] = 'cron 星期 格式填写有错误(取值范围：0-6,0为周一 格式：* a,b,c a/b */a)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)
                        if not len(re.findall(re.compile(P_week, re.S), cron_list[5])):
                            ctx['rlt_message'] = 'cron 日 格式填写有错误(取值范围：01-53 格式：* a,b,c a/b */a)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)
                        if not len(re.findall(re.compile(P_month, re.S), cron_list[6])):
                            ctx['rlt_message'] = 'cron 月 格式填写有错误(取值范围：01-12 格式：* a,b,c a/b */a)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)
                        if not len(re.findall(re.compile(P_year, re.S), cron_list[7])):
                            ctx['rlt_message'] = 'cron 年 格式填写有错误(取值范围：2020-2099 格式：* a,b,c a/b */a)。' + request.POST[
                                'cron_str']
                            return render(request, 'sched_cron_reset.html', ctx)

                        # 更新job的cron
                        job = settings.SCHEDULER.get_job(request.POST['job_id'])
                        job.pause()
                        job.modify(
                            trigger=CronTrigger(year=cron_list[7], week=cron_list[6],
                                                day_of_week=cron_list[5], month=cron_list[4],
                                                day=cron_list[3], hour=cron_list[2],
                                                minute=cron_list[1], second=cron_list[0]))
                        upt_str = 'update apscheduler_jobs_info set cron=\'' + ctx['cron_str'] + \
                                  ' \' where apscheduler_jobs_id=\'' + ctx['job_id'] + '\''
                        settings.LOGGER.debug(upt_str)
                        settings.SQL_CONNECTION.execute(upt_str)
                        job.resume()
                        return HttpResponseRedirect('../search/')
                    else:
                        ctx['rlt_message'] = 'cron长度填写有误。'
                return render(request, 'sched_cron_reset.html', ctx)
    return HttpResponseRedirect('../search/')


