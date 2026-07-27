import hashlib
import datetime
import json

# ==========================================
# 1. UTILITIES & SECURITY
# ==========================================
def hash_password(password: str) -> str:
    """Hashes passwords using SHA-256 to protect company data."""
    return hashlib.sha256(password.encode()).hexdigest()

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
        # Simulated AI analysis
        sentiment = "Positive" if "good" in user_feedback.lower() or "great" in user_feedback.lower() else "Review Needed"
        summary = f"AI Summary: User feedback indicates a {sentiment} experience."
        
        email_body = f"Raw Feedback: {user_feedback}\n{summary}"
        EmailService.send_email(admin_email, "New System Feedback via AI", email_body)

# ==========================================
# 2. SYSTEM MODELS (Multi-Tenant)
# ==========================================
class DocumentGenerator:
    @staticmethod
    def generate_invoice(customer, items, total):
        return f"INVOICE for {customer} | Total: ${total} | Items: {items}"
    
    @staticmethod
    def generate_supply_order(supplier, items):
        return f"SUPPLY ORDER to {supplier} | Requested Items: {items}"

    @staticmethod
    def generate_delivery_note(customer, items):
        return f"DELIVERY NOTE for {customer} | Items to Deliver: {items}"

class InventorySystem:
    def __init__(self):
        # In-memory mock database (Tailored to Multi-Company / Multi-Tenant)
        self.companies = {}   # {company_id: {"name": str, "admin_email": str}}
        self.users = {}       # {username: {"password": hashed, "role": str, "company_id": str}}
        self.inventory = {}   # {company_id: {item_name: quantity}}
        self.tracking = {}    # {company_id: [transaction_logs]}
        
        # Standard Roles - Automated if company doesn't specify
        self.default_roles = ["Admin", "Finance", "Supply", "Sales"]

    # ==========================================
    # 3. COMPANY & USER MANAGEMENT
    # ==========================================
    def register_company(self, company_id, name, admin_email, admin_user, admin_pass):
        """Registers a new company and its Admin/Owner."""
        self.companies[company_id] = {"name": name, "admin_email": admin_email}
        self.inventory[company_id] = {}
        self.tracking[company_id] = []
        
        # Admin is in charge of monitoring the system
        self.register_user(admin_user, admin_pass, "Admin", company_id, admin_user)

    def register_user(self, username, password, role, company_id, requesting_user):
        """Registers users based on roles. Default roles apply if unassigned."""
        if role not in self.default_roles:
            role = "Sales" # Automates basic role if an unrecognized one is given
            
        self.users[username] = {
            "password": hash_password(password),
            "role": role,
            "company_id": company_id
        }

    def authenticate(self, username, password):
        user = self.users.get(username)
        if user and user["password"] == hash_password(password):
            return user
        return None

    # ==========================================
    # 4. GOODS IN & OUT / TRACKING
    # ==========================================
    def log_transaction(self, company_id, action, item, quantity, user):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {quantity}x {item} (Handled by {user['role']})"
        self.tracking[company_id].append(log_entry)

    def process_goods(self, user, action, item, quantity, entity=None):
        """Handles Goods In/Out based on Roles."""
        company_id = user["company_id"]
        role = user["role"]

        if action == "IN" and role in ["Admin", "Supply"]:
            current_qty = self.inventory[company_id].get(item, 0)
            self.inventory[company_id][item] = current_qty + quantity
            self.log_transaction(company_id, "GOODS IN", item, quantity, user)
            
            if entity: # Entity acts as Supplier
                doc = DocumentGenerator.generate_supply_order(entity, f"{quantity}x {item}")
                print(f"[DOCUMENT GENERATED] {doc}")

        elif action == "OUT" and role in ["Admin", "Sales"]:
            current_qty = self.inventory[company_id].get(item, 0)
            if current_qty >= quantity:
                self.inventory[company_id][item] = current_qty - quantity
                self.log_transaction(company_id, "GOODS OUT", item, quantity, user)
                
                if entity: # Entity acts as Customer
                    # Generate Delivery Note & Invoice
                    delivery_note = DocumentGenerator.generate_delivery_note(entity, f"{quantity}x {item}")
                    invoice = DocumentGenerator.generate_invoice(entity, f"{quantity}x {item}", quantity * 10) # Mock price
                    
                    # Email the delivery note to the customer
                    EmailService.send_email(f"{entity.replace(' ', '').lower()}@customer.com", "Your Delivery Note", delivery_note)
            else:
                print(f"[ERROR] Insufficient stock for {item}")
        else:
            print(f"[ACCESS DENIED] Role '{role}' cannot perform '{action}' operations.")

    # ==========================================
    # 5. MONITORING & FEEDBACK
    # ==========================================
    def view_tracking_log(self, user):
        """Allows Admin to monitor all system movements."""
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
        company_id = user["company_id"]
        admin_email = self.companies[company_id]["admin_email"]
        AIFeedbackSystem.process_and_send_feedback(feedback_text, admin_email)


# ==========================================
# 6. SYSTEM DEMONSTRATION
# ==========================================
if __name__ == "__main__":
    # 1. Initialize the central platform
    app = InventorySystem()

    # 2. Register a tailored company (Multi-tenant)
    app.register_company("COMP001", "Global Tech Inc", "owner@globaltech.com", "admin_user", "SuperSecretPass123")

    # 3. Create role-based accounts (Automated defaults applied)
    app.register_user("john_supply", "supplypass", "Supply", "COMP001", "admin_user")
    app.register_user("jane_sales", "salespass", "Sales", "COMP001", "admin_user")

    # 4. Supply department processes Goods IN
    supply_user = app.authenticate("john_supply", "supplypass")
    app.process_goods(supply_user, "IN", "Laptops", 50, "Dell Suppliers")

    # 5. Sales department processes Goods OUT and sends Delivery Note via Email
    sales_user = app.authenticate("jane_sales", "salespass")
    app.process_goods(sales_user, "OUT", "Laptops", 5, "Acme Corp")

    # 6. Admin monitors the complete tracking log
    admin_user = app.authenticate("admin_user", "SuperSecretPass123")
    app.view_tracking_log(admin_user)

    # 7. Built-in AI System processes user feedback and emails it to the owner
    app.submit_feedback(sales_user, "The new invoice generation feature works great, but the UI is a bit slow.")