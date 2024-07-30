from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request, jsonify
from flask_login import UserMixin, login_required
from .addons.forms import ArtistForm, ReleaseForm, TrackForm
from .addons import dbconnection as dbconnect
from wtforms.validators import ValidationError
from pymysql.err import IntegrityError
import pandas as pd
from os import getenv


database = Blueprint('database', __name__, template_folder="templates")

dbconnect.open_ssh_tunnel()

@database.route("/backend/database/tblArtist")
@login_required
def db_artist_show():
    
    current_app.logger.info("Show list of artists.")

    cnx = dbconnect.mysql_connect()

    result = dbconnect.run_query("SELECT * FROM tbl_artist", 0, cnx)
    
    dbconnect.mysql_disconnect(cnx)

    return render_template('query_artists.html', list=result)
    


@database.route("/backend/database/tblRelease")
@login_required
def db_release_show():

    current_app.logger.info("Show list of releases.")

    cnx = dbconnect.mysql_connect()

    result = dbconnect.run_query("SELECT * FROM tbl_release", 0, cnx)
    
    dbconnect.mysql_disconnect(cnx)

    return render_template('query_releases.html', list=result)
   

@database.route("/backend/database/tblTrack")
@login_required
def db_track_show():

    current_app.logger.info("Show list of tracks.")

    cnx = dbconnect.mysql_connect()

    result = dbconnect.run_query("SELECT * FROM tbl_track ORDER BY releaseid ASC", 0, cnx)

    dbconnect.mysql_disconnect(cnx)

    return render_template('query_tracks.html', list=result)
    


@database.route('/backend/database/addArtist', methods=['GET','POST'])
@login_required
def add_artist():

    current_app.logger.info("Adding new artist.")

    artistForm = ArtistForm()

    cnx = dbconnect.mysql_connect()

    try:

        if artistForm.validate_on_submit():

            artistName = artistForm.artistName.data
            artistCountry = artistForm.artistCountry.data

            current_app.logger.info(f'Artist added to the library: {artistName}')


            sql_query = f'INSERT INTO tbl_artist (artistname, artistcountry) VALUES("{artistName}","{artistCountry}")'

            try:
                dbconnect.run_query(sql_query, 1, cnx)
                flash(f'{artistName} added to the DB')
                current_app.logger.info("Artist added to the DB.")

            except IntegrityError:
                current_app.logger.warning("Artist exists in the database.")
                flash(f'{artistName} is already in the DB!')
    
        dbconnect.mysql_disconnect(cnx)

        return render_template("add_artist.html", artistForm=artistForm)   
        # else:
        #     current_app.logger.warning(f'Something went wrong. {artistName} was not added!!!!')
    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500


    


@database.route("/backend/database/addRelease", methods=['GET','POST'])
@login_required
def add_release():

    current_app.logger.info("Adding new release.")

    releaseForm = ReleaseForm()
        
    cnx = dbconnect.mysql_connect()
    
    if releaseForm.validate_on_submit():
            
        artistName = releaseForm.artistName.data
        releaseName = releaseForm.releaseName.data
        releaseFormat = releaseForm.releaseFormat.data
        releaseYear = releaseForm.releaseYear.data
        isCompilation = releaseForm.isCompilation.data
        releaseDesc = releaseForm.releaseDesc.data
        recordingType = releaseForm.recordingType.data
        releaseNotes = releaseForm.releaseNotes.data
        releaseNoTracks = releaseForm.releaseNoTracks.data
        releaseLength = releaseForm.releaseLength.data

        sql_query = f'INSERT INTO tbl_release VALUES ("{releaseName}","{releaseFormat}","{releaseYear}",(SELECT artistid FROM tbl_artist WHERE artistname = "{artistName}"),"{isCompilation}","{releaseDesc}","{recordingType}","{releaseNotes}",CONCAT(releaseformat, LEFT(artistid,4), LEFT(recordingtype,1), FLOOR(1 + (RAND() * 9999)), iscompilation),"{releaseNoTracks}",CONVERT("{releaseLength}", TIME));'
        dbconnect.run_query(sql_query, 1, cnx)
        
        current_app.logger.info("Releases added to the DB.")
        flash(f'{releaseName} added to the DB')

        return redirect(url_for('database.add_release'))
    
    dbconnect.mysql_disconnect(cnx)
    
    return render_template("add_release.html", releaseForm=releaseForm)


@database.route("/backend/database/addTrack", methods=['GET', 'POST'])
@login_required
def add_track():

    trackForm = TrackForm()

    cnx = dbconnect.mysql_connect() 
     
    if trackForm.validate_on_submit():
            
        artistName = trackForm.artistName['artistName']
        releaseName = trackForm.releaseName['releaseName']
        trackTitle = trackForm.trackTitle['trackTitle']
        trackNo = trackForm.trackNo['trackNo']
        trackLength = trackForm.trackLength['trackLength']       


        print(artistName, releaseName, trackTitle, trackNo, trackLength)            
        
        # 'artists_releases_ids' is a View inside the DB
        sql_query = f'INSERT INTO tbl_track (trackTitle, trackno, tracklength, releaseid) SELECT "{trackTitle}","{trackNo}",CONVERT("{trackLength}", TIME), releaseid FROM artists_releases_ids WHERE releasename = "{releaseName}" AND artistname = "{artistName}";'
                    
        dbconnect.run_query(sql_query, 1, cnx)
    
        flash(f'{trackTitle} added to the DB')

        return redirect(url_for('database.add_track'))
    
    dbconnect.mysql_disconnect(cnx)
    
    return render_template("add_track.html", trackForm=trackForm)

