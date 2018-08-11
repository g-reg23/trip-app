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
from sqlalchemy import and_, or_, update
from models import *
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
        # Check if username or email is already taken
        user = User.query.filter(User.username==form.username.data).first()
        email = User.query.filter(User.email==form.email.data).first()
        if user is None and email is None:
            u = User(firstName=form.firstName.data, lastName=form.lastName.data, email=form.email.data, username=form.username.data, password=sha256_crypt.encrypt(str(form.password.data)))
            db.session.add(u)
            db.session.commit()
            flash('Congrats you are now registered. Please sign in.')
            return redirect(url_for('login'))
        if user is not None:
            flash('That username is already in use.')
            # form.username.data = ''

        else:
            flash('That email is already in use')
            form.email.data = ''
        # f_Name = form.firstName.data
        # l_Name = form.lastName.data
        # u_name = form.username.data
        # e_mail = form.email.data
        # e_verified = 0
        # p_word = sha256_crypt.encrypt(str(form.password.data))
        #
        # #create cursor
        # cur = mysql.connection.cursor()
        #
        # check = cur.execute("SELECT * FROM users WHERE username = %s", [u_name])
        # check2 = cur.execute("SELECT * FROM users WHERE email = %s", [e_mail])
        # if check > 0:
        #     #close
        #     cur.close()
        #
        #     error = "That username is already in use, sorry."
        #     return render_template("signup.html", error=error, form=form)
        # elif check2 > 0:
        #     cur.close()
        #     error = "That email address is already in use"
        #     return render_template("signup.html", error=error, form=form)
        # else:
        #     cur.execute("INSERT INTO users(firstName, lastName, username, email, password, e_verified) VALUES(%s, %s, %s, %s, %s, %s)", (f_Name, l_Name, u_name, e_mail, p_word, e_verified))
        #
        #     #Commit to Database
        #     mysql.connection.commit()
        #
        #     #Close connection
        #     cur.close()
        #
        #     flash("Congrats, your are registered, you can now login once you confirm your email")
        #     msg = Message("Email Confirmation", sender=app.config['MAIL_USERNAME'], recipients=[e_mail])
        #     msg.html = render_template("verify_email.html")
        #     mail.send(msg)
        #     return redirect(url_for('login'))

    return render_template('signup.html',form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = User.query.filter(User.username==form.username.data).first()
        if user:
            pass_candidate = form.password.data
            if sha256_crypt.verify(pass_candidate, user.password):
                session['logged_in'] = True
                session['username'] = user.username
                flash("You are now logged in. Welcome!")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid login")
            return render_template("login.html", form=form, error=error)
        else:
            flash('Invalid login')
        # username = form.username.data
        # password_candidate = form.password.data
        #
        # #Create DictCursor
        # cur = mysql.connection.cursor()
        #
        # result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        # if result > 0:
        #     data = cur.fetchone()
        #     password, verified = data['password'], data['e_verified']
        #
        #     if sha256_crypt.verify(password_candidate, password):
        #         if verified == 0:
        #             error = 'You must verifiy your email first'
        #             return render_template('login.html', error=error, form=form)
        #         session['logged_in'] = True
        #         session['username'] = username
        #         userId = data['userId']
        #         cur.execute("SELECT * FROM user_group WHERE userId = %s", [userId])
        #         groups = cur.fetchall()
        #         #user_profile = User(username, userId, groups)
        #         cur.close()
        #         app.logger.info('%s logged in successfully', username)
        #         # msg = Message("Email Confirmation", sender="gstauf5420@att.net", recipients=["gztauf5420@gmail.com"])
        #         # msg.html = render_template("validate_email.html")
        #         # mail.send(msg)
        #         return redirect(url_for('dashboard'))
        #     else:
        #         error = 'Invalid log in.'
        #         return render_template('login.html', error=error, form=form)
        #
        #
        # else:
        #     error = "Username not found"
        #     return render_template('login.html', error=error, form=form)
        # cur.close()

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
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    groups = User_Group.query.filter(User_Group.userId==profile.id).all()
    admins = User_Group.query.filter(and_(User_Group.userId==profile.id), (User_Group.type=='Admin')).all()
    # groups = User_Group.query.filter(User_Group.userId==profile.id).all()

    return render_template("dashboard.html", profile=profile, groups=groups, admins=admins)

@app.route('/edit_profile', methods=['GET', 'POST'])
@is_logged_in
def edit_profile():
    form = EditProfileForm(request.form)
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    if form.validate_on_submit():
        if profile.email == form.email.data:
            newProfile = User.query.filter(User.id==profile.id).update(dict(firstName=form.firstName.data,lastName=form.lastName.data, email=form.email.data))
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            check_email = User.query.filter(User.email==form.email.data).first()
            if check_email is not None:
                flash("Sorry that email is in use.")
                return render_template('edit_profile.html', form=form, profile=profile)
            else:
                newProfile = User.query.filter(User.id==profile.id).update(dict(firstName=form.firstName.data,lastName=form.lastName.data, email=form.email.data))
                db.session.commit()
                return redirect(url_for('dashboard'))

    return render_template('edit_profile.html', form=form, profile=profile)

@app.route('/delete_profile', methods=['GET', 'POST'])
@is_logged_in
def delete_profile():
    form = DeleteProfileForm(request.form)
    user = session['username']
    if form.yes.data:
        # cur = mysql.connection.cursor()
        # cur.execute("SELECT * FROM users WHERE username = %s", [user])
        profile = User.query.filter(User.username==user).first()
        password_candidate = form.password.data
        if sha256_crypt.verify(password_candidate, profile.password):
            db.session.delete(profile)
            db.session.commit()
            flash('Your account was successfully deleted.')
            return redirect(url_for('logout'))
        else:
            flash('Incorrect password')
            return render_template('delete_profile.html', form=form)

    return render_template('delete_profile.html', form=form)

@app.route('/edit_group/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_group(id):
    form = EditGroupForm(request.form)
    user = session['username']
    # cur = mysql.connection.cursor()
    #
    # # Get group info
    # cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    # group = cur.fetchone()
    # passwordGroup = group['password']
    #
    # # Get user credentials in order to get password
    # cur.execute("SELECT * FROM users WHERE username = %s", [user])
    # profile = cur.fetchone()
    # passwordUser = profile['password']
    # cur.close()
    #
    # form.name.data = group['title']
    # form.location.data = group['location']
    # form.dates.data = group['dates']
    # form.description.data = group['description']
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    if form.validate_on_submit():
        password_candidate_user = form.password.data
        password_candidate_group = form.groupPassword.data
        if sha256_crypt.verify(password_candidate_user, profile.password):
            if sha256_crypt.verify(password_candidate_group, group.password):
                # Check if name is the same as before
                if group.groupName == form.name.data:
                    newGroup = Group.query.filter(Group.id==group.id).update(dict(groupName=form.name.data,location=form.location.data, startDate=form.startDate.data, endDate=form.endDate.data, description=form.description.data))
                    db.session.commit()
                    flash('Group was successfully updated')
                    return redirect(url_for('dashboard'))
                # If group is changed, then check if it is already in use
                else:
                    group_check = Group.query.filter(Group.groupName==form.name.data)
                    # If not in use, then make the update
                    if group_check is None:
                        newGroup = Group.query.filter(Group.id==group.id).update(dict(groupName=form.name.data,location=form.location.data, startDate=form.startDate.data, endDate=form.endDate.data, description=form.description.data))
                        db.session.commit()
                        flash('Group was successfully updated')
                        return redirect(url_for('dashboard'))
                    # If name is in use, then inform them and reload page.
                    else:
                        flash("Sorry that group name is already in use")
                        return render_template('edit_group.html', id=id, profile=profile, group=group, form=form)
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
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, profile.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(group)
                db.session.commit()
                flash("Group Deleted")
                return redirect(url_for('dashboard'))
            else:
                flash("Incorrect group password")
                return render_template("delete_group.html", id=id, profile=profile, group=group, form=form)
        else:
            flash("Incorrect user password")
            return render_template("delete_group.html", id=id, profile=profile, group=group, form=form)

    return render_template('delete_group.html', id=id, form=form)
@app.route('/newGroup', methods=['GET', 'POST'])
@is_logged_in
def newGroup():
    form = GroupForm(request.form)
    user = session['username']
    if form.validate_on_submit():
        group = Group.query.filter(Group.groupName==form.groupName.data).first()
        if group is None:
            g = Group(groupName=form.groupName.data, location=form.location.data, startDate=form.startDate.data, endDate=form.endDate.data, admin=session['username'], password=sha256_crypt.encrypt(str(form.password.data)), description=form.description.data)
            profile = User.query.filter(User.username==user).first()
            db.session.add(g)
            db.session.commit()
            user_group = User_Group(groupId=g.id, userId=profile.id, type='Admin', groupName=form.groupName.data)
            db.session.add(user_group)
            db.session.commit()
            flash('Group successfully created.')
            return redirect(url_for('dashboard'))
        else:
            flash("Sorry, that group name is already in use")

    return render_template('newGroup.html', form=form)
@app.route('/group/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def group(id):
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    ifMember = User_Group.query.filter(and_(User_Group.userId==profile.id), (User_Group.groupId==id)).first()
    if ifMember is not None:
        renPins, restPins, transpoPins, activityPins = {}, {}, {}, {}
        members, history = [], []
        pinForm, pinFormTwo = RentalPinForm(request.form), RestPinForm(request.form)
        pinFormThree, pinFormFour = TransportationPinForm(request.form), ActivityPinForm(request.form)
        memList = User_Group.query.filter(User_Group.groupId==id).all()
        for mem in memList:
            member = User.query.filter(User.id==mem.userId).first()
            members.append(member.username)

        if pinForm.submit1.data and pinForm.validate():
            rental = Lodging_Pin(groupId=id, lodgeName=pinForm.rentalName.data, price=pinForm.price.data, rooms=pinForm.rooms.data, description=pinForm.description.data, link=pinForm.link.data, creator=user)
            db.session.add(rental)
            db.session.commit()
            flash("Pin created!")
            return redirect(url_for('group', id=id))

        if pinFormTwo.submit2.data and pinFormTwo.validate():
            rest = Rest_Pin(groupId=id, restName=pinFormTwo.restName.data, description=pinFormTwo.description2.data, link=pinFormTwo.link2.data, types=pinFormTwo.type.data, creator=user)
            db.session.add(rest)
            db.session.commit()
            flash("Pin created")
            return redirect(url_for('group', id=id))
        # Get rental pins and rest pins
        renPins, restPins = Lodging_Pin.query.filter(Lodging_Pin.groupId==id).all(), Rest_Pin.query.filter(Rest_Pin.groupId==id).all()

        if pinFormThree.submit3.data and pinFormThree.validate():
            transport = Transpo_Pin(groupId=id, transpoName=pinFormThree.name.data, price=pinFormThree.price3.data, description=pinFormThree.description3.data, link=pinFormThree.link3.data, creator=user)
            db.session.add(transport)
            db.session.commit()
            flash("Pin created")
            return redirect(url_for('group', id=id))


        if pinFormFour.submit4.data and pinFormFour.validate():
            activity = Activity_Pin(groupId=id, activityName=pinFormFour.activityName.data, price=pinFormFour.price.data, description=pinFormFour.description.data, types=pinFormFour.type.data, link=pinFormFour.link.data, creator=user)
            db.session.add(activity)
            db.session.commit()
            flash("Pin created")
            return redirect(url_for('group', id=id))
        #Get transportation pins and activity pins
        transpoPins, activityPins = Transpo_Pin.query.filter(Transpo_Pin.groupId==id).all(), Activity_Pin.query.filter(Activity_Pin.groupId==id).all()

        history = Chat.query.filter(Chat.groupId==id).all()

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
            chat_mess = Chat(groupId=id, username=user, message=msg)
            db.session.add(chat_mess)
            db.session.commit()
            emit('new message', {'msg': msg, 'user': user}, broadcast=True)
    else:
        flash("You must join the group first!")
        return redirect(url_for('newGroup'))

    return render_template("group.html", group=group, renPins=renPins, restPins=restPins, transpoPins=transpoPins, activityPins=activityPins, pinForm=pinForm, id=id, user=user, pinFormTwo=pinFormTwo, pinFormThree=pinFormThree, pinFormFour=pinFormFour, history=history, members=members)

@app.route('/joinGroup', methods=['GET', 'POST'])
@is_logged_in
def joinGroup():
    form = JoinGroupForm(request.form)
    username = session['username']
    if form.validate_on_submit():
        group = Group.query.filter(Group.groupName==form.name.data).first()
        if group is None:
            flash("Sorry that group does not exist yet.")
            form.name.data = ''
        else:
            user = User.query.filter(User.username==username).first()
            check = User_Group.query.filter(and_(User_Group.userId==user.id), (User_Group.groupId==group.id)).first()
            if check:
                flash('You are already a member of that group!')
            else:
                pass_candidate = form.password.data
                if sha256_crypt.verify(pass_candidate, group.password):
                    g = User_Group(groupId=group.id, userId=user.id, type='Member', groupName=form.name.data)
                    db.session.add(g)
                    db.session.commit()
                    flash('Congrats, you have joined the group')
                    return redirect(url_for('dashboard'))
                else:
                    flash("Incorrect password")

    return render_template('joinGroup.html', form=form)



@app.route('/groups')
@is_logged_in
def groups():
    username = session['username']
    profile = User.query.filter(User.username==username).first()
    groups = User_Group.query.filter(User_Group.userId==profile.id).all()

    if groups is not None:
        return render_template('groups.html', groups=groups)
    else:
        flash("You are not a member of any groups yet.")
        return render_template('groups.html', groups=groups)

@app.route('/edit_rental_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editRentalPin(id, name):
    form = EditRentalPin(request.form)
    user = session['username']
    pin = Lodging_Pin.query.filter(and_(Lodging_Pin.lodgeName==name), (Lodging_Pin.groupId==id)).first()
    form.link.data, form.description.data = pin.link, pin.description
    form.rentalName.data, form.price.data, form.rooms.data = pin.lodgeName, pin.price, pin.rooms
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    userPassCandidate = form.passwordUser.data
    if form.validate_on_submit():
        if sha256_crypt.verify(userPassCandidate, profile.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Lodging_Pin.query.filter(and_(Lodging_Pin.lodgeName==name), (Lodging_Pin.groupId==id)).update(dict(lodgeName=request.form['rentalName'], price=request.form['price'], rooms=request.form['rooms'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))
            else:
                flash("You got your group password twisted")
                return render_template('edit_rental_pins.html', form=form, id=id, pin=pin, group=group, profile=profile, name=name)
        else:
            flash("You got your user password twisted")
            return render_template('edit_rental_pins.html', form=form, id=id, group=group, pin=pin, profile=profile, name=name)

    # cur.close()
    return render_template('edit_rental_pins.html', form=form, id=id, group=group, pin=pin,name=name)

@app.route('/edit_restaurant_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editRestaurantPin(id, name):
    form = EditRestaurantPin(request.form)
    user = session['username']
    pin = Rest_Pin.query.filter(and_(Rest_Pin.restName==name), (Rest_Pin.groupId==id)).first()
    form.link.data, form.description.data = pin.link, pin.description
    form.name.data, form.type.data = pin.restName, pin.types
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    userPassCandidate = form.passwordUser.data
    if form.validate_on_submit():
        if sha256_crypt.verify(userPassCandidate, profile.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Rest_Pin.query.filter(and_(Rest_Pin.restName==name), (Rest_Pin.groupId==id)).update(dict(restName=request.form['name'], types=request.form['type'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))
            else:
                flash("You got your group password twisted")
                return render_template('edit_restaurant_pin.html', form=form, id=id, pin=pin, group=group, profile=profile, name=name)
        else:
            flash("You got your user password twisted")
            return render_template('edit_restaurant_pin.html', form=form, id=id, pin=pin, group=group, profile=profile, name=name)

    return render_template('edit_restaurant_pin.html', form=form, id=id, pin=pin, group=group, name=name)

@app.route('/edit_transportation_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editTransportationPin(id, name):
    form = EditTransportationPin(request.form)
    user = session['username']
    pin = Transpo_Pin.query.filter(and_(Transpo_Pin.transpoName==name), (Transpo_Pin.groupId==id)).first()
    form.name.data, form.price.data= pin.transpoName, pin.price
    form.type.data, form.description.data, form.link.data = pin.types, pin.description, pin.link
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    if form.validate_on_submit():
        app.logger.info('verified')
        if sha256_crypt.verify(form.passwordUser.data, profile.password):

            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Transpo_Pin.query.filter(and_(Transpo_Pin.transpoName==name), (Transpo_Pin.groupId==id)).update(dict(transpoName=request.form['name'], price=request.form['price'], types=request.form['type'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))

            else:
                flash("You got your group password twisted")
                return render_template('edit_transportation_pin.html', form=form, id=id, pin=pin, group=group, profile=profile, name=name)
        else:
            flash("You got your user password twisted")
            return render_template('edit_transportation_pin.html', form=form, id=id, pin=pin, group=group, profile=profile, name=name)

    app.logger.info('unverified')
    return render_template('edit_transportation_pin.html', form=form, id=id, pin=pin, group=group, name=name)

@app.route('/edit_activity_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@is_logged_in
def editActivityPin(id, name):
    form = EditActivityPin(request.form)
    user = session['username']
    pin = Activity_Pin.query.filter(and_(Activity_Pin.activityName==name), (Activity_Pin.groupId==id)).first()
    form.name.data, form.price.data= pin.activityName, pin.price
    form.type.data, form.description.data, form.link.data = pin.types, pin.description, pin.link
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    if form.validate_on_submit():
        if sha256_crypt.verify(form.passwordUser.data, profile.password):

            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Activity_Pin.query.filter(and_(Activity_Pin.activityName==name), (Activity_Pin.groupId==id)).update(dict(activityName=request.form['name'], price=request.form['price'], types=request.form['type'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))
    # form = EditActivityPin(request.form)
    # user = session['username']
    # cur = mysql.connection.cursor()
    #
    # # Get pin info
    # cur.execute("SELECT * FROM activity_pin WHERE name = %s", [name])
    # pin = cur.fetchone()
    # id = pin['groupId']
    #
    # # Get group info
    # cur.execute("SELECT * FROM groups WHERE groupId = %s", [id])
    # group = cur.fetchone()
    #
    # #Populate fields
    # form.name.data = pin['name']
    # form.description.data = pin['description']
    # form.link.data = pin['link']
    # form.type.data = pin['type']
    #
    # if form.validate_on_submit():
    #     #print("Inside first if")
    #     user_pass_candidate = form.passwordUser.data
    #     cur.execute("SELECT * FROM users WHERE username = %s", [user])
    #     profile = cur.fetchone()
    #     passwordUser = profile['password']
    #     # Check Passwords
    #     if sha256_crypt.verify(user_pass_candidate, passwordUser):
    #         group_pass_candidate = form.passwordGroup.data
    #         passwordGroup = group['password']
    #         if sha256_crypt.verify(group_pass_candidate, passwordGroup):
    #             # Create variables with data
    #             name = request.form['name']
    #             description = request.form['description']
    #             link = request.form['link']
    #             type = request.form['type']
    #
    #             pinId = pin['pinId']
    #             cur.execute("UPDATE activity_pin SET name = %s, description = %s, link = %s, type = %s WHERE pinId = %s", [name, description, link,type, pinId])
    #             mysql.connection.commit()
    #             cur.close()
    #             flash("Pin succesfully updated!")
    #             return redirect(url_for('group', id=id))

            else:
                flash("You got your group password twisted")
                return render_template('edit_activity_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)
        else:
            flash("You got your user password twisted")
            return render_template('edit_activity_pin.html', form=form, id=id, pin=pin, group=group, profile=profile)

    return render_template('edit_activity_pin.html', form=form, id=id, pin=pin, group=group)


@app.route('/delete_rental_pin/<int:id>/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteRentalPin(id, name):
    form = DeletePinForm(request.form)
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    pin = Lodging_Pin.query.filter(and_(Lodging_Pin.lodgeName==name), (Lodging_Pin.groupId==id)).first()
    group = Group.query.filter(Group.id==id).first()

    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, profile.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
                return redirect(url_for('group', id=id))
            else:
                flash("Incorrect group password")
                return render_template('delete_rental_pin.html', name=name, form=form)
        else:
            flash("Incorrect user password")
            return render_template('delete_rental_pin.html', name=name, form=form)

    return render_template('delete_rental_pin.html', name=name, form=form)

@app.route('/delete_restaurant_pin/<int:id>/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteRestaurantPin(id, name):
    form = DeletePinForm(request.form)
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    pin = Rest_Pin.query.filter(and_(Rest_Pin.restName==name), (Rest_Pin.groupId==id)).first()
    group = Group.query.filter(Group.id==id).first()
    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, profile.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return render_template('delete_restaurant_pin.html', name=name, form=form, id=id)
        else:
            flash("Incorrect user password")
            return render_template('delete_restaurant_pin.html', name=name, form=form, id=id)

    return render_template('delete_restaurant_pin.html', name=name, form=form, id=id)

@app.route('/delete_transportation_pin/<int:id>/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteTransportationPin(id, name):
    form = DeletePinForm(request.form)
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    pin = Transpo_Pin.query.filter(and_(Transpo_Pin.transpoName==name), (Transpo_Pin.groupId==id)).first()
    group = Group.query.filter(Group.id==id).first()

    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, profile.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return render_template('delete_transportation_pin.html', name=name, form=form)
        else:
            flash("Incorrect user password")
            return render_template('delete_transportation_pin.html', name=name, form=form)

    return render_template('delete_transportation_pin.html', name=name, form=form)

@app.route('/delete_activity_pin/<int:id>/<string:name>', methods=['GET','POST'])
@is_logged_in
def deleteActivityPin(id, name):
    form = DeletePinForm(request.form)
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    pin = Activity_Pin.query.filter(and_(Activity_Pin.activityName==name), (Activity_Pin.groupId==id)).first()
    group = Group.query.filter(Group.id==id).first()

    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, profile.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
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



if __name__ == '__main__':
    socketio.run(app, debug=True)
