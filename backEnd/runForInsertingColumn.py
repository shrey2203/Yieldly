from config import app, db  # Import your Flask app and db instance
from sqlalchemy import inspect 

with app.app_context():  # Ensure the app context is active
    inspector = inspect(db.engine)  # Create an inspector
    print(inspector.get_table_names())  # Get table names correctly
    # db.drop_all()
    db.create_all()

#     # user = User(username="testuser", panNumber="ABCDE1234F")
#     # db.session.add(user)
#     db.session.commit()



