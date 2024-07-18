from flask import Blueprint, render_template, request
from ..addons import dbconnection as dbconnect
from ..addons import forms as forms
import pandas as pd
import math
from math import pi
from bokeh.embed import components
from bokeh.io import show
from bokeh.models import (ColumnDataSource, GeoJSONDataSource, LinearColorMapper, ColorBar, DataTable, HoverTool, 
                          IntEditor, SelectEditor, StringEditor, StringFormatter, TableColumn, CrosshairTool, Span, Column, DatetimeTickFormatter, Whisker)
from bokeh.resources import CDN
from bokeh.plotting import figure
from bokeh.palettes import all_palettes
from bokeh.transform import cumsum, factor_cmap, jitter
from bokeh.io.doc import curdoc
from bokeh.settings import settings as sett

from collections import OrderedDict, defaultdict
from werkzeug import exceptions
import numpy as np
import json
from bokeh.sampledata.autompg import autompg
import geopandas as gpd
from datetime import datetime

BG_FILL_COLOR="lightgrey"
BG_FILL_ALPHA=0.2
TEXT_ALIGN="center"
TEXT_FONT_SIZE="25px"



musicdashboard = Blueprint('musicdashboard', __name__, template_folder="templates")

dbconnect.open_ssh_tunnel()
dbconnect.mysql_connect()

@musicdashboard.route("/musicdashboard", methods=['GET','POST'])
def show_dashboard():

    sett.log_level = "warn"

    cdn_files = CDN.js_files

    script1, div1 = stats_countries_plot_map()
    script2, div2 = stats_format_plot()
    script3, div3 = stats_rel_trx_plot()
    script4, div4 = stats_artists_genre()
    script5, div5 = stats_releases_plot()
    script6, (div_plot, div_table) = datatable_data_plot()

    
        
    return render_template('music_dashboard.html', script_countries=script1, script_formats=script2, script_rel_trx=script3,  script_genres=script4, script_releases=script5, script_plot_table=script6, div_countries=div1, div_formats=div2, div_rel_trx=div3, div_genres=div4, div_releases=div5, div_full_plot=div_plot, div_full_table=div_table, header=cdn_files)

def stats_countries_plot_map():

    pd.set_option('display.max_columns', None)

    cnx = dbconnect.mysql_connect()
   
    top_countries_df = dbconnect.run_query_to_df("SELECT artistcountry AS 'Country', COUNT(*) AS 'no_of_artists' FROM `tbl_artist` WHERE artistcountry NOT LIKE '%/%' GROUP BY artistcountry ORDER BY COUNT(*) DESC;", connection=cnx)

    dbconnect.mysql_disconnect(cnx)

    top_countries_df['Country'] = top_countries_df['Country'].str.strip()

    shapefile = 'website/static/maps/ne_110m_admin_0_countries/ne_110m_admin_0_countries.shp'

    gdf = gpd.read_file(shapefile)[['ADMIN', 'ISO_A2_EH', 'geometry']]


    gdf.rename(columns={'ADMIN':'country','ISO_A2_EH':'country_code','geometry':'geometry'}, inplace=True)

    # gdf['country'] == 'Antartica'] returns the df and checks which line is 'Antartica'
    # gdf[gdf['country'] == 'Antarctica'] returns the position of 'Antartica' 

    gdf = gdf.drop(gdf.index[159])

    merged = gdf.merge(top_countries_df,left_on='country_code', right_on='Country', how='outer')
    
    merged['Country'] = merged['Country'].combine_first(merged['country_code'])
    merged.no_of_artists.fillna(value=0, inplace=True)

    # in order to generate the map, the data needs to be put into json and then GeoJSONDataSource
    merged_json = json.loads(merged.to_json())
    json_data = json.dumps(merged_json)    
    geosource = GeoJSONDataSource(geojson=json_data)

    palette = all_palettes['Iridescent'][14]    
    color_mapper = LinearColorMapper(palette=palette, low_color='gray', low=1.0, high = merged.no_of_artists.max())

    # Creates the color bar. 
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8,width = 500, height = 20, border_line_color=None,location = (0,0), orientation = 'horizontal')

    # Creates the figure object.
    p = figure(height=650, width=1200, toolbar_location='right', tooltips="@country: @no_of_artists", sizing_mode="scale_both")
    p.xgrid.grid_line_color = 'lightgrey'
    p.ygrid.grid_line_color = 'lightgrey'
    p.title.text = "Number of artists by country"
    p.title.align = TEXT_ALIGN
    p.title.text_font_size = TEXT_FONT_SIZE
    p.background_fill_color = BG_FILL_COLOR
    p.background_fill_alpha = BG_FILL_ALPHA

    #Add patch renderer to figure. 
    p.patches('xs','ys', source=geosource, color={'field' :'no_of_artists', 'transform':color_mapper},line_color = 'black', line_width = 0.25, fill_alpha = 1)
    p.add_layout(color_bar, 'below')

    script, div = components(p)
    div_new = "<div class=\"col\" " + div[4:]

    return script, div_new


def stats_format_plot():

    cnx = dbconnect.mysql_connect()

    query = "SELECT tbl_format.formatdesc AS formatdesc, COUNT(tbl_release.releasename) AS total_numbers FROM `tbl_release` JOIN `tbl_format` ON tbl_release.releaseformat = tbl_format.formatname GROUP BY releaseformat;"

    format_numbers_df = dbconnect.run_query_to_df(query, connection=cnx).set_index('formatdesc')

    dbconnect.mysql_disconnect(cnx)


    color = {
        "Compact Disc": "lightskyblue",
        "Compact Disc + Disc Versatile Disc": "sandybrown",
        "Digital Versatile Disc": "orangered",
        "Digital": "crimson",
        "Extended Play": "gold",
        "Cassette":"mediumorchid",
        "Super audio CD": "mediumvioletred",
        "Vinyl": "forestgreen"
    }

    # Gets the available formats inside the df from the SQL Query
    formats = format_numbers_df.index.to_list()

    # Gets the colors of the available formats from the SQL Query
    avail_colors = [color[format] for format in formats]

    # Gets the values for each format
    data_raw = format_numbers_df["total_numbers"].to_dict()

    # zip() aggregates both lists
    # format_colors_dict = dict(zip(formats, avail_colors))

    # Calculates the share of each element of the DataFrame of the SQL query result
    share = format_numbers_df.total_numbers.map(lambda x: x/format_numbers_df.total_numbers.sum()*100)

    # Calculates the angles for each % of element
    angles = share.map(lambda x: 2*pi*(x/100)).cumsum().to_list() 

    format_numbers_source = ColumnDataSource(dict(        
        start  = [0] + angles[:-1],
        end    = angles,
        format = formats,
        colors = [color[format] for format in formats],
        values = [data_raw[format] for format in formats],
        share = share
    ))
 
    p = figure(height=500, x_range=(-0.75, 0.80), toolbar_location="left", sizing_mode="fixed", tools="hover, box_zoom, pan", tooltips="@format: @values (@share %)")

    p.annular_wedge(x=0, y=0, inner_radius=0.30, outer_radius=0.5,
                     start_angle='start', end_angle='end',
                     line_color="white", line_width=0.5, fill_color="colors", legend_field="format", source=format_numbers_source)
    
    p.legend.background_fill_alpha = 0.6
    
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    p.title.text ="Total number of releases by format"
    p.title.align = TEXT_ALIGN
    p.title.text_font_size = TEXT_FONT_SIZE
    p.background_fill_color = BG_FILL_COLOR
    p.background_fill_alpha = BG_FILL_ALPHA
    

    script, div = components(p)
    div_new = "<div class=\"col-md-auto\" " + div[4:]

    return script, div_new



def stats_rel_trx_plot():

    cnx = dbconnect.mysql_connect()
    rt_len_df = dbconnect.run_query_to_df("SELECT SEC_TO_TIME(AVG(TIME_TO_SEC(`Total Duration`))) AS `rel_avg_len`, SEC_TO_TIME(AVG(TIME_TO_SEC(`tracklength`))) AS `trx_avg_len` FROM durations_view; ", connection=cnx)
    longest_rel_df = dbconnect.run_query_to_df("SELECT DISTINCT `Artist`, `Release Name`, `Total Duration` FROM `durations_view` ORDER BY `Total Duration` DESC LIMIT 10;", connection=cnx).rename(columns={'Artist':'artist', 'Release Name':'release_name','Total Duration':'total_duration'})
    shortest_rel_df = dbconnect.run_query_to_df("SELECT DISTINCT `Artist`, `Release Name`, `Total Duration` FROM `durations_view` WHERE `Total Duration` IS NOT NULL ORDER BY `Total Duration` ASC LIMIT 10;",connection=cnx).rename(columns={'Artist':'artist', 'Release Name':'release_name','Total Duration':'total_duration'})
    longest_trx_df = dbconnect.run_query_to_df("SELECT DISTINCT * FROM durations_view WHERE `tracklength` IS NOT NULL AND `Artist` IS NOT NULL ORDER BY `durations_view`.`tracklength` DESC LIMIT 10;",connection=cnx).rename(columns={'Artist':'artist', 'Release Name':'release_name','tracktitle':'track_title','Total Duration':'total_duration'})
    shortest_trx_df = dbconnect.run_query_to_df("SELECT DISTINCT * FROM durations_view WHERE `tracklength` IS NOT NULL AND `Artist` IS NOT NULL ORDER BY `durations_view`.`tracklength` ASC LIMIT 10;",connection=cnx).rename(columns={'Artist':'artist', 'Release Name':'release_name','tracktitle':'track_title','Total Duration':'total_duration'})

    dbconnect.mysql_disconnect(cnx)


    rt_len_df.rel_avg_len = rt_len_df.rel_avg_len.astype(str).map(lambda x: x[7:15])
    rt_len_df.trx_avg_len = rt_len_df.trx_avg_len.astype(str).map(lambda x: x[7:15])
    longest_rel_df.total_duration = longest_rel_df.total_duration.astype(str).map(lambda x: x[7:15])
    shortest_rel_df.total_duration = shortest_rel_df.total_duration.astype(str).map(lambda x: x[7:15])
    longest_trx_df.tracklength = longest_trx_df.tracklength.astype(str).map(lambda x: x[7:15])
    shortest_trx_df.tracklength = shortest_trx_df.tracklength.astype(str).map(lambda x: x[7:15])
    

    def generate_plot(df, tooltips, field, palette, title, location):

        categories = list(sorted(df.title.unique()))

        p = figure(height=250, x_range=categories, tools="hover,pan,box_zoom,xbox_select,reset", tooltips=[*tooltips], title=title, toolbar_location=location)
        p.ygrid.grid_line_color = None
        p.yaxis.visible = False
        p.background_fill_color = BG_FILL_COLOR
        p.background_fill_alpha = BG_FILL_ALPHA

        g = df.groupby('title')
        
        upper = g[field].max()
        lower = g[field].min()

        source = ColumnDataSource(data=dict(base=categories, upper=upper, lower=lower))

        error = Whisker(base="base", upper="upper", lower="lower", source=source, level="annotation", line_width=2)
        error.upper_head.size=20
        error.lower_head.size=20
        p.add_layout(error)

        p.circle(jitter("title", 0.3, range=p.x_range), field, source=df,
            alpha=0.5, size=13, line_color="white",
            color=factor_cmap("title", palette, categories))  
        
        return p


    '''
    Releases Dataframes    
    '''

    average_rel_df = pd.DataFrame({'title':['average duration'], 'artist':['NaN'], 'release_name':['NaN'], 'total_duration': [rt_len_df.rel_avg_len[0]], 'total_duration_str': [rt_len_df.rel_avg_len[0]]})
    longest_rel_df.insert(0, "title", "longest releases")
    shortest_rel_df.insert(0, "title", "shortest releases")
    # ordering from longest to shortest
    shortest_rel_df = shortest_rel_df[::-1].reset_index(drop = True)

    # duplicating total_duration column for the tooltips
    longest_rel_df['total_duration_str'] = longest_rel_df.loc[:, 'total_duration']
    shortest_rel_df['total_duration_str'] = shortest_rel_df.loc[:, 'total_duration']

    # grouping all the releases dataframes in a single dataframe
    releases_df = pd.concat([longest_rel_df, average_rel_df, shortest_rel_df], ignore_index=True)
    
    releases_df.total_duration = pd.to_datetime(releases_df.total_duration,format= '%H:%M:%S').dt.time
   
    tooltips1 = [("Artist","@artist"), ("Release Name", "@release_name"), ("Total Duration", "@total_duration_str")]
    palette1 = ['#fa9fb5', '#e6550d', '#bd9e39']

    title = "Overall stats about releases"

    p1 = generate_plot(releases_df, tooltips1, "total_duration", palette1, title, "right")     



    '''
    Tracks Dataframes    
    '''
    
    average_trx_df = pd.DataFrame({'title':['average duration'], 'artist':['NaN'], 'track_title':['NaN'], 'release_name':['NaN'], 'tracklength': [rt_len_df.trx_avg_len[0]], 'track_length_str': [rt_len_df.trx_avg_len[0]]})
    longest_trx_df.insert(0, "title", "longest tracks")
    shortest_trx_df.insert(0, "title", "shortest tracks")

    # ordering from shortest to longest
    longest_trx_df = longest_trx_df[::-1].reset_index(drop = True)
    
    # duplicating tracklength column for the tooltips
    longest_trx_df['track_length_str'] = longest_trx_df.loc[:, 'tracklength']
    shortest_trx_df['track_length_str'] = shortest_trx_df.loc[:, 'tracklength']

    # grouping all the tracks dataframes in a single dataframe
    tracks_df = pd.concat([shortest_trx_df, average_trx_df, longest_trx_df], ignore_index=True)

    # dfc['Time_of_Sail'] = pd.to_datetime(dfc['Time_of_Sail'],format= '%H:%M:%S' ).dt.time 
    tracks_df.tracklength = pd.to_datetime(tracks_df.tracklength,format= '%H:%M:%S').dt.time

    tooltips2 = [("Artist","@artist"), ("Track Title", "@track_title"), ("Release Name", "@release_name"), ("Track Length", "@track_length_str")]
    palette2 = ['#ff7f0e', '#17becf', '#9467bd']
    title = "Overall stats about tracks"

    p2 = generate_plot(tracks_df, tooltips2, "tracklength", palette2, title, "left") 

    r = Column(children=[p1, p2], sizing_mode="fixed", flow_mode="block")

    script, div = components(r)
    div_new = "<div class=\"col-md-auto\" " + div[4:] 

    return script, div_new
 

def stats_artists_genre():

    cnx = dbconnect.mysql_connect()

    query = "SELECT `artistgenre1` AS `genre`, COUNT(*) AS `artists_per_genre` FROM tbl_artist WHERE `artistgenre1` NOT LIKE \"\" GROUP BY `artistgenre1` ORDER BY COUNT(*) DESC;"

    genres_df = dbconnect.run_query_to_df(query, connection=cnx)
    
    dbconnect.mysql_disconnect(cnx)
    
    # Calculation for the share of the genres and the angles for the chart
    genres_df['share'] = genres_df['artists_per_genre']/genres_df['artists_per_genre'].sum() * 100
    genres_df['angle'] = genres_df['artists_per_genre']/genres_df['artists_per_genre'].sum() * 2*pi

    # Aggregate by share and reduce the number of items
    aggregated = genres_df.groupby("genre").sum(numeric_only=True)
    selected = aggregated[aggregated.share >= 1.5].copy()
    selected.loc["Other"] = aggregated[aggregated.share < 1.5].sum()   
   
    # Selection of colors for the chart
    palette = all_palettes['PiYG'][len(selected)]
    selected['color'] = palette
    
    p = figure(height=500, title="Number of artists per genre", toolbar_location="right",
           tools="hover, box_zoom, pan", tooltips="@genre: @artists_per_genre", x_range=(-0.70, 0.85))

    p.wedge(x=0, y=1, radius=0.5,
        start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
        line_color="white", fill_color='color', legend_field='genre', source=selected)
    
    p.legend.background_fill_alpha = 0.6

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    p.title.align = TEXT_ALIGN
    p.title.text_font_size = TEXT_FONT_SIZE
    p.background_fill_color = BG_FILL_COLOR
    p.background_fill_alpha = BG_FILL_ALPHA

    script, div = components(p)
    div_new = "<div class=\"col-md-auto\" " + div[4:]

    return script, div_new


def stats_releases_plot():
   
    cnx = dbconnect.mysql_connect()

    releases_numbers_df = dbconnect.run_query_to_df("SELECT releaseyear, COUNT(*) AS 'releases_per_year' FROM `tbl_release` GROUP BY releaseyear ASC;", connection=cnx)

    dbconnect.mysql_disconnect(cnx)

    years = releases_numbers_df["releaseyear"].tolist()
    releases = releases_numbers_df["releases_per_year"].tolist()
    
    tooltips = [("Year","@x"), ("Number of releases", "@top")]

    p = figure(sizing_mode="stretch_width", tools="pan,wheel_zoom,box_zoom,reset,hover", tooltips=[*tooltips])
    p.vbar(x=years, top=releases, width=0.7, bottom=0, line_join='bevel')
    p.y_range.start = 0  
    p.background_fill_color = BG_FILL_COLOR
    p.background_fill_alpha = BG_FILL_ALPHA

    # Title components
    p.title.text = "Number of releases by year"
    p.title.align = TEXT_ALIGN
    p.title.text_font_size = TEXT_FONT_SIZE

    script, div = components(p)

    return script, div


def datatable_data_plot():

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
    
    
    dbconnect.mysql_disconnect(cnx)

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
    p.title.text = "Database general overview with table"
    p.title.align = TEXT_ALIGN
    p.title.text_font_size = TEXT_FONT_SIZE
    p.background_fill_color = BG_FILL_COLOR
    p.background_fill_alpha = BG_FILL_ALPHA

    palette = all_palettes['Category10'][10]

    colors = factor_cmap("format", palette=palette, factors=format_type)

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


    return script1, (div_plot, div_table)



