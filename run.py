#!/usr/bin/env python3
"""
Файл для запуска приложения в режиме разработки
"""

import os
from app import create_app
from app.extensions import db
from app.models import User, Category, Brand, Product, Review
from sqlalchemy import text

# Создаем приложение
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Автоматически импортирует модели в консоль Flask
    """
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Brand': Brand,
        'Product': Product,
        'Review': Review
    }


@app.cli.command("create-admin")
def create_admin():
    """
    Создание администратора через командную строку
    Команда: flask create-admin
    """
    from getpass import getpass
    from sqlalchemy import text
    
    print("Создание администратора")
    username = input("Имя пользователя: ").strip()
    email = input("Email: ").strip()
    password = getpass("Пароль: ").strip()
    
    # Проверка существования пользователя через прямой SQL
    result = db.session.execute(
        text("SELECT id FROM users WHERE username = :username"),
        {'username': username}
    ).fetchone()
    if result:
        print("Ошибка: пользователь с таким именем уже существует!")
        return
    
    result = db.session.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {'email': email}
    ).fetchone()
    if result:
        print("Ошибка: пользователь с таким email уже существует!")
        return
    
    # Создаем нового пользователя
    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash(password)
    
    db.session.execute(
        text("""
            INSERT INTO users (username, email, password_hash, is_admin, is_staff, created_at)
            VALUES (:username, :email, :password_hash, true, true, NOW())
        """),
        {
            'username': username,
            'email': email,
            'password_hash': password_hash
        }
    )
    
    db.session.commit()
    
    print(f"Администратор {username} успешно создан!")


@app.cli.command("init-db")
def init_db():
    """
    Инициализация базы данных с тестовыми данными
    Команда: flask init-db
    """
    import random
    from datetime import datetime, timedelta
    
    # Очистка базы данных
    db.drop_all()
    db.create_all()
    
    print("Создание тестовых данных...")
    
    # Создание категорий
    categories = [
        Category(title="Кроссовки", slug="sneakers", 
                description="Спортивная и повседневная обувь"),
        Category(title="Туфли", slug="shoes", 
                description="Классическая и деловая обувь"),
        Category(title="Сапоги", slug="boots", 
                description="Зимняя и демисезонная обувь"),
        Category(title="Ботинки", slug="boots-men", 
                description="Мужская обувь"),
        Category(title="Босоножки", slug="sandals", 
                description="Летняя обувь"),
    ]
    
    for category in categories:
        db.session.add(category)
    db.session.commit()
    print(f"Создано {len(categories)} категорий")
    
    # Создание брендов
    brands = [
        Brand(name="Nike"),
        Brand(name="Adidas"),
        Brand(name="Puma"),
        Brand(name="Reebok"),
        Brand(name="New Balance"),
        Brand(name="Geox"),
        Brand(name="Ecco"),
        Brand(name="Salomon"),
    ]
    
    for brand in brands:
        db.session.add(brand)
    db.session.commit()
    print(f"Создано {len(brands)} брендов")
    
    # Создание тестовых пользователей
    users = [
        User(username="admin", email="admin@example.com", 
             is_staff=True, is_superuser=True),
        User(username="seller1", email="seller1@example.com"),
        User(username="seller2", email="seller2@example.com"),
        User(username="buyer1", email="buyer1@example.com"),
        User(username="buyer2", email="buyer2@example.com"),
    ]
    
    for user in users:
        user.set_password("password123")
        db.session.add(user)
    db.session.commit()
    print(f"Создано {len(users)} пользователей")
    
    # Создание тестовых товаров
    product_names = [
        "Кроссовки беговые",
        "Туфли классические",
        "Сапоги зимние",
        "Ботинки trekking",
        "Босоножки летние",
        "Кроссовки для зала",
        "Туфли офисные",
        "Сапоги резиновые",
        "Ботинки рабочие",
        "Сандалии пляжные",
    ]
    
    descriptions = [
        "Удобная и стильная обувь для повседневной носки",
        "Качественные материалы, отличная посадка по ноге",
        "Подходит для спорта и активного отдыха",
        "Классический дизайн, современные технологии",
        "Надежная обувь для любых погодных условий",
        "Комфорт и стиль в каждой паре",
        "Идеальный выбор для офиса и деловых встреч",
        "Легкие и дышащие материалы",
        "Прочная конструкция, долговечность",
        "Современный дизайн, проверенное качество",
    ]
    
    products = []
    for i in range(20):  # Создаем 20 тестовых товаров
        product = Product(
            title=f"{random.choice(product_names)} {i+1}",
            description=random.choice(descriptions),
            price=random.randint(1000, 10000),
            stock=random.randint(0, 50),
            category_id=random.choice([c.id for c in categories]),
            brand_id=random.choice([b.id for b in brands]),
            seller_id=random.choice([u.id for u in users if u.username != "admin"]),
            pub_date=datetime.now() - timedelta(days=random.randint(0, 30)),
            is_published=random.choice([True, True, True, False]),  # 75% опубликованы
        )
        products.append(product)
        db.session.add(product)
    
    db.session.commit()
    print(f"Создано {len(products)} товаров")
    
    # Создание тестовых отзывов
    reviews = []
    for product in products:
        if product.is_published:
            for _ in range(random.randint(0, 5)):  # 0-5 отзывов на товар
                review = Review(
                    text=random.choice([
                        "Отличный товар, рекомендую!",
                        "Хорошее качество, удобно носить",
                        "Соответствует описанию, покупкой доволен",
                        "Неплохо, но есть небольшие недочеты",
                        "Приемлемое качество за свою цену",
                        "Прекрасная обувь, буду заказывать еще",
                        "Не совсем то, что ожидал, но в целом нормально",
                        "Отлично подошло, всем доволен",
                        "Хорошее соотношение цена/качество",
                        "Быстрая доставка, товар соответствует описанию",
                    ]),
                    rating=random.randint(3, 5),
                    product_id=product.id,
                    author_id=random.choice([u.id for u in users if u.username.startswith("buyer")]),
                    created_at=product.pub_date + timedelta(days=random.randint(1, 7)),
                )
                reviews.append(review)
                db.session.add(review)
    
    db.session.commit()
    print(f"Создано {len(reviews)} отзывов")
    
    print("\nТестовые данные успешно созданы!")
    print("\nДоступные учетные записи:")
    print("1. Администратор - login: admin, password: password123")
    print("2. Продавец 1 - login: seller1, password: password123")
    print("3. Продавец 2 - login: seller2, password: password123")
    print("4. Покупатель 1 - login: buyer1, password: password123")
    print("5. Покупатель 2 - login: buyer2, password: password123")

@app.cli.command("reset-db")
def reset_db():
    """
    Полная пересоздание базы данных
    Команда: flask reset-db
    """
    confirm = input("Вы уверены, что хотите полностью очистить базу данных? (yes/no): ")
    if confirm.lower() == "yes":
        db.drop_all()
        db.create_all()
        print("База данных пересоздана!")
    else:
        print("Операция отменена.")


if __name__ == "__main__":
    # Запуск приложения в режиме разработки
    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=app.config["DEBUG"]
    )