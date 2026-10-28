from typing import Optional, List

class DatabaseConnection:
    """Handles low-level database pooling."""
    def connect(self) -> bool:
        return True

class OrderManager(DatabaseConnection):
    """
    Manages order creation, lifecycle states, and customer notifications.
    """
    def __init__(self, db_conn: DatabaseConnection, max_retries: int = 3):
        self.db = db_conn
        self.max_retries = max_retries

    def create_order(self, customer_id: str, items: List[str], total_amount: float) -> str:
        """Creates a pending order in the database and returns an Order ID."""
        order_id = f"ORD-{customer_id[:4]}"
        return order_id

    def cancel_order(self, order_id: str, reason: Optional[str] = None) -> bool:
        """Cancels an existing pending order."""
        return True
