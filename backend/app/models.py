# /backend/app/models.py
from . import db # Importujemy 'db' z __init__.py
import bcrypt
import datetime
from sqlalchemy.sql import text


# NOWA TABELA ASOCJACYJNA
# Definiuje połączenie Wiele-do-Wielu między User i Product
client_product_assignment = db.Table('client_product_assignment',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # --- NOWE POLA ---
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True) # Nowe pole na adres
    # --- KONIEC NOWYCH PÓL ---
    # Role: 'admin', 'user', 'shipping'
    role = db.Column(db.String(20), nullable=False, default='user')

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    assigned_products = db.relationship('Product', secondary=client_product_assignment, lazy=True,
        backref=db.backref('assigned_to_users', lazy=True))
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    # Relacja "jeden do wielu": Jeden Produkt ma wiele Wariantów
    # 'cascade' usunie warianty, gdy usuniemy produkt
    variants = db.relationship('ProductVariant', back_populates='product', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url, 
            "variants": [variant.to_dict() for variant in self.variants]
        }

class ProductVariant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size = db.Column(db.String(50), nullable=False, default='Uniwersalny')

    # ZMIANA: Cena jest teraz opcjonalna (nullable=True)
    price = db.Column(db.Float, nullable=True) 

    # ZMIANA: Usuwamy stan magazynowy
    # stock = db.Column(db.Integer, nullable=False, default=0) 

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', back_populates='variants')

    def to_dict(self):
        return {
            "id": self.id,
            "size": self.size,
            "price": self.price, # Zostawiamy price, nawet jeśli jest None
            # "stock": self.stock, # Usunięte
            "product_id": self.product_id
        }
    
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Status: 'new' (nowe), 'partial' (częściowe), 'completed' (zrealizowane)
    status = db.Column(db.String(20), nullable=False, default='new')
    notes = db.Column(db.Text, nullable=True)
    # Kto złożył zamówienie
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    
    # Lista pozycji na zamówieniu
    items = db.relationship('OrderItem', back_populates='order', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "notes": self.notes,
            "user_id": self.user_id,
            "items": [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1) # Ile klient zamówił

    # --- NOWA KOLUMNA ---
    # Dodajemy kolumnę śledzącą, ile sztuk z tej pozycji już wysłano.
    shipped_quantity = db.Column(db.Integer, nullable=False, server_default=text('0'))
    
    # Reszta pól pozostaje bez zmian
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=False)
    variant = db.relationship('ProductVariant')
    
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order = db.relationship('Order', back_populates='items')
    
    product_name = db.Column(db.String(100))
    variant_size = db.Column(db.String(50))
    price_at_order = db.Column(db.Float, nullable=True) # Cena w momencie zamówienia

    def to_dict(self):
        return {
            "id": self.id,
            "quantity": self.quantity,
            
            # --- DODANE DO ZWROTU ---
            # Frontend musi wiedzieć, ile wysłano
            "shipped_quantity": self.shipped_quantity, 
            
            "variant_id": self.variant_id,
            "order_id": self.order_id,
            "product_name": self.product_name,
            "variant_size": self.variant_size,
            "price_at_order": self.price_at_order
        }
    
class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Przechowuje cały obiekt subskrypcji (endpoint, klucze) jako JSON
    subscription_json = db.Column(db.Text, nullable=False)
    
    # KLUCZOWE: Łączymy subskrypcję z kontem użytkownika
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('push_subscriptions', lazy=True, cascade="all, delete-orphan"))
    
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "endpoint": self.get_endpoint() # Zwracamy tylko część endpointu dla admina
        }
    
    def get_endpoint(self):
        # Bezpiecznie wyciągamy sam endpoint z JSONa do podglądu
        try:
            import json
            return json.loads(self.subscription_json).get('endpoint', 'Błędny format')
        except:
            return 'Błędny format'
        
class Shipment(db.Model):
    """
    Reprezentuje pojedynczą, fizyczną wysyłkę (paczkę).
    Jedno zamówienie (Order) może mieć wiele wysyłek (Shipment).
    """
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # ID zamówienia, do którego należy ta paczka
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order = db.relationship('Order', backref=db.backref('shipments', lazy=True, cascade="all, delete-orphan"))
    
    # Kto fizycznie przetworzył tę wysyłkę (np. user ze spedycji)
    shipped_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Może być null, jeśli system automatyzuje
    shipped_by_user = db.relationship('User')
    
    # Lista pozycji w tej konkretnej paczce
    items = db.relationship('ShipmentItem', back_populates='shipment', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "order_id": self.order_id,
            "shipped_by_username": self.shipped_by_user.username if self.shipped_by_user else "System",
            "items": [item.to_dict() for item in self.items]
        }


class ShipmentItem(db.Model):
    """
    Reprezentuje jedną pozycję Wewnątrz paczki.
    Np. 2x Koszulka M (z 5 zamówionych).
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # Ile sztuk wysłano w TEJ paczce
    quantity_shipped = db.Column(db.Integer, nullable=False)
    
    # Do jakiej paczki należy ta pozycja
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipment.id'), nullable=False)
    shipment = db.relationship('Shipment', back_populates='items')
    
    # Do jakiej pozycji GŁÓWNEGO ZAMÓWIENIA się odnosi
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_item.id'), nullable=False)
    order_item = db.relationship('OrderItem', backref=db.backref('shipment_items', lazy=True))

    def to_dict(self):
        # Zwracamy kluczowe info, aby frontend nie musiał robić dodatkowych zapytań
        return {
            "id": self.id,
            "quantity_shipped": self.quantity_shipped,
            "order_item_id": self.order_item_id,
            "product_name": self.order_item.product_name, # Pobieramy nazwę z powiązanej pozycji zamówienia
            "variant_size": self.order_item.variant_size  # Pobieramy rozmiar z powiązanej pozycji zamówienia
        }
    
class Notification(db.Model):
    """
    Model do przechowywania powiadomień wewnętrznych (ikona dzwonka).
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # Do kogo należy to powiadomienie
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade="all, delete-orphan"))
    
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=True) # Krótka treść
    
    # Link, na który ma przenieść po kliknięciu (np. /dashboard/orders)
    link_url = db.Column(db.String(255), nullable=True)
    
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "link_url": self.link_url,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat()
        }