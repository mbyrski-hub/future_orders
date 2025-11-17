# /backend/app/routes.py
from flask import Blueprint, request, jsonify, make_response
from .models import User, db, Product, ProductVariant, Order, OrderItem, Shipment, ShipmentItem
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, create_refresh_token, decode_token
from datetime import timedelta
from functools import wraps
import datetime
from flask import render_template # <-- Do generowania PDF z szablonu
from flask_mail import Message # <-- Do wysyłania maila
from app import mail # <-- Zaimportuj obiekt 'mail'
from xhtml2pdf import pisa
import io # Do obsługi PDF w pamięci
from sqlalchemy import func
from .models import PushSubscription # <-- Dodaj ten model
from flask import current_app # <-- Do pobrania configu
from pywebpush import webpush, WebPushException
import json

# Tworzymy "Blueprint" dla naszego API, ułatwi to organizację
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"msg": "Błędna nazwa użytkownika lub hasło"}), 401

    # --- ZMIANA LOGIKI TWORZENIA TOKENU ---
    
    # 1. Tożsamość (identity) będzie teraz prostym stringiem
    identity = user.username 
    
    # 2. Resztę danych przekażemy jako "dodatkowe roszczenia" (claims)
    additional_claims = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }

    # 3. Tworzymy token z nową strukturą
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)

    # 4. Do frontendu wciąż wysyłamy ten sam obiekt 'user', bo tego oczekuje
    user_identity_for_frontend = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }
    
    return jsonify(access_token=access_token, user=user_identity_for_frontend)


# Przykładowy zabezpieczony endpoint (zaktualizowany)
@api_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # get_jwt_identity() zwróci teraz string (nazwę usera)
    current_user_identity = get_jwt_identity() 
    
    # get_jwt() zwróci pełny słownik z naszymi 'claims'
    current_user_claims = get_jwt()
    
    return jsonify(
        logged_in_as_identity=current_user_identity,
        full_claims=current_user_claims
    ), 200


# Dekorator admina (zaktualizowany)
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            
            # --- ZMIANA TUTAJ ---
            # Zezwalamy na dostęp dla 'admin' LUB 'power_user'
            if claims.get("role") not in ['admin', 'power_user']:
            # --- KONIEC ZMIANY ---
                
                return jsonify({"msg": "Tylko administratorzy mają dostęp!"}), 403
            
            return fn(*args, **kwargs)
        return decorator
    return wrapper

# GET - Pobierz wszystkie produkty
@api_bp.route('/products', methods=['GET'])
@jwt_required() # Zabezpieczamy (może user też powinien widzieć? na razie tak)
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products]), 200

# POST - Stwórz nowy produkt
@api_bp.route('/products', methods=['POST'])
@admin_required()
def create_product():
    data = request.get_json()
    
    # Walidacja (bardzo podstawowa)
    if 'name' not in data or 'variants' not in data or not data['variants']:
        return jsonify({"msg": "Brakuje nazwy lub wariantów"}), 400

    new_product = Product(name=data['name'], description=data.get('description'), image_url=data.get('image_url'))
    db.session.add(new_product)
    
    # Musimy zapisać produkt, aby dostać jego ID
    db.session.flush() 

    try:
        for variant_data in data['variants']:
            # ZMIANA: Usunięto walidację 'stock'
            if 'price' not in variant_data:
                # Na razie zakładamy, że frontend wyśle 'price: null' lub 'price: 0'
                # Jeśli 'price' w ogóle nie ma, ustawiamy na None
                variant_data['price'] = None

            new_variant = ProductVariant(
                size=variant_data.get('size', 'Uniwersalny'),
                # ZMIANA: Bezpieczne pobieranie ceny
                price=float(variant_data['price']) if variant_data['price'] is not None and variant_data['price'] != '' else None,
                # ZMIANA: Usunięto 'stock'
                # stock=int(variant_data['stock']),
                product_id=new_product.id
            )
            db.session.add(new_variant)

        db.session.commit()
        return jsonify(new_product.to_dict()), 201
        
    except Exception as e:
        db.session.rollback() # Wycofaj zmiany w razie błędu
        return jsonify({"msg": f"Wystąpił błąd: {str(e)}"}), 400

# GET - Pobierz jeden produkt
@api_bp.route('/products/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict()), 200

@api_bp.route('/products/<int:product_id>', methods=['PUT'])
@admin_required()
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.image_url = data.get('image_url', product.image_url)
    # Aktualizacja wariantów jest złożona. 
    # Uproszczona strategia: usuwamy stare i dodajemy nowe.
    ProductVariant.query.filter_by(product_id=product.id).delete()
    
    try:
        # TA LOGIKA JEST TERAZ IDENTYCZNA JAK W 'create_product'
        for variant_data in data.get('variants', []):
            if 'price' not in variant_data:
                 variant_data['price'] = None

            new_variant = ProductVariant(
                size=variant_data.get('size', 'Uniwersalny'),
                # ZMIANA: Bezpieczne pobieranie ceny
                price=float(variant_data['price']) if variant_data['price'] is not None and variant_data['price'] != '' else None,
                # ZMIANA: Usunięto 'stock'
                product_id=product.id
            )
            db.session.add(new_variant)
            
        db.session.commit()
        return jsonify(product.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Wystąpił błąd: {str(e)}"}), 400

# DELETE - Usuń produkt
@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required()
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product) # Dzięki 'cascade' warianty też się usuną
    db.session.commit()
    return jsonify({"msg": "Produkt usunięty"}), 200

@api_bp.route('/users', methods=['GET'])
@admin_required()
def get_users():
    # Pobieramy wszystkich użytkowników, ale mapujemy ich na bezpieczny słownik
    # Nigdy nie wysyłaj hashy haseł do frontendu!
    users = User.query.all()
    output = []
    for user in users:
        output.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        })
    return jsonify(output), 200

@api_bp.route('/users', methods=['POST'])
@admin_required()
def create_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user') # Domyślnie 'user'

    if not username or not email or not password:
        return jsonify({"msg": "Brakuje nazwy, emaila lub hasła"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Ta nazwa użytkownika jest już zajęta"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Ten email jest już zajęty"}), 400
        
    new_user = User(username=username, email=email, role=role)
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "role": new_user.role
    }), 201

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required()
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # Sprawdź unikalność, jeśli jest zmieniana
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"msg": "Ta nazwa użytkownika jest już zajęta"}), 400
        user.username = data['username']
        
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"msg": "Ten email jest już zajęty"}), 400
        user.email = data['email']
    
    if 'role' in data:
        user.role = data['role']
        
    # Obsługa zmiany hasła (jeśli zostało podane)
    if 'password' in data and data['password']:
        user.set_password(data['password'])
        
    db.session.commit()
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }), 200

@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    # Proste zabezpieczenie, aby admin nie mógł usunąć sam siebie
    current_user_claims = get_jwt()
    if current_user_claims.get('id') == user_id:
        return jsonify({"msg": "Nie możesz usunąć samego siebie"}), 403

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "Użytkownik usunięty"}), 200

@api_bp.route('/users/<int:user_id>/products', methods=['GET'])
@admin_required()
def get_user_assigned_products(user_id):
    """Pobiera listę ID produktów przypisanych do użytkownika."""
    user = User.query.get_or_404(user_id)
    # user.assigned_products to teraz zapytanie (dzięki lazy='dynamic')
    product_ids = [product.id for product in user.assigned_products]
    return jsonify(product_ids), 200

@api_bp.route('/users/<int:user_id>/products', methods=['PUT'])
@admin_required()
def set_user_assigned_products(user_id):
    """Aktualizuje (nadpisuje) listę produktów przypisanych do użytkownika."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'product_ids' not in data or not isinstance(data['product_ids'], list):
        return jsonify({"msg": "Brakuje listy 'product_ids'"}), 400
        
    product_ids_to_assign = data['product_ids']
    
    # 1. Wyczyść stare przypisania
    user.assigned_products.clear()
    
    # 2. Znajdź obiekty Product na podstawie ID
    if product_ids_to_assign: # Tylko jeśli lista nie jest pusta
        products_to_assign = Product.query.filter(Product.id.in_(product_ids_to_assign)).all()
        
        # 3. Dodaj nowe przypisania
        for product in products_to_assign:
            user.assigned_products.append(product)
            
    db.session.commit()
    
    # Zwróć zaktualizowaną listę ID
    updated_product_ids = [product.id for product in user.assigned_products]
    return jsonify(updated_product_ids), 200

# Dekorator do sprawdzania roli 'user'
def user_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") != 'user':
                return jsonify({"msg": "Tylko klienci mają dostęp!"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@api_bp.route('/my-products', methods=['GET'])
@user_required()
def get_my_assigned_products():
    """Zwraca listę produktów przypisanych do zalogowanego klienta."""
    
    # Pobieramy ID zalogowanego usera z tokenu
    current_user_claims = get_jwt()
    user_id = current_user_claims.get('id')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "Użytkownik nie znaleziony"}), 404
        
    # Dzięki naszej relacji, to jest teraz proste
    # 'user.assigned_products' to lista obiektów Product
    products = user.assigned_products 
    
    # Zmieniamy obiekty na słowniki, tak jak w /api/products
    return jsonify([product.to_dict() for product in products]), 200

# /backend/app/routes.py

# --- Funkcja Pomocnicza do PDF ---
def _generate_order_pdf(order, user):
    """Generuje PDF dla danego zamówienia i zwraca surowe dane PDF."""
    try:
        html_content = render_template('pdf/order_confirmation.html', 
                                        order=order, 
                                        user=user)
        
        result_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(
                html_content,
                dest=result_buffer
        )
        if pisa_status.err:
            raise Exception(f"Błąd podczas generowania PDF: {pisa_status.err}")

        pdf_data = result_buffer.getvalue()
        result_buffer.close()
        return pdf_data
    except Exception as e:
        print(f"Błąd podczas _generate_order_pdf: {e}")
        raise e # Przekaż błąd dalej


@api_bp.route('/orders', methods=['POST'])
@user_required()
def create_order():
    """
    Przyjmuje koszyk (items) ORAZ uwagi (notes) od klienta.
    """
    # ZMIANA: Odczytujemy cały obiekt JSON
    data = request.get_json()
    cart_items = data.get('items') # Pobieramy pozycje z klucza 'items'
    notes = data.get('notes')      # Pobieramy uwagi z klucza 'notes'
    
    if not cart_items:
        return jsonify({"msg": "Koszyk jest pusty"}), 400
        
    claims = get_jwt()
    user_id = claims.get('id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"msg": "Użytkownik nie znaleziony"}), 404

    # ZMIANA: Dodajemy 'notes' podczas tworzenia zamówienia
    new_order = Order(user_id=user.id, status='new', notes=notes)
    db.session.add(new_order)
    
    # --- BLOK 1: KRYTYCZNY (Zapis do Bazy Danych) ---
    try:
        for item in cart_items: # Iterujemy po 'cart_items', a nie 'data'
            # ... (reszta tego bloku 'try' pozostaje bez zmian) ...
            variant = ProductVariant.query.get(item.get('variant_id'))
            if not variant:
                raise Exception(f"Wariant o ID {item.get('variant_id')} nie istnieje.")
            
            if variant.product not in user.assigned_products:
                 raise Exception(f"Brak dostępu do produktu: {variant.product.name}")

            order_item = OrderItem(
                order=new_order,
                variant_id=variant.id,
                quantity=item.get('quantity'),
                product_name=variant.product.name,
                variant_size=variant.size,
                price_at_order=variant.price
            )
            db.session.add(order_item)
        
        db.session.commit()
    
    except Exception as e:
        db.session.rollback()
        print(f"KRYTYCZNY BŁĄD BAZY DANYCH: {str(e)}")
        return jsonify({"msg": f"Wystąpił błąd przy zapisie do bazy: {str(e)}"}), 500

    # --- BLOK 2: NIEKRYTYCZNY (PDF i E-mail) ---
    try:
        # 1. Wywołaj nową funkcję pomocniczą
        pdf_file = _generate_order_pdf(new_order, user)
        
        # 2. Stwórz i wyślij e-mail z załącznikiem
        msg = Message(
            subject=f"Potwierdzenie Zamówienia #{new_order.id}",
            recipients=[user.email],
            body=f"Dziękujemy za złożenie zamówienia nr {new_order.id}. Szczegóły znajdują się w załączniku PDF."
        )
        msg.attach(
            f"zamowienie_{new_order.id}.pdf",
            "application/pdf",
            pdf_file
        )
        mail.send(msg)

    except Exception as e:
        # Ta logika pozostaje bez zmian - łapie błędy PDF lub maila
        print(f"--- OSTRZEŻENIE: Nie udało się wysłać e-maila z potw. dla zamówienia #{new_order.id} ---")
        print(f"--- Błąd: {str(e)} ---")
        warning_msg = f"Zamówienie {new_order.id} przyjęte, ale nie udało się wysłać e-maila: {str(e)}"
        response_data = new_order.to_dict()
        response_data['email_warning'] = warning_msg 
        return jsonify(response_data), 201 

    # --- SUKCES ---
    return jsonify(new_order.to_dict()), 201

@api_bp.route('/my-orders', methods=['GET'])
@user_required()
def get_my_orders():
    """Zwraca historię zamówień zalogowanego klienta."""
    claims = get_jwt()
    user_id = claims.get('id')

    # Pobierz zamówienia od najnowszego
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

    return jsonify([order.to_dict() for order in orders]), 200

# --- PANEL SPEDYCJI (rola 'shipping') ---

# Dekorator do sprawdzania roli 'shipping'
def shipping_required():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            # ZEZWÓLMY TEŻ POWER USEROWI
            if claims.get("role") not in ['shipping', 'admin', 'power_user']: # <-- POPRAWKA
                return jsonify({"msg": "Brak uprawnień dostępu!"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@api_bp.route('/shipping/orders', methods=['GET'])
@shipping_required()
def get_all_orders():
    """Zwraca wszystkie zamówienia, posortowane od najnowszego."""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    # Musimy dołączyć dane użytkownika do każdego zamówienia
    orders_data = []
    for order in orders:
        order_dict = order.to_dict()
        order_dict['user_info'] = {
            "username": order.user.username,
            "email": order.user.email
        }
        orders_data.append(order_dict)
            
    return jsonify(orders_data), 200

# ---------------------------------------------------------------------
# NOWA, PRZEBUDOWANA FUNKCJA DO WYSYŁKI (z historią)
# ---------------------------------------------------------------------
@api_bp.route('/shipping/orders/<int:order_id>/ship', methods=['POST'])
@shipping_required()
def ship_order_items(order_id):
    """
    Realizuje wysyłkę, tworzy wpis w historii (Shipment)
    i automatycznie aktualizuje status całego zamówienia.
    Oczekuje JSON: {"items": [{"item_id": 1, "quantity_to_ship": 2}, ...]}
    """
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    items_to_ship_data = data.get('items')

    if not items_to_ship_data:
        return jsonify({"msg": "Brak pozycji do wysłania"}), 400
        
    # Pobierz ID użytkownika spedycji z tokenu
    claims = get_jwt()
    shipping_user_id = claims.get('id')

    try:
        # 1. Stwórz jedną "paczkę" (Shipment) dla tej transakcji
        new_shipment = Shipment(
            order_id=order.id,
            shipped_by_user_id=shipping_user_id
        )
        db.session.add(new_shipment)
        
        # Lista do walidacji (aby nie wysłać niczego pustego)
        processed_items = []

        # 2. Przejdź przez pozycje do wysłania z żądania
        for item_data in items_to_ship_data:
            item_id = item_data.get('item_id')
            try:
                quantity_to_ship = int(item_data.get('quantity_to_ship', 0))
            except ValueError:
                raise Exception(f"Ilość dla pozycji {item_id} musi być liczbą.")
            
            if quantity_to_ship <= 0:
                continue # Pomiń, jeśli ktoś wysłał 0

            order_item = OrderItem.query.get(item_id)
            
            # Walidacja
            if not order_item or order_item.order_id != order_id:
                raise Exception(f"Pozycja o ID {item_id} nie należy do tego zamówienia.")
            
            remaining_to_ship = order_item.quantity - order_item.shipped_quantity
            if quantity_to_ship > remaining_to_ship:
                raise Exception(f"Nie można wysłać {quantity_to_ship} szt. '{order_item.product_name}'. Pozostało: {remaining_to_ship}.")
            
            # --- KLUCZOWA LOGIKA ---
            
            # AKCJA 1: Zaktualizuj starą kolumnę (dla kompatybilności wstecznej)
            order_item.shipped_quantity += quantity_to_ship
            
            # AKCJA 2: Stwórz nowy wpis w historii (ShipmentItem)
            new_shipment_item = ShipmentItem(
                quantity_shipped=quantity_to_ship,
                shipment=new_shipment, # Połącz z nową "paczką"
                order_item=order_item  # Połącz z pozycją zamówienia
            )
            db.session.add(new_shipment_item)
            processed_items.append(new_shipment_item)
            
        # Jeśli formularz był pusty (wszystkie pozycje = 0), rzuć błąd
        if not processed_items:
            raise Exception("Nie wybrano żadnych produktów do wysłania (ilość musi być > 0).")

        # 3. Automatyczna aktualizacja statusu zamówienia (na podstawie starej kolumny)
        total_ordered_count = 0
        total_shipped_count = 0
        for item in order.items:
            total_ordered_count += item.quantity
            total_shipped_count += item.shipped_quantity
            
        if total_shipped_count == 0:
            order.status = 'new'
        elif total_shipped_count < total_ordered_count:
            order.status = 'partial'
        else:
            order.status = 'completed'

        # 4. Zapisz wszystko do bazy (Shipment, ShipmentItems, OrderItems, Order)
        db.session.commit()
        
        # 5. Automatyczne powiadomienia PUSH (ta logika już tu jest i zadziała)
        try:
            if order.status == 'partial' or order.status == 'completed':
                # ... (logika wysyłania PUSH, którą już mamy) ...
                if order.status == 'partial':
                    title = "Twoje zamówienie jest w drodze!"
                    body = f"Część Twojego zamówienia #{order.id} została wysłana."
                else: # completed
                    title = "Twoje zamówienie zostało zrealizowane!"
                    body = f"Wszystkie produkty z zamówienia #{order.id} zostały wysłane."
                
                user_subscriptions = PushSubscription.query.filter_by(user_id=order.user_id).all()
                click_data = {"url": "/dashboard/orders"}
                
                for sub in user_subscriptions:
                    _send_push_notification(sub.subscription_json, title, body, click_data)
        except Exception as e:
            print(f"BŁĄD: Nie udało się wysłać powiadomienia PUSH o statusie: {e}")

        # 6. Zwróć zaktualizowane zamówienie z 'user_info'
        order_dict = order.to_dict()
        order_dict['user_info'] = {
            "username": order.user.username,
            "email": order.user.email
        }
        return jsonify(order_dict), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400
    
@api_bp.route('/me', methods=['GET'])
@jwt_required() # Dowolny zalogowany użytkownik
def get_my_profile():
    """Zwraca dane profilowe zalogowanego użytkownika."""
    claims = get_jwt()
    user_id = claims.get('id')
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role
    }), 200

@api_bp.route('/me', methods=['PUT'])
@jwt_required() # Dowolny zalogowany użytkownik
def update_my_profile():
    """Aktualizuje dane profilowe zalogowanego użytkownika (oprócz hasła)."""
    claims = get_jwt()
    user_id = claims.get('id')
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    # Sprawdzanie unikalności emaila, jeśli jest zmieniany
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"msg": "Ten email jest już zajęty"}), 400
        user.email = data['email']

    if 'first_name' in data:
        user.first_name = data['first_name']
    
    if 'last_name' in data:
        user.last_name = data['last_name']
        
    db.session.commit()
    
    # Zwróć zaktualizowane dane
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role
    }), 200

@api_bp.route('/me/password', methods=['PUT'])
@jwt_required()
def update_my_password():
    """Pozwala zalogowanemu użytkownikowi zmienić swoje hasło."""
    claims = get_jwt()
    user_id = claims.get('id')
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"msg": "Brakuje obecnego lub nowego hasła"}), 400
        
    # Sprawdź obecne hasło
    if not user.check_password(current_password):
        return jsonify({"msg": "Obecne hasło jest nieprawidłowe"}), 401
        
    # Ustaw nowe hasło
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({"msg": "Hasło zostało pomyślnie zmienione"}), 200

@api_bp.route('/admin/dashboard-stats', methods=['GET'])
@admin_required()
def get_dashboard_stats():
    """
    Oblicza i zwraca kluczowe statystyki dla kokpitu admina,
    Z OPCJONALNYM filtrowaniem wg daty.
    """
    try:
        # --- NOWA LOGIKA FILTROWANIA DATY ---
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Bazowe zapytania, które będziemy filtrować
        order_query = Order.query
        item_query = db.session.query(OrderItem).join(Order, OrderItem.order_id == Order.id)
        
        if start_date_str:
            try:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                order_query = order_query.filter(Order.created_at >= start_date)
                item_query = item_query.filter(Order.created_at >= start_date)
            except ValueError:
                return jsonify({"msg": "Nieprawidłowy format start_date. Wymagany RRRR-MM-DD"}), 400

        if end_date_str:
            try:
                # Dodajemy 1 dzień, aby 'end_date' był włącznie (czyli do końca dnia)
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date() + datetime.timedelta(days=1)
                order_query = order_query.filter(Order.created_at < end_date)
                item_query = item_query.filter(Order.created_at < end_date)
            except ValueError:
                return jsonify({"msg": "Nieprawidłowy format end_date. Wymagany RRRR-MM-DD"}), 400
        
        # --- KONIEC LOGIKI FILTROWANIA ---

        # 1. Obliczamy całkowitą wartość (na podstawie przefiltrowanych pozycji)
        total_revenue = item_query.with_entities(
            func.sum(OrderItem.price_at_order * OrderItem.quantity)
        ).scalar() or 0.0

        # 2. Liczymy łączne liczby (na podstawie przefiltrowanych zamówień)
        total_orders = order_query.count()
        
        # Te statystyki są globalne, nie filtrujemy ich
        total_users = db.session.query(func.count(User.id)).scalar()
        total_products = db.session.query(func.count(Product.id)).scalar()

        # 3. Top 5 najczęściej zamawianych produktów (na podstawie przefiltrowanych pozycji)
        top_products = item_query.group_by(
            OrderItem.product_name
        ).with_entities(
            OrderItem.product_name,
            func.sum(OrderItem.quantity).label('total_quantity')
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(5).all()
        
        top_products_data = [
            {"name": name, "quantity": int(qty)} for name, qty in top_products
        ]

        # 4. Top 5 klientów (na podstawie przefiltrowanych zamówień)
        # Musimy użyć 'order_query' jako podzapytania, aby było to wydajne
        
        # Krok 4a: Zdobądź przefiltrowane ID zamówień
        filtered_order_ids = [order.id for order in order_query.all()]
        
        if not filtered_order_ids:
             top_clients_data = []
        else:
            top_clients = db.session.query(
                User.username,
                func.count(Order.id).label('order_count')
            ).join(
                Order, User.id == Order.user_id
            ).filter(
                Order.id.in_(filtered_order_ids) # Filtruj tylko po przefiltrowanych zamówieniach
            ).group_by(
                User.id
            ).order_by(
                func.count(Order.id).desc()
            ).limit(5).all()

            top_clients_data = [
                {"username": username, "orders": count} for username, count in top_clients
            ]

        # Zwróć wszystko w jednym obiekcie
        return jsonify({
            "summary": {
                "total_revenue": total_revenue,
                "total_orders": total_orders,
                "total_users": total_users,
                "total_products": total_products
            },
            "charts": {
                "top_products": top_products_data,
                "top_clients": top_clients_data
            }
        }), 200

    except Exception as e:
        print(f"Błąd podczas generowania statystyk: {str(e)}")
        return jsonify({"msg": f"Błąd serwera: {str(e)}"}), 500
    
@api_bp.route('/admin/latest-orders', methods=['GET'])
@admin_required()
def get_latest_orders():
    """Zwraca 5 ostatnich zamówień dla kokpitu admina."""
    try:
        latest_orders = Order.query.order_by(
            Order.created_at.desc()
        ).limit(5).all()
        
        # Formatujemy dane wyjściowe, dołączając dane klienta
        orders_data = []
        for order in latest_orders:
            order_dict = order.to_dict()
            order_dict['user_info'] = {
                "username": order.user.username,
                "email": order.user.email
            }
            orders_data.append(order_dict)
            
        return jsonify(orders_data), 200

    except Exception as e:
        print(f"Błąd podczas pobierania ostatnich zamówień: {str(e)}")
        return jsonify({"msg": f"Błąd serwera: {str(e)}"}), 500
    
def _send_push_notification(subscription_info_json, title, body, data=None):
    """
    Wysyła pojedyncze powiadomienie.
    'subscription_info_json' to string JSON z bazy danych.
    """
    try:
        subscription_info = json.loads(subscription_info_json)
        payload = {
            "title": title,
            "body": body,
            "data": data or {} # Dodatkowe dane, np. link do kliknięcia
        }
        
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=current_app.config['VAPID_CLAIMS']
        )
    except WebPushException as ex:
        # Jeśli subskrypcja wygasła (kod 410), powinniśmy ją usunąć
        if ex.response.status_code == 410:
            print(f"Subskrypcja wygasła i zostanie usunięta: {ex.response.text}")
            # Znajdź i usuń subskrypcję
            PushSubscription.query.filter_by(subscription_json=subscription_info_json).delete()
            db.session.commit()
        else:
            print(f"Błąd podczas wysyłania PUSH: {ex}")
    except Exception as e:
        print(f"Inny błąd PUSH: {e}")


# --- API do subskrypcji dla Klienta ---

@api_bp.route('/subscribe-push', methods=['POST'])
@user_required()
def subscribe_push():
    """Zapisuje subskrypcję powiadomień dla zalogowanego klienta."""
    claims = get_jwt()
    user_id = claims.get('id')
    
    subscription_data = request.get_json()
    if not subscription_data or 'endpoint' not in subscription_data:
        return jsonify({"msg": "Brak danych subskrypcji"}), 400
        
    subscription_json = json.dumps(subscription_data)
    
    # Sprawdź, czy ta subskrypcja (ten endpoint) już istnieje
    existing_sub = PushSubscription.query.filter_by(subscription_json=subscription_json).first()
    
    if not existing_sub:
        new_sub = PushSubscription(
            user_id=user_id,
            subscription_json=subscription_json
        )
        db.session.add(new_sub)
        db.session.commit()
        print(f"Zapisano nową subskrypcję dla usera {user_id}")
    
    return jsonify({"success": True}), 201

# --- API dla Admina do zarządzania subskrypcjami ---

@api_bp.route('/admin/subscriptions', methods=['GET'])
@admin_required()
def get_all_subscriptions():
    """Zwraca listę wszystkich subskrypcji do podglądu."""
    subs = PushSubscription.query.join(User).order_by(User.username).all()
    
    return jsonify([
        {
            "id": sub.id,
            "user_id": sub.user.id,
            "username": sub.user.username,
            "endpoint": sub.get_endpoint(),
            "created_at": sub.created_at.isoformat()
        } for sub in subs
    ]), 200

@api_bp.route('/admin/subscriptions/<int:sub_id>', methods=['DELETE'])
@admin_required()
def delete_subscription(sub_id):
    """Usuwa konkretną subskrypcję."""
    sub = PushSubscription.query.get_or_404(sub_id)
    db.session.delete(sub)
    db.session.commit()
    return jsonify({"msg": "Subskrypcja usunięta"}), 200

@api_bp.route('/admin/send-push', methods=['POST'])
@admin_required()
def send_custom_push():
    """Wysyła personalizowaną wiadomość do wszystkich lub jednego usera."""
    data = request.get_json()
    title = data.get('title')
    body = data.get('body')
    user_id = data.get('user_id') # Opcjonalne

    if not title or not body:
        return jsonify({"msg": "Tytuł i treść są wymagane"}), 400

    query = PushSubscription.query
    if user_id:
        # Wyślij do konkretnego usera
        query = query.filter_by(user_id=int(user_id))
    
    subscriptions = query.all()
    if not subscriptions:
        return jsonify({"msg": "Nie znaleziono subskrypcji pasujących do kryteriów"}), 404
        
    for sub in subscriptions:
        _send_push_notification(sub.subscription_json, title, body)
        
    return jsonify({"msg": f"Wysłano powiadomienie do {len(subscriptions)} subskrypcji"}), 200

# --- Endpoint do pobierania PDF na żądanie ---

@api_bp.route('/orders/<int:order_id>/pdf', methods=['GET'])
@jwt_required()
def get_order_pdf(order_id):
    """Generuje i zwraca PDF dla konkretnego zamówienia."""
    
    order = Order.query.get_or_404(order_id)
    claims = get_jwt()
    user_id = claims.get('id')
    role = claims.get('role')
    
    # Zabezpieczenie: Sprawdź, czy user jest właścicielem lub adminem/spedycją
    if order.user_id != user_id and role not in ['admin', 'shipping', 'power_user']:
        return jsonify({"msg": "Brak dostępu do tego zasobu"}), 403
        
    try:
        # Wywołaj naszą funkcję pomocniczą
        pdf_data = _generate_order_pdf(order, order.user)
        
        # Stwórz odpowiedź Flask z surowymi danymi PDF
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        # 'inline' otwiera w nowej karcie; 'attachment' wymusza pobieranie
        response.headers['Content-Disposition'] = f'inline; filename=zamowienie_{order.id}.pdf'
        
        return response

    except Exception as e:
        return jsonify({"msg": f"Nie udało się wygenerować PDF: {str(e)}"}), 500
    
@api_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Przyjmuje e-mail, znajduje użytkownika i wysyła mu
    specjalny, krótko-życiowy token do resetu hasła.
    """
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"msg": "Brak adresu e-mail"}), 400
        
    user = User.query.filter_by(email=email).first()
    
    # WAŻNE: Ze względów bezpieczeństwa, ZAWSZE zwracamy sukces,
    # nawet jeśli użytkownik nie istnieje. Zapobiega to "odgadywaniu" e-maili.
    if not user:
        print(f"Próba resetu hasła dla nieistniejącego e-maila: {email}")
        return jsonify({"msg": "Jeśli konto istnieje, link został wysłany."}), 200

    try:
        # 1. Stwórz specjalny token, ważny tylko 15 minut
        # Używamy "claims", aby oznaczyć ten token jako "tylko do resetu"
        reset_claims = {"purpose": "password_reset"}
        expires = timedelta(minutes=15)
        reset_token = create_access_token(
            identity=user.username, # Używamy username jako tożsamości
            additional_claims=reset_claims,
            expires_delta=expires
        )
        
        # 2. Stwórz URL do frontendu, który będzie zawierał ten token
        # UPEWNIJ SIĘ, że adres URL frontendu jest poprawny
        reset_url = f"http://localhost:5173/reset-password?token={reset_token}"
        
        # 3. Wyrenderuj szablon e-maila
        html_content = render_template('email/reset_password.html', 
                                        user=user, 
                                        reset_url=reset_url)
        
        # 4. Wyślij e-mail
        msg = Message(
            subject="Resetowanie hasła w aplikacji MojeZamowienia",
            recipients=[user.email],
            html=html_content # Wysyłamy jako HTML
        )
        mail.send(msg)
        
        return jsonify({"msg": "Jeśli konto istnieje, link został wysłany."}), 200

    except Exception as e:
        print(f"KRYTYCZNY BŁĄD podczas wysyłania e-maila resetującego: {str(e)}")
        # Nadal zwracamy ogólny komunikat, aby nie ujawniać błędu serwera
        return jsonify({"msg": "Wystąpił błąd serwera."}), 500


@api_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Przyjmuje token resetujący oraz nowe hasło.
    Weryfikuje token i ustawia nowe hasło.
    """
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({"msg": "Brakuje tokena lub nowego hasła"}), 400
        
    try:
        # 1. Zdekoduj token ręcznie, aby sprawdzić jego cel
        decoded_token = decode_token(token)
        
        # 2. Sprawdź, czy token jest TYLKO do resetu hasła
        if decoded_token.get('purpose') != 'password_reset':
            return jsonify({"msg": "Nieprawidłowy typ tokena"}), 422
            
        # 3. Znajdź użytkownika na podstawie tożsamości z tokena
        username = decoded_token.get('sub')
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({"msg": "Użytkownik nie istnieje"}), 404
            
        # 4. Ustaw nowe hasło
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({"msg": "Hasło zostało pomyślnie zmienione"}), 200

    except Exception as e:
        # Token mógł wygasnąć (ExpiredSignatureError) lub być nieprawidłowy
        print(f"Błąd podczas resetowania hasła: {str(e)}")
        return jsonify({"msg": "Token jest nieprawidłowy lub wygasł"}), 422
    
@api_bp.route('/orders/<int:order_id>/shipments', methods=['GET'])
@jwt_required()
def get_order_shipments(order_id):
    """
    Zwraca listę historii wysyłek (paczek) dla danego zamówienia.
    """
    order = Order.query.get_or_404(order_id)
    claims = get_jwt()
    user_id = claims.get('id')
    role = claims.get('role')
    
    # Zabezpieczenie: Sprawdź, czy user jest właścicielem lub ma uprawnienia
    if order.user_id != user_id and role not in ['admin', 'shipping', 'power_user']:
        return jsonify({"msg": "Brak dostępu do tego zasobu"}), 403
        
    try:
        # Sortujemy od najnowszej wysyłki
        shipments = Shipment.query.filter_by(
            order_id=order.id
        ).order_by(
            Shipment.created_at.desc()
        ).all()
        
        # Zwracamy listę paczek, używając metody to_dict(), którą stworzyliśmy
        return jsonify([shipment.to_dict() for shipment in shipments]), 200

    except Exception as e:
        print(f"Błąd podczas pobierania historii wysyłek: {str(e)}")
        return jsonify({"msg": f"Błąd serwera: {str(e)}"}), 500
    
    # --- Helper do generowania PDF (zmodyfikowany, aby przyjmował szablon) ---
def _generate_pdf_from_template(template_name, context):
    """Generuje PDF z danego szablonu i kontekstu."""
    try:
        html_content = render_template(template_name, **context)
        
        result_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(
                html_content,
                dest=result_buffer
        )
        if pisa_status.err:
            raise Exception(f"Błąd podczas generowania PDF: {pisa_status.err}")

        pdf_data = result_buffer.getvalue()
        result_buffer.close()
        return pdf_data
    except Exception as e:
        print(f"Błąd podczas _generate_pdf_from_template: {e}")
        raise e

# --- Endpoint do Listy do Spakowania ---
@api_bp.route('/shipping/picking-list-pdf', methods=['POST'])
@shipping_required()
def get_picking_list_pdf():
    """
    Generuje zbiorczego PDF-a "Listę do Spakowania" dla wybranych zamówień.
    Oczekuje JSON: {"order_ids": [1, 2, 3]}
    """
    data = request.get_json()
    order_ids = data.get('order_ids')

    if not order_ids or not isinstance(order_ids, list):
        return jsonify({"msg": "Nie podano listy ID zamówień"}), 400

    try:
        # 1. Znajdź wszystkie NIEREALIZOWANE pozycje z wybranych zamówień
        items_to_pick = db.session.query(OrderItem).filter(
            OrderItem.order_id.in_(order_ids),
            OrderItem.shipped_quantity < OrderItem.quantity # Kluczowy warunek!
        ).all()

        if not items_to_pick:
            return jsonify({"msg": "Wszystkie pozycje z wybranych zamówień zostały już zrealizowane."}), 404

        # 2. Zagreguj (zsumuj) produkty
        aggregated_list = {}
        for item in items_to_pick:
            key = f"{item.product_name}_{item.variant_size}"
            remaining_to_ship = item.quantity - item.shipped_quantity
            
            if key not in aggregated_list:
                aggregated_list[key] = {
                    "name": item.product_name,
                    "size": item.variant_size,
                    "total_quantity": 0,
                    "orders": set() # Używamy 'set', aby uniknąć duplikatów ID
                }
            
            aggregated_list[key]['total_quantity'] += remaining_to_ship
            aggregated_list[key]['orders'].add(f"#{item.order_id}") # Dodaj ID zamówienia

        # Konwertuj 'set' na listę, aby można było ją posortować i połączyć
        final_items_list = sorted(
            [
                {**item, "orders": sorted(list(item["orders"]), key=lambda x: int(x[1:]))} 
                for item in aggregated_list.values()
            ],
            key=lambda x: x['name'] # Sortuj alfabetycznie po nazwie
        )

        # 3. Przygotuj kontekst dla szablonu
        context = {
            "aggregated_items": final_items_list,
            "order_ids_str": ", ".join([f"#{id}" for id in order_ids]),
            "generated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        # 4. Wygeneruj PDF
        pdf_data = _generate_pdf_from_template('pdf/picking_list.html', context)
        
        # 5. Zwróć PDF do przeglądarki
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=lista_do_spakowania.pdf'
        
        return response

    except Exception as e:
        print(f"Błąd podczas generowania listy do spakowania: {str(e)}")
        return jsonify({"msg": f"Błąd serwera: {str(e)}"}), 500