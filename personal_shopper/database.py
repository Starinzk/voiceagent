import os
from typing import List, Dict, Optional, Any
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import json

logger = logging.getLogger("personal-shopper-db")
logger.setLevel(logging.INFO)

class CustomerDatabase:
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """Initialize the customer database with Supabase.
        
        Args:
            supabase_url (str, optional): Supabase project URL. If None, reads from SUPABASE_URL env var.
            supabase_key (str, optional): Supabase API key. If None, reads from SUPABASE_KEY env var.
        """
        load_dotenv()
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided or set in environment variables")
            
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Connected to Supabase database")

    def get_or_create_customer(self, first_name: str, last_name: str) -> int:
        """Get a customer by name or create if not exists.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            int: The customer's ID (either existing or newly created)
        """
        # Check if customer exists
        response = self.client.table('customers') \
            .select('id') \
            .eq('first_name', first_name) \
            .eq('last_name', last_name) \
            .execute()
            
        if response.data:
            customer_id = response.data[0]['id']
            logger.info(f"Found existing customer: {first_name} {last_name} (ID: {customer_id})")
            return customer_id
            
        # Create new customer
        response = self.client.table('customers') \
            .insert({
                'first_name': first_name,
                'last_name': last_name
            }) \
            .execute()
            
        customer_id = response.data[0]['id']
        logger.info(f"Created new customer: {first_name} {last_name} (ID: {customer_id})")
        return customer_id

    def add_order(self, customer_id: int, order_details: Dict[str, Any]) -> int:
        """Add a new order for a customer.
        
        Args:
            customer_id (int): The ID of the customer placing the order
            order_details (Dict[str, Any]): A dictionary containing the order details
            
        Returns:
            int: The ID of the newly created order
        """
        response = self.client.table('orders') \
            .insert({
                'customer_id': customer_id,
                'order_details': order_details
            }) \
            .execute()
            
        order_id = response.data[0]['id']
        logger.info(f"Added new order (ID: {order_id}) for customer ID: {customer_id}")
        return order_id

    def get_customer_orders(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a customer.
        
        Args:
            customer_id (int): The ID of the customer whose orders to retrieve
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing order information
        """
        response = self.client.table('orders') \
            .select('id, order_details, order_date') \
            .eq('customer_id', customer_id) \
            .order('order_date', desc=True) \
            .execute()
            
        orders = []
        for row in response.data:
            orders.append({
                'id': row['id'],
                'date': row['order_date'],
                'details': row['order_details']
            })
            
        return orders

    def get_customer_order_history(self, first_name: str, last_name: str) -> str:
        """Get a formatted string of customer order history for LLM consumption.
        
        Args:
            first_name (str): The customer's first name
            last_name (str): The customer's last name
            
        Returns:
            str: A formatted string containing the customer's order history
        """
        # Get customer ID
        response = self.client.table('customers') \
            .select('id') \
            .eq('first_name', first_name) \
            .eq('last_name', last_name) \
            .execute()
            
        if not response.data:
            return "No order history found for this customer."
            
        customer_id = response.data[0]['id']
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
                history += f"- {json.dumps(details)}\n"
                
            history += "\n"
            
        return history 