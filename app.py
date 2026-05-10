from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("car.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Car(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        year INTEGER,
        plate_id TEXT UNIQUE,
        price REAL,
        status TEXT DEFAULT 'active',
        office TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Customer(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Reservation(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        car_id INTEGER,
        payment REAL,
        status TEXT,
        FOREIGN KEY(car_id) REFERENCES Car(id),
        FOREIGN KEY(customer_id) REFERENCES Customer(id)
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    query = request.args.get("query")
    conn = get_db()

    if query:
        cars = conn.execute("""
            SELECT * FROM Car
            WHERE plate_id LIKE ?
            OR model LIKE ?
            OR year LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    else:
        cars = conn.execute("SELECT * FROM Car").fetchall()

    customers = conn.execute("SELECT * FROM Customer").fetchall()
    conn.close()

    return render_template("index.html", cars=cars, customers=customers)

@app.route("/add_car", methods=["POST"])
def add_car():
    conn = get_db()
    conn.execute("""
    INSERT INTO Car (model, year, plate_id, price, status, office)
    VALUES (?, ?, ?, ?, 'active', ?)
    """, (
        request.form["model"],
        request.form["year"],
        request.form["plate"],
        request.form["price"],
        request.form["office"]
    ))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/add_customer", methods=["POST"])
def add_customer():
    conn = get_db()
    conn.execute("INSERT INTO Customer (name) VALUES (?)",
                 (request.form["name"],))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/reserve/<int:id>", methods=["POST"])
def reserve(id):
    conn = get_db()
    conn.execute("""
    INSERT INTO Reservation (customer_id, car_id, payment, status)
    VALUES (?, ?, ?, 'reserved')
    """, (
        request.form["customer_id"],
        id,
        request.form["payment"]
    ))

    conn.execute("UPDATE Car SET status='rented' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/return/<int:id>", methods=["POST"])
def return_car(id):
    conn = get_db()
    conn.execute("UPDATE Car SET status='active' WHERE id=?", (id,))
    conn.execute("""
    UPDATE Reservation
    SET status='returned'
    WHERE car_id=? AND status='reserved'
    """, (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/reports")
def reports():
    conn = get_db()

    reservations = conn.execute("""
    SELECT Customer.name as c_name,
           Car.model as c_model,
           Car.plate_id,
           Reservation.payment
    FROM Reservation
    JOIN Customer ON Reservation.customer_id = Customer.id
    JOIN Car ON Reservation.car_id = Car.id
    """).fetchall()

    total_payments = conn.execute(
        "SELECT SUM(payment) as total FROM Reservation"
    ).fetchone()

    car_status = conn.execute(
        "SELECT model, plate_id, status FROM Car"
    ).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        reservations=reservations,
        total=total_payments,
        car_status=car_status
    )

if __name__ == "__main__":
    app.run(debug=True)