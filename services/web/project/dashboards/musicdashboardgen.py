from flask import Blueprint, render_template, render_template_string, make_response
from werkzeug import exceptions
from ..addons import dbconnection as dbconnect
from bokeh.layouts import column
from bokeh.models import (ColumnDataSource, DataTable, HoverTool, IntEditor,
                          NumberEditor, NumberFormatter, SelectEditor,
                          StringEditor, StringFormatter, TableColumn, ImportedStyleSheet, CrosshairTool, Span)
from bokeh.plotting import figure, show, curdoc
from bokeh.palettes import d3
from bokeh.transform import factor_cmap
from bokeh.embed import file_html, components
from bokeh.resources import CDN
from pandas import DatetimeIndex as dt

import numpy as np
import pandas as pd
import csv

musicdashboardgen = Blueprint('musicdashboardgen', __name__, template_folder="templates")

dbconnect.open_ssh_tunnel()
dbconnect.mysql_connect()



@musicdashboardgen.route("/musicdashboardgen")
def show_dashboard():

    cdn_files = CDN.js_files
 
    script1, (div_plot, div_table) = data_plot()

    return render_template("music_dashboard_gen.html", script1=script1, div_plot=div_plot, div_table=div_table, header=cdn_files)


def data_plot():

    curdoc().theme = "dark_minimal"

    cnx = dbconnect.mysql_connect()

  
    data_plot_df = dbconnect.run_query_to_df(sql="SELECT * FROM `data_plot_view`", connection=cnx)

    
    data_plot_df.rename(columns={'Artist':'artistname',
                                 'Country':'artistcountry',
                                 'Release Name':'releasename',
                                 'Year':'year',
                                 'Release ID':'releaseid',
                                 'Total Tracks':'totaltracks',
                                 'Total Duration':'totalduration',
                                 'Format':'format'}, inplace=True)
    
    
    ### converts 'totalduration' column into string and then slices the '0 days' part of the string 
    data_plot_df.totalduration = data_plot_df.totalduration.astype(str).map(lambda x: x[7:])


    format_release = data_plot_df['format']

    source = ColumnDataSource(data=data_plot_df)

    artist = sorted(data_plot_df["artistname"])
    country = sorted(data_plot_df["artistcountry"])
    release_name = sorted(data_plot_df["releasename"])
    year = sorted(data_plot_df["year"])
    release_id = sorted(data_plot_df["releaseid"])
    no_tracks = sorted(data_plot_df["totaltracks"])
    length = sorted(data_plot_df["totalduration"])
    format_type = sorted(data_plot_df["format"].unique())


    columns = [
        TableColumn(field="artistname", title="Artist",
                    editor=SelectEditor(),
                    formatter=StringFormatter(font_style="bold")),
        TableColumn(field="artistcountry", title="Country",
                    editor=StringEditor(completions=country)),
        TableColumn(field="releasename", title="Release Name",
                    editor=SelectEditor()),            
        TableColumn(field="year", title="Year", editor=IntEditor()),
        TableColumn(field="releaseid", title="Release ID",
                    editor=SelectEditor()),
        TableColumn(field="totaltracks", title="No of Tracks", editor=IntEditor()),
        TableColumn(field="totalduration", title="Length"),
        TableColumn(field="format", title="Format",
                    editor=SelectEditor(options=format_type)),
    ]
    
    
    data_table = DataTable(source=source, columns=columns, editable=True, width=1280,
                        index_position=-1, index_header="row index", index_width=60, sizing_mode='scale_width')
    

    width = Span(dimension="width", line_dash="dotted", line_width=1)
    height = Span(dimension="height", line_dash="dotted", line_width=1)

    p = figure(width=1000, height=300, tools="pan,wheel_zoom,xbox_select,reset", active_drag="xbox_select", sizing_mode='scale_width')

    colors = factor_cmap("format", palette=d3['Category10'][10], factors=format_type)

    release = p.circle(x="year", y="index", fill_color=colors , size=9, alpha=0.7, source=source)
    

    tooltips = [
        ("Artist", "@artistname"),
        ("Country", "@artistcountry"),
        ("Release Name", "@releasename"),
        ("Year", "@year"),
        ("Release ID", "@releaseid"),
        ("No of Tracks", "@totaltracks"),
        ("Length", "@totalduration"),
        ("Format", "@format")
    ]


    rel_hover_tool = HoverTool(renderers=[release], tooltips=[*tooltips])


    p.add_tools(rel_hover_tool, CrosshairTool(overlay=[width, height]))

    
    script1, (div_plot, div_table) = components((p, data_table), theme="dark_minimal")

    dbconnect.mysql_disconnect(cnx)

    return script1, (div_plot, div_table)


    