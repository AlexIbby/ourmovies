from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField, DateField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Length, Optional
from datetime import date

class ViewingForm(FlaskForm):
    tmdb_id = HiddenField(validators=[DataRequired()])
    media_type = HiddenField(validators=[DataRequired()])
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[Optional(), Length(max=1000)])
    watched_on = DateField('Date Watched', default=date.today, validators=[DataRequired()])
    rewatch = BooleanField('Rewatch', default=False)
    tags = StringField('Tags')  # Will be handled specially for tag chips
    submit = SubmitField('Save Viewing')
