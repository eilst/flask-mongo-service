from flask import Flask, render_template, redirect, jsonify, request
from pymongo import MongoClient
from classes import *

# config system
app = Flask(__name__)
app.config.update(dict(SECRET_KEY='yoursecretkey'))
client = MongoClient('mongo:27017')
db = client.TaskManager

if db.settings.find({'name': 'task_id'}).count() <= 0:
    print("task_id Not found, creating....")
    db.settings.insert_one({'name': 'task_id', 'value': 0})


def updateTaskID(value):
    task_id = db.settings.find_one()['value']
    task_id += value
    db.settings.update_one(
        {'name': 'task_id'},
        {'$set':
            {'value': task_id}
         })


def createTask(form):
    title = form.title.data
    priority = form.priority.data
    shortdesc = form.shortdesc.data
    task_id = db.settings.find_one()['value']

    task = {
        'id': task_id,
        'title': title,
        'shortdesc': shortdesc,
        'priority': priority}

    db.tasks.insert_one(task)
    updateTaskID(1)
    return redirect('/')


def deleteTask(form):
    key = form.key.data
    title = form.title.data

    if(key):
        print(key, type(key))
        db.tasks.delete_many({'id': int(key)})
    else:
        db.tasks.delete_many({'title': title})

    return redirect('/')


def updateTask(form):
    key = form.key.data
    shortdesc = form.shortdesc.data

    db.tasks.update_one(
        {"id": int(key)},
        {"$set":
            {"shortdesc": shortdesc}
         }
    )

    return redirect('/')


def resetTask(form):
    db.tasks.drop()
    db.settings.drop()
    db.settings.insert_one({'name': 'task_id', 'value': 0})
    return redirect('/')


@app.route('/tasks', methods=['GET'])
def get_all_tasks():
    tasks = db.tasks
    output = []
    for q in tasks.find():
        output.append({'id': q['id'],
                       'title': q['title'],
                       'shortdesc': q['shortdesc'],
                       'priority': q['priority']})

    return jsonify({'result': output})


@app.route('/task/<id>', methods=['GET'])
def get_one_task(id):
    tasks = db.tasks
    q = tasks.find_one({'id': int(id)})
    if q:
        output = {
            'id': q['id'],
            'title': q['title'],
            'shortdesc': q['shortdesc'],
            'priority': q['priority']}
    else:
        output = 'No results found'
    return jsonify({'result': output})


@app.route('/task', methods=['POST'])
def add_tasks():
    tasks = db.tasks

    title = request.json['title']
    task_id = db.settings.find_one()['value']
    shortdesc = request.json['shortdesc']
    priority = request.json['priority']
    task = {
        'id': task_id,
        'title': title,
        'shortdesc': shortdesc,
        'priority': priority}
    new_task = tasks.insert_one(task)
    updateTaskID(1)
    resp = jsonify(success=True)
    return resp


@app.route('/', methods=['GET', 'POST'])
def main():
    # create form
    cform = CreateTask(prefix='cform')
    dform = DeleteTask(prefix='dform')
    uform = UpdateTask(prefix='uform')
    reset = ResetTask(prefix='reset')

    # response
    if cform.validate_on_submit() and cform.create.data:
        return createTask(cform)
    if dform.validate_on_submit() and dform.delete.data:
        return deleteTask(dform)
    if uform.validate_on_submit() and uform.update.data:
        return updateTask(uform)
    if reset.validate_on_submit() and reset.reset.data:
        return resetTask(reset)

    # read all data
    docs = db.tasks.find()
    data = []
    for i in docs:
        data.append(i)

    return render_template('home.html', cform=cform, dform=dform, uform=uform,
                           data=data, reset=reset)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
