from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import io
import logging

from app import app, db
from models import User, Distributor, Target, Actual
from utils import (
    calculate_periods, get_current_week_start, generate_performance_data,
    generate_pdf_report, generate_excel_report, send_email_report
)

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
    current_month = today.strftime('%b-%Y')
    current_quarter = f"Q{((today.month - 1) // 3) + 1}-{today.year}"
    current_year = str(today.year)
    
    # Default period identifier based on period type
    if period_type == 'Weekly':
        week_num = int(today.strftime('%W')) + 1  # Week number (1-52)
        default_period = f"Wk {week_num}-{today.year}"
    elif period_type == 'Monthly':
        default_period = current_month
    elif period_type == 'Quarterly':
        default_period = current_quarter
    else:
        default_period = current_year
    
    period_identifier = request.args.get('period_identifier', default_period)
    distributor_id = request.args.get('distributor_id')
    
    # Get all distributors for the dropdown
    distributors = Distributor.query.all()
    
    # Generate period options for dropdowns
    period_options = {
        'Weekly': [f"Wk {w}-{today.year}" for w in range(1, 53)],
        'Monthly': [f"{m}-{today.year}" for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']],
        'Quarterly': [f"Q{q}-{today.year}" for q in range(1, 5)],
        'Yearly': [str(y) for y in range(today.year - 2, today.year + 3)]
    }
    
    # Get performance data
    overall_data = generate_performance_data(None, period_type, period_identifier, db, Actual, Target)
    
    # Get distributor-specific performance data
    distributor_performance = []
    for distributor in distributors:
        perf_data = generate_performance_data(distributor.id, period_type, period_identifier, db, Actual, Target)
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
        
        # Validate name uniqueness
        existing = Distributor.query.filter(db.func.lower(Distributor.name) == db.func.lower(name)).first()
        if existing:
            flash('Distributor name already exists.', 'danger')
            return render_template('distributor_form.html')
        
        distributor = Distributor(name=name, email=email, whatsapp=whatsapp)
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
        period_identifier = request.form.get('period_identifier')
        target_value = request.form.get('target_value')
        
        # Validate inputs
        if not all([distributor_id, period_type, period_identifier, target_value]):
            flash('All fields are required', 'danger')
            return render_template('target_form.html', distributors=distributors)
        
        try:
            # Check for duplicate targets
            existing = Target.query.filter_by(
                distributor_id=distributor_id,
                period_type=period_type,
                period_identifier=period_identifier
            ).first()
            
            if existing:
                flash('Target already set for this distributor/period.', 'danger')
                return render_template('target_form.html', distributors=distributors)
            
            # Create new target
            target = Target(
                distributor_id=distributor_id,
                period_type=period_type,
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
    
    # Generate period options
    today = datetime.now()
    period_options = {
        'Weekly': [f"Wk {w}-{today.year}" for w in range(1, 53)],
        'Monthly': [f"{m}-{today.year}" for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']],
        'Quarterly': [f"Q{q}-{today.year}" for q in range(1, 5)],
        'Yearly': [str(y) for y in range(today.year - 2, today.year + 3)]
    }
    
    return render_template('target_form.html', distributors=distributors, period_options=period_options)

@app.route('/targets/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_target(id):
    target = Target.query.get_or_404(id)
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        period_type = request.form.get('period_type')
        period_identifier = request.form.get('period_identifier')
        target_value = request.form.get('target_value')
        
        # Validate inputs
        if not all([distributor_id, period_type, period_identifier, target_value]):
            flash('All fields are required', 'danger')
            return render_template('target_form.html', target=target, distributors=distributors)
        
        try:
            # Check for duplicate targets (excluding current)
            existing = Target.query.filter_by(
                distributor_id=distributor_id,
                period_type=period_type,
                period_identifier=period_identifier
            ).filter(Target.id != id).first()
            
            if existing:
                flash('Target already set for this distributor/period.', 'danger')
                return render_template('target_form.html', target=target, distributors=distributors)
            
            # Update target
            target.distributor_id = distributor_id
            target.period_type = period_type
            target.period_identifier = period_identifier
            target.target_value = float(target_value)
            
            db.session.commit()
            flash('Target updated successfully!', 'success')
            return redirect(url_for('targets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating target: {str(e)}', 'danger')
    
    # Generate period options
    today = datetime.now()
    period_options = {
        'Weekly': [f"Wk {w}-{today.year}" for w in range(1, 53)],
        'Monthly': [f"{m}-{today.year}" for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']],
        'Quarterly': [f"Q{q}-{today.year}" for q in range(1, 5)],
        'Yearly': [str(y) for y in range(today.year - 2, today.year + 3)]
    }
    
    return render_template('target_form.html', target=target, distributors=distributors, period_options=period_options)

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
        actual_sales = request.form.get('actual_sales')
        
        # Validate inputs
        if not all([distributor_id, week_start_date, actual_sales]):
            flash('All fields are required', 'danger')
            return render_template('actual_form.html', distributors=distributors)
        
        try:
            # Check for duplicate entries
            existing = Actual.query.filter_by(
                distributor_id=distributor_id,
                week_start_date=week_start_date
            ).first()
            
            if existing:
                flash('Sales already logged for this distributor/week.', 'danger')
                return render_template('actual_form.html', distributors=distributors)
            
            # Calculate period identifiers (month, quarter, year)
            month, quarter, year = calculate_periods(week_start_date)
            
            # Create new actual
            actual = Actual(
                distributor_id=distributor_id,
                week_start_date=week_start_date,
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
    
    return render_template('actual_form.html', distributors=distributors, current_week_start=current_week_start)

@app.route('/actuals/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_actual(id):
    actual = Actual.query.get_or_404(id)
    distributors = Distributor.query.all()
    
    if request.method == 'POST':
        distributor_id = request.form.get('distributor_id')
        week_start_date = request.form.get('week_start_date')
        actual_sales = request.form.get('actual_sales')
        
        # Validate inputs
        if not all([distributor_id, week_start_date, actual_sales]):
            flash('All fields are required', 'danger')
            return render_template('actual_form.html', actual=actual, distributors=distributors)
        
        try:
            # Check for duplicate entries (excluding current)
            existing = Actual.query.filter_by(
                distributor_id=distributor_id,
                week_start_date=week_start_date
            ).filter(Actual.id != id).first()
            
            if existing:
                flash('Sales already logged for this distributor/week.', 'danger')
                return render_template('actual_form.html', actual=actual, distributors=distributors)
            
            # Calculate period identifiers (month, quarter, year)
            month, quarter, year = calculate_periods(week_start_date)
            
            # Update actual
            actual.distributor_id = distributor_id
            actual.week_start_date = week_start_date
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
        week_num = int(today.strftime('%W')) + 1  # Week number (1-52)
        default_period = f"Wk {week_num}-{today.year}"
    elif period_type == 'Monthly':
        default_period = today.strftime('%b-%Y')
    elif period_type == 'Quarterly':
        default_period = f"Q{((today.month - 1) // 3) + 1}-{today.year}"
    else:
        default_period = str(today.year)
    
    period_identifier = request.args.get('period_identifier', default_period)
    distributor_id = request.args.get('distributor_id')
    
    # Generate period options for dropdowns
    period_options = {
        'Weekly': [f"Wk {w}-{today.year}" for w in range(1, 53)],
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
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, period_type, period_identifier, db, Actual, Target)
    
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
    
    if not all([distributor_id, period_type, period_identifier]):
        flash('All fields are required', 'danger')
        return redirect(url_for('reports'))
    
    # Get distributor
    distributor = Distributor.query.get_or_404(distributor_id)
    
    # Validate email
    if not distributor.email:
        flash('Distributor has no email address', 'danger')
        return redirect(url_for('reports'))
    
    # Get performance data
    performance_data = generate_performance_data(distributor.id, period_type, period_identifier, db, Actual, Target)
    
    # Generate reports
    pdf_data = generate_pdf_report(distributor.name, period_type, period_identifier, performance_data)
    excel_data = generate_excel_report(distributor.name, period_type, period_identifier, performance_data)
    
    # Send email
    success = send_email_report(distributor.email, distributor.name, period_type, period_identifier, pdf_data, excel_data)
    
    if success:
        flash(f'Report sent to {distributor.email} successfully!', 'success')
    else:
        flash('Failed to send email. Please check email configuration.', 'danger')
    
    return redirect(url_for('reports'))

# AJAX Routes
@app.route('/api/periods/<period_type>')
@login_required
def get_periods(period_type):
    today = datetime.now()
    
    if period_type == 'Weekly':
        periods = [f"Wk {w}-{today.year}" for w in range(1, 53)]
    elif period_type == 'Monthly':
        periods = [f"{m}-{today.year}" for m in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']]
    elif period_type == 'Quarterly':
        periods = [f"Q{q}-{today.year}" for q in range(1, 5)]
    elif period_type == 'Yearly':
        periods = [str(y) for y in range(today.year - 2, today.year + 3)]
    else:
        periods = []
    
    return jsonify(periods)
