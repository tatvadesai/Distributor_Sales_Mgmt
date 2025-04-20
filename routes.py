from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import io
import logging
from sqlalchemy import func
import os
import zipfile

from app import app, db
from models import User, Distributor, Target, Actual
from utils import (
    calculate_periods, get_current_week_start, get_current_week_end, 
    generate_performance_data, generate_pdf_report, generate_excel_report, 
    send_email_report, get_financial_year, get_financial_quarter, get_financial_month, 
    get_all_financial_years, get_financial_quarter_dates, test_email_config, send_test_email
)
from backup_utils import perform_backup, get_available_backups, restore_from_backup

# Add current datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Login/Auth Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Dashboard Route
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Get current date for default values
    today = datetime.now()
    
    # Get financial year data
    current_fin_year = get_financial_year(today)
    current_month = today.strftime('%b')  # Current month name (short form)
    
    # Get selected filters from request or use defaults
    selected_financial_year = request.args.get('financial_year', current_fin_year)
    selected_month = request.args.get('month', current_month)
    selected_date_range = request.args.get('date_range', '')
    distributor_id = request.args.get('distributor_id')
    
    # Get all distributors for the dropdown
    distributors = Distributor.query.all()
    
    # Get all financial years
    financial_years = get_all_financial_years(2020, 2035)
    
    # Get all months
    months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    
    # If no date_range is provided, get the default one for the selected month
    if not selected_date_range:
        # Parse the financial year to get the calendar year
        fy_start_year = int("20" + selected_financial_year[2:4])
        
        # Map months to their calendar values
        month_map = {
            'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 
            'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3
        }
        
        # Determine the year for this month
        month_num = month_map[selected_month]
        year = fy_start_year if month_num >= 4 else fy_start_year + 1
        
        # Get the first day of the month
        first_day = datetime(year, month_num, 1)
        
        # Find the first Monday of the month or last Monday of the previous month
        first_week_start = first_day - timedelta(days=first_day.weekday())
        first_week_end = first_week_start + timedelta(days=6)
        
        # Set the default date range
        selected_date_range = f"{first_week_start.strftime('%d %b')} - {first_week_end.strftime('%d %b')}"
    
    # Generate the period identifier for performance data query (e.g., "Apr-FY24-25")
    period_identifier = f"{selected_month}-{selected_financial_year}"
    
    # Get performance data using the period identifier
    overall_data = generate_performance_data(None, 'Monthly', period_identifier, db, Actual, Target)
    
    # Get distributor-specific performance data
    distributor_performance = []
    for distributor in distributors:
        perf_data = generate_performance_data(distributor.id, 'Monthly', period_identifier, db, Actual, Target)
        distributor_performance.append({
            'id': distributor.id,
            'name': distributor.name,
            **perf_data
        })
    
    # Sort by achievement percent (descending)
    distributor_performance.sort(key=lambda x: x['achievement_percent'], reverse=True)
    
    # Check if the request wants JSON data
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'overall_data': overall_data,
            'distributor_performance': distributor_performance
        })
    
    return render_template(
        'dashboard.html',
        distributors=distributors,
        financial_years=financial_years,
        months=months,
        selected_financial_year=selected_financial_year,
        selected_month=selected_month,
        selected_date_range=selected_date_range,
        selected_distributor_id=distributor_id,
        overall_data=overall_data,
        distributor_performance=distributor_performance
    )

# Distributor Routes
@app.route('/distributors')
@login_required
def distributors():
    distributors = Distributor.query.all()
    return render_template('distributors.html', distributors=distributors)

@app.route('/distributors/new', methods=['GET', 'POST'])
@login_required
def new_distributor():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        whatsapp = request.form.get('whatsapp')
        area = request.form.get('area')
        
        # Validate name uniqueness
        existing = Distributor.query.filter(db.func.lower(Distributor.name) == db.func.lower(name)).first()
        if existing:
            flash('Distributor name already exists.', 'danger')
            return render_template('distributor_form.html')
        
        distributor = Distributor(name=name, email=email, whatsapp=whatsapp, area=area)
        db.session.add(distributor)
        
        try:
            db.session.commit()
            flash('Distributor added successfully!', 'success')
            return redirect(url_for('distributors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating distributor: {str(e)}', 'danger')
    
    return render_template('distributor_form.html')

@app.route('/distributors/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_distributor(id):
    distributor = Distributor.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        whatsapp = request.form.get('whatsapp')
        area = request.form.get('area')
        
        # Validate name uniqueness (excluding current distributor)
        existing = Distributor.query.filter(
            db.func.lower(Distributor.name) == db.func.lower(name),
            Distributor.id != id
        ).first()
        
        if existing:
            flash('Distributor name already exists.', 'danger')
            return render_template('distributor_form.html', distributor=distributor)
        
        distributor.name = name
        distributor.email = email
        distributor.whatsapp = whatsapp
        distributor.area = area
        
        try:
            db.session.commit()
            flash('Distributor updated successfully!', 'success')
            return redirect(url_for('distributors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating distributor: {str(e)}', 'danger')
    
    return render_template('distributor_form.html', distributor=distributor)

@app.route('/distributors/<int:id>/delete', methods=['POST'])
@login_required
def delete_distributor(id):
    distributor = Distributor.query.get_or_404(id)
    
    try:
        db.session.delete(distributor)
        db.session.commit()
        flash('Distributor deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting distributor: {str(e)}', 'danger')
    
    return redirect(url_for('distributors'))

# Target Routes
@app.route('/targets')
@login_required
def targets():
    # Get current date for default values
    today = datetime.now()
    
    # Get financial year data
    current_fin_year = get_financial_year(today)
    current_month = today.strftime('%b')  # Current month name (short form)
    
    # Get selected filters from request or use defaults
    selected_financial_year = request.args.get('financial_year', current_fin_year)
    selected_month = request.args.get('month', current_month)
    selected_date_range = request.args.get('date_range', '')
    
    # Get all distributors
    distributors = Distributor.query.all()
    
    # Get all targets
    targets_list = Target.query.order_by(Target.period_type, Target.period_identifier, Target.distributor_id).all()
    
    # Get all financial years
    financial_years = get_all_financial_years(2020, 2035)
    
    # Get all months
    months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    
    # If no date_range is provided, get the default one for the selected month
    if not selected_date_range:
        # Parse the financial year to get the calendar year
        fy_start_year = int("20" + selected_financial_year[2:4])
        
        # Map months to their calendar values
        month_map = {
            'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 
            'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3
        }
        
        # Determine the year for this month
        month_num = month_map[selected_month]
        year = fy_start_year if month_num >= 4 else fy_start_year + 1
        
        # Get the first day of the month
        first_day = datetime(year, month_num, 1)
        
        # Find the first Monday of the month or last Monday of the previous month
        first_week_start = first_day - timedelta(days=first_day.weekday())
        first_week_end = first_week_start + timedelta(days=6)
        
        # Set the default date range
        selected_date_range = f"{first_week_start.strftime('%d %b')} - {first_week_end.strftime('%d %b')}"
    
    # Create period identifier for existing targets lookup (e.g., "Apr-FY24-25")
    period_identifier = f"{selected_month}-{selected_financial_year}"
    
    # Get current targets for all distributors
    targets = {}
    for distributor in distributors:
        target = Target.query.filter_by(
            distributor_id=distributor.id,
            period_type='Monthly',
            period_identifier=period_identifier
        ).first()
        targets[distributor.id] = target.target_value if target else 0
    
    return render_template(
        'targets.html',
        distributors=distributors,
        targets_list=targets_list,
        financial_years=financial_years,
        months=months,
        selected_financial_year=selected_financial_year,
        selected_month=selected_month,
        selected_date_range=selected_date_range,
        targets=targets
    )

@app.route('/targets/new', methods=['GET', 'POST'])
@login_required
def new_target():
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        financial_year = request.form.get('financial_year')
        month = request.form.get('month')
        target_value = request.form.get('target_value')
        
        # Validate required fields
        if not all([distributor_id, financial_year, month, target_value]):
            flash('All fields are required', 'danger')
            return render_template('target_form.html', distributors=distributors, financial_years=get_all_financial_years(2020, 2035))
        
        try:
            # Create period identifier for database (e.g., "Apr-FY24-25")
            period_identifier = f"{month}-{financial_year}"
            
            # Check for duplicate targets
            existing = Target.query.filter_by(
                distributor_id=distributor_id,
                period_type='Monthly',
                period_identifier=period_identifier
            ).first()
            
            if existing:
                flash('Target already set for this distributor/period.', 'danger')
                return render_template('target_form.html', distributors=distributors, financial_years=get_all_financial_years(2020, 2035))
            
            # Create new target
            target = Target(
                distributor_id=distributor_id,
                period_type='Monthly',
                period_identifier=period_identifier,
                target_value=float(target_value)
            )
            
            db.session.add(target)
            db.session.commit()
            flash('Target added successfully!', 'success')
            return redirect(url_for('targets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating target: {str(e)}', 'danger')
    
    # Get all financial years
    financial_years = get_all_financial_years(2020, 2035)
    
    return render_template('target_form.html', distributors=distributors, financial_years=financial_years)

@app.route('/targets/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_target(id):
    target = Target.query.get_or_404(id)
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        financial_year = request.form.get('financial_year')
        month = request.form.get('month')
        target_value = request.form.get('target_value')
        
        # Validate required fields
        if not all([distributor_id, financial_year, month, target_value]):
            flash('All fields are required', 'danger')
            return render_template('target_form.html', target=target, distributors=distributors, financial_years=get_all_financial_years(2020, 2035))
        
        try:
            # Create period identifier for database (e.g., "Apr-FY24-25")
            period_identifier = f"{month}-{financial_year}"
            
            # Check for duplicate targets (excluding current)
            existing = Target.query.filter_by(
                distributor_id=distributor_id,
                period_type='Monthly',
                period_identifier=period_identifier
            ).filter(Target.id != id).first()
            
            if existing:
                flash('Target already set for this distributor/period.', 'danger')
                return render_template('target_form.html', target=target, distributors=distributors, financial_years=get_all_financial_years(2020, 2035))
            
            # Update target
            target.distributor_id = distributor_id
            target.period_type = 'Monthly'
            target.period_identifier = period_identifier
            target.target_value = float(target_value)
            
            db.session.commit()
            flash('Target updated successfully!', 'success')
            return redirect(url_for('targets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating target: {str(e)}', 'danger')
    
    # Get all financial years
    financial_years = get_all_financial_years(2020, 2035)
    
    return render_template('target_form.html', target=target, distributors=distributors, financial_years=financial_years)

@app.route('/targets/<int:id>/delete', methods=['POST'])
@login_required
def delete_target(id):
    target = Target.query.get_or_404(id)
    
    try:
        db.session.delete(target)
        db.session.commit()
        flash('Target deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting target: {str(e)}', 'danger')
    
    return redirect(url_for('targets'))

# Actual Sales Routes
@app.route('/actuals')
@login_required
def actuals():
    # Get current date for default values
    today = datetime.now()
    
    # Get financial year data
    current_fin_year = get_financial_year(today)
    current_month = today.strftime('%b')  # Current month name (short form)
    
    # Get selected filters from request or use defaults
    selected_financial_year = request.args.get('financial_year', current_fin_year)
    selected_month = request.args.get('month', current_month)
    selected_date_range = request.args.get('date_range', '')
    
    # Get all distributors
    distributors = Distributor.query.all()
    
    # Get all actuals
    actuals_list = Actual.query.order_by(Actual.week_start_date.desc(), Actual.distributor_id).all()
    
    # Get all financial years
    financial_years = get_all_financial_years(2020, 2035)
    
    # Get all months
    months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    
    # If no date_range is provided, get the default one for the selected month
    if not selected_date_range:
        # Parse the financial year to get the calendar year
        fy_start_year = int("20" + selected_financial_year[2:4])
        
        # Map months to their calendar values
        month_map = {
            'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 
            'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3
        }
        
        # Determine the year for this month
        month_num = month_map[selected_month]
        year = fy_start_year if month_num >= 4 else fy_start_year + 1
        
        # Get the first day of the month
        first_day = datetime(year, month_num, 1)
        
        # Find the first Monday of the month or last Monday of the previous month
        first_week_start = first_day - timedelta(days=first_day.weekday())
        first_week_end = first_week_start + timedelta(days=6)
        
        # Set the default date range
        selected_date_range = f"{first_week_start.strftime('%d %b')} - {first_week_end.strftime('%d %b')}"
    
    # Get current actuals for all distributors 
    actuals = {}
    for distributor in distributors:
        # Find matching actuals for this month and get sum
        month_actuals = db.session.query(func.sum(Actual.actual_sales)).filter(
            Actual.distributor_id == distributor.id,
            Actual.month == selected_month,
            Actual.year.like(f"%{selected_financial_year[2:]}")  # Match FY part
        ).scalar()
        actuals[distributor.id] = month_actuals if month_actuals else 0
    
    return render_template(
        'actuals.html',
        distributors=distributors,
        actuals_list=actuals_list,
        financial_years=financial_years,
        months=months,
        selected_financial_year=selected_financial_year,
        selected_month=selected_month,
        selected_date_range=selected_date_range,
        actuals=actuals
    )

@app.route('/actuals/new', methods=['GET', 'POST'])
@login_required
def new_actual():
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        week_start_date = request.form.get('week_start_date')
        week_end_date = request.form.get('week_end_date')
        actual_sales = request.form.get('actual_sales')
        
        # Validate inputs
        if not all([distributor_id, week_start_date, week_end_date, actual_sales]):
            flash('All fields are required', 'danger')
            return render_template('actual_form.html', distributors=distributors)
        
        try:
            # Check for duplicate entries
            existing = Actual.query.filter_by(
                distributor_id=distributor_id,
                week_start_date=week_start_date,
                week_end_date=week_end_date
            ).first()
            
            if existing:
                flash('Sales already logged for this distributor and period.', 'danger')
                return render_template('actual_form.html', distributors=distributors)
            
            # Calculate period identifiers (month, quarter, year)
            month, quarter, year = calculate_periods(week_start_date)
            
            # Create new actual
            actual = Actual(
                distributor_id=distributor_id,
                week_start_date=week_start_date,
                week_end_date=week_end_date,
                actual_sales=float(actual_sales),
                month=month,
                quarter=quarter,
                year=year
            )
            
            db.session.add(actual)
            db.session.commit()
            flash('Sales logged successfully!', 'success')
            return redirect(url_for('actuals'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error logging sales: {str(e)}', 'danger')
    
    # Default to current week
    current_week_start = get_current_week_start()
    current_week_end = get_current_week_end()
    
    return render_template('actual_form.html', distributors=distributors, 
                          current_week_start=current_week_start,
                          current_week_end=current_week_end)

@app.route('/actuals/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_actual(id):
    actual = Actual.query.get_or_404(id)
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        week_start_date = request.form.get('week_start_date')
        week_end_date = request.form.get('week_end_date')
        actual_sales = request.form.get('actual_sales')
        
        # Validate inputs
        if not all([distributor_id, week_start_date, week_end_date, actual_sales]):
            flash('All fields are required', 'danger')
            return render_template('actual_form.html', actual=actual, distributors=distributors)
        
        try:
            # Check for duplicate entries (excluding current)
            existing = Actual.query.filter_by(
                distributor_id=distributor_id,
                week_start_date=week_start_date,
                week_end_date=week_end_date
            ).filter(Actual.id != id).first()
            
            if existing:
                flash('Sales already logged for this distributor and period.', 'danger')
                return render_template('actual_form.html', actual=actual, distributors=distributors)
            
            # Calculate period identifiers (month, quarter, year)
            month, quarter, year = calculate_periods(week_start_date)
            
            # Update actual
            actual.distributor_id = distributor_id
            actual.week_start_date = week_start_date
            actual.week_end_date = week_end_date
            actual.actual_sales = float(actual_sales)
            actual.month = month
            actual.quarter = quarter
            actual.year = year
            
            db.session.commit()
            flash('Sales updated successfully!', 'success')
            return redirect(url_for('actuals'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating sales: {str(e)}', 'danger')
    
    return render_template('actual_form.html', actual=actual, distributors=distributors)

@app.route('/actuals/<int:id>/delete', methods=['POST'])
@login_required
def delete_actual(id):
    actual = Actual.query.get_or_404(id)
    
    try:
        db.session.delete(actual)
        db.session.commit()
        flash('Sales record deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting sales record: {str(e)}', 'danger')
    
    return redirect(url_for('actuals'))

# Report Routes
@app.route('/reports')
@login_required
def reports():
    # Get current date for default values
    today = datetime.now()
    
    # Get financial year data
    current_fin_year = get_financial_year(today)
    current_month = today.strftime('%b')  # Current month name (short form)
    
    # Get selected filters from request or use defaults
    selected_financial_year = request.args.get('financial_year', current_fin_year)
    selected_month = request.args.get('month', current_month)
    distributor_id = request.args.get('distributor_id')
    
    # Get all distributors for the dropdown
    distributors = Distributor.query.all()
    
    # Get all financial years
    financial_years = get_all_financial_years(2020, 2035)
    
    # Get all months
    months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    
    return render_template(
        'reports.html',
        distributors=distributors,
        financial_years=financial_years,
        months=months,
        selected_financial_year=selected_financial_year,
        selected_month=selected_month,
        selected_distributor_id=distributor_id
    )

@app.route('/generate_report/<report_type>', methods=['POST'])
@login_required
def generate_report(report_type):
    distributor_id = request.form.get('distributor_id')
    financial_year = request.form.get('financial_year')
    month = request.form.get('month')
    
    if not all([distributor_id, financial_year, month]):
        flash('All fields are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get distributor
    distributor = Distributor.query.get_or_404(distributor_id)
    
    # Create period identifier for database query (e.g., "Apr-FY24-25")
    period_identifier = f"{month}-{financial_year}"
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, 'Monthly', period_identifier, db, Actual, Target)
    
    # Generate report
    if report_type == 'pdf':
        pdf_data = generate_pdf_report(distributor.name, 'Monthly', period_identifier, performance_data)
        
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{distributor.name}_Report_{month}_{financial_year}.pdf"
        )
    
    elif report_type == 'excel':
        excel_data = generate_excel_report(distributor.name, 'Monthly', period_identifier, performance_data)
        
        return send_file(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{distributor.name}_Report_{month}_{financial_year}.xlsx"
        )
    
    flash('Invalid report type', 'danger')
    return redirect(url_for('reports'))

@app.route('/send_email_report', methods=['POST'])
@login_required
def send_email_report_route():
    distributor_id = request.form.get('distributor_id')
    financial_year = request.form.get('financial_year')
    month = request.form.get('month')
    email = request.form.get('email')
    
    if not all([distributor_id, financial_year, month, email]):
        flash('All fields are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get distributor
    distributor = Distributor.query.get_or_404(distributor_id)
    
    # Create period identifier for database query (e.g., "Apr-FY24-25")
    period_identifier = f"{month}-{financial_year}"
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, 'Monthly', period_identifier, db, Actual, Target)
    
    # Generate reports
    pdf_data = generate_pdf_report(distributor.name, 'Monthly', period_identifier, performance_data)
    excel_data = generate_excel_report(distributor.name, 'Monthly', period_identifier, performance_data)
    
    try:
        # Send email with reports
        send_email_report(email, distributor.name, 'Monthly', period_identifier, pdf_data, excel_data)
        flash('Reports sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')
    
    return redirect(url_for('reports'))

@app.route('/bulk_export_reports', methods=['POST'])
@login_required
def bulk_export_reports():
    financial_year = request.form.get('financial_year')
    month = request.form.get('month')
    
    if not all([financial_year, month]):
        flash('Financial year and month are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get all distributors
    distributors = Distributor.query.all()
    
    if not distributors:
        flash('No distributors found', 'warning')
        return redirect(url_for('reports'))
    
    # Create period identifier for database query (e.g., "Apr-FY24-25")
    period_identifier = f"{month}-{financial_year}"
    
    # Create a ZIP file with reports for all distributors
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for distributor in distributors:
            # Get performance data
            performance_data = generate_performance_data(distributor.id, 'Monthly', period_identifier, db, Actual, Target)
            
            # Generate PDF report
            pdf_data = generate_pdf_report(distributor.name, 'Monthly', period_identifier, performance_data)
            pdf_filename = f"{distributor.name}_Report_{month}_{financial_year}.pdf"
            zf.writestr(pdf_filename, pdf_data)
            
            # Generate Excel report
            excel_data = generate_excel_report(distributor.name, 'Monthly', period_identifier, performance_data)
            excel_filename = f"{distributor.name}_Report_{month}_{financial_year}.xlsx"
            zf.writestr(excel_filename, excel_data)
    
    # Reset file pointer
    memory_file.seek(0)
    
    # Send the ZIP file
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"All_Distributors_Reports_{month}_{financial_year}.zip"
    )

# AJAX Routes
@app.route('/api/periods/<period_type>')
@login_required
def get_periods(period_type):
    today = datetime.now()
    
    if period_type == 'Monthly':
        # Get list of financial years from 2020 to 2035
        all_fin_years = get_all_financial_years(2020, 2035)
        
        # Generate all financial months
        periods = []
        month_names = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
        for fy in all_fin_years:
            for m in month_names:
                periods.append(f"{m}-{fy}")
    elif period_type == 'Quarterly':
        # Get list of financial years from 2020 to 2035
        all_fin_years = get_all_financial_years(2020, 2035)
        
        # Generate all financial quarters
        periods = []
        for fy in all_fin_years:
            for q in range(1, 5):
                periods.append(f"Q{q}-{fy}")
    elif period_type == 'Yearly':
        # Get list of financial years from 2020 to 2035
        periods = get_all_financial_years(2020, 2035)
    else:
        periods = []
    
    return jsonify(periods)

@app.route('/email/test', methods=['GET', 'POST'])
@login_required
def test_email():
    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email')
        
        if not recipient_email:
            flash('Email address is required', 'danger')
            return render_template('email_test.html')
        
        # First check configuration
        config_status = test_email_config()
        
        if not config_status['is_configured']:
            flash(f"Email not properly configured: {config_status['error']}", 'danger')
            return render_template('email_test.html', config_status=config_status)
        
        # Send test email
        result = send_test_email(recipient_email)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'danger')
        
        return render_template('email_test.html', config_status=config_status, result=result)
    
    # Check email configuration
    config_status = test_email_config()
    
    return render_template('email_test.html', config_status=config_status)

# Backup Routes
@app.route('/backup', methods=['GET', 'POST'])
@login_required
def backup_page():
    # Check if Supabase is configured
    is_configured = os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY")
    success_message = None
    error_message = None
    
    if request.method == 'POST':
        if 'perform_backup' in request.form:
            # Perform manual backup
            success = perform_backup()
            if success:
                success_message = "Backup created successfully!"
            else:
                error_message = "Failed to create backup. Check logs for details."
        elif 'restore_backup' in request.form:
            # Restore from selected backup
            backup_id = request.form.get('backup_id')
            if backup_id:
                success = restore_from_backup(backup_id)
                if success:
                    success_message = f"Database restored successfully from backup {backup_id}!"
                else:
                    error_message = f"Failed to restore from backup {backup_id}. Check logs for details."
            else:
                error_message = "No backup selected for restore."
    
    # Get available backups
    available_backups = get_available_backups() if is_configured else []
    
    # Flash messages if any
    if success_message:
        flash(success_message, 'success')
    if error_message:
        flash(error_message, 'danger')
    
    return render_template('backup.html', is_configured=is_configured, available_backups=available_backups)

@app.route('/send_to_distributor', methods=['POST'])
@login_required
def send_to_distributor():
    distributor_id = request.form.get('distributor_id')
    financial_year = request.form.get('financial_year')
    month = request.form.get('month')
    
    if not all([distributor_id, financial_year, month]):
        flash('All fields are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get distributor
    distributor = Distributor.query.get_or_404(distributor_id)
    
    # Verify distributor has an email
    if not distributor.email:
        flash('Selected distributor does not have an email address', 'danger')
        return redirect(url_for('reports'))
    
    # Create period identifier for database query (e.g., "Apr-FY24-25")
    period_identifier = f"{month}-{financial_year}"
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, 'Monthly', period_identifier, db, Actual, Target)
    
    # Generate reports
    pdf_data = generate_pdf_report(distributor.name, 'Monthly', period_identifier, performance_data)
    excel_data = generate_excel_report(distributor.name, 'Monthly', period_identifier, performance_data)
    
    try:
        # Send email with reports to distributor's email
        send_email_report(distributor.email, distributor.name, 'Monthly', period_identifier, pdf_data, excel_data)
        flash(f'Reports sent successfully to {distributor.name} ({distributor.email})!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')
    
    return redirect(url_for('reports'))

@app.route('/api/months/<financial_year>')
@login_required
def get_months(financial_year):
    month_names = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    return jsonify(month_names)

@app.route('/api/date_range/<financial_year>/<month>')
@login_required
def get_date_range(financial_year, month):
    """Return the date range for a given financial year and month."""
    # Parse the financial year to get the calendar year
    fy_start_year = int("20" + financial_year[2:4])
    
    # Map months to their calendar values
    month_map = {
        'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 
        'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3
    }
    
    # Determine the year for this month
    month_num = month_map[month]
    year = fy_start_year if month_num >= 4 else fy_start_year + 1
    
    # Get the first day of the month
    first_day = datetime(year, month_num, 1)
    
    # Calculate the next month's first day (to find end of month)
    if month_num == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month_num + 1, 1)
    
    # Last day of the month
    last_day = next_month - timedelta(days=1)
    
    # Determine the first week's start date (first Monday of month or last Monday of previous month)
    first_week_start = first_day - timedelta(days=first_day.weekday())
    
    # Get all the weeks in the month
    weeks = []
    current_week_start = first_week_start
    while current_week_start <= last_day:
        current_week_end = current_week_start + timedelta(days=6)
        weeks.append({
            'start': current_week_start.strftime('%Y-%m-%d'),
            'end': current_week_end.strftime('%Y-%m-%d'),
            'display': f"{current_week_start.strftime('%d %b')} - {current_week_end.strftime('%d %b')}"
        })
        current_week_start += timedelta(days=7)
    
    # By default, return the first week's date range
    return jsonify(weeks[0]['display'] if weeks else "No dates available")

@app.route('/batch_targets', methods=['GET'])
@login_required
def batch_targets():
    # Redirect to the main targets page
    return redirect(url_for('targets'))

@app.route('/batch_target_entry', methods=['GET'])
@login_required
def batch_target_entry():
    # Redirect to the main targets page
    return redirect(url_for('targets'))

@app.route('/batch_sales_entry', methods=['GET'])
@login_required
def batch_sales_entry():
    # Redirect to the main actuals page
    return redirect(url_for('actuals'))

@app.route('/save_batch_targets', methods=['POST'])
@login_required
def save_batch_targets():
    financial_year = request.form.get('financial_year')
    month = request.form.get('month')
    distributor_ids = request.form.getlist('distributor_ids')
    
    if not all([financial_year, month]) or not distributor_ids:
        flash('Please select at least one distributor and specify the period', 'danger')
        return redirect(url_for('targets'))
    
    # Create period identifier for database (e.g., "Apr-FY24-25")
    period_identifier = f"{month}-{financial_year}"
    
    try:
        # Process each selected distributor
        updated_count = 0
        new_count = 0
        
        for distributor_id in distributor_ids:
            target_value = request.form.get(f'target_values[{distributor_id}]')
            if not target_value or float(target_value) <= 0:
                continue
                
            # Check if target already exists
            existing = Target.query.filter_by(
                distributor_id=distributor_id,
                period_type='Monthly',
                period_identifier=period_identifier
            ).first()
            
            if existing:
                # Update existing target
                existing.target_value = float(target_value)
                updated_count += 1
            else:
                # Create new target
                new_target = Target(
                    distributor_id=distributor_id,
                    period_type='Monthly',
                    period_identifier=period_identifier,
                    target_value=float(target_value)
                )
                db.session.add(new_target)
                new_count += 1
        
        db.session.commit()
        
        if updated_count > 0 or new_count > 0:
            message = []
            if new_count > 0:
                message.append(f"{new_count} new targets set")
            if updated_count > 0:
                message.append(f"{updated_count} targets updated")
            flash(', '.join(message) + ' successfully!', 'success')
        else:
            flash('No changes made to targets', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving targets: {str(e)}', 'danger')
    
    return redirect(url_for('targets'))

@app.route('/save_batch_sales', methods=['POST'])
@login_required
def save_batch_sales():
    financial_year = request.form.get('financial_year')
    month = request.form.get('month')
    date_range = request.form.get('date_range')
    distributor_ids = request.form.getlist('distributor_ids')
    
    if not all([financial_year, month, date_range]) or not distributor_ids:
        flash('Please select at least one distributor and specify the period', 'danger')
        return redirect(url_for('actuals'))
    
    try:
        # Parse date range to get actual dates
        date_parts = date_range.split(' - ')
        if len(date_parts) != 2:
            flash('Invalid date range format', 'danger')
            return redirect(url_for('actuals'))
        
        # Parse "dd MMM" format for start and end dates
        start_day, start_month = date_parts[0].split(' ')
        end_day, end_month = date_parts[1].split(' ')
        
        # Map month abbreviations to numbers
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # Parse the financial year to get the calendar year
        fy_start_year = int("20" + financial_year[2:4])
        
        # Determine the year for start and end dates
        start_month_num = month_map[start_month]
        end_month_num = month_map[end_month]
        
        start_year = fy_start_year if start_month_num >= 4 else fy_start_year + 1
        end_year = fy_start_year if end_month_num >= 4 else fy_start_year + 1
        
        # Create date objects
        week_start_date = datetime(start_year, start_month_num, int(start_day)).strftime('%Y-%m-%d')
        week_end_date = datetime(end_year, end_month_num, int(end_day)).strftime('%Y-%m-%d')
        
        # Process each selected distributor
        updated_count = 0
        new_count = 0
        
        for distributor_id in distributor_ids:
            sales_value = request.form.get(f'sales_values[{distributor_id}]')
            if not sales_value or float(sales_value) <= 0:
                continue
                
            # Check if sales record already exists for this period
            existing = Actual.query.filter_by(
                distributor_id=distributor_id,
                week_start_date=week_start_date,
                week_end_date=week_end_date
            ).first()
            
            if existing:
                # Update existing sales record
                existing.actual_sales = float(sales_value)
                updated_count += 1
            else:
                # Calculate period identifiers
                calculated_month, calculated_quarter, calculated_year = calculate_periods(week_start_date)
                
                # Create new sales record
                new_actual = Actual(
                    distributor_id=distributor_id,
                    week_start_date=week_start_date,
                    week_end_date=week_end_date,
                    actual_sales=float(sales_value),
                    month=month,
                    quarter=calculated_quarter,
                    year=calculated_year
                )
                db.session.add(new_actual)
                new_count += 1
        
        db.session.commit()
        
        if updated_count > 0 or new_count > 0:
            message = []
            if new_count > 0:
                message.append(f"{new_count} new sales records created")
            if updated_count > 0:
                message.append(f"{updated_count} sales records updated")
            flash(', '.join(message) + ' successfully!', 'success')
        else:
            flash('No changes made to sales records', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error saving sales: {str(e)}', 'danger')
    
    return redirect(url_for('actuals'))
