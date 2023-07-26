import os
import uuid
from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messages.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
api = Api(app)
db = SQLAlchemy(app)

UPLOAD_FOLDER = 'messages'
ALLOWED_EXTENSIONS = {'txt'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Endpoint             Methods  Rule
# -------------------  -------  -----------------------
# messageresource      POST     /messages
# nextmessageresource  GET      /next_message
# static               GET      /static/<path:filename>

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.String(500), nullable=False)


class MessageResource(Resource):
    # TODO: 
    # 
    # 1. Add polymorphism here to support future 'Adapters' that
    # modify storage type: S3, Cloud Storage, etc. 
    # This client code shouldn't break when we do, ie, loose coupling. Either:

    #   A. Add optional 'Adaptor' arg to the constructor above. Default to 'File' storage. Or:

    #   B. 'Resource' is different types: File, S3, DB. Then don't pass Adpapter.

    # Optimally, there should not be an case/when (if/else) check here, we need to
    # keep adding to with each new Storage Type. Probably don't need to know details
    # like Path and UUID either. Abstract that away.
    # 
    # Client code for Message creation would DRY up to something like:

    # job = Job.new(user_id)     # from Session / Cookie
    # job.storage_type = 'S3 | File | DB'
    # job.message << 'whatever message'
    # job.save()

    # ^ If type is DB, it saves the DB model called 'Message'.
    # If type is File, it saves to the Linux FS.
    # If type is S3, it saves to AWS S3.

    def post(self):
        message_content = request.json.get('message_content')
        if not message_content:
            return {'error': 'No message content provided'}, 400
        file_uuid = uuid.uuid4().hex
        filename = f"{file_uuid}.txt"
        # CONCERN: Always a small chance of collisions with UUIDs.
        # I'd add something unique to the User, like:

        #    filename = f"{user.id}-{file_uuid}.txt"

        # Or store it in a /<user.id>/ directory.
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, 'w') as f:
            f.write(message_content)
        message = Message(file_path=file_path, content=message_content)
        db.session.add(message)
        db.session.commit()
        return {'id': message.id}, 201

# 1. Spec: Only 1 User can modify a Message.

# “Jobs should be touched once by a User and only available to one user at
#  a time and most often will only need to be processed once.”

# We'd need a "Start Job" button in the GUI. That would flip a Bool in the DB.
# Then lock out other Users by graying out their Edit buttons in the Index view.

class EditMessageResource(Resource):
    # Pseudocode at the moment. Not tested. We have no Views/Forms yet.

    @app.route('/message/<int:id>', methods = ['GET', 'POST'])
    def edit(id):
        qry = db.session.query(Message).filter(Message.id == id)
        message = qry.first()

        if message:
            form = MessageForm(formdata = request.form, obj = message)
            if request.method == 'POST' and form.validate():
                # save edits
                save_changes(message, form)

                flash('Message updated successfully!')

                return redirect('/')
            return render_template('edit_message.html', form = form)
        else:
            return 'Error loading #{id}'.format(id=id)

class UpdateMessageResource(Resource):
    # Pseudocode. Not tested.

    @app.route('/message/<id>', methods = ['PUT'])
    def message_update(id):
        message = Message.query.get(id)
        message.content = request.json['message']

        db.session.commit()

        return message.schema.jsonify(message)


class NextMessageResource(Resource):
    # TODO: Add similar Polymorphism here to support future 'Adapters'.

    def get(self):
        # Client code for getting a Message would be DRYed up to 2 lines
        # Something like:

        # job = Job.find(message_id)     # Add a 'message_id' param to the GET Route.
        # return job.message

        # Should NOT have to pass storage_type. It will just know.
        message = db.session.query(Message).order_by(Message.id.asc()).first()
        if not message:
            return {'error': 'No messages available'}, 404
        with open(message.file_path, 'r') as f:
            content = f.read()
        os.remove(message.file_path)
        db.session.delete(message)
        db.session.commit()
        return {'id': message.id, 'message': content}

# CONCERN with File storage when it's deployed to multi-Process Production env.
# A Prod server has many Python processes. File storage will work fine if they are
# all on the same physical box. They're accessing the same Volume.
# If it's a Web Cluster with seprate VMs / Containers that don't share Disk storage,
# the above code won't work.

# Ideas:

# 1. Clustered File System

# https://www.ufsexplorer.com/articles/clustered-file-systems/

# https://github.com/aws-samples/clustered-storage-gfs2

# 2. HACK: If CFS unavailble, implement some code that distrabutes it to
#   all servers. AWS's API can give us a list of all boxes in the cluter.
#   Iterate them, and SFTP it to all of them.
#   (Feels very risky, tho. No fault tollerance. No guarantees that they arrive safe.
#    We'd have to Auth with SSH Keys, and rotate the keys periocially.)

api.add_resource(MessageResource, '/messages')
api.add_resource(NextMessageResource, '/next_message')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)