import logging
from design_database import CustomerDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_operations():
    """Test all database operations with Supabase."""
    try:
        # Initialize database
        db = CustomerDatabase()
        logger.info("Successfully connected to Supabase")

        # Test 1: Create a new customer
        customer_id = db.get_or_create_customer("Test", "User")
        logger.info(f"Test 1: Created customer with ID {customer_id}")

        # Test 2: Try to get the same customer (should return existing ID)
        existing_id = db.get_or_create_customer("Test", "User")
        logger.info(f"Test 2: Retrieved existing customer with ID {existing_id}")
        assert customer_id == existing_id, "Customer IDs should match"

        # Test 3: Add an order
        order_details = {
            "items": [
                {
                    "name": "Test Product",
                    "quantity": 2,
                    "price": 29.99
                }
            ],
            "total": 59.98
        }
        order_id = db.add_order(customer_id, order_details)
        logger.info(f"Test 3: Added order with ID {order_id}")

        # Test 4: Get customer orders
        orders = db.get_customer_orders(customer_id)
        logger.info(f"Test 4: Retrieved {len(orders)} orders")
        assert len(orders) > 0, "Should have at least one order"
        assert orders[0]['id'] == order_id, "Order ID should match"

        # Test 5: Get order history
        history = db.get_customer_order_history("Test", "User")
        logger.info("Test 5: Retrieved order history")
        assert "Test User" in history, "History should contain customer name"
        assert "Test Product" in history, "History should contain product name"

        logger.info("All tests passed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    test_database_operations() 