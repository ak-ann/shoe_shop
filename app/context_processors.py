import datetime
from flask import session
from flask_login import current_user
from app.database import get_db_connection

def cart_context():
    """Контекстный процессор для корзины"""
    def get_cart_count():
        try:
            if current_user.is_authenticated:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'cart_items'
                    )
                """)
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    cursor.execute("SELECT SUM(quantity) as total FROM cart_items WHERE user_id = %s", 
                                 (current_user.id,))
                    result = cursor.fetchone()
                    cart_count = result[0] or 0 if result else 0
                else:
                    cart_count = 0
                
                cursor.close()
                conn.close()
                return cart_count
            else:
                cart = session.get('cart', {})
                return sum(cart.values()) if cart else 0
        except Exception as e:
            print(f"Error getting cart count: {e}")
            return 0
    
    return {
        'get_cart_count': get_cart_count,
        'cart_count': get_cart_count,
    }

def utility_context():
    """Контекстный процессор для утилит"""
    def format_price(price):
        if price is None:
            return "0.00"
        try:
            return f"{float(price):.2f}"
        except:
            return str(price)
    
    return {
        'format_price': format_price,
        'current_year': datetime.datetime.now().year,
        'now': datetime.datetime.now,
    }