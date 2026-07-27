import datetime
import bcrypt

# ==========================================
# 1. UTILITIES & SECURITY
# ==========================================
def hash_password(password: str) -> bytes:
    """Hashes passwords using bcrypt to protect company data."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed)

class EmailService:
    @staticmethod
    def send_email(recipient: str, subject: str, body: str):
        """Simulates sending an email via an SMTP server."""
        print(f"\n[EMAIL SENT] To: {recipient} | Subject: {subject}")
        print(f"--- Body ---\n{body}\n------------\n")

class AIFeedbackSystem:
    @staticmethod
    def process_and_send_feedback(user_feedback: str, admin_email: str):
        """Simulates an AI analyzing user feedback and emailing it to the Admin."""
        positive_words = ["good", "great", "excellent", "awesome"]
        negative_words = ["bad", "slow", "delete", "error", "bug", "terrible"]
        
        lower_feedback = user_feedback.lower()
        has_pos = any(word in lower_feedback for word in positive_words)
        has_neg = any(word in lower_feedback for word in negative_words)
        
        if has_neg:
            sentiment = "Review Needed (Negative context detected)"
        elif has_pos:
            sentiment = "Positive"
        else:
            sentiment = "Neutral"

        summary = f"AI Summary: User feedback indicates a {sentiment} experience."
        email_body = f"Raw Feedback: {user_feedback}\n{summary}"
        EmailService.send_email(admin_email, "New System Feedback via AI", email_body)

# ==========================================
# 2. SYSTEM MODELS (Multi-Tenant)
# ==========================================
class DocumentGenerator:
    @staticmethod
    def generate_invoice(customer, items, total):
        return f"INVOICE for {customer} | Total: ${total:.2f} | Items: {items}"
    
    @staticmethod
    def generate_supply_order(supplier, items):
        return f"SUPPLY ORDER to {supplier} | Requested Items: {items}"

    @staticmethod
    def generate_delivery_note(customer, items):
        return f"DELIVERY NOTE for {customer} | Items to Deliver: {items}"

class InventorySystem:
    def __init__(self):
        self.companies = {}   # {company_id: {"name": str, "admin_email": str}}
        self.users = {}       # {company_id: {username: {"password": hashed, "role": str, "company_id": str}}}
        self.inventory = {}   # {company_id: {item_name: {"qty": int, "price": float}}}
        self.tracking = {}    # {company_id: [transaction_logs]}
        
        self.default_roles = ["Admin", "Finance", "Supply", "Sales"]

    # ==========================================
    # 3. COMPANY & USER MANAGEMENT
    # ==========================================
    def register_company(self, company_id, name, admin_email, admin_user, admin_pass):
        """Registers a new company and its Admin/Owner."""
        if company_id in self.companies:
            raise ValueError("Company already exists.")

        self.companies[company_id] = {"name": name, "admin_email": admin_email}
        self.users[company_id] = {}
        self.inventory[company_id] = {}
        self.tracking[company_id] = []
        
        # Admin bypasses the requesting_user permission check for initial setup
        self._create_user(admin_user, admin_pass, "Admin", company_id)

    def _create_user(self, username, password, role, company_id):
        """Internal helper to handle the actual user creation logic."""
        if username in self.users[company_id]:
            raise ValueError("Username already exists in this company.")

        if role not in self.default_roles:
            role = "Sales"
            
        self.users[company_id][username] = {
            "username": username,
            "password": hash_password(password),
            "role": role,
            "company_id": company_id
        }

    def register_user(self, username, password, role, company_id, requesting_user):
        """Registers users based on roles, enforcing Admin permissions."""
        requester = self.users.get(company_id, {}).get(requesting_user)
        
        if requester is None or requester["role"] != "Admin":
            raise PermissionError("Only Admins can register users.")
            
        self._create_user(username, password, role, company_id)

    def authenticate(self, company_id, username, password):
        """Authenticates users scoped by company to prevent cross-tenant collisions."""
        user = self.users.get(company_id, {}).get(username)
        if user and check_password(password, user["password"]):
            return user
        return None

    # ==========================================
    # 4. GOODS IN & OUT / TRACKING
    # ==========================================
    def log_transaction(self, company_id, action, item, quantity, user):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Logs now track both the username and role
        log_entry = f"[{timestamp}] {action}: {quantity}x {item} (Handled by {user['username']} - {user['role']})"
        self.tracking[company_id].append(log_entry)

    def process_goods(self, user, action, item, quantity, entity=None, entity_email=None, price=0.0):
        """Handles Goods In/Out with validation and accurate pricing."""
        if user is None:
            raise PermissionError("Authentication failed or user is not logged in.")
        
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        company_id = user["company_id"]
        role = user["role"]

        # Ensure item exists in dictionary structure
        if item not in self.inventory[company_id]:
            self.inventory[company_id][item] = {"qty": 0, "price": price}

        if action == "IN" and role in ["Admin", "Supply"]:
            self.inventory[company_id][item]["qty"] += quantity
            if price > 0:
                self.inventory[company_id][item]["price"] = price
                
            self.log_transaction(company_id, "GOODS IN", item, quantity, user)
            
            if entity: 
                doc = DocumentGenerator.generate_supply_order(entity, f"{quantity}x {item}")
                print(f"[DOCUMENT GENERATED] {doc}")

        elif action == "OUT" and role in ["Admin", "Sales"]:
            current_qty = self.inventory[company_id][item]["qty"]
            
            if current_qty >= quantity:
                self.inventory[company_id][item]["qty"] -= quantity
                self.log_transaction(company_id, "GOODS OUT", item, quantity, user)
                
                if entity and entity_email:
                    # Calculate real totals based on stored pricing
                    item_price = self.inventory[company_id][item]["price"]
                    total_cost = quantity * item_price
                    
                    delivery_note = DocumentGenerator.generate_delivery_note(entity, f"{quantity}x {item}")
                    invoice = DocumentGenerator.generate_invoice(entity, f"{quantity}x {item}", total_cost) 
                    
                    # Email both the delivery note and invoice to the real customer email
                    EmailService.send_email(entity_email, "Your Delivery Note", delivery_note)
                    EmailService.send_email(entity_email, "Your Invoice", invoice)
            else:
                print(f"[ERROR] Insufficient stock for {item}")
        else:
            print(f"[ACCESS DENIED] Role '{role}' cannot perform '{action}' operations.")

    # ==========================================
    # 5. MONITORING & FEEDBACK
    # ==========================================
    def view_tracking_log(self, user):
        """Allows Admin to monitor all system movements."""
        if user is None:
             raise PermissionError("Authentication failed.")
             
        if user["role"] == "Admin":
            company_id = user["company_id"]
            print(f"\n--- TRACKING LOG FOR {self.companies[company_id]['name']} ---")
            for log in self.tracking[company_id]:
                print(log)
            print("-----------------------------------")
        else:
            print("[ACCESS DENIED] Only Admins can view complete logs.")

    def submit_feedback(self, user, feedback_text):
        """In-built AI feedback system sent to the Admin's email."""
        if user is None:
             raise PermissionError("Authentication failed.")
             
        company_id = user["company_id"]
        admin_email = self.companies[company_id]["admin_email"]
        AIFeedbackSystem.process_and_send_feedback(feedback_text, admin_email)


# ==========================================
# 6. SYSTEM DEMONSTRATION
# ==========================================
if __name__ == "__main__":
    try:
        app = InventorySystem()

        # 1. Register a tailored company
        app.register_company("COMP001", "Global Tech Inc", "owner@globaltech.com", "admin_user", "SuperSecretPass123")

        # 2. Create role-based accounts (Using Admin privileges)
        app.register_user("john_supply", "supplypass", "Supply", "COMP001", "admin_user")
        app.register_user("jane_sales", "salespass", "Sales", "COMP001", "admin_user")

        # 3. Supply department processes Goods IN (Sets the real price)
        supply_user = app.authenticate("COMP001", "john_supply", "supplypass")
        app.process_goods(supply_user, "IN", "Laptops", 50, entity="Dell Suppliers", price=899.00)

        # 4. Sales department processes Goods OUT and sends Docs via real Email
        sales_user = app.authenticate("COMP001", "jane_sales", "salespass")
        app.process_goods(sales_user, "OUT", "Laptops", 5, entity="Acme Corp", entity_email="purchasing@acmecorp.com")

        # 5. Admin monitors the complete tracking log (Now shows usernames)
        admin_user = app.authenticate("COMP001", "admin_user", "SuperSecretPass123")
        app.view_tracking_log(admin_user)

        # 6. Built-in AI System processes user feedback (Will now correctly detect negative context)
        app.submit_feedback(sales_user, "Great system, but it deletes my data.")
        
    except Exception as e:
        print(f"\n[SYSTEM ERROR] {e}")