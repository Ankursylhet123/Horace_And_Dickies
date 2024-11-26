from flask import Flask, render_template, request, redirect, url_for, make_response
import sqlite3
import json
import os

app = Flask(__name__, template_folder='templates')


# Initialize the Database
def init_db():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('''
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
    ''')
    conn.commit()
    conn.close()

init_db()

# Welcome route with debugging
@app.route('/')
def root():
    try:
        # Log current directory and templates folder contents
        print("Current Working Directory:", os.getcwd())
        print("Templates Directory Contents:", os.listdir(os.path.join(os.getcwd(), 'templates')))
        
        # Render the welcome page
        return render_template('welcome.html')
    except Exception as e:
        app.logger.error(f"Error loading welcome.html: {e}")
        return f"An error occurred while loading the welcome page: {e}", 500

# Route to Display the Add Sale Form
@app.route('/add_sale', methods=['GET', 'POST'])
def add_sale():
    """
    Add Sale Route:
    Handles both GET and POST requests for adding sales.
    """
    if request.method == 'POST':
        # Extract form data (ensure the form fields match this structure in your HTML)
        date = request.form.get('date')
        cash_sale = float(request.form.get('cash_sale', 0))
        card_sale = float(request.form.get('card_sale', 0))
        total_sale = cash_sale + card_sale
        tips = float(request.form.get('tips', 0))
        tax = float(request.form.get('tax', 0))
        expense = float(request.form.get('expense', 0))
        profit = total_sale - (tips + tax + expense)

        # Save the data to the database
        try:
            import sqlite3
            conn = sqlite3.connect('sales.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sales (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit))
            conn.commit()
            conn.close()
            return redirect(url_for('view_sales'))  # Redirect to a page to view all sales
        except Exception as e:
            app.logger.error(f"Error saving sale: {e}")
            return "An error occurred while saving the sale.", 500
    else:
        # For GET requests, show the Add Sale form
        return render_template('add_sale.html')



# Route to View Sales Data
@app.route('/view_sales', methods=['GET'])
def view_sales():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    # Fetch regular


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

    return render_template('view_sales.html', sales=combined_sales)
# Route to Export Sales Data as CSV
@app.route('/export_sales', methods=['GET'])
def export_sales():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sales ORDER BY date')  # Fetch all sales data
    sales = cursor.fetchall()
    conn.close()

    # Create CSV data
    csv_data = "ID,Date,Cash Sale,Card Sale,Total Sale,Tips,Tax,Expense,Profit\n"
    for sale in sales:
        csv_data += ",".join(map(str, sale)) + "\n"

    # Send the CSV data as a file response
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=sales.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


## Route to Delete a Sale
@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
def delete_sale(sale_id):
    # Connect to the database
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    # Delete the sale with the given ID
    cursor.execute('DELETE FROM sales WHERE id = ?', (sale_id,))
    conn.commit()
    conn.close()

    # Redirect back to the view_sales page
    return redirect(url_for('view_sales'))


    # Create CSV data
    csv_data = "ID,Date,Cash Sale,Card Sale,Total Sale,Tips,Tax,Expense,Profit\n"
    for sale in sales:
        csv_data += ",".join(map(str, sale)) + "\n"

    # Send the CSV data as a file response
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=sales.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response
#Online Sale
# Initialize the Database for Online Sales
def init_online_sales_db():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS online_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            sale_amount REAL,
            sale_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database at the start
init_online_sales_db()

# Route for Online Sale Page
@app.route('/online_sale', methods=['GET', 'POST'])
def online_sale():
    if request.method == 'POST':
        platform = request.form['platform']
        sale_amount = float(request.form['sale_amount'])
        sale_date = request.form['sale_date']
        
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO online_sales (platform, sale_amount, sale_date)
            VALUES (?, ?, ?)
        ''', (platform, sale_amount, sale_date))
        conn.commit()
        conn.close()
        return redirect(url_for('view_sales'))  # Redirect to view all sales
    return render_template('online_sale.html')


# Route to handle Doordash sales
@app.route('/doordash_sale', methods=['GET', 'POST'])
def doordash_sale():
    if request.method == 'POST':
        sale_amount = float(request.form['sale_amount'])
        sale_date = request.form['sale_date']
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO online_sales (platform, sale_amount, sale_date) VALUES (?, ?, ?)',
                       ('Doordash', sale_amount, sale_date))
        conn.commit()
        conn.close()
        return redirect(url_for('online_sale'))
    return render_template('input_sale.html', platform='Doordash')

# Route to handle Uber Eats sales
@app.route('/ubereats_sale', methods=['GET', 'POST'])
def ubereats_sale():
    if request.method == 'POST':
        sale_amount = float(request.form['sale_amount'])
        sale_date = request.form['sale_date']
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO online_sales (platform, sale_amount, sale_date) VALUES (?, ?, ?)',
                       ('Uber Eats', sale_amount, sale_date))
        conn.commit()
        conn.close()
        return redirect(url_for('online_sale'))
    return render_template('input_sale.html', platform='Uber Eats')

# Route to handle Grubhub sales
@app.route('/grubhub_sale', methods=['GET', 'POST'])
def grubhub_sale():
    if request.method == 'POST':
        sale_amount = float(request.form['sale_amount'])
        sale_date = request.form['sale_date']
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO online_sales (platform, sale_amount, sale_date) VALUES (?, ?, ?)',
                       ('Grubhub', sale_amount, sale_date))
        conn.commit()
        conn.close()
        return redirect(url_for('online_sale'))
    return render_template('input_sale.html', platform='Grubhub')

# Route to calculate and display total online sales
@app.route('/total_online_sale')
def total_online_sale():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('SELECT platform, SUM(sale_amount) FROM online_sales GROUP BY platform')
    sales = cursor.fetchall()
    cursor.execute('SELECT SUM(sale_amount) FROM online_sales')
    total_sales = cursor.fetchone()[0] or 0  # Handle None case for total sales
    conn.close()
    return render_template('total_online_sale.html', sales=sales, total_sales=total_sales)


#employee route
# Employee route
@app.route('/employees', methods=['GET'])
def employees():
    try:
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees_data = cursor.fetchall()
        conn.close()
        return render_template('employees.html', employees=employees_data)
    except sqlite3.Error as e:
        app.logger.error(f"Database error: {e}")
        return f"Database error: {e}", 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return f"An unexpected error occurred: {e}", 500



# Initialize the employees table
def init_employees_table():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()





# Employees salary: Add a new employee
@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        # Extract form data
        name = request.form.get('name')
        designation = request.form.get('designation')

        # Insert data into the database
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO employees (name, designation) VALUES (?, ?)', (name, designation))
        conn.commit()
        conn.close()

        return redirect(url_for('employees'))
    return render_template('add_employee.html')



# Delete Employee
@app.route('/delete_employee/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('employees'))


# Route to view salary summary for a specific month
@app.route('/salary_summary', methods=['GET'])
def salary_summary():
    month = request.args.get('month')  # Expected format: YYYY-MM

    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT e.name, e.designation, 
               SUM(CASE WHEN s.payment_type = 'Cash' THEN s.payment_amount ELSE 0 END) AS total_cash,
               SUM(CASE WHEN s.payment_type = 'Cheque' THEN s.payment_amount ELSE 0 END) AS total_cheque,
               SUM(s.payment_amount) AS total_paid
        FROM employees e
        JOIN employee_salaries s ON e.id = s.employee_id
        WHERE s.payment_date LIKE ?
        GROUP BY e.id
    ''', (f'{month}%',))
    summary = cursor.fetchall()
    conn.close()

    return render_template('salary_summary.html', summary=summary, month=month)



#edit employess
@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Handle the form submission
        name = request.form.get('name')
        designation = request.form.get('designation')

        cursor.execute('UPDATE employees SET name = ?, designation = ? WHERE id = ?', 
                       (name, designation, employee_id))
        conn.commit()
        conn.close()
        return redirect(url_for('employees'))
    else:
        # Fetch employee data for pre-filling the form
        cursor.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
        employee = cursor.fetchone()
        conn.close()
        return render_template('edit_employee.html', employee=employee)
#Add payment
@app.route('/add_payment/<int:employee_id>', methods=['GET', 'POST'])
def add_payment(employee_id):
    if request.method == 'POST':
        # Extract form data
        payment_amount = float(request.form.get('payment_amount'))
        payment_type = request.form.get('payment_type')  # Cash or Cheque
        payment_date = request.form.get('payment_date')

        # Save payment to the database
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO employee_salaries (employee_id, payment_amount, payment_type, payment_date)
            VALUES (?, ?, ?, ?)
        ''', (employee_id, payment_amount, payment_type, payment_date))
        conn.commit()
        conn.close()

        return redirect(url_for('employees'))
    else:
        return render_template('add_payment.html', employee_id=employee_id)
#Salary details
@app.route('/salary_details/<int:employee_id>', methods=['GET'])
def salary_details(employee_id):
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
    total_salary = cursor.fetchone()[0] or 0

    # Fetch employee details
    cursor.execute('''
        SELECT name, designation
        FROM employees
        WHERE id = ?
    ''', (employee_id,))
    employee = cursor.fetchone()

    conn.close()

    return render_template('salary_details.html', salary_details=salary_details,
                           total_salary=total_salary, employee=employee)

#route to expense management 
@app.route('/expense_management', methods=['GET', 'POST'])
def expense_management():
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        date = request.form['date']
        
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (category, amount, date)
            VALUES (?, ?, ?)
        ''', (category, amount, date))
        conn.commit()
        conn.close()
        return redirect(url_for('expense_management'))
    
    # Fetch all expenses for display
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
    expenses = cursor.fetchall()
    conn.close()
    return render_template('expense_management.html', expenses=expenses)


#int expense tavle
def init_expenses_table():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_expenses_table()














# Route to View Sales Summary
@app.route('/summary', methods=['GET'])
def summary():
    try:
        # Connect to the database
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()

        # Fetch daily summary
        cursor.execute('''
            SELECT 
                date,
                COALESCE(SUM(total_sale), 0) AS total_sales,
                COALESCE(SUM(tips), 0) AS total_tips,
                COALESCE(SUM(tax), 0) AS total_tax,
                COALESCE(SUM(expense), 0) AS total_expense,
                COALESCE(SUM(profit), 0) AS total_profit
            FROM sales
            GROUP BY date
            ORDER BY date
        ''')
        daily_summaries = cursor.fetchall()

        # Fetch monthly summary
        cursor.execute('''
            SELECT 
                SUBSTR(date, 1, 7) AS month,  -- Extract YYYY-MM
                COALESCE(SUM(total_sale), 0) AS total_sales,
                COALESCE(SUM(tips), 0) AS total_tips,
                COALESCE(SUM(tax), 0) AS total_tax,
                COALESCE(SUM(expense), 0) AS total_expense,
                COALESCE(SUM(profit), 0) AS total_profit
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
            monthly_summaries=monthly_summaries
        )
    except sqlite3.Error as db_error:
        app.logger.error(f"Database error in /summary route: {db_error}")
        return f"Database error: {db_error}", 500
    except Exception as e:
        app.logger.error(f"Unexpected error in /summary route: {e}")
        return f"An unexpected error occurred: {e}", 500



    # Prepare data for charts
    dates = [row[0] for row in daily_summaries]
    daily_totals = [row[1] for row in daily_summaries]
    months = [row[0] for row in monthly_summaries]
    monthly_totals = [row[1] for row in monthly_summaries]

    return render_template("summary.html", 
                           daily_summaries=daily_summaries, 
                           monthly_summaries=monthly_summaries,
                           dates=json.dumps(dates),
                           daily_totals=json.dumps(daily_totals),
                           months=json.dumps(months),
                           monthly_totals=json.dumps(monthly_totals))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port)
