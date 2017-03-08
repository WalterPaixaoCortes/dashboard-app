import labio.configWrapper
import labio.logWrapper
import labio.dbWrapper
import os
import traceback
import datetime

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

app_config = labio.configWrapper.load_configuration('application.config')
if app_config:
    pass
    # log_obj = labio.logWrapper.return_logging(app_config.log)


@app.route('/')
def home():
    data_rows1 = None
    data_rows2 = None
    data_rows3 = None
    data_rows4 = None
    data_rows5 = None
    data_rows6 = None
    data_rows7 = None
    data_rows8 = None
    if app_config:
        db = labio.dbWrapper.dbGenericWrapper(app_config.database).getDB()
        data_rows1 = db.getData(app_config.sql_select_priority1).fetchall()
        data_rows2 = db.getData(app_config.sql_select_priority2).fetchall()
        data_rows3 = db.getData(app_config.sql_select_stats).fetchall()
        data_rows4 = db.getData(app_config.sql_select_priorities).fetchall()
        data_rows5 = db.getData(app_config.sql_select_type_count).fetchall()
        data_rows6 = db.getData(app_config.sql_select_totals).fetchall()
        data_rows7 = db.getData(app_config.sql_select_service).fetchall()
        data_rows8 = db.getData(app_config.sql_select_vcloud).fetchall()
    return render_template('index.html', list1=data_rows1, 
    list2=data_rows2, 
    list3=data_rows3, 
    list4=data_rows4,
    list5=data_rows5,
    list6=data_rows6,
    list7=data_rows7,
    list8=data_rows8
    )


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
                    # db.executeCommand(request.form['cmd'])
                    # db.commit()
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
    return datetime.datetime.strptime(value,'%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y %H:%M:%S')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8080")


