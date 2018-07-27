from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_wtf import FlaskForm, Form
from flask_mysqldb import MySQL
from wtforms.validators import DataRequired, Length, EqualTo, Email, NumberRange
from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, IntegerField, SubmitField, DateField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_bootstrap import Bootstrap
from forms import *
from confi import *
from classes import *
#from routes import *
#from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


socketio = SocketIO(app)

groups = []

@app.route('/')
def gettin():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm(request.form)
    if form.validate_on_submit():
        f_Name = form.firstName.data
        l_Name = form.lastName.data
        u_name = form.username.data
        e_mail = form.email.data
        e_verified = 0
        p_word = sha256_crypt.encrypt(str(form.password.data))

        #create cursor
        cur = mysql.connection.cursor()

        check = cur.execute("SELECT * FROM users WHERE username = %s", [u_name])
        check2 = cur.execute("SELECT * FROM users WHERE email = %s", [e_mail])
        if check > 0:
            #close
            cur.close()

            error = "That username is already in use, sorry."
            return render_template("signup.html", error=error, form=form)
        elif check2 > 0:
            cur.close()
            error = "That email address is already in use"
            return render_template("signup.html", error=error, form=form)
        else:
            cur.execute("INSERT INTO users(firstName, lastName, username, email, password, e_verified) VALUES(%s, %s, %s, %s, %s, %s)", (f_Name, l_Name, u_name, e_mail, p_word, e_verified))

            #Commit to Database
            mysql.connection.commit()

            #Close connection
            cur.close()

            flash("Congrats, your are registered, you can now login once you confirm your email")
            msg = Message("Email Confirmation", sender=app.config['MAIL_USERNAME'], recipients=[e_mail])
            msg.html = render_template("verify_email.html")
            mail.send(msg)
            return redirect(url_for('login'))

    return render_template('signup.html',form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        username = form.username.data
        password_candidate = form.password.data

        #Create DictCursor
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            data = cur.fetchone()
            password, verified = data['password'], data['e_verified']

            if sha256_crypt.verify(password_candidate, password):
                if verified == 0:
                    error = 'You must verifiy your email first'
                    return render_template('login.html', error=error, form=form)
                session['logged_in'] = True
                session['username'] = username
                userId = data['userId']
                cur.execute("SELECT * FROM user_group WHERE userId = %s", [userId])
                groups = cur.fetchall()
                #user_profile = User(username, userId, groups)
                cur.close()
                app.logger.info('%s logged in successfully', username)
                # msg = Message("Email Confirmation", sender="gstauf5420@att.net", recipients=["gztauf5420@gmail.com"])
                # msg.html = render_template("validate_email.html")
                # mail.send(msg)
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid log in.'
                return render_template('login.html', error=error, form=form)


        else:
            error = "Username not found"
            return render_template('login.html', error=error, form=form)
        cur.close()

    return render_template('login.html', form=form)
#Check if logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please log in")
            return redirect(url_for('login'))
    return wrap

@app.route('/validate_email', methods=["GET", "POST"])
def validate_email():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        username = form.username.data
        password_candidate = form.password.data

        #Create DictCursor
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            data = cur.fetchone()
            password, verified = data['password'], data['e_verified']

            if sha256_crypt.verify(password_candidate, password):
                if verified > 0:
                    error = 'You have already verified this email'
                    return render_template('validate_email.html', error=error, form=form)
                session['logged_in'] = True
                session['username'] = username
                userId, verify = data['userId'], 1
                cur.execute("UPDATE users SET e_verified = %s WHERE userId = %s", [verify, userId])
                mysql.connection.commit()
                cur.close()
                app.logger.info('%s validated email successfully', username)

                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid log in.'
                return render_template('validate_email.html', error=error, form=form)


        else:
            error = "Username not found"
            return render_template('validate_email.html', error=error, form=form)
    return render_template("validate_email.html", form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out", "danger")
    return redirect(url_for("login"))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    #groups = []
    username = session['username']
    # Get id from users db
    cur = mysql.connection.cursor()
    # Find user in db
    cur.execute("SELECT * FROM users WHERE username = %s", [username])
    profile = cur.fetchone()
    #store id in 'user'
    id = profile['userId']

    result = cur.execute("SELECT * FROM user_group WHERE userId = %s", [id])

    if result > 0:
        groups = cur.fetchall()
        ad = 'admin'
        cur.execute("SELECT * FROM user_group WHERE userId = %s AND type = %s", [id, ad])
        admins  = cur.fetchall()
        cur.close()
        return render_template('dashboard.html', groups=groups, profile=profile, admins=admins)
    else:
        cur.close()
        return render_template('dashboard.html', profile=profile)

    return render_template('dashboard.html', profile=profile)

@app.route('/edit_profile', methods=['GET', 'POST'])
@is_logged_in
def edit_profile():
    form = EditProfileForm(request.form)
    user = session['username']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", [user])
    profile = cur.fetchone()

    cur.close()

    password = profile['password']
    id = profile['userId']

    form.firstName.data = profile['firstName']
    form.lastName.data = profile['lastName']
    form.username.data = profile['username']
    form.email.data = profile['email']

    if form.validate_on_submit ():
        password_candidate = form.password.data
        if sha256_crypt.verify(password_candidate, password):
            f_Name = request.form['firstName']
            l_Name = request.form['lastName']
            u_name = request.form['username']
            e_mail = request.form['email']
            cur = mysql.connection.cursor()

            cur.execute("UPDATE users SET firstName = %s, lastName = %s, username = %s, email = %s WHERE userId = %s", [f_Name, l_Name, u_name, e_mail, id])

            #Commit to Database
            mysql.connection.commit()
            flash("Your profile was successfully edited. Please re-signin")

            #Close connection
            cur.close()


            return redirect(url_for('logout'))

        flash("Incorrect password")
        return render_template('edit_profile.html', form=form, profile=profile)

    return render_template('edit_profile.html', form=form, profile=profile)

@app.route('/delete_profile', methods=['GET', 'POST'])
@is_logged_in
def delete_profile():
    form = DeleteProfileForm(request.form)
    user = session['username']
    if form.yes.data:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        data = cur.fetchone()
        password_candidate = form.password.data
        password = data['password']
        #Get id to delete this users group affiliations
        id = data['userId']
        if sha256_crypt.verify(password_candidate, password):
            #if password match, delete user;
            cur.execute("DELETE FROM users WHERE userId = %s", [id])
            mysql.connection.commit()
            #All user_group relationships are deleted, however
            #Does not delete groups that user is admin, here deletes group,
            cur.execute("DELETE FROM groups WHERE admin = %s", [user])
            mysql.connection.commit()
            # Close connection
            cur.close()
            session.clear()
            flash("You're account was succesfully deleted.", "danger")
            return redirect(url_for("login"))
        else:
            flash("Incorrect password")
            return render_template('delete_profile.html', form=form)

    return render_template('delete_profile.html', form=form)

@app.route('/edit_group/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_group(id):
    form = EditGroupForm(request.form)
    user = session['username']
    cur = mysql.connection.cursor()

    # Get group info
    cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    group = cur.fetchone()
    passwordGroup = group['password']

    # Get user credentials in order to get password
    cur.execute("SELECT * FROM users WHERE username = %s", [user])
    profile = cur.fetchone()
    passwordUser = profile['password']
    cur.close()

    form.name.data = group['title']
    form.location.data = group['location']
    form.dates.data = group['dates']
    form.description.data = group['description']

    if form.validate_on_submit():
        password_candidate_user = form.password.data
        password_candidate_group = form.groupPassword.data
        if sha256_crypt.verify(password_candidate_user, passwordUser):

            if sha256_crypt.verify(password_candidate_group, passwordGroup):
                name = request.form['name']
                location = request.form['location']
                dates = request.form['dates']
                description = request.form['description']

                cur = mysql.connection.cursor()

                cur.execute("UPDATE groups SET title = %s, location = %s, dates = %s, description = %s WHERE groupId = %s", [name, location, dates, description, id])

                #Commit to Database
                mysql.connection.commit()
                cur.execute("UPDATE user_group SET name = %s", [name])
                mysql.connection.commit()
                cur.close()
                flash("Your group was successfully edited.")
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect group password.")
                return render_template('edit_group.html', id=id, profile=profile, group=group, form=form)
        else:
            flash("Incorrect user password")
            return render_template('edit_group.html', id=id, profile=profile, group=group, form=form)

    return render_template('edit_group.html', id=id, profile=profile, group=group, form=form)



@app.route('/delete_group/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_group(id):
    form = DeleteGroupForm(request.form)
    if form.yes.data:
        #set both password attempts (user, and group), as well as user
        user_pass_candidate = form.passwordUser.data
        group_pass_candidate = form.passwordGroup.data
        user = session['username']

        cur = mysql.connection.cursor()
        # Get user, and group info, as well as all memmbers of group
        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()

        cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
        group = cur.fetchone()

        #close connection
        cur.close()
        # Set both actual passwords
        user_pass, group_pass = profile['password'], group['password']
        if sha256_crypt.verify(user_pass_candidate, user_pass):
            if sha256_crypt.verify(group_pass_candidate, group_pass):
                #Reopen connection if passes both Passwords
                cur = mysql.connection.cursor()
                # Delete group
                cur.execute("DELETE FROM groups WHERE groupId = %s", [id])
                #Commit to db
                mysql.connection.commit()
                # Cascading delete MySQL deletes user_group, chats, and all pins with groupId!
                cur.close()

                flash("Group Deleted")
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect group password")
                return render_template("edit_profile.html", id=id, profile=profile, group=group, form=form)
        else:
            flash("Incorrect user password")
            return render_template("edit_profile.html", id=id, profile=profile, group=group, form=form)

    return render_template('delete_group.html', id=id, form=form)
@app.route('/newGroup', methods=['GET', 'POST'])
@is_logged_in
def newGroup():
    form = GroupForm(request.form)
    user = session['username']
    if form.validate_on_submit():
        groupName = form.groupName.data
        location = form.location.data
        dates = form.dates.data
        admin = session['username']
        password = sha256_crypt.encrypt(str(form.password.data))
        description = form.description.data


        # Create cursor
        cur = mysql.connection.cursor()

        #Check for group name
        check = cur.execute("SELECT * FROM groups WHERE title = %s", [groupName])
        if check > 0:
            cur.close()
            flash("That group name is already in use, sorry.")
            return render_template("newGroup.html", form=form)
        else:
            #Add group to db
            cur.execute("INSERT INTO groups(title, location, dates, admin, password, description) VALUES(%s,%s,%s,%s,%s,%s)", (groupName, location, dates, admin, password, description))

            mysql.connection.commit()

            # Create variables for user ID number, group id number and type(admin), to enter admin into user_groups
            cur.execute("SELECT * FROM users WHERE username = %s", [user])
            profile = cur.fetchone()
            userId = profile['userId']

            cur.execute("SELECT * FROM groups WHERE title = %s", [groupName])
            groupProfile = cur.fetchone()
            groupId = groupProfile['groupId']
            type = 'admin'

            cur.execute("INSERT INTO user_group(userId, groupId, name, type, username) VALUES(%s,%s,%s,%s,%s)", [userId, groupId, groupName, type, user])

            mysql.connection.commit()
            cur.close()

            flash("Group Created")
            return redirect(url_for('dashboard'))

    return render_template('newGroup.html', form=form)

@app.route('/group/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def group(id):

    user = session['username']
    renPins, restPins, transpoPins, activityPins = {}, {}, {}, {}
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    group = cur.fetchone()
    cur.execute("SELECT * FROM users WHERE username = %s", [user])
    profile = cur.fetchone()
    userId = profile['userId']
    ifMember = cur.execute("SELECT * FROM user_group WHERE groupId = %s AND userId = %s", [id, userId])

    if ifMember > 0:

        #Get all the pins
        pinner1 = cur.execute("SELECT * FROM rental_pin WHERE groupId = %s", [id])
        if pinner1 > 0:
            renPins = cur.fetchall()
        pinner2 = cur.execute("SELECT * FROM rest_pin WHERE groupId = %s", [id])
        if pinner2 > 0:
            restPins = cur.fetchall()
        pinner3 = cur.execute("SELECT * FROM transpo_pin WHERE groupId = %s", [id])
        if pinner3 > 0:
            transpoPins = cur.fetchall()
        pinner4 = cur.execute("SELECT * FROM activity_pin WHERE groupId = %s", [id])
        if pinner4 > 0:
            activityPins = cur.fetchall()

        # get all group members
        members = []
        cur.execute("SELECT * FROM user_group WHERE groupId = %s", [id])
        group_data = cur.fetchall()
        for member in group_data:
            members.append(member['username'])


        #Rental pin form
        pinForm = RentalPinForm(request.form)
        if pinForm.submit1.data and pinForm.validate():
            username = session['username']
            rentalName = pinForm.rentalName.data
            price = pinForm.price.data
            rooms = pinForm.rooms.data
            description = pinForm.description.data
            link = pinForm.link.data
            id = id

            cur.execute("INSERT INTO rental_pin(groupId, rental_name, price, rooms, description, link, creator) VALUES(%s,%s,%s,%s,%s,%s,%s)", [id, rentalName, price, rooms, description, link, username])

            cur.connection.commit()
            flash("Pin created!")
            return redirect(url_for('group', id=id))

        pinFormTwo = RestPinForm(request.form)
        if pinFormTwo.submit2.data and pinFormTwo.validate():
            username = session['username']
            restName = pinFormTwo.restName.data
            description = pinFormTwo.description2.data
            link = pinFormTwo.link2.data
            type = pinFormTwo.type.data
            id = id


            cur.execute("INSERT INTO rest_pin(groupId, rest_name, description, link, type, creator) VALUES(%s,%s,%s,%s,%s, %s)", [id, restName, description, link, type, username])

            cur.connection.commit()
            flash("Pin created!")
            return redirect(url_for('group', id=id))

        pinFormThree = TransportationPinForm(request.form)
        if pinFormThree.submit3.data and pinFormThree.validate():
            username = session['username']
            name = pinFormThree.name.data
            date = pinFormThree.date.data
            price = pinFormThree.price3.data
            description = pinFormThree.description3.data
            link = pinFormThree.link3.data
            type = pinFormThree.type.data

            cur.execute("INSERT INTO transpo_pin(groupId, name, date, price, link, description, creator, type) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", [id, name, date, price, link, description, username, type])

            cur.connection.commit()
            flash("Pin created!")
            return redirect(url_for('group', id=id))

        pinFormFour = ActivityPinForm(request.form)
        if pinFormFour.submit4.data and pinFormFour.validate():
            username = session['username']
            activityName = pinFormFour.activityName.data
            description = pinFormFour.description.data
            link = pinFormFour.link.data
            type = pinFormFour.type.data

            cur.execute("INSERT INTO activity_pin(groupId, creator, name, description, link, type) VALUES(%s,%s,%s,%s,%s,%s)", [id, username,  activityName, description, link, type])
            cur.connection.commit()
            flash("Pin created!")
            return redirect(url_for('group', id=id))

        cur.execute("SELECT * FROM chats WHERE groupId = %s", [id])
        history = cur.fetchall()
    else:
        flash("You must join the group first!")
        return redirect(url_for("joinGroup"))

    cur.close()


    return render_template("group.html", group=group, renPins=renPins, restPins=restPins, transpoPins=transpoPins, activityPins=activityPins, pinForm=pinForm, id=id, user=user, pinFormTwo=pinFormTwo, pinFormThree=pinFormThree, pinFormFour=pinFormFour, history=history, members=members)

@app.route('/joinGroup', methods=['GET', 'POST'])
@is_logged_in
def joinGroup():
    form = JoinGroupForm(request.form)
    username = session['username']
    if form.validate_on_submit():
        groupName = request.form['name']
        password_candidate = request.form['password']

        #Create DictCursor
        cur = mysql.connection.cursor()
        #Check if already a member

        result = cur.execute("SELECT * FROM groups WHERE title = %s", [groupName])
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            username = session['username']
            type = 'member'
            if sha256_crypt.verify(password_candidate, password):
                cur.execute("SELECT * FROM users WHERE username = %s", [username])
                profile = cur.fetchone()
                userId = profile['userId']
                # Make sure they arent already part of the group
                ifMember = cur.execute("SELECT * FROM user_group WHERE name = %s AND userId = %s", [groupName, userId])
                if ifMember > 0:
                    flash("You are already a member of the group")
                    return redirect(url_for("dashboard"))

                # Get id's from user and group db
                groupId = data['groupId']

                # put user/group ids in user/group database
                cur.execute("INSERT INTO user_group(userId, groupId, name, type, username) VALUES(%s, %s, %s, %s, %s)", (userId, groupId, groupName, type, username))
                #commit
                cur.connection.commit()

                #redirect to Dashboard
                flash("Group joined!")

                #Close connection
                cur.close()
                return redirect(url_for("groups"))
            else:
                cur.close()
                error = 'Invalid group password.'
                return render_template('joinGroup.html', error=error, form=form)


        else:
            cur.close()
            error = "Group not found"
            return render_template('joinGroup.html', error=error, form=form)


    return render_template('joinGroup.html', form=form)



@app.route('/groups')
@is_logged_in
def groups():
    groups = []
    username = session['username']
    # Get id from users db
    cur = mysql.connection.cursor()

    # Find user in db
    cur.execute("SELECT * FROM users WHERE username = %s", [username])
    data = cur.fetchone()
    #store id in 'user'
    user = data['userId']

    result = cur.execute("SELECT * FROM user_group WHERE userId = %s", [user])

    if result > 0:
        groups = cur.fetchall()
        cur.close()
        return render_template('groups.html', groups=groups)
    else:
        msg = "You are not a member of any groups yet."
        cur.close()
        return render_template('groups.html', groups=groups)

@app.route('/edit_rental_pin/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editRentalPin(name):
    form = EditRentalPin(request.form)
    user = session['username']
    cur = mysql.connection.cursor()

    # Get pin info
    cur.execute("SELECT * FROM rental_pin WHERE rental_name = %s", [name])
    pin = cur.fetchone()
    id = pin['groupId']

    # Get group info
    cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    group = cur.fetchone()

    #Populate fields
    form.rentalName.data = pin['rental_name']
    form.price.data = pin['price']
    form.rooms.data = pin['rooms']
    form.description.data = pin['description']
    form.link.data = pin['link']

    if form.validate_on_submit():
        #print("Inside first if")
        user_pass_candidate = form.passwordUser.data
        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        passwordUser = profile['password']
        # Check Passwords
        if sha256_crypt.verify(user_pass_candidate, passwordUser):
            group_pass_candidate = form.passwordGroup.data
            passwordGroup = group['password']
            if sha256_crypt.verify(group_pass_candidate, passwordGroup):
                # Create variables with data
                name = request.form['rentalName']
                price = request.form['price']
                rooms = request.form['rooms']
                description = request.form['description']
                link = request.form['link']

                pinId = pin['pinId']
                cur.execute("UPDATE rental_pin SET rental_name = %s, price = %s, rooms = %s, description = %s, link = %s WHERE pinId = %s", [name, price, rooms, description, link, pinId])
                mysql.connection.commit()
                cur.close()
                flash("Pin succesfully updated!")
                return redirect(url_for('group', id=id))

            else:
                flash("You got your group password twisted")
                return render_template('edit_rental_pins.html', form=form, id=id, pin=pin, group=group, profile=profile)
        else:
            flash("You got your user password twisted")
            return render_template('edit_rental_pins.html', form=form, id=id, pin=pin, group=group, profile=profile)

    cur.close()
    return render_template('edit_rental_pins.html', form=form, id=id, pin=pin, group=group)

@app.route('/edit_restaurant_pin/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editRestaurantPin(name):
    form = EditRestaurantPin(request.form)
    user = session['username']
    cur = mysql.connection.cursor()

    # Get pin info
    cur.execute("SELECT * FROM rest_pin WHERE rest_name = %s", [name])
    pin = cur.fetchone()
    id = pin['groupId']

    # Get group info
    cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    group = cur.fetchone()

    #Populate fields
    form.name.data = pin['rest_name']
    form.description.data = pin['description']
    form.link.data = pin['link']
    form.type.data = pin['type']

    if form.validate_on_submit():
        #print("Inside first if")
        user_pass_candidate = form.passwordUser.data
        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        passwordUser = profile['password']
        # Check Passwords
        if sha256_crypt.verify(user_pass_candidate, passwordUser):
            group_pass_candidate = form.passwordGroup.data
            passwordGroup = group['password']
            if sha256_crypt.verify(group_pass_candidate, passwordGroup):
                # Create variables with data
                name = request.form['name']
                description = request.form['description']
                link = request.form['link']
                type = request.form['type']

                pinId = pin['pinId']
                cur.execute("UPDATE rest_pin SET rest_name = %s, description = %s, link = %s, type = %s WHERE pinId = %s", [name, description, link,type, pinId])
                mysql.connection.commit()
                cur.close()
                flash("Pin succesfully updated!")
                return redirect(url_for('group', id=id))

            else:
                flash("You got your group password twisted")
                return render_template('edit_restaurant_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)
        else:
            flash("You got your user password twisted")
            return render_template('edit_restaurant_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)

    cur.close()
    return render_template('edit_restaurant_pin.html', form=form, id=id, pin=pin, group=group)

@app.route('/edit_transportation_pin/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editTransportationPin(name):
    form = EditTransportationPin(request.form)
    user = session['username']
    cur = mysql.connection.cursor()

    # Get pin info
    cur.execute("SELECT * FROM transpo_pin WHERE name = %s", [name])
    pin = cur.fetchone()
    id = pin['groupId']

    # Get group info
    cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    group = cur.fetchone()

    #Populate fields
    form.name.data = pin['name']
    form.date.data = pin['date']
    form.price.data = pin['price']
    form.description.data = pin['description']
    form.link.data = pin['link']
    form.type.data = pin['type']

    if form.validate_on_submit():
        #print("Inside first if")
        user_pass_candidate = form.passwordUser.data
        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        passwordUser = profile['password']
        # Check Passwords
        if sha256_crypt.verify(user_pass_candidate, passwordUser):
            group_pass_candidate = form.passwordGroup.data
            passwordGroup = group['password']
            if sha256_crypt.verify(group_pass_candidate, passwordGroup):
                # Create variables with data
                name = request.form['name']
                date = request.form['date']
                price = request.form['price']
                description = request.form['description']
                link = request.form['link']
                type = request.form['type']

                pinId = pin['pinId']
                cur.execute("UPDATE transpo_pin SET name = %s, date = %s, price = %s,  description = %s, link = %s, type = %s WHERE pinId = %s", [name, date, price, description, link,type, pinId])
                mysql.connection.commit()
                cur.close()
                flash("Pin succesfully updated!")
                return redirect(url_for('group', id=id))

            else:
                flash("You got your group password twisted")
                return render_template('edit_transportation_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)
        else:
            flash("You got your user password twisted")
            return render_template('edit_transportation_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)

    cur.close()
    return render_template('edit_transportation_pin.html', form=form, id=id, pin=pin, group=group)

@app.route('/edit_activity_pin/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editActivityPin(name):
    form = EditActivityPin(request.form)
    user = session['username']
    cur = mysql.connection.cursor()

    # Get pin info
    cur.execute("SELECT * FROM activity_pin WHERE name = %s", [name])
    pin = cur.fetchone()
    id = pin['groupId']

    # Get group info
    cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    group = cur.fetchone()

    #Populate fields
    form.name.data = pin['name']
    form.description.data = pin['description']
    form.link.data = pin['link']
    form.type.data = pin['type']

    if form.validate_on_submit():
        #print("Inside first if")
        user_pass_candidate = form.passwordUser.data
        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        passwordUser = profile['password']
        # Check Passwords
        if sha256_crypt.verify(user_pass_candidate, passwordUser):
            group_pass_candidate = form.passwordGroup.data
            passwordGroup = group['password']
            if sha256_crypt.verify(group_pass_candidate, passwordGroup):
                # Create variables with data
                name = request.form['name']
                description = request.form['description']
                link = request.form['link']
                type = request.form['type']

                pinId = pin['pinId']
                cur.execute("UPDATE activity_pin SET name = %s, description = %s, link = %s, type = %s WHERE pinId = %s", [name, description, link,type, pinId])
                mysql.connection.commit()
                cur.close()
                flash("Pin succesfully updated!")
                return redirect(url_for('group', id=id))

            else:
                flash("You got your group password twisted")
                return render_template('edit_activity_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)
        else:
            flash("You got your user password twisted")
            return render_template('edit_activity_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)

    cur.close()
    return render_template('edit_activity_pin.html', form=form, id=id, pin=pin, group=group)


@app.route('/delete_rental_pin/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteRentalPin(name):
    form = DeletePinForm(request.form)
    if form.yes.data:
        cur = mysql.connection.cursor()
        user = session['username']

        cur.execute("SELECT * FROM rental_pin WHERE rental_name = %s", [name])
        pin = cur.fetchone()
        id = pin['groupId']

        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        userPassword = profile['password']
        user_pass_candidate = form.passwordUser.data
        if sha256_crypt.verify(user_pass_candidate, userPassword):

            cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
            group = cur.fetchone()
            groupPassword = group['password']
            group_pass_candidate = form.passwordGroup.data
            if sha256_crypt.verify(group_pass_candidate, groupPassword):

                cur.execute("DELETE FROM rental_pin WHERE rental_name = %s", [name])
                mysql.connection.commit()
                cur.close()
                flash("Pin deleted")

                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return render_template('delete_rental_pin.html', name=name, form=form)
        else:
            flash("Incorrect user password")
            return render_template('delete_rental_pin.html', name=name, form=form)

    return render_template('delete_rental_pin.html', name=name, form=form)

@app.route('/delete_restaurant_pin/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteRestaurantPin(name):
    form = DeletePinForm(request.form)
    if form.yes.data:
        cur = mysql.connection.cursor()
        user = session['username']

        cur.execute("SELECT * FROM rest_pin WHERE rest_name = %s", [name])
        pin = cur.fetchone()
        id = pin['groupId']

        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        userPassword = profile['password']
        user_pass_candidate = form.passwordUser.data
        if sha256_crypt.verify(user_pass_candidate, userPassword):

            cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
            group = cur.fetchone()
            groupPassword = group['password']
            group_pass_candidate = form.passwordGroup.data
            if sha256_crypt.verify(group_pass_candidate, groupPassword):

                cur.execute("DELETE FROM rest_pin WHERE rest_name = %s", [name])
                mysql.connection.commit()
                cur.close()
                flash("Pin deleted")

                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return render_template('delete_restaurant_pin.html', name=name, form=form)
        else:
            flash("Incorrect user password")
            return render_template('delete_restaurant_pin.html', name=name, form=form)

    return render_template('delete_restaurant_pin.html', name=name, form=form)

@app.route('/delete_transportation_pin/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteTransportationPin(name):
    form = DeletePinForm(request.form)
    if form.yes.data:
        cur = mysql.connection.cursor()
        user = session['username']

        cur.execute("SELECT * FROM transpo_pin WHERE name = %s", [name])
        pin = cur.fetchone()
        id = pin['groupId']

        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        userPassword = profile['password']
        user_pass_candidate = form.passwordUser.data
        if sha256_crypt.verify(user_pass_candidate, userPassword):

            cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
            group = cur.fetchone()
            groupPassword = group['password']
            group_pass_candidate = form.passwordGroup.data
            if sha256_crypt.verify(group_pass_candidate, groupPassword):

                cur.execute("DELETE FROM transpo_pin WHERE name = %s", [name])
                mysql.connection.commit()
                cur.close()
                flash("Pin deleted")

                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return render_template('delete_transportation_pin.html', name=name, form=form)
        else:
            flash("Incorrect user password")
            return render_template('delete_transportation_pin.html', name=name, form=form)

    return render_template('delete_transportation_pin.html', name=name, form=form)

@app.route('/delete_activity_pin/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteActivityPin(name):
    form = DeletePinForm(request.form)
    if form.yes.data:
        cur = mysql.connection.cursor()
        user = session['username']

        cur.execute("SELECT * FROM activity_pin WHERE name = %s", [name])
        pin = cur.fetchone()
        id = pin['groupId']

        cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = cur.fetchone()
        userPassword = profile['password']
        user_pass_candidate = form.passwordUser.data
        if sha256_crypt.verify(user_pass_candidate, userPassword):

            cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
            group = cur.fetchone()
            groupPassword = group['password']
            group_pass_candidate = form.passwordGroup.data
            if sha256_crypt.verify(group_pass_candidate, groupPassword):

                cur.execute("DELETE FROM activity_pin WHERE name = %s", [name])
                mysql.connection.commit()
                cur.close()
                flash("Pin deleted")

                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return render_template('delete_activity_pin.html', name=name, form=form)
        else:
            flash("Incorrect user password")
            return render_template('delete_activity_pin.html', name=name, form=form)

    return render_template('delete_activity_pin.html', name=name, form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internalerror(error):
    session.rollback()
    return render_template('500.html'), 500


users = []

@socketio.on('connect', namespace='/chat')
def connect():
    user = session['username']
    users.append(user)
    msg = " just connected!"
    emit('on connect', {'msg': msg, 'user': user, 'users': users}, broadcast=True)

@socketio.on('disconnect', namespace='/chat')
def disconnect():
    user = session['username']
    users.remove(user)
    msg = " just disconnected :("
    emit('on disconnect', {'msg': msg, 'user': user, "users": users}, broadcast=True)

@socketio.on('send message', namespace='/chat')
def handle_my_custom_event(msg, id):
    user = session['username']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO chats(groupId, user, message) VALUES(%s,%s,%s)", [id, user, msg])
    cur.connection.commit()
    cur.close()
    emit('new message', {'msg': msg, 'user': user}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
