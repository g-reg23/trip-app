from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from functools import wraps
from confi import *
from forms import *
from flask_mysqldb import MySQL


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
        p_word = sha256_crypt.encrypt(str(form.password.data))

        #create cursor
        cur = mysql.connection.cursor()

        check = cur.execute("SELECT * FROM users WHERE username = %s", [u_name])

        if check > 0:
            #close
            cur.close()

            error = "That username is already in use, sorry."
            return render_template("signup.html", error=error)

        else:
            cur.execute("INSERT INTO users(firstName, lastName, username, email, password) VALUES(%s, %s, %s, %s, %s)", (f_Name, l_Name, u_name, e_mail, p_word))

            #Commit to Database
            mysql.connection.commit()

            #Close connection
            cur.close()

            flash("Congrats, your are registered, you can now login")
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
            password = data['password']
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid log in.'
                return render_template('login.html', error=error, form=form)


        else:
            error = "Username not found"
            return render_template('login.html', error=error, form=form)

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



@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out", "danger")
    return redirect(url_for("login"))

@app.route('/dashboard')
@is_logged_in
def dashboard():
    groups = []
    username = session['username']
    # Get id from users db
    cur = mysql.connection.cursor()


    # Find user in db
    cur.execute("SELECT * FROM users WHERE username = %s", [username])
    profile = cur.fetchone()
    #store id in 'user'
    id = profile['id']

    result = cur.execute("SELECT * FROM user_groups WHERE user = %s", [id])

    if result > 0:
        groups = cur.fetchall()
        cur.close()
        return render_template('dashboard.html', groups=groups, profile=profile)
    else:
        msg = "You are not a member of any groups yet."
        cur.close()
        return render_template('dashboard.html', groups=groups, profile=profile)


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
    id = profile['id']

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

            cur.execute("UPDATE users SET firstName = %s, lastName = %s, username = %s, email = %s WHERE id = %s", [f_Name, l_Name, u_name, e_mail, id])

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
        id = data['id']
        if sha256_crypt.verify(password_candidate, password):
            #if password match, delete user;
            cur.execute("DELETE FROM users WHERE username = %s", [user])
            mysql.connection.commit()
            # delete all of this users groups from user_groups;
            cur.execute("DELETE FROM user_groups WHERE user = %s", [id])
            mysql.connection.commit()
            # Close connection
            cur.close()

            return redirect(url_for('logout'))
        else:
            error = error
            flash("Invalid password", error=error)

    return render_template('delete_profile.html', form=form)

@app.route('/newGroup', methods=['GET', 'POST'])
@is_logged_in
def newGroup():
    form = GroupForm(request.form)
    if request.method == 'POST' and form.validate():
        groupName = form.groupName.data
        location = form.location.data
        dates = form.dates.data
        admin = session['username']
        password = sha256_crypt.encrypt(str(form.password.data))
        description = form.description.data


        # Create cursor
        cur = mysql.connection.cursor()

        #Check for group name
        check = cur.execute("SELECT * FROM grouper WHERE groupName = %s" [groupName])

        if check > 0:
            cur.close()
            flash("That group name is already in use, sorry.")
            return render_template("newGroup.html", form=form)
        else:
            cur.execute("INSERT INTO grouper(title, location, dates, admin, password, description) VALUES(%s, %s, %s, %s,%s,%s)", (groupName, location, dates, admin, password, description))

            cur.connection.commit()

            flash('Group created!')


            return redirect(url_for('group'))


    return render_template('newGroup.html', form=form)

@app.route('/group/<int:id>', methods=['GET', 'POST'])
@is_logged_in
def group(id):

    user = session['username']
    renPins, restPins, flightPins, activityPins = {}, {}, {}, {}
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM grouper WHERE id = %s", [id])
    group = cur.fetchone()
    if group == 0:
        flash("You must join the group first!")
        return redirect(url_for("joinGroup"))
    #Get all the pins
    pinner1 = cur.execute("SELECT * FROM rental_pins WHERE groupId = %s", [id])
    if pinner1 > 0:
        renPins = cur.fetchall()
    pinner2 = cur.execute("SELECT * FROM rest_pins WHERE groupId = %s", [id])
    if pinner2 > 0:
        restPins = cur.fetchall()
    pinner3 = cur.execute("SELECT * FROM flight_pins WHERE groupId = %s", [id])
    if pinner3 > 0:
        flightPins = cur.fetchall()
    pinner4 = cur.execute("SELECT * FROM activity_pins WHERE groupId = %s", [id])
    if pinner4 > 0:
        activityPins = cur.fetchall()

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

        cur.execute("INSERT INTO rental_pins(groupId, rental_name, price, rooms, description, link, creator) VALUES(%s,%s,%s,%s,%s,%s,%s)", [id, rentalName, price, rooms, description, link, username])

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


        cur.execute("INSERT INTO rest_pins(groupId, rest_name, description, link, type, creator) VALUES(%s,%s,%s,%s,%s, %s)", [id, restName, description, link, type, username])

        cur.connection.commit()
        flash("Pin created!")
        return redirect(url_for('group', id=id))

    pinFormThree = FlightPinForm(request.form)
    if pinFormThree.submit3.data and pinFormThree.validate():
        username = session['username']
        airline = pinFormThree.airline.data
        date = pinFormThree.date.data
        price = pinFormThree.price3.data
        description = pinFormThree.description3.data
        link = pinFormThree.link3.data

        cur.execute("INSERT INTO flight_pins(groupId, airline, date, price, link, description, creator) VALUES(%s,%s,%s,%s,%s,%s,%s)", [id, airline, date, price, link, description, username])

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

        cur.execute("INSERT INTO activity_pins(groupId, creator, name, description, link, type) VALUES(%s,%s,%s,%s,%s,%s)", [id, username,  activityName, description, link, type])
        cur.connection.commit()
        flash("Pin created!")
        return redirect(url_for('group', id=id))

    cur.execute("SELECT * FROM chats WHERE id = %s", [id])
    history = cur.fetchall()

    cur.close()


    return render_template("group.html", group=group, renPins=renPins, restPins=restPins, flightPins=flightPins, activityPins=activityPins, pinForm=pinForm, id=id, user=user, pinFormTwo=pinFormTwo, pinFormThree=pinFormThree, pinFormFour=pinFormFour, history=history)

@app.route('/joinGroup', methods=['GET', 'POST'])
@is_logged_in
def joinGroup():
    username = session['username']
    if request.method == 'POST':
        groupName = request.form['groupName']
        password_candidate = request.form['password']

        #Create DictCursor
        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM grouper WHERE title = %s", [groupName])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                # Get id's from user and group db
                groupId = data['id']
                cur.execute("SELECT * FROM users WHERE username = %s", [username])
                user_data = cur.fetchone()
                user = user_data['id']
                # put user/group ids in user/group database
                cur.execute("INSERT INTO user_groups(user, groupId, groupName) VALUES(%s, %s, %s)", (user, groupId, groupName))
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
                return render_template('joinGroup.html', error=error)


        else:
            cur.close()
            error = "Group not found"
            return render_template('joinGroup.html', error=error)


    return render_template('joinGroup.html')



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
    user = data['id']

    result = cur.execute("SELECT * FROM user_groups WHERE user = %s", [user])

    if result > 0:
        groups = cur.fetchall()
        cur.close()
        return render_template('groups.html', groups=groups)
    else:
        msg = "You are not a member of any groups yet."
        cur.close()
        return render_template('groups.html', groups=groups)
