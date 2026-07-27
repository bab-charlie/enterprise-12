
import bcrypt
import datetime

class EmailService:
    @staticmethod
    def send_email(recipient, subject, body):
        print(f"[EMAIL] {recipient} | {subject}\n{body}")

def hash_password(password:str)->bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

class InventorySystem:
    def __init__(self):
        self.companies={}
        self.users={}  # {company:{user:data}}
        self.inventory={}
        self.logs={}
        self.roles={"Admin","Finance","Supply","Sales"}

    def register_company(self,cid,name,email,admin_user,admin_pass):
        if cid in self.companies: raise ValueError("Company exists")
        self.companies[cid]={"name":name,"admin_email":email}
        self.users[cid]={}
        self.inventory[cid]={}
        self.logs[cid]=[]
        self.users[cid][admin_user]={"password":hash_password(admin_pass),"role":"Admin"}

    def register_user(self,cid,requester,username,password,role):
        req=self.users[cid].get(requester)
        if not req or req["role"]!="Admin": raise PermissionError
        if username in self.users[cid]: raise ValueError("Username exists")
        self.users[cid][username]={"password":hash_password(password),"role":role if role in self.roles else "Sales"}

    def authenticate(self,cid,username,password):
        u=self.users.get(cid,{}).get(username)
        return u if u and verify_password(password,u["password"]) else None

    def process_goods(self,cid,user,item,qty,price=0,action="IN",customer_email=None):
        if user is None: raise PermissionError("Authenticate first")
        if qty<=0: raise ValueError("Positive qty required")
        inv=self.inventory[cid]
        if action=="IN":
            e=inv.setdefault(item,{"qty":0,"price":price})
            e["qty"]+=qty
            if price: e["price"]=price
        else:
            e=inv.get(item)
            if not e or e["qty"]<qty: raise ValueError("Insufficient stock")
            e["qty"]-=qty
            invoice=f"Invoice total: ${qty*e['price']}"
            if customer_email: EmailService.send_email(customer_email,"Invoice",invoice)
        self.logs[cid].append(f"{datetime.datetime.now()}: {user['role']} {action} {qty} {item}")
