from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, EqualTo, Email, NumberRange
from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, IntegerField, SubmitField, DateField, validators


class LoginForm(FlaskForm):
    username = StringField([validators.Length(min=1, max=30)], render_kw={"placeholder": "Username"})
    password = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField('Submit')

class EditRentalPin(FlaskForm):
    rentalName = StringField([validators.Length(min=2, max=35)], render_kw={"placeholder": "Rental Name"})
    price = IntegerField([validators.NumberRange(min=0, max=350000)], render_kw={"placeholder": "Price"})
    rooms = IntegerField([validators.NumberRange(min=0, max=100)], render_kw={"placeholder": "Rooms"})
    description = TextAreaField([validators.Length(min=10)], render_kw={"placeholder": "Decription"})
    link = StringField([validators.Length(min=4, max=355)], render_kw={"placeholder": "Link"})
    passwordUser = PasswordField([validators.InputRequired()], render_kw={"placeholder": "User Password"})
    passwordGroup = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Group Password"})
    submit = SubmitField("Submit")

class EditRestaurantPin(FlaskForm):
    name = StringField([validators.Length(min=2, max=35)], render_kw={"placeholder": "Name"})
    description = TextAreaField([validators.Length(min=10)], render_kw={"placeholder": "Decription"})
    link = StringField([validators.Length(min=4, max=355)], render_kw={"placeholder": "Link"})
    type = SelectField("Type", choices=[('Restaurant', 'Restaurant'), ('Nightclub', 'Nightclub')])
    passwordUser = PasswordField([validators.InputRequired()], render_kw={"placeholder": "User Password"})
    passwordGroup = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Group Password"})
    submit = SubmitField("Submit")

class EditTransportationPin(FlaskForm):
    name = StringField([validators.Length(min=2, max=35)], render_kw={"placeholder": "Name"})
    date = StringField([validators.Length(min=4, max=35)], render_kw={"placeholder": "Dates"})
    price = IntegerField([validators.NumberRange(min=0, max=100000)], render_kw={"placeholder": "Price"})
    description = TextAreaField([validators.Length(min=10)], render_kw={"placeholder": "Decription"})
    link = StringField([validators.Length(min=4, max=355)], render_kw={"placeholder": "Link"})
    type = SelectField("Type", choices=[('Flight', 'Flight'), ('Train', 'Train'), ('Bus', 'Bus'), ('Other', 'Other')])
    passwordUser = PasswordField([validators.InputRequired()], render_kw={"placeholder": "User Password"})
    passwordGroup = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Group Password"})
    submit = SubmitField("Submit")

class EditActivityPin(FlaskForm):
    name = StringField([validators.Length(min=2, max=35)], render_kw={"placeholder": "Name"})
    description = TextAreaField([validators.Length(min=10)], render_kw={"placeholder": "Decription"})
    link = StringField([validators.Length(min=4, max=355)], render_kw={"placeholder": "Link"})
    type = SelectField("Type", choices=[('Indoor', 'Indoor'), ('Outdoor', 'Outdoor')])
    passwordUser = PasswordField([validators.InputRequired()], render_kw={"placeholder": "User Password"})
    passwordGroup = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Group Password"})
    submit = SubmitField("Submit")

class SignupForm(FlaskForm):
    firstName = StringField('First Name:', [validators.Length(min=1, max=30)], render_kw={"placeholder": "First Name"})
    lastName = StringField('Last Name:', [validators.Length(min=1, max=30)], render_kw={"placeholder": "Last Name"})
    username = StringField('Username:', [validators.Length(min=1, max=30)], render_kw={"placeholder": "Username"})
    email = StringField('Email:', [validators.Email()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password:', [
    validators.InputRequired(),
    validators.EqualTo('confirm', message='Passwords do not match.')], render_kw={"placeholder": "Password"})
    confirm = PasswordField('Confirm Password:', render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Submit')

class EditProfileForm(FlaskForm):
    firstName = StringField('First Name:', [validators.Length(min=1, max=30)], render_kw={"placeholder": "First Name"})
    lastName = StringField('Last Name:', [validators.Length(min=1, max=30)], render_kw={"placeholder": "Last Name"})
    username = StringField('Username:', [validators.Length(min=1, max=30)], render_kw={"placeholder": "Username"})
    email = StringField('Email:', [validators.Email()], render_kw={"placeholder": "Email"})
    password = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField('Submit')

class GroupForm(FlaskForm):
    groupName = StringField('Group Name:', [validators.Length(min=2, max=30)], render_kw={"placeholder": "Group Name"})
    location = StringField('Location', [validators.Length(min=2, max=30)], render_kw={"placeholder": "Location"})
    dates = StringField('Dates:', [validators.Length(min=5, max=45)], render_kw={"placeholder": "Dates"})
    password = PasswordField('Password:', [
    validators.InputRequired(),
    validators.EqualTo('confirm', message='Passwords do not match.')], render_kw={"placeholder": "Password"})
    confirm = PasswordField('Confirm Password:', render_kw={"placeholder": "Confirm password"})
    description = TextAreaField('Description/Message:', [validators.Length(min=10, max=500)], render_kw={"placeholder": "Description/Message"})
    submit = SubmitField('Submit')

class DeleteProfileForm(FlaskForm):
    password = PasswordField([validators.InputRequired()], render_kw={'placeholder': 'Password'})
    yes = SubmitField('Yes')

class RentalPinForm(FlaskForm):
    rentalName = StringField('Name:', [validators.Length(min=2, max=40)], render_kw={"placeholder": "Rental Name"})
    price = IntegerField('Price:', [validators.NumberRange(min=0, max=10000)], render_kw={"placeholder": "Price"})
    rooms = IntegerField('Rooms', [validators.NumberRange(min=0, max=35)], render_kw={"placeholder": "Rooms"})
    description = TextAreaField('Description:', [validators.Length(min=10)], render_kw={"placeholder": "Description"})
    link = StringField('Link to this rental:', [validators.Length(min=5, max=255)], render_kw={"placeholder": "Link"})
    submit1 = SubmitField('Submit')
    # Images(blob) TODO

class RestPinForm(FlaskForm):
    restName = StringField('Name:', [validators.Length(min=2, max=40)], render_kw={"placeholder": "Name"})
    description2 = TextAreaField('Description:', [validators.Length(min=10)], render_kw={"placeholder": "Description"})
    link2 = StringField('Link:', [validators.Length(min=5, max=255)], render_kw={"placeholder": "Link"})
    type = SelectField('Type', choices=[('Restaurant', 'Restaurant'), ('Nightclub', 'Nightclub')])
    submit2 = SubmitField('Submit')

class ActivityPinForm(FlaskForm):
    activityName = StringField('Name', [validators.Length(min=4, max=40)], render_kw={"placeholder": "Activity Name"})
    description = TextAreaField('Description', [validators.Length(min=4)], render_kw={"placeholder": "Description"})
    link = StringField('Link', [validators.Length(min=6, max=255)], render_kw={"placeholder": "Link"})
    type = SelectField('Type', choices=[('Indoor', 'Indoor'), ('Outdoor', 'Outdoor')])
    submit4 = SubmitField('Submit')

class TransportationPinForm(FlaskForm):
    name = StringField([validators.Length(min=3, max=45)], render_kw={"placeholder": "Name"})
    price3 = IntegerField([validators.NumberRange(min=0, max= 1000000)], render_kw={"placeholder": "Price"})
    date = StringField(render_kw={"placeholder": "Date"})
    link3 = StringField([validators.Length(min=5, max=255)], render_kw={"placeholder": "Link"})
    description3 = TextAreaField([validators.Length(min=10, max=500)], render_kw={"placeholder": "Description"})
    type = SelectField("Type", choices=[('Flight', 'Flight'), ('Train', 'Train'), ('Bus', 'Bus'), ('Rental Car', 'Rental Car'), ('Other', 'Other')])
    submit3 = SubmitField('Submit')

class EditGroupForm(FlaskForm):
    name = StringField([validators.Length(min=2, max=30)], render_kw={"placeholder": "Group Name"})
    location = StringField([validators.Length(min=2, max=35)], render_kw={"placeholder": "Location"})
    dates = StringField([validators.Length(min=5, max=35)], render_kw={"placeholder": "Dates"})
    description = TextAreaField([validators.Length(min=10)], render_kw={"placeholder": "Description/Message"})
    groupPassword = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Group Password"})
    password = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Your Password"})
    submit = SubmitField('Submit')

class DeleteGroupForm(FlaskForm):
    passwordUser = PasswordField([validators.InputRequired()], render_kw={'placeholder': 'User Password'})
    passwordGroup = PasswordField([validators.InputRequired()], render_kw={'placeholder': 'Group Password'})
    yes = SubmitField('Yes')

class JoinGroupForm(FlaskForm):
    name = StringField([validators.Length(min=2, max=35)], render_kw={"placeholder": "Group Name"})
    password = PasswordField([validators.InputRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField()

class DeletePinForm(FlaskForm):
    passwordUser = PasswordField([validators.InputRequired()], render_kw={'placeholder': 'User Password'})
    passwordGroup = PasswordField([validators.InputRequired()], render_kw={'placeholder': 'Group Password'})
    yes = SubmitField('Yes')
