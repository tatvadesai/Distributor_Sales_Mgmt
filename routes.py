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
    # Set default period if none selected
    period_type = request.args.get('period_type', 'Weekly')
    
    # Get current dates for default selections
    today = datetime.now()
    current_week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    current_week_end = (today + timedelta(days=6-today.weekday())).strftime('%Y-%m-%d')
    current_month = today.strftime('%b-%Y')
    current_quarter = f"Q{((today.month - 1) // 3) + 1}-{today.year}"
    current_year = str(today.year)
    
    # Get financial year data
    current_fin_year = get_financial_year(today)
    current_fin_quarter = get_financial_quarter(today)
    current_fin_month = get_financial_month(today)
    
    # Default period identifier based on period type
    if period_type == 'Weekly':
        week_num = int(today.strftime('%W')) + 1  # Week number (1-52)
        default_period = f"{current_week_start} to {current_week_end}"
    elif period_type == 'Monthly':
        default_period = current_fin_month
    elif period_type == 'Quarterly':
        default_period = current_fin_quarter
    elif period_type == 'Yearly':
        default_period = current_fin_year
    else:
        default_period = current_year
    
    period_identifier = request.args.get('period_identifier', default_period)
    distributor_id = request.args.get('distributor_id')
    
    # Get all distributors for the dropdown
    distributors = Distributor.query.all()
    
    # Generate period options for dropdowns
    if period_type == 'Weekly':
        # Get all weekly targets
        weekly_targets = Target.query.filter_by(period_type='Weekly').all()
        period_options = {
            'Weekly': []
        }
        
        # Use date ranges from targets
        for target in weekly_targets:
            if target.week_start_date and target.week_end_date:
                date_range = f"{target.week_start_date} to {target.week_end_date}"
                if date_range not in period_options['Weekly']:
                    period_options['Weekly'].append(date_range)
        
        # If no targets with dates found, use current week
        if not period_options['Weekly']:
            period_options['Weekly'] = [f"{current_week_start} to {current_week_end}"]
    else:
        # Get list of financial years from 2020 to 2035
        all_fin_years = get_all_financial_years(2020, 2035)
        
        # Generate all financial quarters
        all_fin_quarters = []
        for fy in all_fin_years:
            for q in range(1, 5):
                all_fin_quarters.append(f"Q{q}-{fy}")
        
        # Generate all financial months
        all_fin_months = []
        month_names = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
        for fy in all_fin_years:
            for m in month_names:
                all_fin_months.append(f"{m}-{fy}")
        
        period_options = {
            'Weekly': [f"Wk {w}-{today.year}" for w in range(1, 53)],
            'Monthly': all_fin_months,
            'Quarterly': all_fin_quarters,
            'Yearly': all_fin_years
        }
    
    # Get lookup period identifier for database query
    lookup_period_identifier = period_identifier
    if period_type == 'Weekly' and ' to ' in period_identifier:
        # Find target with these dates
        start_date, end_date = period_identifier.split(' to ')
        target = Target.query.filter_by(
            period_type='Weekly',
            week_start_date=start_date,
            week_end_date=end_date
        ).first()
        
        if target:
            lookup_period_identifier = target.period_identifier
        else:
            # Find the week number for this date range
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                week_num = int(start_dt.strftime('%W')) + 1
                year = start_dt.year
                lookup_period_identifier = f"Wk {week_num}-{year}"
            except:
                pass
    
    # Get performance data
    overall_data = generate_performance_data(None, period_type, lookup_period_identifier, db, Actual, Target)
    
    # Get distributor-specific performance data
    distributor_performance = []
    for distributor in distributors:
        perf_data = generate_performance_data(distributor.id, period_type, lookup_period_identifier, db, Actual, Target)
        distributor_performance.append({
            'id': distributor.id,
            'name': distributor.name,
            **perf_data
        })
    
    # Sort by achievement percent (descending)
    distributor_performance.sort(key=lambda x: x['achievement_percent'], reverse=True)
    
    return render_template(
        'dashboard.html',
        distributors=distributors,
        period_type=period_type,
        period_identifier=period_identifier,
        selected_distributor_id=distributor_id,
        period_options=period_options,
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
    targets = Target.query.order_by(Target.period_type, Target.period_identifier, Target.distributor_id).all()
    distributors = Distributor.query.all()
    
    return render_template('targets.html', targets=targets, distributors=distributors)

@app.route('/targets/new', methods=['GET', 'POST'])
@login_required
def new_target():
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        period_type = request.form.get('period_type')
        period_identifier = request.form.get('period_identifier', '')
        target_value = request.form.get('target_value')
        week_start_date = request.form.get('week_start_date', '')
        week_end_date = request.form.get('week_end_date', '')
        
        # For Weekly periods, we now use custom dates
        if period_type == 'Weekly':
            # Validate weekly dates are provided
            if not all([distributor_id, period_type, target_value, week_start_date, week_end_date]):
                flash('Distributor, period type, start date, end date, and target value are required', 'danger')
                return render_template('target_form.html', distributors=distributors)
                
            # Generate a period identifier based on the start date
            start_date = datetime.strptime(week_start_date, '%Y-%m-%d')
            week_num = int(start_date.strftime('%W')) + 1  # Week number (1-52)
            period_identifier = f"Wk {week_num}-{start_date.year}"
        else:
            # For non-weekly periods, validate as before
            if not all([distributor_id, period_type, period_identifier, target_value]):
                flash('All fields are required', 'danger')
                return render_template('target_form.html', distributors=distributors)
        
        try:
            # Check for duplicate targets
            existing_query = Target.query.filter_by(
                distributor_id=distributor_id,
                period_type=period_type
            )
            
            if period_type == 'Weekly':
                # For weekly, check for overlapping dates
                existing = existing_query.filter(
                    ((Target.week_start_date <= week_start_date) & (Target.week_end_date >= week_start_date)) | 
                    ((Target.week_start_date <= week_end_date) & (Target.week_end_date >= week_end_date)) |
                    ((Target.week_start_date >= week_start_date) & (Target.week_end_date <= week_end_date))
                ).first()
                
                if existing:
                    flash('Target already exists for this date range. Please select a different week.', 'danger')
                    return render_template('target_form.html', distributors=distributors)
            else:
                # For non-weekly, check by period identifier
                existing = existing_query.filter_by(period_identifier=period_identifier).first()
                
                if existing:
                    flash('Target already set for this distributor/period.', 'danger')
                    return render_template('target_form.html', distributors=distributors)
            
            # Create new target
            target = Target(
                distributor_id=distributor_id,
                period_type=period_type,
                period_identifier=period_identifier,
                target_value=float(target_value),
                week_start_date=week_start_date if period_type == 'Weekly' else None,
                week_end_date=week_end_date if period_type == 'Weekly' else None
            )
            
            db.session.add(target)
            db.session.commit()
            flash('Target added successfully!', 'success')
            return redirect(url_for('targets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating target: {str(e)}', 'danger')
    
    # Generate period options
    today = datetime.now()
    
    # Get list of financial years from 2020 to 2035
    all_fin_years = get_all_financial_years(2020, 2035)
    
    # Generate all financial quarters
    all_fin_quarters = []
    for fy in all_fin_years:
        for q in range(1, 5):
            all_fin_quarters.append(f"Q{q}-{fy}")
    
    # Generate all financial months
    all_fin_months = []
    month_names = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    for fy in all_fin_years:
        for m in month_names:
            all_fin_months.append(f"{m}-{fy}")
    
    period_options = {
        'Weekly': [f"Wk {w}-{today.year}" for w in range(1, 53)],
        'Monthly': all_fin_months,
        'Quarterly': all_fin_quarters,
        'Yearly': all_fin_years
    }
    
    # Get current week dates for default values
    current_week_start = get_current_week_start()
    current_week_end = get_current_week_end()
    
    return render_template('target_form.html', distributors=distributors, period_options=period_options,
                           current_week_start=current_week_start, current_week_end=current_week_end)

@app.route('/targets/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_target(id):
    target = Target.query.get_or_404(id)
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        period_type = request.form.get('period_type')
        period_identifier = request.form.get('period_identifier', '')
        target_value = request.form.get('target_value')
        week_start_date = request.form.get('week_start_date', '')
        week_end_date = request.form.get('week_end_date', '')
        
        # For Weekly periods, we now use custom dates
        if period_type == 'Weekly':
            # Validate weekly dates are provided
            if not all([distributor_id, period_type, target_value, week_start_date, week_end_date]):
                flash('Distributor, period type, start date, end date, and target value are required', 'danger')
                return render_template('target_form.html', target=target, distributors=distributors)
                
            # Generate a period identifier based on the start date
            start_date = datetime.strptime(week_start_date, '%Y-%m-%d')
            week_num = int(start_date.strftime('%W')) + 1  # Week number (1-52)
            period_identifier = f"Wk {week_num}-{start_date.year}"
        else:
            # For non-weekly periods, validate as before
            if not all([distributor_id, period_type, period_identifier, target_value]):
                flash('All fields are required', 'danger')
                return render_template('target_form.html', target=target, distributors=distributors)
        
        try:
            # Check for duplicate targets (excluding current)
            existing_query = Target.query.filter_by(
                distributor_id=distributor_id,
                period_type=period_type
            ).filter(Target.id != id)
            
            if period_type == 'Weekly':
                # For weekly, check for overlapping dates
                existing = existing_query.filter(
                    ((Target.week_start_date <= week_start_date) & (Target.week_end_date >= week_start_date)) | 
                    ((Target.week_start_date <= week_end_date) & (Target.week_end_date >= week_end_date)) |
                    ((Target.week_start_date >= week_start_date) & (Target.week_end_date <= week_end_date))
                ).first()
                
                if existing:
                    flash('Target already exists for this date range. Please select a different week.', 'danger')
                    return render_template('target_form.html', target=target, distributors=distributors)
            else:
                # For non-weekly, check by period identifier
                existing = existing_query.filter_by(period_identifier=period_identifier).first()
                
                if existing:
                    flash('Target already set for this distributor/period.', 'danger')
                    return render_template('target_form.html', target=target, distributors=distributors)
            
            # Update target
            target.distributor_id = distributor_id
            target.period_type = period_type
            target.period_identifier = period_identifier
            target.target_value = float(target_value)
            target.week_start_date = week_start_date if period_type == 'Weekly' else None
            target.week_end_date = week_end_date if period_type == 'Weekly' else None
            
            db.session.commit()
            flash('Target updated successfully!', 'success')
            return redirect(url_for('targets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating target: {str(e)}', 'danger')
    
    # Generate period options
    today = datetime.now()
    
    # Get list of financial years from 2020 to 2035
    all_fin_years = get_all_financial_years(2020, 2035)
    
    # Generate all financial quarters
    all_fin_quarters = []
    for fy in all_fin_years:
        for q in range(1, 5):
            all_fin_quarters.append(f"Q{q}-{fy}")
    
    # Generate all financial months
    all_fin_months = []
    month_names = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    for fy in all_fin_years:
        for m in month_names:
            all_fin_months.append(f"{m}-{fy}")
    
    period_options = {
        'Weekly': [f"Wk {w}-{today.year}" for w in range(1, 53)],
        'Monthly': all_fin_months,
        'Quarterly': all_fin_quarters,
        'Yearly': all_fin_years
    }
    
    # Get current week dates for default values
    current_week_start = get_current_week_start()
    current_week_end = get_current_week_end()
    
    return render_template('target_form.html', target=target, distributors=distributors, period_options=period_options,
                          current_week_start=current_week_start, current_week_end=current_week_end)

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
    actuals = Actual.query.order_by(Actual.week_start_date.desc(), Actual.distributor_id).all()
    distributors = Distributor.query.all()
    
    return render_template('actuals.html', actuals=actuals, distributors=distributors)

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
    distributors = Distributor.query.all()
    
    # Default to current period
    today = datetime.now()
    period_type = request.args.get('period_type', 'Monthly')
    
    if period_type == 'Weekly':
        # Use date format instead of week number
        current_week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        current_week_end = (today + timedelta(days=6-today.weekday())).strftime('%Y-%m-%d')
        default_period = f"{current_week_start} to {current_week_end}"
        
        # Try to find a target with these dates
        target = Target.query.filter_by(
            period_type='Weekly',
            week_start_date=current_week_start,
            week_end_date=current_week_end
        ).first()
        
        if target:
            default_period = f"{target.week_start_date} to {target.week_end_date}"
    elif period_type == 'Monthly':
        default_period = today.strftime('%b-%Y')
    elif period_type == 'Quarterly':
        default_period = f"Q{((today.month - 1) // 3) + 1}-{today.year}"
    else:
        default_period = str(today.year)
    
    period_identifier = request.args.get('period_identifier', default_period)
    distributor_id = request.args.get('distributor_id')
    
    # Generate period options for dropdowns
    if period_type == 'Weekly':
        # Get all weekly targets
        weekly_targets = Target.query.filter_by(period_type='Weekly').all()
        period_options = {
            'Weekly': []
        }
        
        # Use date ranges from targets
        for target in weekly_targets:
            if target.week_start_date and target.week_end_date:
                date_range = f"{target.week_start_date} to {target.week_end_date}"
                if date_range not in period_options['Weekly']:
                    period_options['Weekly'].append(date_range)
        
        # If no targets with dates found, use current week
        if not period_options['Weekly']:
            period_options['Weekly'] = [f"{current_week_start} to {current_week_end}"]
    else:
        period_options = {
            'Weekly': [],  # Will be populated by the API if needed
            'Monthly': [f"{m}-{today.year}" for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']],
            'Quarterly': [f"Q{q}-{today.year}" for q in range(1, 5)],
            'Yearly': [str(y) for y in range(today.year - 2, today.year + 3)]
        }
    
    return render_template(
        'reports.html',
        distributors=distributors,
        period_type=period_type,
        period_identifier=period_identifier,
        selected_distributor_id=distributor_id,
        period_options=period_options
    )

@app.route('/generate_report/<report_type>', methods=['POST'])
@login_required
def generate_report(report_type):
    distributor_id = request.form.get('distributor_id')
    period_type = request.form.get('period_type')
    period_identifier = request.form.get('period_identifier')
    
    if not all([distributor_id, period_type, period_identifier]):
        flash('All fields are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get distributor
    distributor = Distributor.query.get_or_404(distributor_id)
    
    # Convert date range to period identifier for database query if needed
    lookup_period_identifier = period_identifier
    if period_type == 'Weekly' and ' to ' in period_identifier:
        # Extract dates from the format "YYYY-MM-DD to YYYY-MM-DD"
        dates = period_identifier.split(' to ')
        if len(dates) == 2:
            # Find the target with these dates
            target = Target.query.filter_by(
                period_type='Weekly', 
                week_start_date=dates[0], 
                week_end_date=dates[1]
            ).first()
            
            if target:
                lookup_period_identifier = target.period_identifier
            else:
                # Try to calculate the week number
                try:
                    start_dt = datetime.strptime(dates[0], '%Y-%m-%d')
                    week_num = int(start_dt.strftime('%W')) + 1
                    year = start_dt.year
                    lookup_period_identifier = f"Wk {week_num}-{year}"
                except:
                    pass
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, period_type, lookup_period_identifier, db, Actual, Target)
    
    # Generate report
    if report_type == 'pdf':
        pdf_data = generate_pdf_report(distributor.name, period_type, period_identifier, performance_data)
        
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{distributor.name}_Report_{period_identifier}.pdf"
        )
    
    elif report_type == 'excel':
        excel_data = generate_excel_report(distributor.name, period_type, period_identifier, performance_data)
        
        return send_file(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{distributor.name}_Report_{period_identifier}.xlsx"
        )
    
    flash('Invalid report type', 'danger')
    return redirect(url_for('reports'))

@app.route('/send_email_report', methods=['POST'])
@login_required
def send_email_report_route():
    distributor_id = request.form.get('distributor_id')
    period_type = request.form.get('period_type')
    period_identifier = request.form.get('period_identifier')
    email = request.form.get('email')
    
    if not all([distributor_id, period_type, period_identifier, email]):
        flash('All fields are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get distributor
    distributor = Distributor.query.get_or_404(distributor_id)
    
    # Convert date range to period identifier for database query if needed
    lookup_period_identifier = period_identifier
    if period_type == 'Weekly' and ' to ' in period_identifier:
        # Extract dates from the format "YYYY-MM-DD to YYYY-MM-DD"
        dates = period_identifier.split(' to ')
        if len(dates) == 2:
            # Find the target with these dates
            target = Target.query.filter_by(
                period_type='Weekly', 
                week_start_date=dates[0], 
                week_end_date=dates[1]
            ).first()
            
            if target:
                lookup_period_identifier = target.period_identifier
            else:
                # Try to calculate the week number
                try:
                    start_dt = datetime.strptime(dates[0], '%Y-%m-%d')
                    week_num = int(start_dt.strftime('%W')) + 1
                    year = start_dt.year
                    lookup_period_identifier = f"Wk {week_num}-{year}"
                except:
                    pass
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, period_type, lookup_period_identifier, db, Actual, Target)
    
    # Generate reports
    pdf_data = generate_pdf_report(distributor.name, period_type, period_identifier, performance_data)
    excel_data = generate_excel_report(distributor.name, period_type, period_identifier, performance_data)
    
    try:
        # Send email with reports
        send_email_report(email, distributor.name, period_type, period_identifier, pdf_data, excel_data)
        flash('Reports sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')
    
    return redirect(url_for('reports'))

@app.route('/bulk_export_reports', methods=['POST'])
@login_required
def bulk_export_reports():
    period_type = request.form.get('period_type')
    period_identifier = request.form.get('period_identifier')
    
    if not all([period_type, period_identifier]):
        flash('Period type and period are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get all distributors
    distributors = Distributor.query.all()
    
    if not distributors:
        flash('No distributors found', 'warning')
        return redirect(url_for('reports'))
    
    # Create a ZIP file with reports for all distributors
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for distributor in distributors:
            # Convert date range to period identifier for database query if needed
            lookup_period_identifier = period_identifier
            if period_type == 'Weekly' and ' to ' in period_identifier:
                # Extract dates from the format "YYYY-MM-DD to YYYY-MM-DD"
                dates = period_identifier.split(' to ')
                if len(dates) == 2:
                    # Find the target with these dates
                    target = Target.query.filter_by(
                        period_type='Weekly', 
                        week_start_date=dates[0], 
                        week_end_date=dates[1]
                    ).first()
                    
                    if target:
                        lookup_period_identifier = target.period_identifier
                    else:
                        # Try to calculate the week number
                        try:
                            start_dt = datetime.strptime(dates[0], '%Y-%m-%d')
                            week_num = int(start_dt.strftime('%W')) + 1
                            year = start_dt.year
                            lookup_period_identifier = f"Wk {week_num}-{year}"
                        except:
                            pass
            
            # Get performance data
            performance_data = generate_performance_data(distributor.id, period_type, lookup_period_identifier, db, Actual, Target)
            
            # Generate PDF report
            pdf_data = generate_pdf_report(distributor.name, period_type, period_identifier, performance_data)
            pdf_filename = f"{distributor.name}_Report_{period_identifier}.pdf"
            zf.writestr(pdf_filename, pdf_data)
            
            # Generate Excel report
            excel_data = generate_excel_report(distributor.name, period_type, period_identifier, performance_data)
            excel_filename = f"{distributor.name}_Report_{period_identifier}.xlsx"
            zf.writestr(excel_filename, excel_data)
    
    memory_file.seek(0)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"All_Distributors_Reports_{period_type}_{period_identifier}_{timestamp}.zip"
    )

# AJAX Routes
@app.route('/api/periods/<period_type>')
@login_required
def get_periods(period_type):
    today = datetime.now()
    
    if period_type == 'Weekly':
        # Get all weekly targets
        weekly_targets = Target.query.filter_by(period_type='Weekly').all()
        
        # Extract date ranges from targets
        periods = []
        for target in weekly_targets:
            if target.week_start_date and target.week_end_date:
                date_range = f"{target.week_start_date} to {target.week_end_date}"
                if date_range not in periods:
                    periods.append(date_range)
        
        # If no targets with dates found, use current week
        if not periods:
            current_week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            current_week_end = (today + timedelta(days=6-today.weekday())).strftime('%Y-%m-%d')
            periods = [f"{current_week_start} to {current_week_end}"]
    elif period_type == 'Monthly':
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
    period_type = request.form.get('period_type')
    period_identifier = request.form.get('period_identifier')
    
    if not all([distributor_id, period_type, period_identifier]):
        flash('All fields are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get distributor
    distributor = Distributor.query.get_or_404(distributor_id)
    
    # Verify distributor has an email
    if not distributor.email:
        flash('Selected distributor does not have an email address', 'danger')
        return redirect(url_for('reports'))
    
    # Convert date range to period identifier for database query if needed
    lookup_period_identifier = period_identifier
    if period_type == 'Weekly' and ' to ' in period_identifier:
        # Extract dates from the format "YYYY-MM-DD to YYYY-MM-DD"
        dates = period_identifier.split(' to ')
        if len(dates) == 2:
            # Find the target with these dates
            target = Target.query.filter_by(
                period_type='Weekly', 
                week_start_date=dates[0], 
                week_end_date=dates[1]
            ).first()
            
            if target:
                lookup_period_identifier = target.period_identifier
            else:
                # Try to calculate the week number
                try:
                    start_dt = datetime.strptime(dates[0], '%Y-%m-%d')
                    week_num = int(start_dt.strftime('%W')) + 1
                    year = start_dt.year
                    lookup_period_identifier = f"Wk {week_num}-{year}"
                except:
                    pass
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, period_type, lookup_period_identifier, db, Actual, Target)
    
    # Generate reports
    pdf_data = generate_pdf_report(distributor.name, period_type, period_identifier, performance_data)
    excel_data = generate_excel_report(distributor.name, period_type, period_identifier, performance_data)
    
    try:
        # Send email with reports to distributor's email
        send_email_report(distributor.email, distributor.name, period_type, period_identifier, pdf_data, excel_data)
        flash(f'Reports sent successfully to {distributor.name} ({distributor.email})!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')
    
    return redirect(url_for('reports'))
