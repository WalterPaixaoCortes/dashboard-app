#!/usr/bin/python
# created by walter_ritzel at 2017/02
# last version: 2017/03/06

import traceback
import datetime
import time
import sys

import labio.configWrapper
import labio.logWrapper
import labio.dbWrapper
from labio.utils import GenericJsonObject

import requests


# -----------------------------------------------------------------------------
def clean_tables(cfg, db, log):
    return_value = True
    try:
        tables = db.getData(cfg.sql_select_tables)

        for table in tables:
            cmd = 'DELETE FROM %s' % table[0]
            db.executeCommand(cmd)
        db.commit()
    except:
        return_value = False
        log.error(traceback.format_exc())
    return return_value

# -----------------------------------------------------------------------------
def generate_types(cfg, db, log):
    return_value = True
    try:
        db.executeCommand(cfg.sql_insert_type % ('Tickets',
        datetime.datetime.now().strftime('%Y-%m-%d')))
        db.executeCommand(cfg.sql_insert_type % ('Incidents',
        datetime.datetime.now().strftime('%Y-%m-%d')))
        db.commit()
    except:
        return_value = False
        log.error(traceback.format_exc())
    return return_value

# -----------------------------------------------------------------------------
def generate_dates(cfg, db, log):
    return_value = True
    try:
        initial_date = datetime.datetime(2017,1,1)
        final_date = datetime.datetime.now()

        while initial_date < final_date:
            cmd = cfg.sql_insert_date % (
                initial_date.strftime('%Y%m%d'),
                initial_date.strftime('%Y-%m-%d'),
                initial_date.year, 
                initial_date.month, 
                initial_date.strftime('%W')
                )
            db.executeCommand(cmd)
            initial_date += datetime.timedelta(days=1)

        db.commit()
    except:
        return_value = False
        log.error(traceback.format_exc())
    return return_value

# -----------------------------------------------------------------------------
def import_tickets(cfg, db, log):
    return_value = True
    try:
        start = 0
        parse_url = cfg.ticket_url % (
            cfg.ticket_output,
            cfg.ticket_content,
            cfg.ticket_output,
            cfg.ticket_user,
            cfg.ticket_pass,
            cfg.ticket_columns,
            cfg.ticket_obj_id,
            cfg.ticket_page_size,
            start
        )

        response = requests.get(parse_url)
        if response.status_code == 200:
            try:
                parsed_data = GenericJsonObject(response.text)
                if len(parsed_data.messages) > 0:
                    idx = 0
                    for item in parsed_data.messages:
                        cmd_ins = cfg.sql_insert_ticket % (
                            item['datetime_raw'] + idx,
                            1,
                            item['name'],
                            datetime.datetime.strptime(item['datetime'],'%d/%m/%Y %H:%M:%S').strftime('%Y%m%d'),
                            0,
                            item['status'],
                            item['priority'],
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
                        db.executeCommand(cmd_ins)
                        idx += 10
                    db.commit()
            except:
                log.error(traceback.format_exc())
                return_value = False

            db.commit()
        else:
            log.error('Error when trying the first access.')
            log.error(response.text)
            return_value = False
    except:
        return_value = False
        log.error(traceback.format_exc())
    return return_value

# -----------------------------------------------------------------------------
def execute(cfg_name="application.config"):
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

                    log_obj.info('Cleaning Tables...')
                    clean_tables(file_config, db_obj, log_obj)

                    log_obj.info('Generating type dimension...')
                    generate_types(file_config, db_obj, log_obj)

                    log_obj.info('Generating date dimension...')
                    generate_dates(file_config, db_obj, log_obj)

                    log_obj.info('Importing tickets...')
                    import_tickets(file_config, db_obj, log_obj)

                else:
                    log_obj.error('Database is not opened.')

                log_obj.info('--- FIRST LOAD PROCESS FINISHED ---')
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
    exit_code = 0
    try:
        if len(sys.argv) < 2:
            cfg_name = "application.config"
        else:
            cfg_name = sys.argv[1]

        exit_code = execute(cfg_name)
    except:
        print(traceback.format_exc())
        exit_code = 1
    sys.exit(exit_code)

