from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_wtf import FlaskForm, Form
from flask_mysqldb import MySQL
from wtforms.validators import DataRequired, Length, EqualTo, Email, NumberRange
from wtforms import Form, StringField, SelectField, TextAreaField, PasswordField, IntegerField, SubmitField, DateField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import calendar
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from threading import Thread
from flask_bootstrap import Bootstrap
from forms import *
from confi import *
from sqlalchemy import and_, or_, update
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


from models import *
import jwt
import json
#from routes import *

socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)

def sendVerificationEmail(user):
    profile = User.getProfile(user)
    token = profile.getEmailVerificationToken()
    msg = Message("Email Confirmation", sender=app.config['MAIL_USERNAME'], recipients=[profile.email])
    msg.html = render_template("verify_email.html", profile=profile, token=token)
    Thread(target=send_async_email, args=(app, msg)).start()

def sendInviteEmail(email, group):
    msg = Message("TripLounge Invitation", sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.html = render_template("inviteEmailFromGroup.html", group=group)
    Thread(target=send_async_email, args=(app, msg)).start()

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def sendPassResetEmail(userProfile):
    token = userProfile.getNewPassToken()
    msg = Message("Email Confirmation", sender=app.config['MAIL_USERNAME'], recipients=[userProfile.email])
    msg.html = render_template("email_new_password.html", profile=userProfile, token=token)
    Thread(target=send_async_email, args=(app, msg)).start()
    return

@login_manager.user_loader
def load_user(userId):
    return User.query.get(int(userId))

@app.route('/')
def gettin():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # if is_logged_in:
    #     flash("You are already logged in!")
    #     return redirect(url_for("dashboard"))
    form = SignupForm(request.form)
    if form.validate_on_submit():
        # Check if username or email is already taken
        user = User.query.filter(User.username==form.username.data).first()
        email = User.query.filter(User.email==form.email.data).first()
        if user is None and email is None:
            email2 = Invite_New_Account_Group.query.filter(Invite_New_Account_Group.email==form.email.data).first()
            u = User(firstName=form.firstName.data, lastName=form.lastName.data, email=form.email.data, username=form.username.data, password=sha256_crypt.encrypt(str(form.password.data)))
            db.session.add(u)
            db.session.commit()
            if email2 is not None:
                pend = Pending_Member(groupId=email2.groupId, userId=u.id, type='Invite')
                db.session.add(pend)
                db.session.commit()
                db.session.delete(email2)
                db.session.commit()
            flash('Congrats you are all signed up. We have sent you an email verification link. Please follow the steps in said email in order to verify your email and start using TripLounge.')
            sendVerificationEmail(form.username.data)
            return redirect(url_for('login'))
        if user is not None:
            flash('That username is already in use.')
            # form.username.data = ''

        else:
            flash('That email is already in use')
            form.email.data = ''

    return render_template('signup.html',form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    # if is_logged_in:
    #     flash("You are already logged in!")
    #     return redirect(url_for("dashboard"))
    if form.validate_on_submit():
        user = User.query.filter(User.username==form.username.data).first()
        if user:
            pass_candidate = form.password.data
            if sha256_crypt.verify(pass_candidate, user.password):
                if user.e_verified == 0:
                    flash("You must validate your email first")
                    return render_template('login.html', form=form)
                session['logged_in'] = True
                session['username'] = user.username
                flash("You are now logged in. Welcome!")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid login")
                return render_template("login.html", form=form)
        else:
            flash('Invalid login')
            return render_template('login.html', form=form)

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

@app.route('/validate_email/<token>', methods=["GET", "POST"])
def validate_email(token):
    # if is_logged_in:
    #     flash("You are already logged in!")
    #     return redirect(url_for("dashboard"))
    form = LoginForm(request.form)
    user = User.verifyEmailToken(token)
    if user is not None:
        if form.validate_on_submit():
            if user.username == form.username.data:
                profile = User.getProfile(form.username.data)
                newProfile =  User.query.filter(User.username==form.username.data).update(dict(e_verified=1))
                db.session.commit()
                session['logged_in'] = True
                session['username'] = profile.username
                flash("Your email was successfully verified. Enjoy TripLounge!!!")
                return redirect(url_for('dashboard'))
            else:
                flash("Sorry that is not the account that you requested")
                return render_template("validate_email.html", form=form)
    else:
        flash("Sorry, the token is not valid. You should try to re-sign up")
        return render_template("validate_email.html", form=form)
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
    profile = User.getProfile(user)
    groupies = User_Group.getUserGroups(profile.id)
    pends = Pending_Member.query.filter(Pending_Member.userId==profile.id)
    invitePends, requestPends = [], []
    # invitePends = [Group.getGroupInfo(x.groupId) for x in pends if x.type=='Invite']
    for x in pends:
        if x.type=='Invite':
            invitePends.append(Group.getGroupInfo(x.groupId))
        else:
            requestPends.append(Group.getGroupInfo(x.groupId))
    # app.logger.info(invitePends[0].groupName)
    # for group in groupies:
    #     if group.status == 'Accepted':
    #         groups.append(group)
    #     else:
    #         pends.append(group)
    admins = User_Group.query.filter(and_(User_Group.userId==profile.id), (User_Group.type=='Admin')).all()
    # groups = User_Group.query.filter(User_Group.userId==profile.id).all()

    return render_template("dashboard.html", profile=profile, groupies=groupies, admins=admins, invitePends=invitePends, requestPends=requestPends)

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
        profile = User.query.filter(User.username==user).first()
        password_candidate = form.password.data
        if sha256_crypt.verify(password_candidate, profile.password):
            db.session.delete(profile)
            db.session.commit()
            admins = Group.query.filter(Group.admin==profile.username).all()
            for admin in admins:
                Group.deleteGroup(admin)
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
    profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    form.name.data, form.location.data, form.description.data = group.groupName, group.location, group.description

    if form.validate_on_submit():
        password_candidate_user = form.password.data
        password_candidate_group = form.groupPassword.data
        if sha256_crypt.verify(password_candidate_user, profile.password):
            if sha256_crypt.verify(password_candidate_group, group.password):
                # Check if name is the same as before
                if group.groupName == form.name.data:
                    newGroup = Group.query.filter(Group.id==group.id).update(dict(groupName=request.form['name'],location=request.form['location'], startDate=request.form['startDate'], endDate=request.form['endDate'], description=request.form['description']))
                    db.session.commit()
                    flash('Group was successfully updated')
                    return redirect(url_for('dashboard'))
                # If group is changed, then check if it is already in use
                else:
                    group_check = Group.query.filter(Group.groupName==form.name.data)
                    # If not in use, then make the update
                    if group_check is None:
                        newGroup = Group.query.filter(Group.id==group.id).update(dict(groupName=request.form['name'],location=request.form['location'], startDate=request.form['startDate'], endDate=request.form['endDate'], description=request.form['description']))
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
                Group.deleteGroup(group)
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
            user_group = User_Group(groupId=g.id, userId=profile.id, status='Accepted', type='Admin', groupName=form.groupName.data)
            db.session.add(user_group)
            db.session.commit()
            flash('Group successfully created.')
            return redirect(url_for('dashboard'))
        else:
            flash("Sorry, that group name is already in use")

    return render_template('newGroup.html', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_req():
    # if is_logged_in:
    #     flash("You are already logged in!")
    #     return redirect(url_for("dashboard"))
    form = RequestNewPassword(request.form)
    if form.validate_on_submit():
        profile = User.query.filter(User.email==form.email.data).first()
        if profile is not None:
            sendPassResetEmail(profile)
            flash("The link has been sent, please check your email")
            return redirect(url_for('login'))
        else:
            flash("That email is not in our records, try again, or sign up for a new account!!")
    return render_template('reset_password_request.html', form=form)

@app.route('/email_new_password')
def emailNewPass():
    return render_template('email_new_password.html', profile=profile, token=token)

@app.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    if is_logged_in:
        flash("You are already logged in!")
        return redirect(url_for("dashboard"))
    form = ResetPassword(request.form)
    user = User.verifyNewPassToken(token)

    if user is not None:
        if form.validate_on_submit():
            if user.username == form.username.data:
                newPass =  User.query.filter(User.username==form.username.data).update(dict(password=sha256_crypt.encrypt(form.password.data)))
                db.session.commit()
                flash("Your password was updated, you may now login.")
                return redirect(url_for('login'))
            else:
                flash('Sorry, that is not the same user as requested.')
    else:
        flash("Sorry your link token expired, please request another")
        return redirect(url_for('reset_password_req'))
    return render_template("reset_password.html", form=form)

# def getChatHistAsync(groupNum):
#     return Chat.query.filter(Chat.groupId==groupNum).all()


@app.route('/group/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def group(id):
    user = session['username']
    profile = User.query.filter(User.username==user).first()
    group = Group.getGroupInfo(id)
    ifMember = User_Group.query.filter(and_(User_Group.userId==profile.id), (User_Group.groupId==id)).first()
    if ifMember is not None:
        renPins, restPins, transpoPins, activityPins = {}, {}, {}, {}
        members, history = [], []
        pinForm, pinFormTwo = RentalPinForm(request.form), RestPinForm(request.form)
        pinFormThree, pinFormFour = TransportationPinForm(request.form), ActivityPinForm(request.form)
        memList = User_Group.getMembers(id)
        members = [User.getProfileById(member.userId).username for member in memList]
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
            transport = Transpo_Pin(groupId=id, transpoName=pinFormThree.name.data, price=pinFormThree.price3.data, description=pinFormThree.description3.data, link=pinFormThree.link3.data, types=pinFormThree.type.data, creator=user)
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

        history = Chat.getChatHist(group.id)

        @socketio.on('connect', namespace='/chat' )
        def connect():
            group.addOnlineUser(user)
            msg = " just connected!"
            emit('on connect', {'msg': msg, 'user': user, 'users': group.users}, broadcast=True)

        @socketio.on('disconnect', namespace='/chat')
        def disconnect():
            group.removeOnlineUser(user)
            msg = " just disconnected :("
            emit('on disconnect', {'msg': msg, 'user': user, 'users': group.users}, broadcast=True)

        @socketio.on('send message', namespace='/chat')
        def handle_my_custom_event(msg):
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
    formTwo = JoinGroupRequestForm(request.form)
    username = session['username']
    if form.submit.data and form.validate():
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
                    u_g = User_Group(groupId=group.id, userId=user.id, status='Accepted', type='Member', groupName=form.name.data)
                    db.session.add(u_g)
                    db.session.commit()
                    flash('Congrats, you have joined the group')
                    return redirect(url_for('dashboard'))
                else:
                    flash("Incorrect password")
    if formTwo.submit2.data and formTwo.validate():
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
                u_g = Pending_Member(groupId=group.id, userId=user.id, type='Request')
                db.session.add(u_g)
                db.session.commit()
                flash('A request to join the group has been sent to the group admin. You will have access to the group once the admin approves your request.')
                return redirect(url_for('dashboard'))
    return render_template('joinGroup.html', form=form, formTwo=formTwo)



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

@app.route('/group/<int:id>/join', methods=['GET', 'POST'])
@is_logged_in
def groupInviteChoice(id):
    group = Group.getGroupInfo(id)
    form = JoinGroupFromInviteForm(request.form)
    return render_template('group_join_invite.html', group=group, form=form)

@app.route('/group/<int:id>/get_members', methods=['GET', 'POST'])
@is_logged_in
def groupGetMembers(id):
    # Get the group info and list of all members
    user = session['username']
    group = Group.getGroupInfo(id)
    if group.admin == user:
        members = User_Group.getMembers(id)
        mems = [User.getProfileById(x.userId).username for x in members]
        pends = Pending_Member.query.filter(Pending_Member.groupId==id).all()
        invitePends, displayPends, pendingMems =  [], [], []
        for pend in pends:
            if pend.type == 'Invite':
                invitePends.append(pend.userId)
                pendingMems.append(pend.userId)
            else:
                user = User.getProfileById(pend.userId)
                # app.logger.info(user.username)
                displayPends.append(user)
                pendingMems.append(pend.userId)
        # Form for users that have requested to join group, Accept or Decline
        requestForm = UserGroupJoinDecisionForm(request.form)
        # Form for admin invite users without account, by email. TODO
        formOne = InviteGroupNoAccountForm(request.form)
        # Form to look up users by username and send a request to join the group
        formTwo = InviteGroupByUsernameForm(request.form)
        # Form to look up users by email and send a request to join the group
        formThree = InviteGroupByEmailForm(request.form)
        if requestForm.accept.data == True and requestForm.validate():
            # requestForm.accept.data = False
            user = User.getProfile(requestForm.username.data)
            displayPends = [x for x in displayPends if x.id!=user.id]
            pender = Pending_Member.query.filter(and_(Pending_Member.groupId==group.id), (Pending_Member.userId==user.id)).first()
            db.session.delete(pender)
            db.session.commit()
            u_g = User_Group(groupId=id, userId=user.id, type='Member', groupName=group.groupName)
            db.session.add(u_g)
            db.session.commit()
            flash(requestForm.username.data + " has been added to the group!!")
            return redirect(url_for('groupGetMembers', id=id))

        if requestForm.decline.data == True and requestForm.validate_on_submit():
            user = User.getProfile(requestForm.username.data)
            pender = Pending_Member.query.filter(and_(Pending_Member.groupId==group.id), (Pending_Member.userId==user.id)).first()
            displayPends = [x for x in displayPends if x.id!=user.id]
            db.session.delete(pender)
            db.session.commit()
            flash("User " + requestForm.username.data + " request to join has been declined")
            return redirect(url_for('groupGetMembers', id=id))
        if formOne.submit1.data and formOne.validate():
            email = User.query.filter(User.email==formOne.email1.data).first()
            if email is None:
                sendInviteEmail(formOne.email1.data, group)
                invited = Invite_New_Account_Group(groupId= id, email=formOne.email1.data)
                db.session.add(invited)
                db.session.commit()
                flash("We have sent an email to " + formOne.email1.data + ". Once they have signed up for and account, they can accept the invitation.")
                return redirect(url_for('groupGetMembers', id=id))
            else:
                flash('That email address has a TripLounge account associated with it. You can use it below in the email with account sextion')
                return redirect(url_for('groupGetMembers', id=id))
        if formTwo.submit2.data and formTwo.validate():
            user = User.query.filter(User.username==formTwo.username.data).first()
            if user is not None:
                if user.id in mems:
                    flash('That user is already in the group!!')
                    formTwo.username.data = ''
                    return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)
                if user.id in pendingMems:
                    flash('That user already has a pending invite to the group. You must for them to respond')
                    formTwo.username.data = ''
                    return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)
                else:
                    u_g = Pending_Member(groupId=group.id, userId=user.id, type='Request')
                    db.session.add(u_g)
                    db.session.commit()
                    formTwo.username.data = ''
                    flash('An invitation to join the group has been sent to ' + user.username + "'s dashboard. They must accept accept the invite in order to access the group")
                    return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)

            else:
                formTwo.username.data = ''
                flash('User not found')
                return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)

        if formThree.submit3.data and formThree.validate():
            user = User.query.filter(User.email==formThree.email2.data).first()
            if user is not None:
                if user.id in mems:
                    flash('That user is already in the group!!')
                    formThree.email2.data = ''
                    return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)
                if user.id in pendingMems:
                    flash('That user already has a pending invite to the group. You must wait for them to respond')
                    formThree.email2.data = ''
                    return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)
                else:
                    u_g = Pending_Member(groupId=group.id, userId=user.id, type='Request')
                    db.session.add(u_g)
                    db.session.commit()
                    formThree.email2.data = ''
                    flash('An invitation to join the group has been sent to ' + user.username + "'s dashboard. They must accept accept the invite in order to access the group")
                    return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)
            else:
                flash('User not found')
                formThree.email2.data = ''
                return render_template('get_members.html', requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree,group=group)
    else:
        flash('You are not that groups admin!!!')
        return redirect(url_for('dashboard'))

    return render_template('get_members.html', pends=pends, requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group)

@app.route('/group/<int:id>/calendar', methods=['GET', 'POST'])
@is_logged_in
def groupCalendarDay(id):
    group = Group.getGroupInfo(id)
    notes = Calendar_Note.getNotes(id)
    cur = mysql.connection.cursor()
    sql = 'SELECT * FROM calendarnotes WHERE groupId = %s'
    cur.execute(sql, [id])
    listNotes = cur.fetchall()
    listNotes = json.dumps(listNotes)
    listNotes = json.loads(listNotes)
    fullStartDate, fullEndDate = str(group.startDate), str(group.endDate)
    # fullStartDate, fullEndDate = fullStartDate[::-1], fullEndDate[::-1]
    startMonth, endMonth = fullStartDate[5:7], fullEndDate[5:7]

    eventForm = CalendarEventForm(request.form)
    @socketio.on('connect', namespace='/calendar' )
    def connect():
        app.logger.info(listNotes)
        emit('on connect', {'notes': listNotes}, broadcast=True)

    @socketio.on('store note', namespace='/calendar')
    def handle_my_custom_event(name, time, date):
        app.logger.info(name + time + date)
        dateTime = date + ' ' + time
        newNote = Calendar_Note(groupId=id, name=name, date=dateTime, username=session['username'])
        db.session.add(newNote)
        db.session.commit()
        msg = 'Event saved!!'
        emit('note saved', {'msg': msg, 'name': name, 'time': time, 'date': date}, broadcast=True)

    return render_template("calendar.html", group=group, eventForm=eventForm, fullStartDate=fullStartDate, fullEndDate=fullEndDate, startMonth=startMonth, endMonth=endMonth, listNotes=listNotes)


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


if __name__ == '__main__':
    socketio.run(app, debug=True)
