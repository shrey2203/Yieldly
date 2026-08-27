from config import db
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'USERS' 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    panNumber = db.Column(db.String(80), unique=True, nullable=False)
    emailAddress = db.Column(db.String(120), unique=True, nullable=False)

    def getUserName(self):
        return self.username
    
    def getPanNumber(self):
        return self.panNumber
    
    def getEmailAddress(self):
        return self.emailAddress

    def getId(self):
        return self.id
