import os
import uuid
from .lib.io import FileHandler
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


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.String(500), nullable=False)


class MessageResource(Resource):
    def post(self):
        handler = FileHandler() # No args defaults "Local"
        # handler = FileHandler(storage_type = 's3', bucket_name = 's3_bucket')
        # Set up AWS creds using `boto3.setup_default_session()` or ENV VARS.
        message_content = request.json.get('message_content')
        if not message_content:
            return {'error': 'No message content provided'}, 400

        file_uuid = uuid.uuid4().hex
        filename = f"{file_uuid}.txt"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        handler.create_file(file_path, message_content) 
        # No breakage here needed when moving to S3, ie, loosely coupled.
        message = Message(file_path = file_path, content = message_content)
        db.session.add(message)
        db.session.commit()

        return {'id': message.id}, 201


class NextMessageResource(Resource):
    def get(self):
        handler = FileHandler()
        # handler = FileHandler(storage_type = 's3', bucket_name = 's3_bucket_name')
        message = db.session.query(Message).order_by(Message.id.asc()).first()
        if not message:
            return {'error': 'No messages available'}, 404

        content = handler.read_file(message.file_path)

        os.remove(message.file_path)

        db.session.delete(message)
        db.session.commit()

        return {'id': message.id, 'message': content}


api.add_resource(MessageResource, '/messages')
api.add_resource(NextMessageResource, '/next_message')

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)