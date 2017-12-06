import json
import copy

from bson import json_util
from flask import Flask, request, Response, session, jsonify, render_template, url_for, redirect
from flask_pymongo import PyMongo
#from pymongo.errors import DuplicateKeyError
from werkzeug import security
from werkzeug.exceptions import BadRequest, NotFound, UnsupportedMediaType, Unauthorized
from validate_email import validate_email

from exceptions import JSONExceptionHandler

# This defines a Flask application
app = Flask(__name__)

# This code here converts Flask's default (HTML) errors to Json errors.
# This is helpful because HTML breaks clients that are expecting JSON
JSONExceptionHandler(app)

# We configure the app object
app.config['MONGO_DBNAME'] = 'adv_startup_sys'
app.config['MONGO_URI'] = 'mongodb://jobs:jobs@ds147421.mlab.com:47421/adv_startup_sys'
app.secret_key = 'secret'

# This initializes PyMongo and makes `mongo` available
mongo = PyMongo(app)


@app.route('/', methods=['GET'])
def who_am_i():
    if session.get('user') is None:
        raise Unauthorized()
    return jsonify(session.get('user'))


@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        raise UnsupportedMediaType()

    body = request.get_json()
    if body.get('username') is None:
        raise BadRequest('missing username property')
    if body.get('password') is None:
        raise BadRequest('missing password property')

    users = mongo.db.users
    login_user = users.find_one({'username': body.get('username')})

    if login_user:
        if security.check_password_hash(login_user['password'], body.get('password')):
            serializable_user_obj = json.loads(json_util.dumps(login_user))
            session['user'] = serializable_user_obj
            return Response(status=200)

        raise BadRequest('wrong password')

    session.clear()
    raise BadRequest('Invalid Username/Password Combo')


@app.route('/logout')
def logout():
    """
    This 'logs out' the user by clearing the session data
    """
    session.clear()
    return Response(status=200)


@app.route('/register', methods=['POST'])
def register():
    if not request.is_json:
        raise UnsupportedMediaType()

    body = request.get_json()
    if body.get('username') is None:
        raise BadRequest('missing username property')
    if not (isinstance(body.get('username'), str)):
        raise BadRequest('Bad Username Input')
    if body.get('password') is None:
        raise BadRequest('missing password property')
    if not (isinstance(body.get('password'), str)):
        raise BadRequest('Bad Password Input')
    if body.get('phone_number') is None:
        raise BadRequest('missing phone number property')
    if not (isinstance(body.get('phone_number'), str) and body.get('phone_number').isdigit() and len(body.get('phone_number')) == 10):
        raise BadRequest('Invalid Phone Number')
    if body.get('email') is None:
        raise BadRequest('missing email property')
    if not (isinstance(body.get('email'), str) and validate_email(body.get('email'))):
        raise BadRequest('Invalid email')
    if body.get('type') is None:
        raise BadRequest('missing type property')
    if not (body.get('type') == 'driver' or body.get('type') == 'client'):
        raise BadRequest('type can only be driver or client')

    users = mongo.db.users
    existing_user = users.find_one({'username': body.get('username')})

    if existing_user is None:
        password_hash = security.generate_password_hash(body.get('password'))
        users.insert({'username': body.get('username'), 'password': password_hash, 'phone_number': body.get('phone_number'),
             'email': body.get('email'), 'type': body.get('type')})
        serializable_user_obj = json.loads(json_util.dumps(users.find_one({'username': body.get('username')})))
        session['user'] = serializable_user_obj
        return Response(status=201)

    raise NotFound('User already exists')

@app.route('/account/settings', methods=['POST'])
def editAccount():
    if not request.is_json:
        raise UnsupportedMediaType()

    body = request.get_json()
    users = mongo.db.users
    existing_user = users.find_one({'username': session.get('user')['username']})
    existing_user_tmp = copy.deepcopy(existing_user)

    if body.get('phone_number'):
        if not (isinstance(body.get('phone_number'), str) and body.get('phone_number').isdigit() and len(body.get('phone_number')) == 10):
            raise BadRequest('Invalid Phone Number')
        existing_user['phone_number'] = body.get('phone_number')

    if body.get('email'):
        if not (isinstance(body.get('email'), str) and validate_email(body.get('email'))):
            raise BadRequest('Invalid email')
        existing_user['email'] = body.get('email')

    if existing_user is None:
        raise Unauthorized('You must be logged in')

    mongo.db.users.remove(existing_user_tmp)
    res = mongo.db.users.insert_one(existing_user)
    session['user'] = json.loads(json_util.dumps(existing_user))
    return Response(str(res.inserted_id), 200)

@app.route('/account/delete')
def deleteAccount():
    if session.get('user') is None:
        raise Unauthorized('You must be logged in')
    users = mongo.db.users
    mongo.db.users.remove(users.find_one({'username': session.get('user')['username']}))
    session.clear()
    return Response(status=200)


@app.route('/job/show', methods=['GET'])
def showClientJobs():
    if session.get('user') is None or session.get('user')['type'] == 'driver':
        raise Unauthorized('You must be a client')

    jobs = mongo.db.jobs
    existing_job = jobs.find_one({'client': session['user']['_id']['$oid']})
    if existing_job is None:
        raise BadRequest('You do not have any jobs')

    return jsonify(json.loads(json_util.dumps(jobs.find({'client': session['user']['_id']['$oid']}))))

@app.route('/job/create', methods=['POST'])
def postJob():
    if not request.is_json:
        raise UnsupportedMediaType()
    if session.get('user') is None or session.get('user')['type'] == 'driver':
        raise Unauthorized('You must be a client')

    body = request.get_json()
    if body.get('location') is None:
        raise BadRequest('missing location property')
    if body.get('start_time') is None:
        raise BadRequest('missing start_time property')
    if body.get('finish_time') is None:
        raise BadRequest('missing finish_time property')
    if body.get('max_price') is None:
        raise BadRequest('missing max_price property')
    if not (isinstance(body.get('max_price'), str) and body.get('max_price').isdigit() and len(body.get('max_price')) <= 4):
        raise BadRequest('Invalid Price')
    if body.get('description') is None:
        raise BadRequest('missing description property')

    jobs = mongo.db.jobs
    existing_jobs = jobs.find_one({'location': body.get('location'), 'client': session['user']['_id']['$oid']})
    if existing_jobs:
        raise BadRequest('You have already requested a job in this location')

    job_record = {'location': body.get('location'), 'start_time': body.get('start_time'),
                  'finish_time': body.get('finish_time'), 'max_price': body.get('max_price'),
                  'description': body.get('description')}
    job_record.update({'client': session['user']['_id']['$oid'], 'driver': 'None'})

    res = mongo.db.jobs.insert_one(job_record)
    return Response(str(res.inserted_id), 200)

@app.route('/job/edit', methods=['POST'])
def editJob():
    if not request.is_json:
        raise UnsupportedMediaType()
    if session.get('user') is None or session.get('user')['type'] == 'driver':
        raise Unauthorized('You must be a client')

    body = request.get_json()
    jobs = mongo.db.jobs
    existing_job = jobs.find_one({'client': session['user']['_id']['$oid'], 'location': body.get('location')})
    existing_job_tmp = copy.deepcopy(existing_job)

    if existing_job is None:
        raise BadRequest('You do not have any jobs in this location')
    if not (existing_job['driver'] == 'None'):
        raise BadRequest('You cannot edit. A driver has already accepted')

    if body.get('location') is None:
        raise BadRequest('The location is required to know which job')
    if body.get('start_time'):
        existing_job['start_time'] = body.get('start_time')
    if body.get('finish_time'):
        existing_job['finish_time'] = body.get('finish_time')
    if body.get('max_price'):
        if not (isinstance(body.get('max_price'), str) and body.get('max_price').isdigit() and len(body.get('max_price')) <= 4):
            raise BadRequest('Invalid Price')
        existing_job['max_price'] = body.get('max_price')
    if body.get('description'):
        existing_job['description'] = body.get('description')

    mongo.db.jobs.remove(existing_job_tmp)
    res = mongo.db.jobs.insert_one(existing_job)
    return Response(str(res.inserted_id), 200)

@app.route('/job/delete', methods=['POST'])
def deleteJob():
    if not request.is_json:
        raise UnsupportedMediaType()
    if session.get('user') is None or session.get('user')['type'] == 'driver':
        raise Unauthorized('You must be logged in as client')

    body = request.get_json()
    if body.get('location') is None:
        raise BadRequest('The location is required to know which job')

    jobs = mongo.db.jobs
    existing_job = jobs.find_one({'client': session['user']['_id']['$oid'], 'location': body.get('location')})

    if existing_job is None:
        raise BadRequest('You do not have any jobs in this location')
    if not (existing_job['driver'] == 'None'):
        raise BadRequest('You cannot delete. A driver has already accepted')

    mongo.db.jobs.remove(existing_job)
    return Response(status=200)

@app.route('/job/available', methods=['GET'])
def seeJobs():
    if session.get('user') is None or session.get('user')['type'] == 'client':
        raise Unauthorized('You must be a driver')

    jobs = mongo.db.jobs
    return jsonify(json.loads(json_util.dumps(jobs.find({'driver': 'None'}))))

@app.route('/job/accept', methods=['POST'])
def accept():
    if not request.is_json:
        raise UnsupportedMediaType()
    if session.get('user') is None or session.get('user')['type'] == 'client':
        raise Unauthorized('You must be a driver')

    body = request.get_json()
    if body.get('client') is None:
        raise BadRequest('missing client property')
    if body.get('location') is None:
        raise BadRequest('missing location property')

    jobs = mongo.db.jobs
    existing_job = jobs.find_one({'client': body.get('client'), 'location': body.get('location')})
    if existing_job is None:
        raise BadRequest('This job does not exist')

    if not existing_job['driver'] == 'None':
        raise Unauthorized('Another Driver has already accepted that job')

    mongo.db.jobs.remove(existing_job)
    existing_job['driver'] = session['user']['_id']['$oid']

    res = mongo.db.jobs.insert_one(existing_job)
    return Response(str(res.inserted_id), 200)

@app.route('/job/accept/show', methods=['GET'])
def seeDriverJobs():
    if session.get('user') is None or session.get('user')['type'] == 'client':
        raise Unauthorized('You must be a driver')

    jobs = mongo.db.jobs
    existing_job = jobs.find_one({'driver': session['user']['_id']['$oid']})
    if existing_job is None:
        raise BadRequest('You do have not accepted any jobs')

    return jsonify(json.loads(json_util.dumps(jobs.find_one({'driver': session['user']['_id']['$oid']}))))

@app.route('/job/cancel', methods=['POST'])
def cancelJob():
    if not request.is_json:
        raise UnsupportedMediaType()
    if session.get('user') is None or session.get('user')['type'] == 'client':
        raise Unauthorized('You must be a driver')

    body = request.get_json()
    if body.get('location') is None:
        raise BadRequest('The location is required to know which job')

    jobs = mongo.db.jobs
    existing_job = jobs.find_one({'driver': session['user']['_id']['$oid'], 'location': body.get('location')})
    if existing_job is None:
        raise BadRequest('You do not have any jobs in this location')

    mongo.db.jobs.remove(existing_job)
    existing_job['driver'] = 'None'
    res = mongo.db.jobs.insert_one(existing_job)
    return Response(str(res.inserted_id), 200)

# @app.route('/mail')
# def send_email():
#     # Import smtplib for the actual sending function
#     import smtplib
#
#     # Import the email modules we'll need
#     from email.mime.text import MIMEText
#
#     # me == the sender's email address
#     # you == the recipient's email address
#     msg = MIMEText('this is my message')
#     msg['Subject'] = 'The subject'
#     msg['From'] = 'a@b.com'
#     msg['To'] = 'b@c.com'
#
#     # Send the message via our own SMTP server, but don't include the
#     # envelope header.
#     s = smtplib.SMTP(host='smtp.lively-marking-181419.appspot.com', port=1025)
#     s.sendmail('a@b.com', [], msg.as_string())
#     s.quit()
#
#     return 'Sent the mail'


# This allows you to run locally.
# When run in GCP, Gunicorn is used instead (see entrypoint in app.yaml) to
# Access the Flack app via WSGI
if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)