from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3
import json
import os

app = Flask(__name__, template_folder="templates")


# Initialize the Database
def init_db():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            cash_sale REAL,
            card_sale REAL,
            total_sale REAL,
            tips REAL,
            tax REAL,
            expense REAL,
            profit REAL
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


# Welcome route with debugging
@app.route("/")
def root():
    try:
        # Log current directory and templates folder contents
        print("Current Working Directory:", os.getcwd())
        print(
            "Templates Directory Contents:",
            os.listdir(os.path.join(os.getcwd(), "templates")),
        )

        # Connect to the database
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Get the last 5 regular sales entries with timestamp
        cursor.execute(
            'SELECT "Sale" AS type, datetime(date), total_sale FROM sales ORDER BY id DESC LIMIT 5'
        )
        sales_activity = cursor.fetchall()

        # Get the last 5 online sales entries with timestamp
        cursor.execute(
            'SELECT "Online Sale" AS type, datetime(sale_date), sale_amount FROM online_sales ORDER BY id DESC LIMIT 5'
        )
        online_sales_activity = cursor.fetchall()

        # Get the last 5 employee entries with timestamp
        cursor.execute(
            'SELECT "Employee" AS type, datetime("now"), name || " Hired" AS action FROM employees ORDER BY id DESC LIMIT 5'
        )
        employees_activity = cursor.fetchall()

        # Combine all activities and sort them by most recent date
        recent_activity = sales_activity + online_sales_activity + employees_activity
        recent_activity.sort(key=lambda x: x[1], reverse=True)  # Sort by datetime

        conn.close()

        # Pass the recent activity data to the template
        return render_template("welcome.html", recent_activity=recent_activity)
    except Exception as e:
        app.logger.error(f"Error loading welcome.html: {e}")
        return f"An error occurred while loading the welcome page: {e}", 500


# Route to Display the Add Sale Form
@app.route('/add_sale', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        date = request.form.get('date')
        cash_sale = float(request.form.get('cash_sale', 0))
        card_sale = float(request.form.get('card_sale', 0))
        tips = float(request.form.get('tips', 0))
        tax = float(request.form.get('tax', 0))
        expense = float(request.form.get('expense', 0))
        total_sale = cash_sale + card_sale
        profit = total_sale - (tips + tax + expense)

        # Insert into database
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sales (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit))
        conn.commit()
        conn.close()

        return redirect(url_for('view_sales'))  # Redirect to view_sales page

    return render_template('add_sale.html')
# Route to View Sales Data
@app.route('/view_sales', methods=['GET'])
def view_sales():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    # Fetch regular sales
    cursor.execute('''
        SELECT id, date, cash_sale, card_sale, total_sale, tips, tax, expense, profit
        FROM sales
        ORDER BY date
    ''')
    regular_sales = cursor.fetchall()

    # Fetch online sales grouped by date
    cursor.execute('''
        SELECT sale_date, SUM(sale_amount)
        FROM online_sales
        GROUP BY sale_date
    ''')
    online_sales = cursor.fetchall()
    conn.close()

    # Create a dictionary for online sales by date
    online_sales_dict = {row[0]: row[1] for row in online_sales}

    # Combine online sales into the regular sales data
    combined_sales = []
    for sale in regular_sales:
        sale_date = sale[1]
        total_online_sale = online_sales_dict.get(sale_date, 0)  # Default to 0 if no online sales for the date
        updated_profit = sale[8] + total_online_sale  # Add total online sale to profit
        combined_sales.append(sale + (total_online_sale, updated_profit))

    # Prepare data for the chart
    dates = [sale[1] for sale in combined_sales]
    daily_totals = [sale[4] for sale in combined_sales]

    return render_template('view_sales.html', sales=combined_sales, dates=json.dumps(dates), daily_totals=json.dumps(daily_totals))
# Route to Export Sales Data as CSV
@app.route("/export_sales", methods=["GET"])
def export_sales():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales ORDER BY date")  # Fetch all sales data
    sales = cursor.fetchall()
    conn.close()

    # Create CSV data
    csv_data = "ID,Date,Cash Sale,Card Sale,Total Sale,Tips,Tax,Expense,Profit\n"
    for sale in sales:
        csv_data += ",".join(map(str, sale)) + "\n"

    # Send the CSV data as a file response
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=sales.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


## Route to Delete a Sale
@app.route('/delete_sale', methods=['POST'])
def delete_sale():
    sale_id = request.form.get('sale_id')
    if not sale_id:
        return "Bad Request: Sale ID missing", 400

    try:
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sales WHERE id = ?', (sale_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('view_sales'))
    except sqlite3.Error as e:
        app.logger.error(f"Error deleting sale: {e}")
        return "Internal Server Error", 500


    # Redirect back to the view_sales page
    return redirect(url_for("view_sales"))

    # Create CSV data
    csv_data = "ID,Date,Cash Sale,Card Sale,Total Sale,Tips,Tax,Expense,Profit\n"
    for sale in sales:
        csv_data += ",".join(map(str, sale)) + "\n"

    # Send the CSV data as a file response
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = "attachment; filename=sales.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


# Online Sale
# Initialize the Database for Online Sales
def init_online_sales_db():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS online_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            sale_amount REAL,
            sale_date TEXT
        )
    """
    )
    conn.commit()
    conn.close()


# Initialize the database at the start
init_online_sales_db()


# Route for Online Sale Page
@app.route("/online_sale", methods=["GET", "POST"])
def online_sale():
    if request.method == "POST":
        platform = request.form["platform"]
        sale_amount = float(request.form["sale_amount"])
        sale_date = request.form["sale_date"]

        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO online_sales (platform, sale_amount, sale_date)
            VALUES (?, ?, ?)
        """,
            (platform, sale_amount, sale_date),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("view_sales"))  # Redirect to view all sales
    return render_template("online_sale.html")


# Route to handle Doordash sales
@app.route("/doordash_sale", methods=["GET", "POST"])
def doordash_sale():
    if request.method == "POST":
        sale_amount = float(request.form["sale_amount"])
        sale_date = request.form["sale_date"]
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO online_sales (platform, sale_amount, sale_date) VALUES (?, ?, ?)",
            ("Doordash", sale_amount, sale_date),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("online_sale"))
    return render_template("input_sale.html", platform="Doordash")


# Route to handle Uber Eats sales
@app.route("/ubereats_sale", methods=["GET", "POST"])
def ubereats_sale():
    if request.method == "POST":
        sale_amount = float(request.form["sale_amount"])
        sale_date = request.form["sale_date"]
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO online_sales (platform, sale_amount, sale_date) VALUES (?, ?, ?)",
            ("Uber Eats", sale_amount, sale_date),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("online_sale"))
    return render_template("input_sale.html", platform="Uber Eats")


# Route to handle Grubhub sales
@app.route("/grubhub_sale", methods=["GET", "POST"])
def grubhub_sale():
    if request.method == "POST":
        sale_amount = float(request.form["sale_amount"])
        sale_date = request.form["sale_date"]
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO online_sales (platform, sale_amount, sale_date) VALUES (?, ?, ?)",
            ("Grubhub", sale_amount, sale_date),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("online_sale"))
    return render_template("input_sale.html", platform="Grubhub")


# Route to calculate and display total online sales
@app.route("/total_online_sale")
def total_online_sale():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT platform, SUM(sale_amount) FROM online_sales GROUP BY platform"
    )
    sales = cursor.fetchall()
    cursor.execute("SELECT SUM(sale_amount) FROM online_sales")
    total_sales = cursor.fetchone()[0] or 0  # Handle None case for total sales
    conn.close()
    return render_template(
        "total_online_sale.html", sales=sales, total_sales=total_sales
    )


# employee route
# Employee route
@app.route("/employees", methods=["GET"])
def employees():
    try:
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees")
        employees_data = cursor.fetchall()
        conn.close()
        return render_template("employees.html", employees=employees_data)
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        return f"Database error: {e}", 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return f"An unexpected error occurred: {e}", 500


# Initialize the employees table
def init_employees_table():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


# Employees salary: Add a new employee
@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        # Extract form data
        name = request.form.get("name")
        designation = request.form.get("designation")

        # Insert data into the database
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO employees (name, designation) VALUES (?, ?)",
            (name, designation),
        )
        conn.commit()
        conn.close()

        return redirect(url_for("employees"))
    return render_template("add_employee.html")


# Delete Employee
@app.route("/delete_employee/<int:employee_id>", methods=["POST"])
def delete_employee(employee_id):
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("employees"))


# Route to view salary summary for a specific month
@app.route("/salary_summary", methods=["GET"])
def salary_summary():
    month = request.args.get("month")  # Expected format: YYYY-MM

    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT e.name, e.designation, 
               SUM(CASE WHEN s.payment_type = 'Cash' THEN s.payment_amount ELSE 0 END) AS total_cash,
               SUM(CASE WHEN s.payment_type = 'Cheque' THEN s.payment_amount ELSE 0 END) AS total_cheque,
               SUM(s.payment_amount) AS total_paid
        FROM employees e
        JOIN employee_salaries s ON e.id = s.employee_id
        WHERE s.payment_date LIKE ?
        GROUP BY e.id
    """,
        (f"{month}%",),
    )
    summary = cursor.fetchall()
    conn.close()

    return render_template("salary_summary.html", summary=summary, month=month)


# edit employess
@app.route("/edit_employee/<int:employee_id>", methods=["GET", "POST"])
def edit_employee(employee_id):
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()

    if request.method == "POST":
        # Handle the form submission
        name = request.form.get("name")
        designation = request.form.get("designation")

        cursor.execute(
            "UPDATE employees SET name = ?, designation = ? WHERE id = ?",
            (name, designation, employee_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("employees"))
    else:
        # Fetch employee data for pre-filling the form
        cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
        employee = cursor.fetchone()
        conn.close()
        return render_template("edit_employee.html", employee=employee)


# Add payment
@app.route("/add_payment/<int:employee_id>", methods=["GET", "POST"])
@app.route('/add_payment/<int:employee_id>', methods=['GET', 'POST'])
def add_payment(employee_id):
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        try:
            # Extract form data
            payment_amount = float(request.form['payment_amount'])
            payment_type = request.form['payment_type']  # Cash or Cheque
            payment_date = request.form['payment_date']

            # Save payment to the database
            cursor.execute('''
                INSERT INTO employee_salaries (employee_id, payment_amount, payment_type, payment_date)
                VALUES (?, ?, ?, ?)
            ''', (employee_id, payment_amount, payment_type, payment_date))
            conn.commit()
        except Exception as e:
            app.logger.error(f"Error adding payment: {e}")
            return f"An error occurred: {e}", 500
        finally:
            conn.close()
        return redirect(url_for('employees'))

    # If GET request, fetch employee details for displaying on the form
    cursor.execute('SELECT name, designation FROM employees WHERE id = ?', (employee_id,))
    employee = cursor.fetchone()
    conn.close()
    if not employee:
        return f"Employee with ID {employee_id} not found.", 404

    return render_template('add_payment.html', employee_id=employee_id, employee=employee)
# Salary details
@app.route('/salary_details/<int:employee_id>', methods=['GET'])
def salary_details(employee_id):
    try:
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()

        # Fetch salary details for the employee
        cursor.execute('''
            SELECT payment_date, payment_amount, payment_type
            FROM employee_salaries
            WHERE employee_id = ?
            ORDER BY payment_date
        ''', (employee_id,))
        salary_details = cursor.fetchall()

        # Fetch total salary paid
        cursor.execute('''
            SELECT SUM(payment_amount)
            FROM employee_salaries
            WHERE employee_id = ?
        ''', (employee_id,))
        total_salary = cursor.fetchone()[0] or 0  # Handle None case for total salary

        # Fetch employee details
        cursor.execute('''
            SELECT name, designation
            FROM employees
            WHERE id = ?
        ''', (employee_id,))
        employee = cursor.fetchone()

        conn.close()

        if not employee:
            return f"No employee found with ID {employee_id}", 404

        return render_template(
            'salary_details.html',
            salary_details=salary_details,
            total_salary=total_salary,
            employee=employee
        )
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        return f"Database error: {e}", 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return f"An unexpected error occurred: {e}", 500

#expense management
@app.route('/expense_management', methods=['GET', 'POST'])
def expense_management():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']

        cursor.execute('INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)',
                       (description, amount, category, date))
        conn.commit()

    # Pagination setup
    items_per_page = 10
    page = int(request.args.get('page', 1))
    offset = (page - 1) * items_per_page

    # Fetch paginated expenses
    cursor.execute('SELECT COUNT(*) FROM expenses')
    total_items = cursor.fetchone()[0]
    total_pages = (total_items + items_per_page - 1) // items_per_page

    cursor.execute('SELECT rowid, date, description, amount, category FROM expenses ORDER BY date DESC LIMIT ? OFFSET ?',
                   (items_per_page, offset))
    expenses = cursor.fetchall()

    # Chart data
    cursor.execute('SELECT category, SUM(amount) FROM expenses GROUP BY category')
    chart_data = cursor.fetchall()
    conn.close()

    labels = [row[0] for row in chart_data]
    amounts = [row[1] for row in chart_data]

    return render_template(
        'expense_management.html',
        expenses=expenses,
        expense_chart_data={'labels': labels, 'amounts': amounts},
        current_page=page,
        total_pages=total_pages
    )
    # Fetch total number of expenses for pagination
    cursor.execute('SELECT COUNT(*) FROM expenses')
    total_expenses = cursor.fetchone()[0]

    # Calculate total pages
    total_pages = (total_expenses + per_page - 1) // per_page

    # Chart data
    cursor.execute('SELECT category, SUM(amount) FROM expenses GROUP BY category')
    chart_data = cursor.fetchall()
    conn.close()

    labels = [row[0] for row in chart_data]
    amounts = [row[1] for row in chart_data]

    return render_template(
        'expense_management.html',
        expenses=expenses,
        expense_chart_data={'labels': labels, 'amounts': amounts},
        page=page,
        total_pages=total_pages
    )

    
#delete salary
@app.route('/delete_payment/<int:payment_id>', methods=['POST'])
def delete_payment(payment_id):
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM employee_salaries WHERE rowid = ?', (payment_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer)  # Redirect back to the salary details page












# int expense tavle
def init_expenses_table():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


init_expenses_table()


def recent_activity():
    conn = sqlite3.connect("sales.db")
    cursor = conn.cursor()

    # Fetch activities
    cursor.execute(
        'SELECT "Sale", date, total_sale FROM sales ORDER BY date DESC LIMIT 5'
    )
    sales_activity = cursor.fetchall()

    cursor.execute(
        'SELECT "Employee", name, designation FROM employees ORDER BY id DESC LIMIT 5'
    )
    employee_activity = cursor.fetchall()

    # Combine and sort activities
    combined_activity = sales_activity + employee_activity
    combined_activity.sort(key=lambda x: x[1], reverse=True)

    conn.close()

    # Return the top 5 activities
    return combined_activity[:5]

#Monthly report
@app.route('/monthly_report', methods=['GET'])
def monthly_report():
    """
    Route to generate the Monthly Performance Report.
    """
    try:
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()

        # Query to fetch monthly performance
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', date) AS month, 
                SUM(total_sale) AS total_sales,
                SUM(tips) AS total_tips,
                SUM(tax) AS total_tax,
                SUM(expense) AS total_expense,
                SUM(profit) AS total_profit
            FROM sales
            GROUP BY month
            ORDER BY month DESC
        ''')
        monthly_data = cursor.fetchall()

        conn.close()

        return render_template('monthly_report.html', monthly_data=monthly_data)
    except Exception as e:
        app.logger.error(f"Error generating monthly report: {e}")
        return f"An error occurred: {e}", 500
@app.route('/debug_expenses', methods=['GET'])
def debug_expenses():
    try:
        # Connect to the database
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        
        # Fetch all expenses
        cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
        expenses = cursor.fetchall()
        conn.close()
        
        # Return the data as JSON
        return {'expenses': expenses}, 200
    except Exception as e:
        app.logger.error(f"Error fetching expenses: {e}")
        return {'error': str(e)}, 500

@app.route('/summary', methods=['GET'])
def summary():
    try:
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()

        # Daily summary query
        cursor.execute('''
            SELECT 
                date,
                SUM(total_sale) AS total_sales,
                SUM(tips) AS total_tips,
                SUM(tax) AS total_tax,
                SUM(expense) AS total_expense,
                SUM(profit) AS total_profit
            FROM sales
            GROUP BY date
            ORDER BY date
        ''')
        daily_summaries = cursor.fetchall()

        # Monthly summary query
        cursor.execute('''
            SELECT 
                SUBSTR(date, 1, 7) AS month,  -- Extract YYYY-MM
                SUM(total_sale) AS total_sales,
                SUM(tips) AS total_tips,
                SUM(tax) AS total_tax,
                SUM(expense) AS total_expense,
                SUM(profit) AS total_profit
            FROM sales
            GROUP BY month
            ORDER BY month
        ''')
        monthly_summaries = cursor.fetchall()
        conn.close()

        # Render the summary template
        return render_template(
            "summary.html",
            daily_summaries=daily_summaries,
            monthly_summaries=monthly_summaries,
        )
    except sqlite3.Error as db_error:
        app.logger.error(f"Database error in /summary route: {db_error}")
        return f"Database error: {db_error}", 500
    except Exception as e:
        app.logger.error(f"Unexpected error in /summary route: {e}")
        return f"Unexpected error: {e}", 500
#delete expense
@app.route('/delete_expense', methods=['POST'])
def delete_expense():
    try:
        expense_id = request.form['delete_id']  # Get the expense ID from the form
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()
        return redirect('/expense_management')  # Redirect back to the expense management page
    except Exception as e:
        app.logger.error(f"Error deleting expense: {e}")
        return f"An error occurred: {e}", 500













# Daily sale report
@app.route("/daily_sales_report")
def daily_sales_report():
    try:
        # Connect to the database
        conn = sqlite3.connect("sales.db")
        cursor = conn.cursor()

        # Query to fetch sales for today
        cursor.execute(
            """
            SELECT date, SUM(cash_sale), SUM(card_sale), SUM(total_sale), SUM(tips), SUM(tax), SUM(expense), SUM(profit)
            FROM sales
            WHERE date = DATE('now')
            GROUP BY date
        """
        )
        report = cursor.fetchone()  # Fetch today's report

        conn.close()

        # If no sales are found, display a default message
        if not report:
            report = ["No sales recorded for today.", 0, 0, 0, 0, 0, 0, 0]

        # Render the report on a template
        return render_template("daily_sales_report.html", report=report)
    except Exception as e:
        app.logger.error(f"Error generating daily sales report: {e}")
        return f"An error occurred while generating the daily sales report: {e}", 500




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port)
