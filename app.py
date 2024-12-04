from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
import sqlite3
import json
import os
from datetime import datetime

app = Flask(__name__, template_folder="templates")


@app.route("/")
def root():
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        cursor.execute('SELECT "Sale" AS type, datetime(date), total_sale FROM sales ORDER BY id DESC LIMIT 5')
        sales_activity = cursor.fetchall()
        print("Sales Activity:", sales_activity)

        cursor.execute('SELECT "Online Sale" AS type, datetime(sale_date), sale_amount FROM online_sales ORDER BY id DESC LIMIT 5')
        online_sales_activity = cursor.fetchall()
        print("Online Sales Activity:", online_sales_activity)

        cursor.execute('SELECT "Employee" AS type, datetime("now"), name || " Hired" AS action FROM employees ORDER BY id DESC LIMIT 5')
        employees_activity = cursor.fetchall()
        print("Employees Activity:", employees_activity)

        recent_activity = sales_activity + online_sales_activity + employees_activity
        recent_activity = [activity for activity in recent_activity if activity[1] is not None]
        recent_activity.sort(key=lambda x: x[1], reverse=True)
        conn.close()

        return render_template("welcome.html", recent_activity=recent_activity)
    except Exception as e:
        return f"Error: {e}", 500



@app.route("/clock_in/<int:employee_id>", methods=["POST"])
def clock_in(employee_id):
    try:
        date_today = datetime.now().strftime("%Y-%m-%d")
        clock_in_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Check if already clocked in today
        cursor.execute("""
            SELECT id FROM employee_attendance
            WHERE employee_id = ? AND date = ? AND clock_out_time IS NULL
        """, (employee_id, date_today))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Already clocked in today."})

        # Record clock-in time
        cursor.execute("""
            INSERT INTO employee_attendance (employee_id, clock_in_time, date)
            VALUES (?, ?, ?)
        """, (employee_id, clock_in_time, date_today))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Clocked in successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})




@app.route("/clock_out/<int:employee_id>", methods=["POST"])
def clock_out(employee_id):
    try:
        clock_out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Check if there is an open clock-in entry
        cursor.execute("""
            SELECT id FROM employee_attendance
            WHERE employee_id = ? AND clock_out_time IS NULL
        """, (employee_id,))
        attendance = cursor.fetchone()

        if not attendance:
            return jsonify({"success": False, "message": "No open clock-in entry found."})

        # Record clock-out time
        cursor.execute("""
            UPDATE employee_attendance
            SET clock_out_time = ?
            WHERE id = ?
        """, (clock_out_time, attendance[0]))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Clocked out successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})





@app.route("/add_sale", methods=["GET", "POST"])
def add_new_sale():
    if request.method == "POST":
        try:
            # Debug: Log form submission
            print("Form submitted. Data received:", request.form)

            # Get data from the form
            date = request.form.get("date")
            cash_sale = float(request.form.get("cash_sale"))
            card_sale = float(request.form.get("card_sale"))
            tips = float(request.form.get("tips"))
            tax = float(request.form.get("tax"))
            expense = float(request.form.get("expense"))

            # Calculate total sale and profit
            total_sale = cash_sale + card_sale
            profit = total_sale + tips - tax - expense

            # Insert data into the database
            conn = sqlite3.connect("sales.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sales (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit))
            conn.commit()
            conn.close()

            # Debug: Log successful database insertion
            print("Data inserted successfully. Redirecting to /view_sales")

            # Redirect to the View Sales page
            return redirect(url_for("view_sales"))
        except Exception as e:
            print(f"Error occurred: {e}")
            return f"Error: {e}", 500

    # Render the Add Sale form
    return render_template("add_sale.html")





@app.route("/view_sales", methods=["GET"])
def view_sales():
    try:
        # Connect to the database
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Fetch all sales data
        cursor.execute("""
            SELECT id, date, total_sale, cash_sale, card_sale, tips, tax, expense, profit
            FROM sales
            ORDER BY id DESC
        """)
        sales = cursor.fetchall()

        # Calculate total sales and profit
        cursor.execute("SELECT SUM(total_sale), SUM(profit) FROM sales")
        stats = cursor.fetchone()
        total_sales = stats[0] if stats[0] else 0.0
        total_profit = stats[1] if stats[1] else 0.0

        conn.close()

        # Render the template with sales data and stats
        return render_template("view_sales.html", sales=sales, total_sales=total_sales, total_profit=total_profit)
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/edit_sale/<int:sale_id>", methods=["GET", "POST"])
def edit_sale(sale_id):
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()

    if request.method == "POST":
        sale_date = request.form.get("sale_date")
        total_sale = request.form.get("total_sale")
        cursor.execute("UPDATE sales SET date = ?, total_sale = ? WHERE id = ?", (sale_date, total_sale, sale_id))
        conn.commit()
        conn.close()
        return redirect(url_for("view_sales"))

    cursor.execute("SELECT date, total_sale FROM sales WHERE id = ?", (sale_id,))
    sale = cursor.fetchone()
    conn.close()
    return render_template("edit_sale.html", sale=sale, sale_id=sale_id)

@app.route("/delete_sale/<int:sale_id>", methods=["POST"])
def delete_sale(sale_id):
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_sales"))

@app.route("/report", methods=["GET"])
def report():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y-%m', date) AS month, SUM(total_sale) AS total_sales
        FROM sales
        GROUP BY month
        ORDER BY month DESC
    """)
    reports = cursor.fetchall()
    conn.close()
    return render_template("report.html", reports=reports)

@app.route("/employees", methods=["GET"])
def employees():
    try:
        # Connect to the database and fetch employee data
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, designation FROM employees")
        employees = cursor.fetchall()
        conn.close()

        # Render the employees template with the fetched data
        return render_template("employees.html", employees=employees)
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/salary_details/<int:employee_id>")
def salary_details(employee_id):
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Fetch basic employee details
        cursor.execute("""
            SELECT id, name, designation, salary
            FROM employees
            WHERE id = ?
        """, (employee_id,))
        employee = cursor.fetchone()

        # Fetch salary details for the employee
        cursor.execute("""
            SELECT date, amount, method
            FROM employee_salary
            WHERE employee_id = ?
            ORDER BY date DESC
        """, (employee_id,))
        salary_records = cursor.fetchall()

        conn.close()

        return render_template(
            "salary_details.html",
            employee=employee,
            salary_records=salary_records
        )
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Handle deletion of attendance record
        if request.method == "POST" and "delete_id" in request.form:
            delete_id = request.form.get("delete_id")
            cursor.execute("DELETE FROM employee_attendance WHERE id = ?", (delete_id,))
            conn.commit()

        # Fetch attendance data
        cursor.execute("""
            SELECT a.id, a.employee_id, e.name, a.date, a.clock_in_time, a.clock_out_time
            FROM employee_attendance a
            JOIN employees e ON a.employee_id = e.id
            ORDER BY a.date DESC, a.clock_in_time ASC
        """)
        attendance_data = cursor.fetchall()

        # Calculate total hours worked per employee
        cursor.execute("""
            SELECT e.id, e.name, 
                   SUM((julianday(a.clock_out_time) - julianday(a.clock_in_time)) * 24) AS total_hours
            FROM employee_attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE a.clock_out_time IS NOT NULL
            GROUP BY e.id, e.name
        """)
        total_hours_data = cursor.fetchall()

        conn.close()

        return render_template(
            "attendance.html",
            attendance=attendance_data,
            total_hours=total_hours_data
        )
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/edit_attendance/<int:attendance_id>", methods=["GET", "POST"])
def edit_attendance(attendance_id):
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        if request.method == "POST":
            # Update attendance record
            date = request.form.get("date")
            clock_in_time = request.form.get("clock_in_time")
            clock_out_time = request.form.get("clock_out_time")

            cursor.execute("""
                UPDATE employee_attendance
                SET date = ?, clock_in_time = ?, clock_out_time = ?
                WHERE id = ?
            """, (date, clock_in_time, clock_out_time, attendance_id))
            conn.commit()
            conn.close()

            return redirect(url_for("attendance"))

        # Fetch the attendance record
        cursor.execute("SELECT id, date, clock_in_time, clock_out_time FROM employee_attendance WHERE id = ?", (attendance_id,))
        record = cursor.fetchone()
        conn.close()

        return render_template("edit_attendance.html", record=record)
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/summary", methods=["GET"])
def summary():
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Fetch daily summaries
        cursor.execute("""
            SELECT date, SUM(total_sale), SUM(tips), SUM(tax), SUM(expense), SUM(profit)
            FROM sales
            GROUP BY date
            ORDER BY date DESC
        """)
        daily_summaries = cursor.fetchall()

        # Calculate daily totals
        cursor.execute("""
            SELECT SUM(total_sale), SUM(tips), SUM(tax), SUM(expense), SUM(profit)
            FROM sales
        """)
        daily_totals = cursor.fetchone()

        # Fetch monthly summaries
        cursor.execute("""
            SELECT strftime('%Y-%m', date) AS month, SUM(total_sale), SUM(tips), SUM(tax), SUM(expense), SUM(profit)
            FROM sales
            GROUP BY month
            ORDER BY month DESC
        """)
        monthly_summaries = cursor.fetchall()

        # Calculate monthly totals
        cursor.execute("""
            SELECT SUM(total_sale), SUM(tips), SUM(tax), SUM(expense), SUM(profit)
            FROM sales
        """)
        monthly_totals = cursor.fetchone()

        # Fetch total online sales
        cursor.execute("SELECT SUM(sale_amount) FROM online_sales")
        total_online_sales = cursor.fetchone()[0] or 0.0

        # Fetch total expenses from sales and other sources
        cursor.execute("""
            SELECT SUM(expense) FROM sales
        """)
        total_sales_expenses = cursor.fetchone()[0] or 0.0

        # Fetch total other expenses
        try:
            cursor.execute("""
                SELECT SUM(amount) FROM other_expenses
            """)
            total_other_expenses = cursor.fetchone()[0] or 0.0
        except sqlite3.OperationalError:
            # Handle missing other_expenses table
            total_other_expenses = 0.0

        total_expenses = total_sales_expenses + total_other_expenses

        # Integrate online sales into overall totals
        overall_total_sales = (daily_totals[0] or 0.0) + total_online_sales
        overall_total_profit = overall_total_sales - total_expenses

        conn.close()

        # Render the summary page
        return render_template(
            "summary.html",
            daily_summaries=daily_summaries,
            daily_totals={
                "sales": daily_totals[0] or 0.0,
                "tips": daily_totals[1] or 0.0,
                "tax": daily_totals[2] or 0.0,
                "expenses": daily_totals[3] or 0.0,
                "profit": daily_totals[4] or 0.0
            },
            monthly_summaries=monthly_summaries,
            monthly_totals={
                "sales": monthly_totals[0] or 0.0,
                "tips": monthly_totals[1] or 0.0,
                "tax": monthly_totals[2] or 0.0,
                "expenses": monthly_totals[3] or 0.0,
                "profit": monthly_totals[4] or 0.0
            },
            total_online_sales=total_online_sales,
            overall_totals={
                "sales": overall_total_sales,
                "expenses": total_expenses,
                "profit": overall_total_profit
            }
        )
    except Exception as e:
        return f"Error: {e}", 500




@app.route("/online_sale", methods=["GET", "POST"])
def online_sale():
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        if request.method == "POST":
            # Add a new online sale
            platform = request.form.get("platform")
            sale_amount = float(request.form.get("sale_amount"))
            sale_date = request.form.get("sale_date")

            cursor.execute("""
                INSERT INTO online_sales (platform, sale_amount, sale_date)
                VALUES (?, ?, ?)
            """, (platform, sale_amount, sale_date))
            conn.commit()

        # Fetch all online sales
        cursor.execute("""
            SELECT id, platform, sale_amount, sale_date
            FROM online_sales
            ORDER BY sale_date DESC
        """)
        online_sales = cursor.fetchall()

        # Calculate total online sales
        cursor.execute("SELECT SUM(sale_amount) FROM online_sales")
        total_online_sales = cursor.fetchone()[0] or 0.0

        conn.close()

        return render_template(
            "online_sale.html",
            online_sales=online_sales,
            total_online_sales=total_online_sales
        )
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/delete_online_sale/<int:sale_id>", methods=["POST"])
def delete_online_sale(sale_id):
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM online_sales WHERE id = ?", (sale_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("online_sale"))
    except Exception as e:
        return f"Error: {e}", 500
@app.route("/pay_employee/<int:employee_id>", methods=["POST"])
def pay_employee(employee_id):
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Mark clock entries as inactive
        cursor.execute("""
            UPDATE employee_attendance
            SET active = 0
            WHERE employee_id = ? AND active = 1
        """, (employee_id,))

        # Log the pay cycle
        paid_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO pay_cycles (employee_id, start_date, end_date, paid_date)
            VALUES (
                ?, 
                (SELECT MIN(date) FROM employee_attendance WHERE employee_id = ? AND active = 0),
                (SELECT MAX(date) FROM employee_attendance WHERE employee_id = ? AND active = 0),
                ?
            )
        """, (employee_id, employee_id, employee_id, paid_date))

        conn.commit()
        conn.close()

        # Redirect to the employee list with a success message
        return redirect(url_for("employees", message="Employee paid successfully!"))
    except Exception as e:
        # Redirect with an error message
        return redirect(url_for("employees", message=f"Error: {str(e)}"))


@app.route("/restart_clock/<int:employee_id>", methods=["POST"])
def restart_clock(employee_id):
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Restart clock entries by setting active back to 1
        cursor.execute("""
            UPDATE employee_attendance
            SET active = 1
            WHERE employee_id = ? AND active = 0
        """, (employee_id,))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Clock restarted for employee."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/add_salary/<int:employee_id>", methods=["POST", "GET"])
def add_salary(employee_id):
    if request.method == "GET":
        # Render a page to input salary details
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, designation FROM employees WHERE id = ?", (employee_id,))
        employee = cursor.fetchone()
        conn.close()
        return render_template("add_salary.html", employee=employee)
    elif request.method == "POST":
        try:
            # Add salary and stop the clock
            salary_date = request.form.get("salary_date")
            salary_amount = request.form.get("salary_amount")
            payment_method = request.form.get("payment_method")

            conn = sqlite3.connect("sales.db")
            cursor = conn.cursor()

            # Insert salary into a salary table (if not already created, create it first)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employee_salary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER,
                    date TEXT,
                    amount REAL,
                    method TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)
            cursor.execute("""
                INSERT INTO employee_salary (employee_id, date, amount, method)
                VALUES (?, ?, ?, ?)
            """, (employee_id, salary_date, salary_amount, payment_method))

            # Stop the clock for the employee
            cursor.execute("""
                UPDATE employee_attendance
                SET active = 0
                WHERE employee_id = ? AND active = 1
            """, (employee_id,))

            conn.commit()
            conn.close()

            return redirect(url_for("employees", message="Salary added and clock stopped successfully!"))
        except Exception as e:
            return redirect(url_for("employees", message=f"Error: {str(e)}"))

import csv
from flask import Response

@app.route("/export_sales", methods=["GET"])
def export_sales():
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Fetch all valid sales data
        cursor.execute("""
            SELECT id, date, total_sale, cash_sale, card_sale, tips, tax, expense, profit
            FROM sales
            WHERE total_sale > 0
        """)
        sales = cursor.fetchall()
        conn.close()

        # Create CSV in memory
        output = []
        header = ["Sale ID", "Date", "Total Sale", "Cash Sale", "Card Sale", "Tips", "Tax", "Expense", "Profit"]
        output.append(header)

        for sale in sales:
            # Format the date dynamically based on its structure
            try:
                if " " in sale[1]:  # Date includes time
                    formatted_date = datetime.strptime(sale[1], "%Y-%m-%d %H:%M:%S").strftime("%m/%d/%Y")
                else:  # Date without time
                    formatted_date = datetime.strptime(sale[1], "%Y-%m-%d").strftime("%m/%d/%Y")
            except Exception as e:
                formatted_date = sale[1]  # If formatting fails, use the raw value

            row = (sale[0], formatted_date, *sale[2:])
            output.append(row)

        # Convert list to CSV format
        def generate_csv():
            for row in output:
                yield ','.join(map(str, row)) + '\n'

        # Create response with CSV data
        response = Response(generate_csv(), mimetype="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=sales.csv"
        return response

    except Exception as e:
        return f"Error: {e}", 500

@app.route("/expense_management", methods=["GET", "POST"])
def expense_management():
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        if request.method == "POST":
            # Retrieve form data
            description = request.form.get("description")
            amount = request.form.get("amount")
            expense_date = request.form.get("expense_date")
            category = request.form.get("category")

            # Ensure table has the correct schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS other_expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    description TEXT,
                    category TEXT
                )
            """)
            
            # Insert new expense
            cursor.execute("""
                INSERT INTO other_expenses (expense_date, amount, description, category)
                VALUES (?, ?, ?, ?)
            """, (expense_date, amount, description, category))
            conn.commit()

        # Fetch all expenses
        cursor.execute("""
            SELECT id, expense_date, amount, description, category
            FROM other_expenses
            ORDER BY expense_date DESC
        """)
        expenses = cursor.fetchall()
        conn.close()

        return render_template("expense_management.html", expenses=expenses)
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/delete_expense/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Delete the expense with the given ID
        cursor.execute("DELETE FROM other_expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()

        # Redirect back to the expense management page
        return redirect(url_for("expense_management"))
    except Exception as e:
        return f"Error: {e}", 500


























if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
