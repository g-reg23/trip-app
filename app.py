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
from forms import *
from confi import *
from sqlalchemy import and_, or_, update
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug import secure_filename
# from datetime import datetime
from validate_email import validate_email
from validators import *
import datetime
from models import *
import jwt
import json
#from routes import *

socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

def getAllGroups():
    groups = User_Group.getUserGroups(current_user.id)
    return [Group.query.filter(Group.id==g.groupId).first() for g in groups]


@login_manager.user_loader
def load_user(userId):
    return User.query.get(int(userId))

@app.route('/')
def gettin():
    groupIds = []
    if current_user.is_authenticated:
        groupIds = getAllGroups()
    return render_template('home.html', groupIds=groupIds)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        flash("You are already logged in!")
        return redirect(url_for("dashboard"))
    form = SignupForm(request.form)
    if form.validate_on_submit():
        # Check if username or email is already taken
        user = User.query.filter(User.username==form.username.data).first()
        email = User.query.filter(User.email==form.email.data).first()
        if user is None and email is None:
            if has_upper(form.password.data) and has_lower(form.password.data) and has_digit(form.password.data) and check_length_min(form.password.data, 8):
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
                flash('Congrats you are all signed up. We have sent you an email verification link. Please follow the steps in said email in order to verify your account and start using TripLounge.')
                sendVerificationEmail(form.username.data)
                return redirect(url_for('login'))
            else:
                flash('Sorry, the password must contain at least 8 characters including 1 lower case, 1 upper case and 1 number digit.')
                return redirect(url_for('signup'))
        if user is not None:
            flash('That username is already in use.')
            # form.username.data = ''

        else:
            flash('That email is already in use')
            form.email.data = ''

    return render_template('signup.html',form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in!")
        return redirect(url_for("dashboard"))
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
                # session['logged_in'] = True
                # session['username'] = user.username
                login_user(user)
                # app.logger.info(session['username'])
                flash("You are now logged in. Welcome!")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid login")
                return render_template("login.html", form=form)
        else:
            flash('Invalid login')
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/validate_email/<token>', methods=["GET", "POST"])
def validate_email(token):
    if current_user.is_anonymous == False:
        flash("You are already logged in!")
        return redirect(url_for("dashboard"))
    form = LoginForm(request.form)
    user = User.verifyEmailToken(token)
    if user is not None:
        if form.validate_on_submit():
            if user.username == form.username.data:
                profile = User.getProfile(form.username.data)
                newProfile =  User.query.filter(User.username==form.username.data).update(dict(e_verified=1))
                db.session.commit()
                login_user(profile)
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
@login_required
def logout():
    logout_user()
    flash("You are now logged out", "danger")
    return redirect(url_for("login"))

@app.route('/dashboard', methods=["GET", "POST"])
@login_required
def dashboard():
    pends = Pending_Member.query.filter(and_(Pending_Member.userId==current_user.id), (Pending_Member.type=='Invite')).all()
    invitePends, requestPends = [], []
    profile = User.query.filter(User.id==current_user.id).first()
    groupIds = getAllGroups()
    admin_group_info = Group.query.filter(Group.admin==current_user.username).all()
    form1, form2 = DeleteGroupForm(request.form), DeleteProfileForm(request.form)
    deleteAccountForm, editAccountForm = DeleteProfileForm(request.form), EditProfileForm(request.form)
    cur = mysql.connection.cursor()
    invitePends = [Group.getGroupInfo(x.groupId) for x in pends]
    # for pend in pends:
    #     invitePends.push(Group.getGroupInfo(pend.))
    app.logger.info(pends)
    # for group in admin_group_info:
        # requests = Pending_Member.query.filter(and_(Pending_Member.groupId==group.id), (Pending_Member.type=='Request')).all()
        # requestPends = [x for x in requests]
    # sql = 'SELECT * FROM users WHERE id = %s'
    # cur.execute(sql, [profile.id])
    # prof = cur.fetchone()
    # prof['registerDate'] = '{:%B %d, %Y}'.format(prof['registerDate'])
    # # del prof['registerDate']
    # prof = json.dumps(prof)
    # prof = json.loads(prof)
    # for x in pends:
    #     if x.type=='Invite':
    #         invitePends.append(Group.getGroupInfo(x.groupId))
    #     else:
    #         requestPends.append(Group.getGroupInfo(x.groupId))
    admins = Group.query.filter(Group.admin==current_user.username).all()

    if deleteAccountForm.yes.data and deleteAccountForm.validate_on_submit():
        if sha256_crypt.verify(deleteAccountForm.password.data, profile.password):
            db.session.delete(profile)
            db.session.commit()
            admins = Group.query.filter(Group.admin==current_user.userame).all()
            for admin in admins:
                Group.deleteGroup(admin)
            flash('You have successfully deleted your account. Come back soon!!!')
            return redirect(url_for('logout'))
        else:
            flash('Incorrect Password.')
            return redirect(url_for('dashboard'))
    room = current_user.id
    @socketio.on('connect', namespace='/dash')
    def connect():
        join_room(room)
        emit('on connect', room=room)

    @socketio.on('leave group', namespace='/dash')
    def handle_my_custom_event(group_id, group_name):
        user_group = User_Group.query.filter(and_(User_Group.groupId==group_id), (User_Group.userId==current_user.id)).first()
        db.session.delete(user_group)
        db.session.commit()
        # admins_to_delete = Group.query.filter(Group.admin==current_user.userame).all()
        # for admin in admins_to_delete:
        #     Group.deleteGroup(admin)
        emit('group left', {'name': group_name}, room=room)

    @socketio.on('group edit', namespace='/dash')
    def handle_my_custom_event(name, location, start, end, description, edit_id, user_pass, group_pass):
        update = Group.query.filter(Group.id==edit_id).first();
        # update2 = User_Group.query.filter(User_Group.groupId==edit_id).update(dict(groupName=name))
        if sha256_crypt.verify(user_pass, current_user.password):
            if sha256_crypt.verify(group_pass, update.password):
                check = Group.query.filter(Group.groupName==name).first()
                idCheck = Group.query.filter(Group.id==edit_id).first()
                if check:
                    if check.groupName == idCheck.groupName:
                        if date_check(start) and date_check(end):
                            if dates_are_possible(start, end):
                                # app.logger.info(check_length_min(name))
                                if check_length_min(location, 3) and check_length_max(location, 35) and check_length_min(description, 10) and check_length_max(description, 255):
                                    update2 = Group.query.filter(Group.id==edit_id).update(dict(location=location, startDate=start, endDate=end, description=description))
                                    db.session.commit()
                                    emit('group edited', {'id': edit_id, 'name': name, 'location': location, 'start': start, 'end': end, 'description': description}, room=room)
                                else:
                                    emit('group edit bad length', room=room)
                            else:
                                emit('dates not possible', room=room)
                        else:
                            emit('incorrect date format', room=room)
                    else:
                        emit('group name in use', {'name': name}, room=room)

                else:
                    if date_check(start) and date_check(end):
                        if dates_are_possible(start, end):
                            if check_length_min(name, 3)==True and check_length_max(name, 35) and check_length_min(location, 3) and check_length_max(location, 35) and check_length_min(description, 10) and check_length_max(description, 255):
                                update2 = Group.query.filter(Group.id==edit_id).update(dict(groupName=name, location=location, startDate=start, endDate=end, description=description))
                                db.session.commit()
                                emit('group edited', {'id': edit_id, 'name': name, 'location': location, 'start': start, 'end': end, 'description': description}, room=room)
                            else:
                                emit('group edit bad length', room=room)
                        else:
                            emit('dates not possible', room=room)
                    else:
                        emit('incorrect date format', room=room)
            else:
                emit('bad pass group', room=room)
        else:
            emit('bad pass group', room=room)

    @socketio.on('delete group', namespace='/dash')
    def handle_my_custom_event(group_name, password):
        app.logger.info('hi')
        if sha256_crypt.verify(password, current_user.password):
            group = Group.query.filter(Group.groupName==group_name).first()
            db.session.delete(group)
            db.session.commit()
            emit('group deleted', {'name': group_name}, room=room)
        else:
            emit('bad pass group', room=room)

    @socketio.on('edit account', namespace='/dash')
    def handle_my_custom_event(first_name, last_name, email, password):
        is_val = validate_email(email)
        if is_val:
            if len(first_name) >= 3 and len(first_name) <= 35 and len(last_name) >= 3 and len(last_name) <= 35:
                if sha256_crypt.verify(password, current_user.password):
                    newProfile = User.query.filter(User.id==current_user.id).update(dict(firstName=first_name,lastName=last_name, email=email))
                    db.session.commit()
                    editAccountForm.password2.data = ''
                    emit('account edited', room=room)
                else:
                    editAccountForm.password2.data = ''
                    emit('bad pass edit account', room=room)
            else:
                emit('back end invalid form', room=room)
        else:
            emit('not email', {'email': email}, room=room)

    @socketio.on('join pend', namespace='/dash')
    def handle_my_custom_event(pend_id):
        pend = User_Group(groupId=pend_id, userId=current_user.id, type='Member')
        db.session.add(pend)
        db.session.commit()
        pend = Pending_Member.query.filter(and_(Pending_Member.userId==current_user.id), (Pending_Member.groupId==pend_id)).first()
        db.session.delete(pend)
        db.session.commit()
        emit('pend joined', room=room)

    @socketio.on('decline pend', namespace='/dash')
    def handle_my_custom_event(pend_id):
        pend = Pending_Member.query.filter(and_(Pending_Member.userId==current_user.id), (Pending_Member.groupId==pend_id)).first()
        db.session.delete(pend)
        db.session.commit()
        emit('pend declined', room=room)

    @socketio.on('disconnect', namespace='/dash')
    def disconnect():
        leave_room(room)
        emit('on disconnect', room=room)

    return render_template("dashboard.html", admin_group_info=admin_group_info, profile=current_user, groupIds=groupIds, editAccountForm=editAccountForm, deleteAccountForm=deleteAccountForm, admins=admins, invitePends=invitePends, requestPends=requestPends, form1=form1, form2=form2)



@app.route('/newGroup', methods=['GET', 'POST'])
@login_required
def newGroup():
    form = GroupForm(request.form)
    groupIds = getAllGroups()
    if form.validate_on_submit():
        group = Group.query.filter(Group.groupName==form.groupName.data).first()
        if group is None:
            app.logger.info(form.startDate.data)
            if dates_are_possible(str(form.startDate.data), str(form.endDate.data)):
                g = Group(groupName=form.groupName.data, location=form.location.data, startDate=form.startDate.data, endDate=form.endDate.data, admin=current_user.username, password=sha256_crypt.encrypt(str(form.password.data)), description=form.description.data)
                profile = User.query.filter(User.username==current_user.username).first()
                db.session.add(g)
                db.session.commit()
                user_group = User_Group(groupId=g.id, userId=current_user.id, type='Admin')
                db.session.add(user_group)
                db.session.commit()
                # calNote = Calendar_Note(groupId=g.id, name='First Day of Trip', )
                flash('Group successfully created.')
                return redirect(url_for('dashboard'))
            else:
                flash('The end date cannot be before the start date, also the start and end dates can not be in the past, sorry!!')
        else:
            flash("Sorry, that group name is already in use")

    return render_template('newGroup.html', form=form, groupIds=groupIds)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_req():
    if current_user.is_anonymous:
        form = RequestNewPassword(request.form)
        if form.validate_on_submit():
            profile = User.query.filter(User.email==form.email.data).first()
            if profile is not None:
                sendPassResetEmail(profile)
                flash("The link has been sent, please check your email")
                return redirect(url_for('login'))
            else:
                flash("That email is not in our records, try again, or sign up for a new account!!")
    else:
        flash("You are already logged in!")
        return redirect(url_for("dashboard"))
    return render_template('reset_password_request.html', form=form)

@app.route('/email_new_password')
def emailNewPass():
    return render_template('email_new_password.html', profile=profile, token=token)

@app.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        flash("You are already logged in!")
        return redirect(url_for("dashboard"))
    form = ResetPassword(request.form)
    user = User.verifyNewPassToken(token)

    if user is not None:
        if form.validate_on_submit():
            if user.username == form.username.data:
                if has_lower(form.password.data) and has_upper(form.password.data) and has_digit(form.password.data) and check_length_min(form.password.data, 8):
                    newPass =  User.query.filter(User.username==form.username.data).update(dict(password=sha256_crypt.encrypt(form.password.data)))
                    db.session.commit()
                    flash("Your password was updated, you may now login.")
                    return redirect(url_for('login'))
                else:
                    flash('Sorry, the password must contain at least 8 characters including 1 lower case, 1 upper case and 1 number digit.')
            else:
                flash('Sorry, that is not the same user as requested.')
    else:
        flash("Sorry your link token expired, please request another")
        return redirect(url_for('reset_password_req'))
    return render_template("reset_password.html", form=form)


@app.route('/group/<int:id>', methods=['GET', 'POST'])
@login_required
def group(id):
    # profile = User.query.filter(User.username==current_user.username).first()
    group = Group.getGroupInfo(id)
    groupIds = getAllGroups()
    ifMember = User_Group.query.filter(and_(User_Group.userId==current_user.id), (User_Group.groupId==id)).first()
    if ifMember is not None:
        renPins, restPins, transpoPins, activityPins = {}, {}, {}, {}
        members, history, budget = [], [], Budget.getBudget(current_user.id)
        pinForm, pinFormTwo = RentalPinForm(request.form), RestPinForm(request.form)
        pinFormThree, pinFormFour = TransportationPinForm(request.form), ActivityPinForm(request.form)
        budgetForm, expenseForm, expenses = BudgetForm(request.form), ExpenseForm(request.form), Expense.getExpenses(group.id, current_user.id)
        memList = User_Group.getMembers(id)
        members = [User.getProfileById(member.userId).username for member in memList]
        # if pinForm.submit1.data and pinForm.validate():
        #     rental = Lodging_Pin(groupId=id, lodgeName=pinForm.rentalName.data, price=pinForm.price.data, rooms=pinForm.rooms.data, description=pinForm.description.data, link=pinForm.link.data, creator=current_user.username)
        #     db.session.add(rental)
        #     db.session.commit()
        #     flash("Pin created!")
        #     return redirect(url_for('group', id=id))

        # if pinFormTwo.submit2.data and pinFormTwo.validate():
        #     rest = Rest_Pin(groupId=id, restName=pinFormTwo.restName.data, description=pinFormTwo.description2.data, link=pinFormTwo.link2.data, types=pinFormTwo.type.data, creator=current_user.username)
        #     db.session.add(rest)
        #     db.session.commit()
        #     flash("Pin created")
        #     return redirect(url_for('group', id=id))
        # # Get rental pins and rest pins
        renPins, restPins = Lodging_Pin.query.filter(Lodging_Pin.groupId==id).all(), Rest_Pin.query.filter(Rest_Pin.groupId==id).all()
        #
        # if pinFormThree.submit3.data and pinFormThree.validate():
        #     transport = Transpo_Pin(groupId=id, transpoName=pinFormThree.name.data, price=pinFormThree.price3.data, description=pinFormThree.description3.data, link=pinFormThree.link3.data, types=pinFormThree.type.data, creator=current_user.username)
        #     db.session.add(transport)
        #     db.session.commit()
        #     flash("Pin created")
        #     return redirect(url_for('group', id=id))
        #
        #
        # if pinFormFour.submit4.data and pinFormFour.validate():
        #     activity = Activity_Pin(groupId=id, activityName=pinFormFour.activityName.data, price=pinFormFour.price.data, description=pinFormFour.description.data, types=pinFormFour.type.data, link=pinFormFour.link.data, creator=current_user.username)
        #     db.session.add(activity)
        #     db.session.commit()
        #     flash("Pin created")
        #     return redirect(url_for('group', id=id))
        #Get transportation pins and activity pins
        transpoPins, activityPins = Transpo_Pin.query.filter(Transpo_Pin.groupId==id).all(), Activity_Pin.query.filter(Activity_Pin.groupId==id).all()
        #
        # if budgetForm.submit5.data and budgetForm.validate():
        #     query = Budget.query.filter(and_(Budget.userId==current_user.id), (Budget.groupId==group.id)).first()
        #     if query is None:
        #         budge = Budget(groupId=group.id, userId=current_user.id, total=budgetForm.budget.data)
        #         db.session.add(budge)
        #         db.session.commit()
        #         flash('Your budget has been added!!!')
        #         return redirect(url_for('group', id=id))
        #     else:
        #         newQuery = Budget.query.filter(and_(Budget.userId==current_user.id), (Budget.groupId==group.id)).update(dict(total=budgetForm.budget.data))
        #         db.session.commit()
        #         flash('Your budget has been updated!!!')
        #         return redirect(url_for('group', id=id))


        history = Chat.getChatHist(group.id)
        room = group.id
        @socketio.on('connect', namespace='/chat' )
        def connect():
            group.addOnlineUser(current_user.username)
            msg = current_user.username + " just connected."
            join_room(id)
            emit('on connect', {'msg': msg, 'user': current_user.username, 'users': group.users}, room=room)

        @socketio.on('disconnect', namespace='/chat')
        def disconnect():
            group.removeOnlineUser(current_user.username)
            msg = " just disconnected :("
            leave_room(room)
            emit('on disconnect', {'msg': msg, 'user': current_user.username, 'users': group.users}, room=room)

        @socketio.on('submit expense', namespace='/chat')
        def handle_my_custom_event(name, price, pays, splits, type):
            expense = Expense(groupId=group.id, userId=current_user.id, name=name, cost=price, payments=pays, splits=splits, type=type)
            db.session.add(expense)
            db.session.commit()
            emit('expense saved', room=room)

        @socketio.on('change budget', namespace='/chat')
        def handle_my_custom_event(new_budget):
            if_budget = Budget.query.filter(and_(Budget.userId==current_user.id), (Budget.groupId==group.id)).first()
            if if_budget is None:
                new_query = Budget(groupId=group.id, userId=current_user.id, total=new_budget)
                db.session.add(new_query)
                db.session.commit()
            else:
                new_query = Budget.query.filter(and_(Budget.userId==current_user.id), (Budget.groupId==group.id)).update(dict(total=new_budget))
                db.session.commit()
            emit('budget changed', room=room)

        @socketio.on('rental submit', namespace='/chat')
        def handle_my_custom_event(name, price, rooms, description, link):
            rental = Lodging_Pin(groupId=id, lodgeName=name, price=price, rooms=rooms, description=description, link=link, creator=current_user.username)
            db.session.add(rental)
            db.session.commit()
            emit('rental saved', room=room)

        @socketio.on('rest submit', namespace='/chat')
        def handle_my_custom_event(name, description, type, link):
            rental = Rest_Pin(groupId=id, restName=name, description=description, types=type, link=link, creator=current_user.username)
            db.session.add(rental)
            db.session.commit()
            emit('rest saved', room=room)

        @socketio.on('trans submit', namespace='/chat')
        def handle_my_custom_event(name, price, description, type, link):
            trans = Transpo_Pin(groupId=id, transpoName=name, description=description, types=type, link=link, creator=current_user.username)
            db.session.add(trans)
            db.session.commit()
            emit('trans saved', room=room)

        @socketio.on('act submit', namespace='/chat')
        def handle_my_custom_event(name, price, description, type, link):
            rental = Activity_Pin(groupId=id, activityName=name, price=price, description=description, types=type, link=link, creator=current_user.username)
            db.session.add(rental)
            db.session.commit()
            emit('act saved', room=room)

        @socketio.on('send message', namespace='/chat')
        def handle_my_custom_event(msg):
            chat_mess = Chat(groupId=id, username=current_user.username, message=msg)
            db.session.add(chat_mess)
            db.session.commit()
            emit('new message', {'msg': msg, 'user': current_user.username}, room=room)

        @socketio.on('delete all expenses', namespace='/chat')
        def handle_my_custom_event():
            for i in range(len(expenses)):
                expensed = Expense.query.filter(and_(Expense.groupId==group.id), (Expense.userId==current_user.id)).first()
                db.session.delete(expensed)
                db.session.commit()
            msg = 'All expenses deleted!!'
            emit('allDeleted', room=room)

        @socketio.on('delete one expense', namespace='/chat')
        def handle_my_custom_event(name):
            exper = Expense.query.filter(and_(Expense.userId==current_user.id), (Expense.name==name)).first()
            db.session.delete(exper)
            db.session.commit()
            emit('oneDeleted', room=room)
    else:
        flash("You must join the group first!")
        return redirect(url_for('newGroup'))

    return render_template("group.html", groupIds=groupIds, expenses=expenses, expenseForm=expenseForm, budget=budget, budgetForm=budgetForm, group=group, renPins=renPins, restPins=restPins, transpoPins=transpoPins, activityPins=activityPins, pinForm=pinForm, id=id, user=current_user.username, pinFormTwo=pinFormTwo, pinFormThree=pinFormThree, pinFormFour=pinFormFour, history=history, members=members)

@app.route('/joinGroup', methods=['GET', 'POST'])
@login_required
def joinGroup():
    form = JoinGroupForm(request.form)
    formTwo = JoinGroupRequestForm(request.form)
    groupIds = getAllGroups()
    if form.submit.data and form.validate():
        group = Group.query.filter(Group.groupName==form.name.data).first()
        if group is None:
            flash("Sorry that group does not exist yet.")
            form.name.data = ''
        else:
            check = User_Group.query.filter(and_(User_Group.userId==current_user.id), (User_Group.groupId==group.id)).first()
            if check:
                flash('You are already a member of that group!')
            else:
                pass_candidate = form.password.data
                if sha256_crypt.verify(pass_candidate, group.password):
                    u_g = User_Group(groupId=group.id, userId=current_user.id, type='Member')
                    db.session.add(u_g)
                    db.session.commit()
                    flash('Congrats, you have joined the group')
                    return redirect(url_for('dashboard'))
                else:
                    flash("Incorrect password")
    if formTwo.submit2.data and formTwo.validate():
        group = Group.query.filter(Group.groupName==formTwo.name2.data).first()
        if group is None:
            flash("Sorry that group does not exist yet.")
            formTwo.name2.data = ''
        else:
            check = User_Group.query.filter(and_(User_Group.userId==current_user.id), (User_Group.groupId==group.id)).first()
            if check:
                flash('You are already a member of that group!')
                return redirect(url_for('joinGroup'))
            else:
                check2 = Pending_Member.query.filter(and_(Pending_Member.userId==current_user.id), (Pending_Member.groupId==group.id)).first()
                if check2 is None:
                    u_g = Pending_Member(groupId=group.id, userId=current_user.id, type='Request', message=formTwo.messageJoin.data)
                    db.session.add(u_g)
                    db.session.commit()
                    flash('A request to join the group has been sent to the group admin. You will have access to the group once the admin approves your request.')
                    return redirect(url_for('dashboard'))
                else:
                    if check2.type == 'Request':
                        flash('You already have a pending requestto join the group. You must wait for the group admin to respond.')
                        return redirect(url_for('dashboard'))
                    else:
                        flash('This group has already sent you an invitation to join. Please respond to this on your profile page.')
                        return redirect(url_for('dashboard'))

    return render_template('joinGroup.html', form=form, formTwo=formTwo, groupIds=groupIds)


@app.route('/group/<int:id>/join', methods=['GET', 'POST'])
@login_required
def groupInviteChoice(id):
    group = Group.getGroupInfo(id)
    form = JoinGroupFromInviteForm(request.form)
    groupIds = getAllGroups()
    return render_template('group_join_invite.html', group=group, form=form, groupIds=groupIds)

@app.route('/group/<int:id>/get_members', methods=['GET', 'POST'])
@login_required
def groupGetMembers(id):
    # Get the group info and list of all members
    group = Group.getGroupInfo(id)
    groupIds = getAllGroups()
    if group.admin == current_user.username:
        members = User_Group.getMembers(id)
        mems = [User.getProfileById(x.userId).username for x in members]
        memNames = [User.getProfileById(x.userId).firstName + ' ' + User.getProfileById(x.userId).lastName for x in members]
        app.logger.info(memNames)
        pends = Pending_Member.query.filter(Pending_Member.groupId==id).all()
        invitePends, displayPends, pendingMems, messages =  [], [], [], []
        # reqs = {}
        for pend in pends:
            if pend.type == 'Invite':
                invitePends.append(pend.userId)
                pendingMems.append(pend.userId)
            else:
                user = User.getProfileById(pend.userId)
                # app.logger.info(user.username)
                displayPends.append(user)
                pendingMems.append(pend.userId)

                messages.append(pend.message)
        #         cur = mysql.connection.cursor()
        #         sql = 'SELECT * FROM users WHERE id = %s'
        #         cur.execute(sql, [user.id])
        #         request = cur.fetchone()
        #         request.pop('registerDate')
        #         reqs.update(request)
        # reqs = json.dumps(reqs)
        # reqs = json.loads(reqs)
        # app.logger.info(reqs)
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
            u_g = User_Group(groupId=id, userId=user.id, type='Member')
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
                invited = Invite_New_Account_Group(groupId=id, email=formOne.email1.data)
                db.session.add(invited)
                db.session.commit()
                flash("We have sent an email to " + formOne.email1.data + ". Once they have signed up for and account, they can accept the invitation.")
                return redirect(url_for('groupGetMembers', id=id))
            else:
                flash('That email address has a TripLounge account associated with it. You can use it below in the email with account sextion')
                return redirect(url_for('groupGetMembers', id=id))
        if formTwo.submit2.data and formTwo.validate():
            if formTwo.username.data == current_user.username:
                flash('You cannot invite yourself, you are already in the group! HeHe')
                return redirect(url_for('groupGetMembers', id=id))
            else:
                user = User.query.filter(User.username==formTwo.username.data).first()
                if user is not None:
                    if formTwo.username.data in mems:
                        flash('That user is already in the group!!')
                        formTwo.username.data = ''
                        return redirect(url_for('groupGetMembers', id=id))
                    if user.id in pendingMems:
                        if user.id in invitePends:
                            flash(user.username + ' already has a pending invite to the group. You must wait for them to respond')
                            formTwo.username.data = ''
                            return redirect(url_for('groupGetMembers', id=id))
                        else:
                            flash(user.username + ' has requested to join the group. Look in the first section of join requests.')
                            formTwo.username.data = ''
                            return redirect(url_for('groupGetMembers', id=id))

                    else:
                        u_g = Pending_Member(groupId=group.id, userId=user.id, type='Invite')
                        db.session.add(u_g)
                        db.session.commit()
                        formTwo.username.data = ''
                        flash('An invitation to join the group has been sent to ' + user.username + "'s dashboard. They must accept accept the invite in order to access the group")
                        return redirect(url_for('groupGetMembers', id=id))

                else:
                    formTwo.username.data = ''
                    flash('User not found')
                    return redirect(url_for('groupGetMembers', id=id))
        if formThree.submit3.data and formThree.validate():
            if formThree.email2.data == current_user.email:
                flash('You cannot invite yourself. You are already in the group. HeHe')
                return redirect(url_for('groupGetMembers', id=id))
            else:
                user = User.query.filter(User.email==formThree.email2.data).first()
                if user is not None:
                    if user.username in mems:
                        flash('That user is already in the group!!')
                        formThree.email2.data = ''
                        return redirect(url_for('groupGetMembers', id=id))
                    if user.id in pendingMems:
                        flash('That user already has a pending invite to the group. You must wait for them to respond')
                        formThree.email2.data = ''
                        return redirect(url_for('groupGetMembers', id=id))
                    else:
                        u_g = Pending_Member(groupId=group.id, userId=user.id, type='Invite')
                        db.session.add(u_g)
                        db.session.commit()
                        formThree.email2.data = ''
                        flash('An invitation to join the group has been sent to ' + user.username + "'s dashboard. They must accept accept the invite in order to access the group")
                        return redirect(url_for('groupGetMembers', id=id))
                else:
                    flash('User not found')
                    formThree.email2.data = ''
                    return redirect(url_for('groupGetMembers', id=id))
        room = id
        @socketio.on('connect', namespace='/getMems')
        def connect():
            join_room(room)
            emit('on connect', room=room)
        @socketio.on('accept to group', namespace='/getMems')
        def handle_my_custom_event(username):
            new_user = User.getProfile(username)
            unpend = Pending_Member.query.filter(and_(Pending_Member.userId==new_user.id), (Pending_Member.groupId==id)).first()
            db.session.delete(unpend)
            db.session.commit()
            u_g = User_Group(userId=new_user.id, groupId=id, type='Member')
            db.session.add(u_g)
            db.session.commit()
            emit('accepted', {'user': username}, room=room)

        @socketio.on('deny to group', namespace='/getMems')
        def handle_my_custom_event(username):
            new_user = User.getProfile(username)
            unpend = Pending_Member.query.filter(and_(Pending_Member.userId==new_user.id), (Pending_Member.groupId==id)).first()
            db.session.delete(unpend)
            db.session.commit()
            emit('denied',{'user': username}, room=room)
        @socketio.on('remove member', namespace='/getMems')
        def handle_my_custom_event(username, name):
            app.logger.info(username)
            user = User.getProfile(username)
            if user is not None:
                check_relation = User_Group.query.filter(and_(User_Group.userId==user.id), (User_Group.groupId==id)).first()
                if check_relation:
                    if check_relation.type == 'Admin':
                        emit('admin no remove', room=room)
                    else:
                        db.session.delete(check_relation)
                        db.session.commit()
                        emit('member removed', {'username': username, 'group':group.groupName}, room=room)
                else:
                    emit('not member', room=room)
            else:
                # flash('Sorry that user does not have an account with us, and therefore cannot be in the group. What had happened was...')
                emit('not a user', room=room)
    else:
        flash('You are not that groups admin!!!')
        return redirect(url_for('dashboard'))

    return render_template('get_members.html', messages=messages, groupIds=groupIds, pends=pends, requestForm=requestForm, displayPends=displayPends, invitePends=invitePends, formOne=formOne, formTwo=formTwo, formThree=formThree, group=group, mems=mems, memNames=memNames)

@app.route('/group/<int:id>/calendar', methods=['GET', 'POST'])
@login_required
def groupCalendarDay(id):
    member = User_Group.query.filter(and_(User_Group.groupId==id), (User_Group.userId==current_user.id)).first()
    if member is not None:
        notes = Calendar_Note.getNotes(id)
        group = Group.getGroupInfo(id)
        groupIds = getAllGroups()
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
        room = id
        @socketio.on('connect', namespace='/calendar')
        def connect():
            join_room(room)
            emit('on connect', {'name': group.groupName, 'id': group.id}, room=room)

        @socketio.on('store note', namespace='/calendar')
        def handle_my_custom_event(name, time, date, length):
            check = Calendar_Note.query.filter(and_(Calendar_Note.username==current_user.username), (Calendar_Note.name==name), (Calendar_Note.groupId==group.id)).first()
            if check is not None:
                emit('note name used', {'name': name}, room=room)
            else:
                app.logger.info(time)
                if time[3:5] == '30':
                    mins = '30'
                else:
                    mins = '00'
                if int(time[0:2]) > 11:
                    ampm = 'PM'
                    hours = str(int(time[0:2])-12)
                    if hours == '0':
                        hours = '12'
                else:
                    ampm = 'AM'
                    hours = str(time[0:2])
                    if hours == '00':
                        hours = '12'
                new_time = hours + ':' + mins + ' ' + ampm
                dateTime = date + ' ' + time
                newNote = Calendar_Note(groupId=id, name=name, date=dateTime, username=current_user.username, event_length=length, time=new_time)
                db.session.add(newNote)
                db.session.commit()
                msg = 'Event saved!!'
                emit('note saved', {'msg': msg, 'name': name, 'time': newNote.time, 'date': date, 'length': length}, room=room)

        @socketio.on('edit note', namespace='/calendar')
        def handle_my_custom_event(new_name, time, length, old_name):
            check_user = Calendar_Note.query.filter(and_(Calendar_Note.name==old_name), (Calendar_Note.groupId==group.id)).first()
            if check_user.username == current_user.username:
                if time[3:5] == '30':
                    mins = '30'
                else:
                    mins = '00'
                if int(time[0:2]) > 11:
                    ampm = 'PM'
                    hours = str(int(time[0:2])-12)
                    if hours == '0':
                        hours = '12'
                else:
                    ampm = 'AM'
                    hours = str(time[0:2])
                    if hours == '00':
                        hours = '12'
                new_time = hours + ':' + mins + ' ' + ampm
                if old_name == new_name:
                    # Name is the same, so only update time and length
                    new_note = Calendar_Note.query.filter(and_(Calendar_Note.username==current_user.username), (Calendar_Note.name==old_name)).update(dict(time=time, event_length=length))
                    db.session.commit()
                    emit('note edited', {'name': new_name, 'time': new_time, 'length': length}, room=room)
                else:
                    # Update all, besides date
                    check = Calendar_Note.query.filter(and_(Calendar_Note.name==new_name), (Calendar_Note.username==current_user.username)).first()
                    if check is None:
                        app.logger.info('hi')
                        new_note = Calendar_Note.query.filter(and_(Calendar_Note.username==current_user.username), (Calendar_Note.name==old_name)).update(dict(name=new_name, time=time, event_length=length))
                        db.session.commit()
                        emit('note edited', {'name': new_name, 'time': new_time, 'length': length},room=room)
                    else:
                        emit('note name used', {'name': new_name}, room=room)
            else:
                emit('not note creator', room=room)
    else:
        flash('You must join the group first!')
        return redirect(url_for('dashboard'))

    return render_template("calendar2.html", group=group, groupIds=groupIds, eventForm=eventForm, fullStartDate=fullStartDate, fullEndDate=fullEndDate, startMonth=startMonth, endMonth=endMonth, listNotes=listNotes)


@app.route('/edit_rental_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@login_required
def editRentalPin(id, name):
    form = EditRentalPin(request.form)
    groupIds = getAllGroups()
    pin = Lodging_Pin.query.filter(and_(Lodging_Pin.lodgeName==name), (Lodging_Pin.groupId==id)).first()
    form.link.data, form.description.data = pin.link, pin.description
    form.rentalName.data, form.price.data, form.rooms.data = pin.lodgeName, pin.price, pin.rooms
    # profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    userPassCandidate = form.passwordUser.data
    if form.validate_on_submit():
        if sha256_crypt.verify(userPassCandidate, current_user.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Lodging_Pin.query.filter(and_(Lodging_Pin.lodgeName==name), (Lodging_Pin.groupId==id)).update(dict(lodgeName=request.form['rentalName'], price=request.form['price'], rooms=request.form['rooms'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))
            else:
                flash("You got your group password twisted")
                return redirect(url_for('editRentalPin', id=id, name=name))
        else:
            flash("You got your user password twisted")
            return render_template('edit_rental_pins.html', form=form, id=id, group=group, pin=pin, profile=profile, name=name)

    # cur.close()
    return render_template('edit_rental_pins.html', form=form, id=id, group=group, pin=pin,name=name, groupIds=groupIds)

@app.route('/edit_restaurant_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@login_required
def editRestaurantPin(id, name):
    form = EditRestaurantPin(request.form)
    groupIds = getAllGroups()
    pin = Rest_Pin.query.filter(and_(Rest_Pin.restName==name), (Rest_Pin.groupId==id)).first()
    form.link.data, form.description.data = pin.link, pin.description
    form.name.data, form.type.data = pin.restName, pin.types
    # profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    userPassCandidate = form.passwordUser.data
    if form.validate_on_submit():
        if sha256_crypt.verify(userPassCandidate, current_user.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Rest_Pin.query.filter(and_(Rest_Pin.restName==name), (Rest_Pin.groupId==id)).update(dict(restName=request.form['name'], types=request.form['type'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))
            else:
                flash("You got your group password twisted")
            return redirect(url_for('editRestaurantPin', id=id, name=name))
        else:
            flash("You got your user password twisted")
            return redirect(url_for('editRestaurantPin', id=id, name=name))

    return render_template('edit_restaurant_pin.html', form=form, id=id, pin=pin, group=group, name=name, groupIds=groupIds)

@app.route('/edit_transportation_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@login_required
def editTransportationPin(id, name):
    form = EditTransportationPin(request.form)
    groupIds = getAllGroups()
    pin = Transpo_Pin.query.filter(and_(Transpo_Pin.transpoName==name), (Transpo_Pin.groupId==id)).first()
    form.name.data, form.price.data= pin.transpoName, pin.price
    form.type.data, form.description.data, form.link.data = pin.types, pin.description, pin.link
    # profile = User.query.filter(User.username==user).first()
    group = Group.query.filter(Group.id==id).first()
    if form.validate_on_submit():
        app.logger.info('verified')
        if sha256_crypt.verify(form.passwordUser.data, current_user.password):

            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Transpo_Pin.query.filter(and_(Transpo_Pin.transpoName==name), (Transpo_Pin.groupId==id)).update(dict(transpoName=request.form['name'], price=request.form['price'], types=request.form['type'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))

            else:
                flash("You got your group password twisted")
                return redirect(url_for('editTransportationtPin', id=id, name=name))
        else:
            flash("You got your user password twisted")
            return redirect(url_for('editTransportatPin', id=id, name=name))

    return render_template('edit_transportation_pin.html', form=form, id=id, pin=pin, group=group, name=name, groupIds=groupIds)

@app.route('/edit_activity_pin/<int:id>/<string:name>', methods=['GET', 'POST'])
@login_required
def editActivityPin(id, name):
    form = EditActivityPin(request.form)
    groupIds = getAllGroups()
    pin = Activity_Pin.query.filter(and_(Activity_Pin.activityName==name), (Activity_Pin.groupId==id)).first()
    form.name.data, form.price.data= pin.activityName, pin.price
    form.type.data, form.description.data, form.link.data = pin.types, pin.description, pin.link
    group = Group.query.filter(Group.id==id).first()
    if form.validate_on_submit():
        if sha256_crypt.verify(form.passwordUser.data, current_user.password):

            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                newPin = Activity_Pin.query.filter(and_(Activity_Pin.activityName==name), (Activity_Pin.groupId==id)).update(dict(activityName=request.form['name'], price=request.form['price'], types=request.form['type'], description=request.form['description'], link=request.form['link']))
                db.session.commit()
                flash("Pin updated!!")
                return redirect(url_for('group', id=id))
            else:
                flash("You got your group password twisted")
                return redirect(url_for('editActivityPin', id=id, name=name))
        else:
            flash("You got your user password twisted")
            return redirect(url_for('editActivityPin', id=id, name=name))

    return render_template('edit_activity_pin.html', groupIds=groupIds, form=form, id=id, pin=pin, group=group)


@app.route('/delete_rental_pin/<int:id>/<string:name>', methods=['GET','POST'])
@login_required
def deleteRentalPin(id, name):
    form = DeletePinForm(request.form)
    # profile = User.query.filter(User.username==user).first()
    groupIds = getAllGroups()
    pin = Lodging_Pin.query.filter(and_(Lodging_Pin.lodgeName==name), (Lodging_Pin.groupId==id)).first()
    group = Group.query.filter(Group.id==id).first()

    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, current_user.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
                return redirect(url_for('group', id=id))
            else:
                flash("Incorrect group password")
                return redirect(url_for('deleteRentalPin', id=id, name=name))
        else:
            flash("Incorrect user password")
            return redirect(url_for('deleteRentalPin', id=id, name=name))

    return render_template('delete_rental_pin.html', name=name, form=form, groupIds=groupIds)

@app.route('/delete_restaurant_pin/<int:id>/<string:name>', methods=['GET','POST'])
@login_required
def deleteRestaurantPin(id, name):
    form = DeletePinForm(request.form)
    pin = Rest_Pin.query.filter(and_(Rest_Pin.restName==name), (Rest_Pin.groupId==id)).first()
    groupIds = getAllGroups()
    group = Group.query.filter(Group.id==id).first()
    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, current_user.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return redirect(url_for('deleteRestaurantPin', id=id, name=name))
            flash("Incorrect user password")
            return redirect(url_for('deleteRestaurantPin', id=id, name=name))

    return render_template('delete_restaurant_pin.html', name=name, form=form, id=id, groupIds=groupIds)

@app.route('/delete_transportation_pin/<int:id>/<string:name>', methods=['GET','POST'])
@login_required
def deleteTransportationPin(id, name):
    form = DeletePinForm(request.form)
    pin = Transpo_Pin.query.filter(and_(Transpo_Pin.transpoName==name), (Transpo_Pin.groupId==id)).first()
    groupIds = getAllGroups()
    group = Group.query.filter(Group.id==id).first()
    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, current_user.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
                return redirect(url_for('group', id=id))

            else:
                flash("Incorrect group password")
                return redirect(url_for('deleteTransportationPin', id=id, name=name))
        else:
            flash("Incorrect user password")
            return redirect(url_for('deleteTransportationPin', id=id, name=name))

    return render_template('delete_transportation_pin.html', name=name, form=form, groupIds=groupIds)

@app.route('/delete_activity_pin/<int:id>/<string:name>', methods=['GET','POST'])
@login_required
def deleteActivityPin(id, name):
    form = DeletePinForm(request.form)
    pin = Activity_Pin.query.filter(and_(Activity_Pin.activityName==name), (Activity_Pin.groupId==id)).first()
    group = Group.query.filter(Group.id==id).first()
    groupIds = getAllGroups()
    if form.yes.data:
        if sha256_crypt.verify(form.passwordUser.data, current_user.password):
            if sha256_crypt.verify(form.passwordGroup.data, group.password):
                db.session.delete(pin)
                db.session.commit()
                flash('Pin deleted.')
                return redirect(url_for('group', id=id))
            else:
                flash("Incorrect group password")
                return redirect(url_for('deleteActivityPin', id=id, name=name))
        else:
            flash("Incorrect user password")
            return redirect(url_for('deleteActivityPin', id=id, name=name))

    return render_template('delete_activity_pin.html', name=name, form=form)

@app.route('/chatroom/<int:id>', methods=['GET', 'POST'])
def chatroom(id):
    groupIds = getAllGroups()
    @socketio.on('connect', namespace='/chatroom' )
    def connect():
        app.logger.info('Someone connected')
        msg = "Someone just connected!"
        room = id
        join_room(room)
        emit('on connect', {'msg': msg}, room=room)

        # emit('on connect', {'msg': msg}, broadcast=True)

    # @socketio.on('join', namespace='/chatroom')
    # def on_join(room):
    #     app.logger.info(room)
    #     msg = 'Room joined!!'
    #     join_room(room)
    #     emit('room response', {'msg': 'Joined a fucking room!!!'}, room=room)


    @socketio.on('disconnect', namespace='/chatroom')
    def disconnect():
        app.logger.info('someone jsut disconnected')
        msg = "Someone just disconnected :("
        room = id
        leave_room(room)
        emit('on disconnect', {'msg': msg}, room=room)

    @socketio.on('send message', namespace='/chatroom')
    def handle_my_custom_event(msg):
        room = id
        app.logger.info('a message was sent')
        emit('room response', {'msg': msg}, room=room )

    if request.method == 'POST':
        file = request.files['file']
        if allowed_file(file.filename):
            app.logger.info(request.files['file'])
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('file uploaded successfully')
        else:
            flash('That file type is not supported!')
            return redirect(url_for('chatroom'))

    return render_template('chatroom.html', id=id, groupIds=groupIds)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(404)
def not_found_error(error):
    groupIds = getAllGroups()
    return render_template('404.html', groupIds=groupIds), 404

@app.errorhandler(500)
def internalerror(error):
    groupIds = getAllGroups()
    session.rollback()
    return render_template('500.html', groupIds=groupIds), 500


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',debug=True)
    # socketio.run(app, debug=True)
