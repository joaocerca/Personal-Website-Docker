from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, FormField, SelectField, SelectMultipleField, IntegerField, DecimalField, DateTimeField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, InputRequired, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .. import dbase



# Create a Form Class
class ArtistForm(FlaskForm):
    artistName = StringField("Artist Name", validators=[InputRequired(), Length(max=60)])
    artistCountry = StringField("Artist Country", validators=[InputRequired(), Length(max=15)])
    submit = SubmitField("Submit artist")

class ReleaseForm(FlaskForm):
    artistName = StringField("Artist Name", validators=[InputRequired(), Length(max=60)])
    releaseName = StringField("Release Name", validators=[InputRequired(), Length(max=60)])
    releaseFormat = SelectField("Release Format", 
                                choices=[('CD','Compact Disc'),
                                         ('CD+DVD','Compact Disc + Disc Versatile Disc'),
                                         ('D','Digital'),
                                         ('DVD', 'Digital Versatile Disc'),
                                         ('EP', 'Extended Play'),
                                         ('K7','Cassette'),
                                         ('SACD', 'Super audio CD'),
                                         ('V','Vinyl')], 
                                validators=[InputRequired()])
    releaseYear = IntegerField("Release Year", validators=[InputRequired(), NumberRange(min=1900)])    
    isCompilation = SelectField("Is Compilation:", choices=[('Y', 'Yes'), ('N', 'No')])
    releaseDesc = StringField("Release Description", validators=[Optional(), Length(max=30)])
    recordingType = StringField("Recording Type", validators=[InputRequired(), Length(max=10)])
    releaseNotes = StringField("Release Notes", validators=[Length(max=40)])
    releaseNoTracks = IntegerField("Number of Tracks", validators=[InputRequired(), NumberRange(min=1)])
    releaseLength = StringField("Release Total Length (format hhmmss)", validators=[InputRequired(), Length(max=10)])
    submit = SubmitField("Submit")


class TrackForm(FlaskForm):
    artistName = StringField("Artist Name", validators=[InputRequired(), Length(max=60)])
    releaseName = StringField("Release Name", validators=[InputRequired(), Length(max=30)])
    trackTitle = StringField("Track Name", validators=[InputRequired()])
    trackNo = IntegerField("Track No", validators=[InputRequired(), NumberRange(min=1)])
    trackLength = StringField("Track Length (format mmss)", validators=[InputRequired()])
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class User(dbase.Model, UserMixin):
    __tablename__ = 'user'
    id = dbase.Column(dbase.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    username = dbase.Column(dbase.String(1000))
    password = dbase.Column(dbase.String(100))

    # def set_password(self, password):
    #     """Create hashed password."""
    #     self.password = generate_password_hash(password, method='sha256')

class DiscogsForm(FlaskForm):
    # barcodeRelease = StringField("Barcode of the Release", validators=[InputRequired(), Length(max=40)])
    barcodeRelease = TextAreaField("Barcode of the Release", validators=[InputRequired(), Length(max=40)])
    countryRelease = StringField("Country of the Release", validators=[Length(max=30)])
    submit = SubmitField("Submit")
