# /backend/create_admin.py
from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    username = "admin"
    email = "m.byrski@hoxa.pl"
    password = "gumisie" # Pamiętaj, aby zmienić na silne hasło!

    if User.query.filter_by(username=username).first():
        print(f"Użytkownik {username} już istnieje.")
    else:
        admin_user = User(username=username, email=email, role="admin")
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Stworzono użytkownika: {username}")