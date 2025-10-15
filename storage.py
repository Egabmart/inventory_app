import sqlite3, os, uuid, shutil, mimetypes
from pathlib import Path
from typing import Optional
from .models import Department, SubDepartment, Product, Local

DB_PATH = os.path.join(os.path.expanduser("~"), ".pyqt_inventory_app.sqlite3")
_MEDIA_ROOT = Path.home() / ".pyqt_inventory_app_media" / "products"
_ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS departments(
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbreviation TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL
    )""" )
    cur.execute("""CREATE TABLE IF NOT EXISTS subdepartments(
        sub_id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_dept_id INTEGER NOT NULL,
        abbreviation TEXT NOT NULL,
        name TEXT NOT NULL,
        UNIQUE(parent_dept_id, abbreviation),
        FOREIGN KEY(parent_dept_id) REFERENCES departments(dept_id) ON DELETE CASCADE
    )""" )
    cur.execute("""CREATE TABLE IF NOT EXISTS products(
        prod_id TEXT PRIMARY KEY,
        parent_sub_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY(parent_sub_id) REFERENCES subdepartments(sub_id) ON DELETE CASCADE
    )""" )
    cur.execute("""CREATE TABLE IF NOT EXISTS locals(
        local_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        retail_rate REAL NOT NULL DEFAULT 0
    )""" )
    cur.execute("""CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""" )
    cur.execute("""CREATE TABLE IF NOT EXISTS product_images(
        image_id TEXT PRIMARY KEY,
        prod_id TEXT NOT NULL,
        rel_path TEXT NOT NULL,
        mime_type TEXT,
        is_primary INTEGER NOT NULL DEFAULT 0,
        sort_order INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(prod_id) REFERENCES products(prod_id) ON DELETE CASCADE
    )""" )
    cur.execute("""CREATE TABLE IF NOT EXISTS local_products(
        local_id INTEGER NOT NULL,
        prod_id TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(local_id, prod_id),
        FOREIGN KEY(local_id) REFERENCES locals(local_id) ON DELETE CASCADE,
        FOREIGN KEY(prod_id) REFERENCES products(prod_id) ON DELETE CASCADE
    )""" )
    cur.execute("""CREATE TABLE IF NOT EXISTS sold_products(
        sale_id TEXT PRIMARY KEY,
        prod_id TEXT NOT NULL,
        qty INTEGER NOT NULL,
        location_type TEXT NOT NULL,
        local_id INTEGER,
        sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(prod_id) REFERENCES products(prod_id) ON DELETE CASCADE,
        FOREIGN KEY(local_id) REFERENCES locals(local_id) ON DELETE SET NULL
    )""" )
    conn.commit(); conn.close()

def _get_setting(key: str) -> Optional[str]:
    conn = get_conn(); row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close(); return row[0] if row else None

def _set_setting(key: str, value: str) -> None:
    conn = get_conn()
    conn.execute("""INSERT INTO settings(key,value) VALUES(?,?)
                  ON CONFLICT(key) DO UPDATE SET value=excluded.value""", (key, value))
    conn.commit(); conn.close()

def get_conversion_rate(default: float = 36.62) -> float:
    v = _get_setting("conversion_rate")
    if v is None:
        _set_setting("conversion_rate", str(default)); return default
    try: return float(v)
    except: return default

def set_conversion_rate(rate: float) -> None:
    _set_setting("conversion_rate", str(rate))

def get_local_retail_rate(local: Local, default: float = 0.0) -> float:
    conn = get_conn(); row = conn.execute("SELECT retail_rate FROM locals WHERE local_id=?", (local.local_id,)).fetchone()
    conn.close()
    if not row: return default
    try: return float(row[0])
    except: return default

def set_local_retail_rate(local: Local, rate: float) -> None:
    conn = get_conn(); conn.execute("UPDATE locals SET retail_rate=? WHERE local_id=?", (float(rate), local.local_id))
    conn.commit(); conn.close()

def list_departments():
    conn = get_conn(); rows = conn.execute("SELECT dept_id, abbreviation, name FROM departments ORDER BY name").fetchall()
    conn.close(); return [Department(*r) for r in rows]

def add_department(abbrev: str, name: str) -> Department:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO departments(abbreviation,name) VALUES(?,?)", (abbrev, name))
    dept_id = cur.lastrowid; conn.commit(); conn.close()
    return Department(dept_id, abbrev, name)

def rename_department(dept: Department, new_name: str):
    conn = get_conn(); conn.execute("UPDATE departments SET name=? WHERE dept_id=?", (new_name, dept.dept_id)); conn.commit(); conn.close()

def delete_department_if_empty(dept: Department) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) FROM subdepartments WHERE parent_dept_id=?", (dept.dept_id,)).fetchone()
    if row and row[0]==0:
        conn.execute("DELETE FROM departments WHERE dept_id=?", (dept.dept_id,)); conn.commit(); conn.close(); return True
    conn.close(); return False

def list_subdepartments(dept: Department):
    conn = get_conn()
    rows = conn.execute("""SELECT sub_id, abbreviation, name FROM subdepartments WHERE parent_dept_id=? ORDER BY name""", (dept.dept_id,)).fetchall()
    conn.close(); return [SubDepartment(r[0], dept, r[1], r[2]) for r in rows]

def add_subdepartment(dept: Department, abbrev: str, name: str) -> SubDepartment:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO subdepartments(parent_dept_id,abbreviation,name) VALUES(?,?,?)", (dept.dept_id, abbrev, name))
    sub_id = cur.lastrowid; conn.commit(); conn.close()
    return SubDepartment(sub_id, dept, abbrev, name)

def rename_subdepartment(sub: SubDepartment, new_name: str):
    conn = get_conn(); conn.execute("UPDATE subdepartments SET name=? WHERE sub_id=?", (new_name, sub.sub_id)); conn.commit(); conn.close()

def delete_subdepartment_if_empty(sub: SubDepartment) -> bool:
    conn = get_conn(); row = conn.execute("SELECT COUNT(*) FROM products WHERE parent_sub_id=?", (sub.sub_id,)).fetchone()
    if row and row[0]==0:
        conn.execute("DELETE FROM subdepartments WHERE sub_id=?", (sub.sub_id,)); conn.commit(); conn.close(); return True
    conn.close(); return False

def list_products(sub: SubDepartment):
    conn = get_conn()
    rows = conn.execute("""SELECT prod_id, name, description, price, quantity FROM products WHERE parent_sub_id=? ORDER BY name""", (sub.sub_id,)).fetchall()
    conn.close(); return [Product(r[0], sub, r[1], r[2], float(r[3]), int(r[4])) for r in rows]

def add_product(product: Product):
    conn = get_conn()
    conn.execute("""INSERT INTO products(prod_id,parent_sub_id,name,description,price,quantity)
                  VALUES(?,?,?,?,?,?)""", (product.prod_id, product.parent.sub_id, product.name, product.description, float(product.price), int(product.quantity)))
    conn.commit(); conn.close()

def update_product(product: Product):
    conn = get_conn()
    conn.execute("""UPDATE products SET name=?, description=?, price=?, quantity=? WHERE prod_id=?""" ,
                 (product.name, product.description, float(product.price), int(product.quantity), product.prod_id))
    conn.commit(); conn.close()

def delete_product(product: Product):
    conn = get_conn(); conn.execute("DELETE FROM products WHERE prod_id=?", (product.prod_id,)); conn.commit(); conn.close()

def count_products(sub: SubDepartment) -> int:
    conn = get_conn(); row = conn.execute("SELECT COUNT(*) FROM products WHERE parent_sub_id=?", (sub.sub_id,)).fetchone()
    conn.close(); return int(row[0] or 0)

def list_locals():
    conn = get_conn(); rows = conn.execute("SELECT local_id, name FROM locals ORDER BY name").fetchall()
    conn.close(); return [Local(*r) for r in rows]

def add_local(name: str) -> Local:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO locals(name) VALUES(?)", (name,))
    local_id = cur.lastrowid; conn.commit(); conn.close()
    return Local(local_id, name)

def delete_local(local: Local):
    conn = get_conn(); conn.execute("DELETE FROM locals WHERE local_id=?", (local.local_id,)); conn.commit(); conn.close()

def count_local_products(local: Local) -> int:
    conn = get_conn(); row = conn.execute("SELECT COUNT(*) FROM local_products WHERE local_id=?", (local.local_id,)).fetchone()
    conn.close(); return int(row[0] or 0)

def generate_next_product_id(sub: SubDepartment) -> str:
    conn = get_conn()
    row = conn.execute("""SELECT d.abbreviation, s.abbreviation
                         FROM subdepartments s JOIN departments d ON d.dept_id=s.parent_dept_id
                         WHERE s.sub_id=?""", (sub.sub_id,)).fetchone()
    if not row:
        conn.close(); raise ValueError("Subdepartment not found")
    d_abbr, s_abbr = row[0], row[1]
    row = conn.execute("SELECT COUNT(*) FROM products WHERE parent_sub_id=?", (sub.sub_id,)).fetchone()
    order = int(row[0]) + 1; conn.close()
    return f"{d_abbr}{s_abbr}{order}"

def _ensure_media_dir(prod_id: str) -> Path:
    d = _MEDIA_ROOT / prod_id; d.mkdir(parents=True, exist_ok=True); return d

def add_product_images(prod: Product, src_paths):
    if not src_paths: return []
    dest_dir = _ensure_media_dir(prod.prod_id); rels = []
    conn = get_conn()
    try:
        for p in src_paths:
            sp = Path(p)
            if not sp.exists() or not sp.is_file(): continue
            ext = sp.suffix.lower()
            if ext not in _ALLOWED_EXT: continue
            fname = f"{uuid.uuid4().hex}{ext}"; dp = dest_dir / fname
            try: shutil.copy2(sp, dp)
            except Exception: continue
            rel_path = str(Path(prod.prod_id) / fname); mime, _ = mimetypes.guess_type(str(dp))
            conn.execute("INSERT INTO product_images(image_id, prod_id, rel_path, mime_type) VALUES(?,?,?,?)",
                         (uuid.uuid4().hex, prod.prod_id, rel_path, mime or ""))
            rels.append(rel_path)
        conn.commit()
    finally:
        conn.close()
    return rels

def list_product_images(prod: Product):
    conn = get_conn()
    rows = conn.execute("""SELECT rel_path, image_id, is_primary FROM product_images WHERE prod_id=?
                          ORDER BY COALESCE(sort_order,999999), created_at""", (prod.prod_id,)).fetchall()
    conn.close(); return [{"rel_path": r[0], "image_id": r[1], "is_primary": int(r[2])} for r in rows]

def get_image_abspath(rel_path: str) -> Path:
    return _MEDIA_ROOT / rel_path

def delete_product_image(image_id: str) -> None:
    conn = get_conn(); conn.execute("DELETE FROM product_images WHERE image_id=?", (image_id,)); conn.commit(); conn.close()

def get_product_total_quantity(product) -> int:
    prod_id = product.prod_id if hasattr(product, "prod_id") else str(product)
    conn = get_conn(); row = conn.execute("SELECT quantity FROM products WHERE prod_id=?", (prod_id,)).fetchone()
    conn.close(); return int(row[0]) if row else 0

def get_allocated_qty_for_product(product) -> int:
    prod_id = product.prod_id if hasattr(product, "prod_id") else str(product)
    conn = get_conn(); row = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM local_products WHERE prod_id=?", (prod_id,)).fetchone()
    conn.close(); return int(row[0] or 0)

def add_product_to_local(local: Local, product: Product, qty: int) -> None:
    qty = int(qty)
    if qty <= 0: return
    conn = get_conn(); cur = conn.cursor()
    row = cur.execute("SELECT quantity FROM local_products WHERE local_id=? AND prod_id=?", (local.local_id, product.prod_id)).fetchone()
    if row:
        new_q = int(row[0]) + qty
        cur.execute("UPDATE local_products SET quantity=? WHERE local_id=? AND prod_id=?", (new_q, local.local_id, product.prod_id))
    else:
        cur.execute("INSERT INTO local_products(local_id, prod_id, quantity) VALUES(?,?,?)", (local.local_id, product.prod_id, qty))
    conn.commit(); conn.close()

def remove_product_from_local(local: Local, product: Product) -> None:
    conn = get_conn(); conn.execute("DELETE FROM local_products WHERE local_id=? AND prod_id=?", (local.local_id, product.prod_id))
    conn.commit(); conn.close()

def list_products_for_local(local: Local):
    conn = get_conn()
    rows = conn.execute("""
        SELECT p.prod_id, p.name, p.description, p.price, p.quantity AS total_qty,
               lp.quantity AS local_qty,
               s.sub_id, s.parent_dept_id, s.abbreviation, s.name,
               d.dept_id, d.abbreviation, d.name
        FROM local_products lp
        JOIN products p ON p.prod_id = lp.prod_id
        JOIN subdepartments s ON s.sub_id = p.parent_sub_id
        JOIN departments d ON d.dept_id = s.parent_dept_id
        WHERE lp.local_id = ?
        ORDER BY p.name COLLATE NOCASE
    """, (local.local_id,)).fetchall()
    conn.close()
    out = []
    for r in rows:
        dept = Department(r[10], r[11], r[12]); sub = SubDepartment(r[6], dept, r[8], r[9])
        prod = Product(r[0], sub, r[1], r[2], float(r[3]), int(r[5]))
        try: prod.total_quantity = int(r[4])
        except: pass
        out.append(prod)
    return out

def get_product_by_id(prod_code: str):
    conn = get_conn()
    row = conn.execute("""
        SELECT p.prod_id, p.parent_sub_id, p.name, p.description, p.price, p.quantity,
               s.sub_id, s.parent_dept_id, s.abbreviation, s.name,
               d.dept_id, d.abbreviation, d.name
        FROM products p
        JOIN subdepartments s ON s.sub_id = p.parent_sub_id
        JOIN departments d ON d.dept_id = s.parent_dept_id
        WHERE UPPER(p.prod_id) = UPPER(?)
    """, (prod_code,)).fetchone()
    if not row: conn.close(); return None
    dept = Department(row[10], row[11], row[12]); sub = SubDepartment(row[6], dept, row[8], row[9])
    prod = Product(row[0], sub, row[2], row[3], float(row[4]), int(row[5]))
    conn.close(); return prod

def register_sale(prod: Product, qty: int, location_type: str, local: Local|None) -> bool:
    total = get_product_total_quantity(prod)
    if qty <= 0 or qty > total: return False
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE products SET quantity = quantity - ? WHERE prod_id = ?", (qty, prod.prod_id))
    if location_type == "local" and local is not None:
        row = cur.execute("SELECT quantity FROM local_products WHERE local_id=? AND prod_id=?", (local.local_id, prod.prod_id)).fetchone()
        allocated = int(row[0]) if row else 0
        if allocated < qty:
            conn.rollback(); conn.close(); return False
        cur.execute("UPDATE local_products SET quantity = quantity - ? WHERE local_id=? AND prod_id=?", (qty, local.local_id, prod.prod_id))
        cur.execute("DELETE FROM local_products WHERE local_id=? AND prod_id=? AND quantity <= 0", (local.local_id, prod.prod_id))
    cur.execute("""INSERT INTO sold_products(sale_id, prod_id, qty, location_type, local_id)
                  VALUES(?,?,?,?,?)""", (uuid.uuid4().hex, prod.prod_id, qty, location_type, local.local_id if local else None))
    conn.commit(); conn.close(); return True
