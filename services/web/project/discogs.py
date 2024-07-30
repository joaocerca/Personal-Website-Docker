from flask import Blueprint, render_template, flash, redirect, url_for, logging, current_app
from flask_login import UserMixin, login_required
from .addons.forms import DiscogsForm
from wtforms.validators import ValidationError
from pymysql.err import IntegrityError
from os import getenv, path, environ
from dotenv import load_dotenv

import pandas as pd
import numpy as np
import requests
import json


load_dotenv("./.env")

api_token = environ.get("DISCOGS_API_TOKEN")

discogs = Blueprint('discogs', __name__, template_folder="templates")


@discogs.route('/backend/searchDiscogs', methods=['GET','POST'])
@login_required
def search_query():

    discogsForm = DiscogsForm()
    trackList_df = pd.DataFrame()

    if discogsForm.validate_on_submit():
        barcodeRelease = discogsForm.barcodeRelease.data
        current_app.logger.info(f'Barcode entered: {barcodeRelease}')        
        countryRelease = discogsForm.countryRelease.data

        url = getUrl(barcodeRelease, countryRelease)
        response = getConnection(url)['results']
        print(barcodeRelease + " and " + countryRelease)
        resource_url = getRelease(response)
        trackList_df = getTracklist(resource_url)


    # return redirect(url_for(f'/backend/resultDiscogs/barcode={barcodeRelease}&country={countryRelease}'))
    # return redirect(url_for())
    return render_template("search_discogs.html", discogsForm=discogsForm, table=[trackList_df.to_html()])



def getUrl(barcode, country):

    if country != '':
        url = f'https://api.discogs.com/database/search?barcode={barcode}&country={country}&token={api_token}'
        print("Hello")
    else:
        url =  f'https://api.discogs.com/database/search?barcode={barcode}&token={api_token}'
        print("Hello World!!!")

    return url


def getConnection(url):
    
    response = requests.get(url)
    if response != '':
        return response.json()
    else:
        current_app.logger.info(f'There are no results for this combination')
        return -1


def getRelease(results):
    resource_url = results[0]['resource_url']
    print(results[0]['country'])
    print(results[0]['year'])
    print(results[0]['format'])
    print(results[0]['title'])
    
    return resource_url



def getTracklist(resource_url):

    
    tracklist_df = pd.DataFrame(getConnection(resource_url)['tracklist'], columns=['position', 'title', 'duration'])
    
    # adds index from 1 to the column 'position'
    tracklist_df['position'] = np.arange(1, len(tracklist_df) + 1)
    
    return tracklist_df
