from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "inventory_secret_key"

DATABASE = "inventory.db"


# ---------------- DATABASE ----------------

def connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():

    conn = connect()
    cur = conn.cursor()

    # USERS

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        shop_name TEXT,

        username TEXT UNIQUE,

        password TEXT

    )
    """)

    # STOCK

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        supplier TEXT,

        item TEXT,

        quantity TEXT,

        price REAL,

        date TEXT,

        time TEXT

    )
    """)

    # CUSTOMER CREDIT

    cur.execute("""
    CREATE TABLE IF NOT EXISTS customer_credit(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_name TEXT,

        contact TEXT,

        item TEXT,

        total_price REAL,

        paid REAL,

        remaining REAL,

        date TEXT,

        time TEXT

    )
    """)

    # PAYMENT HISTORY

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payment_history(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        customer_name TEXT,

        contact TEXT,

        item TEXT,

        total_price REAL,

        payment_amount REAL,

        paid REAL,

        remaining REAL,

        payment_date TEXT,

        payment_time TEXT

    )
    """)

    conn.commit()

    conn.close()


create_tables()


# ---------------- LOGIN CHECK ----------------

def login_required():

    return "user" in session


# ---------------- HOME ----------------

@app.route("/")
def home():

    return render_template("home.html")


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        shop = request.form["shop_name"]

        username = request.form["username"]

        password = request.form["password"]

        conn = connect()

        cur = conn.cursor()

        try:

            cur.execute("""

            INSERT INTO users

            (shop_name,username,password)

            VALUES(?,?,?)

            """,

            (shop, username, password))

            conn.commit()

            session["shop"] = shop

            session["user"] = username

            conn.close()

            return redirect("/dashboard")

        except:

            conn.close()

            return render_template(

                "signup.html",

                error="Username already exists."

            )

    return render_template("signup.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        conn = connect()

        cur = conn.cursor()

        cur.execute("""

        SELECT *

        FROM users

        WHERE username=?

        AND password=?

        """,

        (username, password))

        user = cur.fetchone()

        conn.close()

        if user:

            session["shop"] = user["shop_name"]

            session["user"] = user["username"]

            return redirect("/dashboard")

        return render_template(

            "login.html",

            error="Invalid Username or Password"

        )

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect("/")

    conn = connect()

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM stock")

    total_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM customer_credit")

    total_credit = cur.fetchone()[0]

    cur.execute("SELECT SUM(payment_amount) FROM payment_history")

    total_payment = cur.fetchone()[0]

    if total_payment is None:

        total_payment = 0

    cur.execute("SELECT SUM(remaining) FROM customer_credit")

    pending = cur.fetchone()[0]

    if pending is None:

        pending = 0

    conn.close()

    return render_template(

        "dashboard.html",

        shop=session["shop"],

        user=session["user"],

        total_stock=total_stock,

        total_credit=total_credit,

        total_payment=total_payment,

        pending=pending

    )

# ==========================
# STOCK MODULE STARTS HERE
# PART 2
# ==========================

# ==========================
# ADD STOCK
# ==========================

@app.route("/add_stock", methods=["GET", "POST"])
def add_stock():

    if not login_required():
        return redirect("/")

    if request.method == "POST":

        supplier = request.form["supplier"]
        item = request.form["item"]
        quantity = request.form["quantity"]      # Example: 5 kg, 2 L, 10 pcs
        price = float(request.form["price"])

        today = datetime.now()

        date = today.strftime("%d-%m-%Y")
        time = today.strftime("%I:%M %p")

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO stock
        (
            supplier,
            item,
            quantity,
            price,
            date,
            time
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            supplier,
            item,
            quantity,
            price,
            date,
            time
        ))

        conn.commit()
        conn.close()

        # Save ke baad Dashboard
        return redirect("/dashboard")

    return render_template("add_stock.html")


# ==========================
# VIEW STOCK
# ==========================

@app.route("/stock")
def stock():

    if not login_required():
        return redirect("/")

    search = request.args.get("search")

    conn = connect()
    cur = conn.cursor()

    if search:

        cur.execute("""
        SELECT *
        FROM stock
        WHERE
        supplier LIKE ?
        OR item LIKE ?
        """,
        (
            "%" + search + "%",
            "%" + search + "%"
        ))

    else:

        # Purana record upar, naya niche
        cur.execute("""
        SELECT *
        FROM stock
        ORDER BY id ASC
        """)

    data = cur.fetchall()

    conn.close()

    return render_template(
        "stock.html",
        data=data,
        search=search
    )


# ==========================
# EDIT STOCK
# ==========================

@app.route("/edit_stock/<int:id>", methods=["GET", "POST"])
def edit_stock(id):

    if not login_required():
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    if request.method == "POST":

        supplier = request.form["supplier"]
        item = request.form["item"]
        quantity = request.form["quantity"]
        price = float(request.form["price"])

        cur.execute("""
        UPDATE stock
        SET
        supplier=?,
        item=?,
        quantity=?,
        price=?
        WHERE id=?
        """,
        (
            supplier,
            item,
            quantity,
            price,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/stock")

    cur.execute(
        "SELECT * FROM stock WHERE id=?",
        (id,)
    )

    stock = cur.fetchone()

    conn.close()

    return render_template(
        "edit_stock.html",
        stock=stock
    )
    
    # ==========================
# DELETE STOCK
# ==========================

@app.route("/delete_stock/<int:id>")
def delete_stock(id):

    if not login_required():
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM stock WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/stock")


# ==========================
# ADD CUSTOMER CREDIT
# ==========================

@app.route("/add_credit", methods=["GET", "POST"])
def add_credit():

    if not login_required():
        return redirect("/")

    if request.method == "POST":

        customer = request.form["customer_name"]
        contact = request.form["contact"]
        item = request.form["item"]

        total = float(request.form["total_price"])
        paid = float(request.form["paid"])

        remaining = total - paid

        if remaining < 0:
            remaining = 0

        now = datetime.now()

        date = now.strftime("%d-%m-%Y")
        time = now.strftime("%I:%M %p")

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO customer_credit
        (
            customer_name,
            contact,
            item,
            total_price,
            paid,
            remaining,
            date,
            time
        )
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            customer,
            contact,
            item,
            total,
            paid,
            remaining,
            date,
            time
        ))

        conn.commit()
        conn.close()

        # Save ke baad Dashboard
        return redirect("/dashboard")

    return render_template("add_credit.html")


# ==========================
# VIEW CUSTOMER CREDIT
# ==========================

@app.route("/customer_credit")
def customer_credit():

    if not login_required():
        return redirect("/")

    search = request.args.get("search")

    conn = connect()
    cur = conn.cursor()

    if search:

        cur.execute("""
        SELECT *
        FROM customer_credit
        WHERE
        customer_name LIKE ?
        OR contact LIKE ?
        OR item LIKE ?
        ORDER BY id ASC
        """,
        (
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        ))

    else:

        cur.execute("""
        SELECT *
        FROM customer_credit
        ORDER BY id ASC
        """)

    data = cur.fetchall()

    conn.close()

    return render_template(
        "customer_credit.html",
        data=data,
        search=search
    )
    
    # ==========================
# EDIT CUSTOMER CREDIT
# ==========================

@app.route("/edit_credit/<int:id>", methods=["GET", "POST"])
def edit_credit(id):

    if not login_required():
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    if request.method == "POST":

        customer = request.form["customer_name"]
        contact = request.form["contact"]
        item = request.form["item"]

        total = float(request.form["total_price"])
        paid = float(request.form["paid"])

        remaining = total - paid

        if remaining < 0:
            remaining = 0

        cur.execute("""
        UPDATE customer_credit
        SET
        customer_name=?,
        contact=?,
        item=?,
        total_price=?,
        paid=?,
        remaining=?
        WHERE id=?
        """,
        (
            customer,
            contact,
            item,
            total,
            paid,
            remaining,
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/customer_credit")

    cur.execute(
        "SELECT * FROM customer_credit WHERE id=?",
        (id,)
    )

    credit = cur.fetchone()

    conn.close()

    return render_template(
        "edit_credit.html",
        credit=credit
    )


# ==========================
# DELETE CUSTOMER CREDIT
# ==========================

@app.route("/delete_credit/<int:id>")
def delete_credit(id):

    if not login_required():
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM customer_credit WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/customer_credit")


# ==========================
# PAYMENT
# ==========================

@app.route("/payment/<int:id>", methods=["GET", "POST"])
def payment(id):

    if not login_required():
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM customer_credit WHERE id=?",
        (id,)
    )

    customer = cur.fetchone()

    if request.method == "POST":

        payment_amount = float(request.form["payment_amount"])

        new_paid = customer["paid"] + payment_amount
        new_remaining = customer["remaining"] - payment_amount

        if new_remaining < 0:
            new_remaining = 0
            payment_amount = customer["remaining"]
            new_paid = customer["total_price"]

        cur.execute("""
        UPDATE customer_credit
        SET
        paid=?,
        remaining=?
        WHERE id=?
        """,
        (
            new_paid,
            new_remaining,
            id
        ))
        
                # -------- SAVE PAYMENT HISTORY --------

        now = datetime.now()

        payment_date = now.strftime("%d-%m-%Y")
        payment_time = now.strftime("%I:%M %p")

        cur.execute("""
        INSERT INTO payment_history
        (
            customer_name,
            contact,
            item,
            total_price,
            payment_amount,
            paid,
            remaining,
            payment_date,
            payment_time
        )
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            customer["customer_name"],
            customer["contact"],
            customer["item"],
            customer["total_price"],
            payment_amount,
            new_paid,
            new_remaining,
            payment_date,
            payment_time
        ))

        conn.commit()
        conn.close()

        return redirect("/customer_credit")

    conn.close()

    return render_template(
        "payment.html",
        customer=customer
    )


# ==========================
# PAYMENT HISTORY
# ==========================

@app.route("/history")
def history():

    if not login_required():
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM payment_history
    ORDER BY id ASC
    """)

    data = cur.fetchall()

    conn.close()

    return render_template(
        "history.html",
        data=data
    )
@app.route("/delete_history/<int:id>")
def delete_history(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("inventory.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM payment_history WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/history")


# ==========================
# RUN APP
# ==========================

if __name__ == "__main__":

    app.run(
        debug=True
    )