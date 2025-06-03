import sqlite3
import os
import json
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger("personal-shopper-db")
logger.setLevel(logging.INFO)

class CustomerDatabase:
    def __init__(self, db_path: str = None):
        """Initialize the customer database.
        
        Args:
            db_path (str, optional): Path to the SQLite database file. If None, creates a default
                database file named 'customer_data.db' in the same directory as this file.
        """
        if db_path is None:
            # Use a default path in the same directory as this file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'customer_data.db')
        
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create the database and tables if they don't exist.
        
        Creates two tables:
        - customers: Stores customer information (id, first_name, last_name, created_at)
        - orders: Stores order information (id, customer_id, order_details, order_date)
        
        The orders table has a foreign key relationship with the customers table.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create customers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create orders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_details TEXT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def get_or_create_customer(self, first_name: str, last_name: str) -> int:
        """Get a customer by name or create if not exists.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            int: The customer's ID (either existing or newly created)
            
        Note:
            If a customer with the given name doesn't exist, a new customer record is created.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if customer exists
        cursor.execute(
            "SELECT id FROM customers WHERE first_name = ? AND last_name = ?", 
            (first_name, last_name)
        )
        result = cursor.fetchone()
        
        if result:
            customer_id = result[0]
            logger.info(f"Found existing customer: {first_name} {last_name} (ID: {customer_id})")
        else:
            # Create new customer
            cursor.execute(
                "INSERT INTO customers (first_name, last_name) VALUES (?, ?)",
                (first_name, last_name)
            )
            customer_id = cursor.lastrowid
            logger.info(f"Created new customer: {first_name} {last_name} (ID: {customer_id})")
        
        conn.commit()
        conn.close()
        return customer_id
    
    def add_order(self, customer_id: int, order_details: Dict[str, Any]) -> int:
        """Add a new order for a customer.
        
        Args:
            customer_id (int): The ID of the customer placing the order
            order_details (Dict[str, Any]): A dictionary containing the order details.
                Expected to include at least an 'items' list with item details.
                
        Returns:
            int: The ID of the newly created order
            
        Note:
            The order_details dictionary is stored as a JSON string in the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert order details to JSON string
        order_json = json.dumps(order_details)
        
        cursor.execute(
            "INSERT INTO orders (customer_id, order_details) VALUES (?, ?)",
            (customer_id, order_json)
        )
        
        order_id = cursor.lastrowid
        logger.info(f"Added new order (ID: {order_id}) for customer ID: {customer_id}")
        
        conn.commit()
        conn.close()
        return order_id
    
    def get_customer_orders(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a customer.
        
        Args:
            customer_id (int): The ID of the customer whose orders to retrieve
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing order information.
                Each dictionary includes:
                - id: The order ID
                - date: The order date
                - details: The order details (parsed from JSON)
                
        Note:
            Orders are returned in descending order by date (most recent first).
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, order_details, order_date FROM orders WHERE customer_id = ? ORDER BY order_date DESC",
            (customer_id,)
        )
        
        orders = []
        for row in cursor.fetchall():
            order_data = json.loads(row['order_details'])
            orders.append({
                'id': row['id'],
                'date': row['order_date'],
                'details': order_data
            })
        
        conn.close()
        return orders
    
    def get_customer_order_history(self, first_name: str, last_name: str) -> str:
        """Get a formatted string of customer order history for LLM consumption.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            str: A formatted string containing the customer's order history.
                If no customer is found, returns "No order history found for this customer."
                If customer has no orders, returns a message indicating no orders.
                Otherwise, returns a detailed history of all orders with items and prices.
                
        Note:
            The returned string is formatted specifically for consumption by language models,
            with clear sections and itemized details for each order.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get customer ID
        cursor.execute(
            "SELECT id FROM customers WHERE first_name = ? AND last_name = ?", 
            (first_name, last_name)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return "No order history found for this customer."
        
        customer_id = result[0]
        orders = self.get_customer_orders(customer_id)
        
        if not orders:
            return f"Customer {first_name} {last_name} has no previous orders."
        
        # Format order history for LLM
        history = f"Order history for {first_name} {last_name}:\n\n"
        
        for order in orders:
            history += f"Order #{order['id']} (Date: {order['date']}):\n"
            details = order['details']
            
            if 'items' in details:
                for item in details['items']:
                    history += f"- {item.get('quantity', 1)}x {item.get('name', 'Unknown Item')}"
                    if 'price' in item:
                        history += f" (${item['price']})"
                    history += "\n"
            else:
                # Handle case where order details might be in a different format
                history += f"- {json.dumps(details)}\n"
            
            history += "\n"
        
        conn.close()
        return history 