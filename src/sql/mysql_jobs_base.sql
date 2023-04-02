CREATE TABLE IF NOT EXISTS apscheduler_jobs_info (
	apscheduler_jobs_id VARCHAR(191) PRIMARY KEY COMMENT '与apscheduler_jobs.id关联',
	deploy_host VARCHAR(80) COMMENT '部署任务主机',
	db_type smallint COMMENT '1:MySQL 2:oracle',
	remote_host VARCHAR(80) NOT NULL,
	db_port VARCHAR(6),
	db_name VARCHAR(20),
	table_name VARCHAR(20),
	check_type SMALLINT COMMENT '检查类型 1:手机 2:身份证',
	cron VARCHAR(35)COMMENT '定时',
	limit_row unsigned BIGINT COMMENT '限定查询行数',
	create_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	key remote_host(remote_host),
	key db_name(db_name),
	key create_time(create_time)
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS apscheduler_jobs_history (
  id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  apscheduler_jobs_id varchar(191) NOT NULL COMMENT '与apscheduler_jobs.id关联',
  start_time timestamp NOT NULL DEFAULT '0000-00-00 00:00:00' COMMENT '任务开始时间',
  end_time timestamp not NULL DEFAULT '0000-00-00 00:00:00' COMMENT '任务结束时间',
  used_time varchar(10) DEFAULT '00:00:00',
  PRIMARY KEY (`id`),
  KEY apscheduler_jobs_id (apscheduler_jobs_id),
  KEY start_time (start_time),
  KEY end_time (end_time)
) ENGINE=InnoDB;