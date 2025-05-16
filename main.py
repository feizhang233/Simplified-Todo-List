# Import necessary libraries
import os
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional

# Initialize Flask application
app = Flask(__name__)
# Set a secret key for form security
app.config['SECRET_KEY'] = 'mysecretkey'
# Disable SQLAlchemy modification tracking for better performance
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Define the base class for SQLAlchemy models using the DeclarativeBase
class Base(DeclarativeBase):
    pass

# Create the instance folder if it doesn't exist (for database storage)
os.makedirs(app.instance_path, exist_ok=True)

# Configure SQLite database path in the instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(app.instance_path, "todos.db")

# Initialize SQLAlchemy with the Flask app and custom base model class
db = SQLAlchemy(app, model_class=Base)
# No need to call init_app() again as it's already initialized in SQLAlchemy constructor

# Define Todo_model for database table
class Todo(db.Model):
    # Primary key auto-incrementing ID field
    id: Mapped[int] = mapped_column(primary_key=True)
    # Task name field (required, max 100 characters)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Category field (max 100 characters)
    category: Mapped[str] = mapped_column(String(100))
    # Description field (max 200 characters)
    description: Mapped[str] = mapped_column(String(200))
    # Completion status stored as integer percentage (0-100)
    completed: Mapped[int] = mapped_column(Integer, default=0)

# Define form for adding new Todo_items
class ListForm(FlaskForm):
    # Name field with required validator
    name = StringField('Name', validators=[DataRequired()])
    # Optional category field
    category = StringField('Category', validators=[Optional()])
    # Optional description field
    description = StringField('Description', validators=[Optional()])
    # Submit button
    submit = SubmitField('Submit')

# Function to initialize database tables
def init_db():
    # Use application context to create all defined tables
    with app.app_context():
        db.create_all()

# Route for home page, handles both GET and POST requests
@app.route('/', methods=['GET', 'POST'])
def home():
    # Initialize the form for adding new tasks
    form = ListForm()
    # If form is submitted and validates
    if form.validate_on_submit():
        # Create a new Todo_item from form data
        new_item = Todo(
            name=form.name.data,
            category=form.category.data,
            description=form.description.data,
            completed=0  # Initial completion status is 0%
        )
        # Add the new item to the database session
        db.session.add(new_item)
        # Commit the transaction to save the item
        db.session.commit()
        # Redirect to home to show updated list
        return redirect(url_for('home'))
    
    # Initialize empty list to store Todo_items
    items = []
    # Query all Todo_items from database, ordered by ID
    todos = db.session.execute(db.select(Todo).order_by(Todo.id)).scalars().all()
    # Convert database objects to dictionaries for template rendering
    for item in todos:
        items.append({
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "description": item.description,
            "completed": item.completed
        })
    # Render the template with form and Todo_items
    return render_template("index.html",form=form, items=items)

# Route to update progress of a Todo_item
@app.route("/progress/<int:id>")
def progress(id):
    # Retrieve the specific Todo_item by ID
    item = db.session.get(Todo, id)
    # If completion status is 100% or more, delete the item
    if item.completed >= 100:
        db.session.delete(item)
    else:
        # Otherwise, increase completion by 10%
        item.completed += 10
    # Commit changes to database
    db.session.commit()
    # Redirect to home page
    return redirect(url_for('home'))

# Route to mark a Todo_item as complete and remove it
@app.route("/complete/<int:id>")
def complete(id):
    # Retrieve the specific Todo_item by ID
    item = db.session.get(Todo, id)
    # Delete the item directly (complete = remove)
    db.session.delete(item)
    # Commit changes to database
    db.session.commit()
    # Redirect to home page
    return redirect(url_for('home'))

# Only run the app when this file is executed directly (not imported)
if __name__ == '__main__':
    # Initialize the database before starting the app
    init_db()
    # Run the Flask application in debug mode for development
    app.run(debug=True)