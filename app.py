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

#Welcome route
@app.route('/')
def welcome():
    try:
        # Log current working directory and templates directory for debugging
        print("Current working directory:", os.getcwd())
        templates_path = os.path.join(os.getcwd(), 'templates')
        print("Templates directory contents:", os.listdir(templates_path))

        # Render the welcome page
        return render_template('welcome.html')
    except Exception as e:
        app.logger.error(f"Error loading welcome.html: {e}")
        return f"An error occurred while loading the welcome page: {e}", 500








# Route to Display the Add Sale Form
@app.route('/add_sale', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        # Extract form data
        date = request.form.get('date')
        cash_sale = float(request.form.get('cash_sale', 0))
        card_sale = float(request.form.get('card_sale', 0))
        total_sale = cash_sale + card_sale
        tips = float(request.form.get('tips', 0))  # Tips field
        tax = float(request.form.get('tax', 0))
        expense = float(request.form.get('expense', 0))

        # Calculate profit (deduct tips, tax, and other expenses)
        profit = (total_sale) - (tips + tax + expense)

        # Save the data to the database
        conn = sqlite3.connect('sales.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sales (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, cash_sale, card_sale, total_sale, tips, tax, expense, profit))
        conn.commit()
        conn.close()

        return redirect(url_for('view_sales'))
    else:
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
@app.route('/online_sale', methods=['GET'])
def online_sale():
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
@app.route('/employees', methods=['GET'])
def employees():
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    employees_data = cursor.fetchall()
    conn.close()
    return render_template('employees.html', employees=employees_data)


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













# Route to View Sales Summary
@app.route('/summary', methods=['GET'])
def summary():
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

    # Debugging Output
    print("Daily Summaries:", daily_summaries)
    print("Monthly Summaries:", monthly_summaries)

    return render_template(
        "summary.html",
        daily_summaries=daily_summaries,
        monthly_summaries=monthly_summaries
    )


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
    app.run(debug=True)
