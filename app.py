from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ihssan is writing her exams'

#config mysql 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'users'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init mysql
mysql = MySQL(app)

#Article = Articles()

@app.route('/')
def index():
    return render_template('home.html')

#about route 
@app.route('/About')
def about():
    return render_template('about.html')

#All artilces
@app.route('/Articles')
def articles():
    cursor = mysql.connection.cursor()
    #get article 
    result =  cursor.execute("SELECT * FROM articles")
    articles = cursor.fetchall()

    if result > 0:
        return render_template('article.html', articles=articles)
    else:
        message = 'No Articles Found'
        return render_template('article.html', message=message)
    cursor.close()


#registration form 
class RegisterForm(Form):
    name = StringField('Name',[validators.InputRequired()])
    username = StringField('Username', [validators.Length(min=3, max=6)] )
    email = StringField('Email', [validators.InputRequired() ])
    password = PasswordField('Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password', [validators.InputRequired()])

#Registration users
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.hash(str(form.password.data))
        #create cursor
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO user(name,email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        #commit to db
        mysql.connection.autocommit(on=any)
        #close connection
        cursor.close()

        #flash message 
        flash("You are now registered and can login", 'success')
        return redirect(url_for('index'))

    return render_template('register.html', form=form)

#Login 
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_hash = request.form['password']
        #create cursor
        cursor = mysql.connection.cursor()
        #get user by name
        result = cursor.execute("SELECT * FROM user where username = %s", [username])
        if result > 0:
            data = cursor.fetchone()
            password = data['password']
            #compare passwords
            if sha256_crypt.verify(password_hash, password):
                session['logged_in'] = True
                session['username'] = username
               
                #flash message 
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            cursor.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    
    return render_template('login.html')

#session control function 
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, Please login", 'danger')
            return redirect(url_for('login'))
    return wrap

#logout 
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', "success")
    return redirect(url_for('login'))

#Dashboard class
@app.route('/dashboard')
@is_logged_in
def dashboard():
    cursor = mysql.connection.cursor()
    #get article 
    result =  cursor.execute("SELECT * FROM articles")
    articles = cursor.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        message = 'No Articles Found'
        return render_template('dashboard.html', message=message)
    cursor.close()

#Article class 
class ArticleForm(Form):
    title = StringField('Title',[validators.InputRequired()])
    body = TextAreaField('Body', [validators.Length(min=30)] )

#article articles 
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
        
        #commit db 
        mysql.connection.commit()
        #close connection 
        cursor.close()

        flash('Article created', 'success')

        return redirect(url_for('dashboard'))
        
    return render_template('add_article.html', form=form)
    
#single article
@app.route('/Articles/<string:id>/')
@is_logged_in
def article(id):

    cursor = mysql.connection.cursor()
    #get article 
    result =  cursor.execute("SELECT * FROM articles WHERE id = %s ", [id])

    article = cursor.fetchone()

    return render_template('articles.html', article=article)

#Edit articles 
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    #create cursor
    cursor = mysql.connection.cursor()
    
    #get article by id
    result = cursor.execute("SELECT * FROM articles WHERE id = %s ", [id])

    article = cursor.fetchone()
    
    #get form
    form = ArticleForm(request.form)

    #populate article form fields 
    form.title.data = article['title']
    form.body.data =article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #create cursor
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE articles SET title=%s, body=%s WHERE id = %s", (title, body, id))
        
        #commit db 
        mysql.connection.commit()
        #close connection 
        cursor.close()

        flash('Article updated', 'success')

        return redirect(url_for('dashboard'))
        
    return render_template('edit_article.html', form=form, article=article)

#DELETE ARTICLE
@app.route('/delete_article/<string:id>', methods=['POST', 'GET'])
@is_logged_in
def delete_article(id):
    #create cursor
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM articles WHERE id=%s", [id])

    #commit db
    mysql.connection.commit()
        #close connection 
    cursor.close()

    flash('Article deleted.', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)