import traceback
import datetime
import json

import labio.configWrapper
import labio.logWrapper
import labio.dbWrapper

from flask import Flask, render_template, request, redirect, url_for, flash
from bs4 import UnicodeDammit

app = Flask(__name__)

app_config = labio.configWrapper.load_configuration('application.config')
if app_config:
    log_obj = labio.logWrapper.return_logging(app_config.log)


@app.route('/')
def home():
    data_rows5 = None
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data_rows5 = db.getData(app_config.sql_select_type_count).fetchall()
        except:
            log_obj.error(traceback.format_exc())
    return render_template('index.html', list5=data_rows5)


@app.route('/priority1')
def priority1():
    data = None
    rows = {"data":[]}
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_priority1).fetchall()
            for row in data:
                rows["data"].append([item for item in row])
        except:
            log_obj.error(traceback.format_exc())
    return json.dumps(rows)


@app.route('/priority2')
def priority2():
    data = None
    rows = {'data':[]}
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_priority2).fetchall()
            for row in data:
                rows['data'].append([item for item in row])
        except:
            log_obj.error(traceback.format_exc())
    return json.dumps(rows)


@app.route('/periods')
def periods():
    data = None
    rows = {'data':[]}
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_periods).fetchall()
            for row in data:
                rows['data'].append([item for item in row])
        except:
            log_obj.error(traceback.format_exc())
    return json.dumps(rows)


@app.route('/ticket_types')
def ticket_types():
    data = None
    rows = {'data':[]}
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_type_count).fetchall()
            for row in data:
                rows['data'].append([item for item in row])
        except:
            log_obj.error(traceback.format_exc())
    return json.dumps(rows)


@app.route('/donuts')
def donuts():
    data = None
    rows = []
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_type_count).fetchall()
            for row in data:
                rows.append({"label": row[0], "value": row[1]})
        except:
            log_obj.error(traceback.format_exc())
    str_return = json.dumps(rows)
    return str_return.replace('"label"','label').replace('"value"','value')


@app.route('/services')
def services():
    data = None
    rows = {'data':[]}
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_service).fetchall()
            for row in data:
                val1 = '{:.6} %'.format(row[1])
                val2 = '{:.6} %'.format(row[2])
                rows['data'].append([row[0], val1, val2])
        except:
            log_obj.error(traceback.format_exc())
    return json.dumps(rows)


@app.route('/vcloud')
def vcloud():
    data = None
    rows = {'data':[]}
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_vcloud).fetchall()
            for row in data:
                val1 = '{:.6} %'.format(row[1])
                val2 = '{:.6} %'.format(row[2])
                rows['data'].append([row[0], val1, val2])
        except:
            log_obj.error(traceback.format_exc())
    return json.dumps(rows)


@app.route('/resources')
def resources():
    data = None
    rows = {'data':[]}
    if app_config:
        try:
            db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
            data = db.getData(app_config.sql_select_resources).fetchall()
            for row in data:
                rows['data'].append([item for item in row])
        except:
            log_obj.error(traceback.format_exc())
    return json.dumps(rows)


@app.route('/query', methods=['GET', 'POST'])
def query():
    tabs = None
    if app_config:
        db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
        tabs = db.getData(app_config.sql_select_object).fetchall()
        if request.method == "POST":
            try:
                if request.form['qtype'] == 'SQL':
                    rows = db.getData(request.form['cmd'])
                else:
                    rows = None
                    db.executeCommand(request.form['cmd'])
                    db.commit()
            except:
                rows = None
                log_obj.error(traceback.format_exc())

            if rows:
                data = ["<thead>"]

                for column in rows.description:
                    data.append("<th>" + UnicodeDammit(column[0]).unicode_markup + "</th>")

                data.append("</thead>")
                data.append("<tbody>")

                for row in rows:
                    data.append("<tr>")
                    for col in row:
                        if col is not None:
                            if isinstance(col, basestring):
                                data.append("<td>" + UnicodeDammit(col).unicode_markup + "</td>")
                            else:
                                data.append("<td>" + str(col) + "</td>")
                        else:
                            data.append("<td>&nbsp;</td>")
                    data.append("</tr>")

                data.append("</tbody>")

                tbl = ''.join(data)
            else:
                tbl = None
        else:
            tbl = None
    else:
        tbl = None

    return render_template('query.html', data=tbl, objs=tabs)

@app.template_filter('datetime')
def format_datetime(value):
    return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y %H:%M:%S')

@app.template_filter('float')
def format_float(value):
    return '{:.6} %'.format(value)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
