import sqlite3, hashlib, os, random
from datetime import datetime, timedelta
from config import DB_PATH

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def _hash(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ── Schema ────────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Vendeur',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    lens_type TEXT,
    index_value TEXT,
    coating TEXT,
    brand TEXT,
    supplier_id INTEGER REFERENCES suppliers(id),
    sph_min REAL DEFAULT 0, sph_max REAL DEFAULT 0,
    cyl_min REAL DEFAULT 0, cyl_max REAL DEFAULT 0,
    purchase_price REAL DEFAULT 0,
    sale_price REAL DEFAULT 0,
    stock INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 5,
    description TEXT,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    city TEXT,
    balance REAL DEFAULT 0,
    active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE,
    customer_id INTEGER REFERENCES customers(id),
    user_id INTEGER REFERENCES users(id),
    total REAL DEFAULT 0,
    discount REAL DEFAULT 0,
    tax REAL DEFAULT 0,
    payment_method TEXT DEFAULT 'Espèces',
    status TEXT DEFAULT 'paid',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sale_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER REFERENCES sales(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    unit_price REAL DEFAULT 0,
    discount REAL DEFAULT 0,
    total REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref TEXT UNIQUE,
    supplier_id INTEGER REFERENCES suppliers(id),
    user_id INTEGER REFERENCES users(id),
    total REAL DEFAULT 0,
    status TEXT DEFAULT 'received',
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS purchase_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_id INTEGER REFERENCES purchases(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER DEFAULT 1,
    unit_price REAL DEFAULT 0,
    total REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS delivery_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bl_number TEXT UNIQUE,
    customer_id INTEGER REFERENCES customers(id),
    sale_id INTEGER REFERENCES sales(id),
    status TEXT DEFAULT 'delivered',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    module TEXT,
    detail TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

def init_db():
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    _seed(conn)
    conn.close()

def _seed(conn):
    # Users
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        for u, p, n, r in [
            ("admin",   "admin123",   "Admin Système",    "Administrateur"),
            ("manager", "manager123", "Mohammed Alami",   "Manager"),
            ("vendeur", "vendeur123", "Sara Benali",      "Vendeur"),
        ]:
            conn.execute("INSERT INTO users(username,password,full_name,role) VALUES(?,?,?,?)",
                         (u, _hash(p), n, r))

    # Suppliers
    if conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0] == 0:
        for name, phone in [
            ("Essilor Maroc", "0522-101010"),
            ("Hoya Vision",   "0522-202020"),
            ("Zeiss Maroc",   "0522-303030"),
            ("Shamir Optic",  "0522-404040"),
        ]:
            conn.execute("INSERT INTO suppliers(name,phone) VALUES(?,?)", (name, phone))

    # Products
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        cats = ["Unifocal", "Progressif", "Bifocal", "Lentilles"]
        types_ = ["Organique", "Polycarbonate", "Hi-index"]
        indices = ["1.50", "1.56", "1.60", "1.67", "1.74"]
        coats = ["Anti-reflet", "AR + UV", "Blue Protect", "Photochromique"]
        brands = ["Essilor", "Hoya", "Zeiss", "Shamir", "Nikon"]
        for i in range(1, 51):
            ref = f"P{i:04d}"
            cat = cats[i % len(cats)]
            brand = brands[i % len(brands)]
            pp = round(random.uniform(80, 400), 2)
            sp = round(pp * random.uniform(1.3, 2.0), 2)
            stock = random.randint(0, 60)
            min_s = 5
            conn.execute("""INSERT INTO products
                (reference,name,category,lens_type,index_value,coating,brand,
                 supplier_id,sph_min,sph_max,cyl_min,cyl_max,
                 purchase_price,sale_price,stock,min_stock)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (ref, f"{brand} {cat} {indices[i%len(indices)]}",
                 cat, types_[i%len(types_)], indices[i%len(indices)],
                 coats[i%len(coats)], brand, (i%4)+1,
                 -6.0, 6.0, 0.0, -2.0,
                 pp, sp, stock, min_s))

    # Customers
    if conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        names = ["Optique Lumière","Optique Vision","Optique Atlas","Optique Soleil",
                 "Optique Zénith","Optique Clair","Optique Maroc","Optique Expert",
                 "Optique Plus","Optique Central"]
        cities = ["Casablanca","Rabat","Fès","Marrakech","Oujda","Tanger","Agadir"]
        for i, nm in enumerate(names):
            conn.execute("INSERT INTO customers(code,full_name,phone,city) VALUES(?,?,?,?)",
                         (f"C{i+1:04d}", nm, f"06{i:08d}", cities[i%len(cities)]))

    # Historical sales (12 months)
    if conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0:
        today = datetime.now()
        inv_n = 1
        for m in range(11, -1, -1):
            base_date = today - timedelta(days=m*30)
            n_sales = random.randint(15, 40)
            for _ in range(n_sales):
                day_offset = random.randint(0, 28)
                sale_date = base_date + timedelta(days=day_offset)
                if sale_date > today: sale_date = today
                cust_id = random.randint(1, 10)
                total = round(random.uniform(500, 8000), 2)
                pmt = random.choice(["Espèces","Virement","Chèque","Carte bancaire"])
                inv_num = f"FAC-{inv_n:05d}"
                sid = conn.execute("""INSERT INTO sales
                    (invoice_number,customer_id,user_id,total,payment_method,status,created_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (inv_num, cust_id, 1, total, pmt, "paid",
                     sale_date.strftime("%Y-%m-%d %H:%M:%S"))).lastrowid
                # sale_items
                pids = [random.randint(1,50) for _ in range(random.randint(1,3))]
                for pid in pids:
                    up = round(total/len(pids), 2)
                    conn.execute("INSERT INTO sale_items(sale_id,product_id,quantity,unit_price,discount,total) VALUES(?,?,?,?,?,?)",
                                 (sid, pid, 1, up, 0, up))
                inv_n += 1
    conn.commit()

# ── Auth ──────────────────────────────────────────────────────────────────────
def authenticate(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND active=1",
        (username, _hash(password))).fetchone()
    conn.close()
    return dict(row) if row else None

# ── Dashboard stats ───────────────────────────────────────────────────────────
def get_dashboard_stats():
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    sales_today = conn.execute(
        "SELECT COALESCE(SUM(total),0) FROM sales WHERE DATE(created_at)=?", (today,)
    ).fetchone()[0]

    sales_month = conn.execute(
        "SELECT COALESCE(SUM(total),0) FROM sales WHERE strftime('%Y-%m',created_at)=?", (month,)
    ).fetchone()[0]

    sales_year = conn.execute(
        "SELECT COALESCE(SUM(total),0) FROM sales WHERE strftime('%Y',created_at)=?",
        (datetime.now().strftime("%Y"),)
    ).fetchone()[0]

    invoices_month = conn.execute(
        "SELECT COUNT(*) FROM sales WHERE strftime('%Y-%m',created_at)=?", (month,)
    ).fetchone()[0]

    total_products = conn.execute("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0]
    low_stock = conn.execute("SELECT COUNT(*) FROM products WHERE stock<=min_stock AND active=1").fetchone()[0]
    total_customers = conn.execute("SELECT COUNT(*) FROM customers WHERE active=1").fetchone()[0]

    # CA 12 derniers mois
    monthly_ca = []
    monthly_labels = []
    for i in range(11, -1, -1):
        d = datetime.now() - timedelta(days=i*30)
        ym = d.strftime("%Y-%m")
        ca = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM sales WHERE strftime('%Y-%m',created_at)=?", (ym,)
        ).fetchone()[0]
        monthly_ca.append(round(ca, 2))
        monthly_labels.append(d.strftime("%b"))

    # Top categories
    cat_data = conn.execute("""
        SELECT p.category, COALESCE(SUM(si.total),0) as cnt
        FROM sale_items si JOIN products p ON si.product_id=p.id
        GROUP BY p.category ORDER BY cnt DESC LIMIT 6
    """).fetchall()

    # Recent sales
    recent = conn.execute("""
        SELECT s.invoice_number, c.full_name, s.total, s.created_at, s.payment_method
        FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
        ORDER BY s.created_at DESC LIMIT 8
    """).fetchall()

    # Top customers
    top_customers = conn.execute("""
        SELECT c.full_name, COUNT(s.id) as orders, SUM(s.total) as rev
        FROM sales s JOIN customers c ON s.customer_id=c.id
        GROUP BY c.id ORDER BY rev DESC LIMIT 5
    """).fetchall()

    # Payment methods breakdown
    pmt_data = conn.execute("""
        SELECT payment_method, COUNT(*) as cnt, SUM(total) as total
        FROM sales GROUP BY payment_method
    """).fetchall()

    conn.close()
    return {
        "sales_today":    sales_today,
        "sales_month":    sales_month,
        "sales_year":     sales_year,
        "invoices_month": invoices_month,
        "total_products": total_products,
        "low_stock":      low_stock,
        "total_customers":total_customers,
        "monthly_ca":     monthly_ca,
        "monthly_labels": monthly_labels,
        "cat_data":       [dict(r) for r in cat_data],
        "recent_sales":   [dict(r) for r in recent],
        "top_customers":  [dict(r) for r in top_customers],
        "pmt_data":       [dict(r) for r in pmt_data],
    }

# ── Products ──────────────────────────────────────────────────────────────────
def get_products(active_only=True, search=""):
    conn = get_conn()
    q = "SELECT p.*, s.name as supplier_name FROM products p LEFT JOIN suppliers s ON p.supplier_id=s.id WHERE 1=1"
    params = []
    if active_only: q += " AND p.active=1"
    if search:
        q += " AND (p.name LIKE ? OR p.reference LIKE ? OR p.brand LIKE ?)"
        params += [f"%{search}%"]*3
    q += " ORDER BY p.name"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_product(data, pid=None):
    conn = get_conn()
    cols = ["reference","name","category","lens_type","index_value","coating","brand",
            "supplier_id","sph_min","sph_max","cyl_min","cyl_max",
            "purchase_price","sale_price","stock","min_stock","description","active"]
    vals = [data.get(c) for c in cols]
    if pid:
        sets = ", ".join(f"{c}=?" for c in cols)
        conn.execute(f"UPDATE products SET {sets} WHERE id=?", vals+[pid])
    else:
        ph = ",".join(["?"]*len(cols))
        conn.execute(f"INSERT INTO products({','.join(cols)}) VALUES({ph})", vals)
    conn.commit(); conn.close()

# ── Customers ─────────────────────────────────────────────────────────────────
def get_customers(search=""):
    conn = get_conn()
    q = "SELECT * FROM customers WHERE active=1"
    params = []
    if search:
        q += " AND (full_name LIKE ? OR code LIKE ? OR phone LIKE ?)"
        params = [f"%{search}%"]*3
    q += " ORDER BY full_name"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_customer(data, cid=None):
    conn = get_conn()
    cols = ["code","full_name","phone","email","address","city"]
    vals = [data.get(c,"") for c in cols]
    if cid:
        sets = ", ".join(f"{c}=?" for c in cols)
        conn.execute(f"UPDATE customers SET {sets} WHERE id=?", vals+[cid])
    else:
        ph = ",".join(["?"]*len(cols))
        conn.execute(f"INSERT INTO customers({','.join(cols)}) VALUES({ph})", vals)
    conn.commit(); conn.close()

# ── Suppliers ─────────────────────────────────────────────────────────────────
def get_suppliers():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM suppliers WHERE active=1 ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_supplier(data, sid=None):
    conn = get_conn()
    cols = ["name","contact","phone","email","address"]
    vals = [data.get(c,"") for c in cols]
    if sid:
        sets = ", ".join(f"{c}=?" for c in cols)
        conn.execute(f"UPDATE suppliers SET {sets} WHERE id=?", vals+[sid])
    else:
        ph = ",".join(["?"]*len(cols))
        conn.execute(f"INSERT INTO suppliers({','.join(cols)}) VALUES({ph})", vals)
    conn.commit(); conn.close()

# ── Sales ─────────────────────────────────────────────────────────────────────
def get_sales(limit=50, search=""):
    conn = get_conn()
    q = """SELECT s.*, c.full_name as customer_name
           FROM sales s LEFT JOIN customers c ON s.customer_id=c.id"""
    params = []
    if search:
        q += " WHERE (s.invoice_number LIKE ? OR c.full_name LIKE ?)"
        params = [f"%{search}%"]*2
    q += " ORDER BY s.created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_sale(customer_id, items, payment_method, user_id, discount=0, notes=""):
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] + 1
    inv = f"FAC-{n:05d}"
    total = sum(it["qty"]*it["price"]*(1-it.get("disc",0)/100) for it in items)
    total = round(total * (1 - discount/100), 2)
    conn.execute("""INSERT INTO sales(invoice_number,customer_id,user_id,total,discount,payment_method,notes)
                    VALUES(?,?,?,?,?,?,?)""",
                 (inv, customer_id, user_id, total, discount, payment_method, notes))
    sale_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for it in items:
        line_total = round(it["qty"]*it["price"]*(1-it.get("disc",0)/100), 2)
        conn.execute("""INSERT INTO sale_items(sale_id,product_id,quantity,unit_price,discount,total)
                        VALUES(?,?,?,?,?,?)""",
                     (sale_id, it["product_id"], it["qty"], it["price"], it.get("disc",0), line_total))
        conn.execute("UPDATE products SET stock=stock-? WHERE id=?", (it["qty"], it["product_id"]))
    conn.commit(); conn.close()
    return inv

# ── Audit ─────────────────────────────────────────────────────────────────────
def log_action(user_id, action, module, detail=""):
    conn = get_conn()
    conn.execute("INSERT INTO audit_log(user_id,action,module,detail) VALUES(?,?,?,?)",
                 (user_id, action, module, detail))
    conn.commit(); conn.close()

def get_audit_log(limit=100):
    conn = get_conn()
    rows = conn.execute("""
        SELECT a.*, u.full_name FROM audit_log a
        LEFT JOIN users u ON a.user_id=u.id
        ORDER BY a.created_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Users ─────────────────────────────────────────────────────────────────────
def get_users():
    conn = get_conn()
    rows = conn.execute("SELECT id,username,full_name,role,active,created_at FROM users ORDER BY full_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_user(data, uid=None):
    conn = get_conn()
    if uid:
        conn.execute("UPDATE users SET full_name=?,role=?,active=? WHERE id=?",
                     (data["full_name"], data["role"], data.get("active",1), uid))
        if data.get("password"):
            conn.execute("UPDATE users SET password=? WHERE id=?", (_hash(data["password"]), uid))
    else:
        conn.execute("INSERT INTO users(username,password,full_name,role) VALUES(?,?,?,?)",
                     (data["username"], _hash(data["password"]), data["full_name"], data["role"]))
    conn.commit(); conn.close()

# ── Settings ──────────────────────────────────────────────────────────────────
def get_settings():
    conn = get_conn()
    rows = conn.execute("SELECT key,value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, value))
    conn.commit(); conn.close()

# ── Reports ───────────────────────────────────────────────────────────────────
def get_sales_report(start, end):
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.invoice_number, c.full_name, s.total, s.payment_method,
               s.created_at, s.status
        FROM sales s LEFT JOIN customers c ON s.customer_id=c.id
        WHERE DATE(s.created_at) BETWEEN ? AND ?
        ORDER BY s.created_at DESC
    """, (start, end)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_stock_alerts():
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.*, s.name as supplier_name
        FROM products p LEFT JOIN suppliers s ON p.supplier_id=s.id
        WHERE p.stock <= p.min_stock AND p.active=1
        ORDER BY p.stock ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Purchases ─────────────────────────────────────────────────────────────────
def get_purchases(status=None, search=""):
    conn = get_conn()
    q = """SELECT p.*, s.name as supplier_name
           FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id"""
    params = []
    where = []
    if status:
        where.append("p.status=?"); params.append(status)
    if search:
        where.append("(p.ref LIKE ? OR s.name LIKE ?)"); params += [f"%{search}%"]*2
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY p.created_at DESC LIMIT 200"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_purchase(pid):
    conn = get_conn()
    p = conn.execute("""
        SELECT p.*, s.name as supplier_name
        FROM purchases p LEFT JOIN suppliers s ON p.supplier_id=s.id
        WHERE p.id=?""", (pid,)).fetchone()
    items = conn.execute("""
        SELECT pi.*, pr.name as product_name, pr.reference
        FROM purchase_items pi JOIN products pr ON pi.product_id=pr.id
        WHERE pi.purchase_id=?""", (pid,)).fetchall()
    conn.close()
    if not p: return None, []
    return dict(p), [dict(i) for i in items]

def create_purchase(supplier_id, items, notes, user_id, status="draft"):
    """items = [{"product_id":x, "quantity":y, "unit_price":z}]"""
    conn = get_conn()
    total = sum(it["quantity"] * it["unit_price"] for it in items)
    n = conn.execute("SELECT COUNT(*) FROM purchases").fetchone()[0] + 1
    ref = f"BC-{n:05d}"
    pid = conn.execute(
        "INSERT INTO purchases(ref,supplier_id,user_id,total,status,notes) VALUES(?,?,?,?,?,?)",
        (ref, supplier_id, user_id, total, status, notes)).lastrowid
    for it in items:
        line_total = it["quantity"] * it["unit_price"]
        conn.execute(
            "INSERT INTO purchase_items(purchase_id,product_id,quantity,unit_price,total) VALUES(?,?,?,?,?)",
            (pid, it["product_id"], it["quantity"], it["unit_price"], line_total))
    conn.commit(); conn.close()
    log_action(user_id, "Création", "Achats", f"BC {ref}")
    return ref, pid

def receive_purchase(pid, user_id):
    """Marque comme reçu et met à jour le stock."""
    conn = get_conn()
    items = conn.execute(
        "SELECT * FROM purchase_items WHERE purchase_id=?", (pid,)).fetchall()
    for it in items:
        conn.execute(
            "UPDATE products SET stock = stock + ? WHERE id=?",
            (it["quantity"], it["product_id"]))
    conn.execute("UPDATE purchases SET status='received' WHERE id=?", (pid,))
    conn.commit(); conn.close()
    log_action(user_id, "Réception", "Achats", f"Purchase #{pid}")

def update_purchase_status(pid, status, user_id):
    conn = get_conn()
    conn.execute("UPDATE purchases SET status=? WHERE id=?", (status, pid))
    conn.commit(); conn.close()
    log_action(user_id, "Statut", "Achats", f"Purchase #{pid} → {status}")

def get_purchase_stats():
    conn = get_conn()
    total_month = conn.execute("""
        SELECT COALESCE(SUM(total),0) FROM purchases
        WHERE strftime('%Y-%m', created_at)=strftime('%Y-%m','now')
        AND status='received'""").fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM purchases WHERE status IN ('draft','ordered')").fetchone()[0]
    received = conn.execute(
        "SELECT COUNT(*) FROM purchases WHERE status='received'").fetchone()[0]
    top_suppliers = conn.execute("""
        SELECT s.name, COUNT(p.id) as cnt, COALESCE(SUM(p.total),0) as total
        FROM purchases p JOIN suppliers s ON p.supplier_id=s.id
        WHERE p.status='received'
        GROUP BY s.id ORDER BY total DESC LIMIT 5
    """).fetchall()
    conn.close()
    return {
        "total_month": total_month,
        "pending": pending,
        "received": received,
        "top_suppliers": [dict(r) for r in top_suppliers],
    }
