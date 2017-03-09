#!/usr/bin/python
# created by walter_ritzel at 2017/02
# last version: 2017/03/06

import traceback
import datetime
import time
import sys
import base64
import json

import labio.configWrapper
import labio.logWrapper
import labio.dbWrapper
from labio.utils import GenericJsonObject

import requests
import schedule

# -----------------------------------------------------------------------------
def import_tickets(cfg, db, log):
    return_value = True
    try:
        rs_last_date = db.getData(cfg.sql_select_last_date).fetchall()

        if len(rs_last_date) > 0:
            last_date = datetime.datetime.strptime(rs_last_date[0][0],'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%SZ')
            log.info('Cut Date: %s' % last_date)

            proxy = None
            if cfg.use_proxy:
                proxy = {'https': cfg.proxy}

            b_auth_string = str.encode(cfg.tickets_auth % (cfg.tickets_cid, cfg.tickets_pbk, cfg.tickets_pvk))
            b_auth_token = base64.b64encode(b_auth_string)
            auth_token = b_auth_token.decode('utf-8')

            header = cfg.tickets_header.copy()
            header['Authorization'] = header['Authorization'] % auth_token

            response = requests.get(cfg.tickets_count_url % last_date, headers=header, proxies=proxy)
            if response.status_code == 200:
                try:
                    page_count = round(json.loads(response.text)['count'] / cfg.tickets_page_size)
                    parsed_data = json.loads(response.text)
                    idx = 0
                    page = 1
                    log.info('Page count: %s' % str(page_count))

                    while page <= page_count:
                        try:
                            url = cfg.tickets_url % (str(page), str(cfg.tickets_page_size), last_date)
                            response = requests.get(url, headers=header, proxies=proxy)

                            if response.status_code != 200:
                                log.error('Error when trying to access information.')
                                log.error(response.text)
                                return_value = False
                                break

                            parsed_data = json.loads(response.text)

                            for item in parsed_data:
                                cmd_ins = ''
                                cmd_upd = ''
                                try:
                                    date_closed_wid = 0
                                    date_closed_date = ''
                                    date_closed_time = ''
                                    if item['closedDate'] != '' and item['closedDate'] is not None:
                                        date_closed_wid = datetime.datetime.strptime(item['closedDate'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d')
                                        date_closed_date = datetime.datetime.strptime(item['closedDate'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                                        date_closed_time = datetime.datetime.strptime(item['closedDate'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%H:%M:%S')

                                    cmd_ins = cfg.sql_insert_ticket % (
                                        item['id'],
                                        cfg.tickets_types[item['recordType']],
                                        item['company']['name'].replace("'","''"),
                                        datetime.datetime.strptime(item['dateEntered'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'),
                                        date_closed_wid,
                                        datetime.datetime.strptime(item['dateEntered'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                                        datetime.datetime.strptime(item['dateEntered'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%H:%M:%S'),
                                        date_closed_date,
                                        date_closed_time,
                                        item['status']['id'],
                                        item['priority']['id'],
                                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    )

                                    cmd_upd = cfg.sql_update_ticket % (
                                        cfg.tickets_types[item['recordType']],
                                        item['company']['name'].replace("'","''"),
                                        datetime.datetime.strptime(item['dateEntered'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y%m%d'),
                                        date_closed_wid,
                                        datetime.datetime.strptime(item['dateEntered'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                                        datetime.datetime.strptime(item['dateEntered'],
                                        '%Y-%m-%dT%H:%M:%SZ').strftime('%H:%M:%S'),
                                        date_closed_date,
                                        date_closed_time,
                                        item['status']['id'],
                                        item['priority']['id'],
                                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        item['id']
                                    )

                                    try:
                                        db.executeCommand(cmd_ins)
                                    except:
                                        db.executeCommand(cmd_upd)
                                    idx += 1
                                except:
                                    log.error('Record missed: %s' % item)
                                    log.error('Insert: %s' % cmd_ins)
                                    log.error('Update: %s' % cmd_upd)
                                    pass

                            db.commit()

                            log.info('Records processed: %s' % str(idx))
                            page += 1
                            time.sleep(2)
                        except:
                            log.error('Page %s skipped due to errors.' % page)
                            log.error(traceback.format_exc())
                            return_value = False
                            page += 1

                except:
                    log.error(traceback.format_exc())
                    return_value = False

                if return_value:
                    cmd_update_last_date = cfg.sql_update_last_date % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    db.executeCommand(cmd_update_last_date)

                db.commit()
            else:
                log.error('Error when trying the first access.')
                log.error(response.text)
                return_value = False
        else:
            log.error('No initial load date defined.')
    except:
        return_value = False
        log.error(traceback.format_exc())
    return return_value

# -----------------------------------------------------------------------------
def import_sensors(cfg, db, log):
    return_value = True
    try:
        start = 0
        parse_url = cfg.prtg_url % (
            cfg.sensor_output,
            cfg.sensor_content,
            cfg.sensor_output,
            cfg.prtg_user,
            cfg.prtg_pass,
            cfg.sensor_columns,
            cfg.sensor_page_size,
            start
        )

        proxy = None
        if cfg.use_proxy:
            proxy = {'https': cfg.proxy}

        response = requests.get(parse_url, proxies=proxy)
        if response.status_code == 200:
            try:
                
                db.executeCommand('DELETE FROM w_sensor_f')

                parsed_data = GenericJsonObject(response.text)
                effective_date = datetime.datetime.now()

                for item in parsed_data.sensors:
                    cum_since_dt = datetime.datetime.fromtimestamp((item['cumsince_raw']-25569)*86400)

                    last_uptime_date = cum_since_dt
                    if 'lastup_raw' in item.keys():
                        last_uptime_date = datetime.datetime.fromtimestamp((item['lastup_raw']-25569)*86400)

                    last_downtime_date = cum_since_dt
                    if 'lastdown_raw' in item.keys():
                        last_downtime_date = datetime.datetime.fromtimestamp((item['lastdown_raw']-25569)*86400)

                    cmd_ins = cfg.sql_insert_sensor % (
                        item['objid'],
                        item['sensor'],
                        item['device'],
                        item['group'],
                        item['status'],
                        item['priority'],
                        item['uptime_raw'] / 10000,
                        item['downtime_raw'] / 10000,
                        last_uptime_date,
                        last_downtime_date,
                        cum_since_dt
                    )

                    db.executeCommand(cmd_ins)

                db.commit()
                
                log.info('Records processed: %s.' % parsed_data.treesize)
            except:
                log.error(traceback.format_exc())
                return_value = False
        else:
            log.error('Error when trying the first access.')
            log.error(response.text)
            return_value = False
    except:
        return_value = False
        log.error(traceback.format_exc())
    return return_value

# -----------------------------------------------------------------------------
def execute(cfg_name="job.config"):
    return_value = 0
    print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    print("Loading Configuration...")

    file_config = labio.configWrapper.load_configuration(cfg_name)

    if file_config.isLoaded:
        log_obj = None
        try:
            log_obj = labio.logWrapper.return_logging(file_config.log)
        except:
            return_value = 1
            print(traceback.format_exc())

        if return_value == 0:
            try:
                log_obj.info('--- FIRST LOAD PROCESS STARTED ---')

                db_obj = labio.dbWrapper.dbGenericWrapper(file_config.database).getDB()

                if db_obj.isDatabaseOpen():
                    log_obj.info('Importing sensors data...')
                    import_sensors(file_config, db_obj, log_obj)

                    log_obj.info('Importing tickets...')
                    import_tickets(file_config, db_obj, log_obj)
                else:
                    log_obj.error('Database is not opened.')

                log_obj.info('--- FIRST LOAD PROCESS FINISHED ---')
                for handler in log_obj.handlers:
                    handler.close()
                    log_obj.removeHandler(handler)
            except:
                return_value = 1
                log_obj.error('Unexpected error at process: %s' % traceback.format_exc())
                log_obj.info('Execution aborted due to errors. Please see the log file for more details.')
        else:
            return_value = 1
    else:
        return_value = 1

    return return_value


# -----------------------------------------------------------------------------
# Main routine
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    schedule.every(1).minute.do(execute)

    while True:
        schedule.run_pending()
        time.sleep(2)

