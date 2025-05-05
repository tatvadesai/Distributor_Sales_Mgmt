from datetime import datetime, timedelta
import pandas as pd
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import logging
from sqlalchemy import func # Ensure func is imported

def calculate_periods(week_start_date_str):
    """
    Calculate month, quarter, and year for a given week start date
    Now supporting financial years (April-March)
    
    Args:
        week_start_date_str (str): Week start date in 'YYYY-MM-DD' format
        
    Returns:
        tuple: (month, quarter, year) as strings
    """
    try:
        dt = datetime.strptime(week_start_date_str, '%Y-%m-%d')
        
        # Get financial year, quarter and month
        fin_year = get_financial_year(dt)
        fin_quarter = get_financial_quarter(dt)
        fin_month = get_financial_month(dt)
        
        return fin_month, fin_quarter, fin_year
    except Exception as e:
        # Fallback to standard calendar periods if there's an error
        month = dt.strftime('%b-%Y')
        quarter = f"Q{((dt.month - 1) // 3) + 1}-{dt.year}"
        year = str(dt.year)
        return month, quarter, year

def get_current_week_start():
    """Get the Monday of the current week"""
    today = datetime.now()
    return (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

def get_current_week_end():
    """Get the Sunday of the current week"""
    today = datetime.now()
    return (today + timedelta(days=6-today.weekday())).strftime('%Y-%m-%d')

def get_period_weeks(period_type, period_identifier):
    """
    Get list of week start dates for a given period
    
    Args:
        period_type (str): 'Weekly', 'Monthly', 'Quarterly', 'Yearly'
        period_identifier (str): Period identifier like 'Apr-2025', 'Q2-2025', '2025'
        
    Returns:
        list: List of week start dates in 'YYYY-MM-DD' format
    """
    if period_type == 'Weekly':
        # Assuming period_identifier is in 'Wk XX-YYYY' format
        parts = period_identifier.split(' ')
        if len(parts) >= 2:
            week_num = int(parts[1].split('-')[0])
            year = int(parts[1].split('-')[1])
            # Calculate the date of the first day of the week
            first_day = datetime(year, 1, 1)
            if first_day.weekday() != 0:  # If not Monday
                first_day = first_day - timedelta(days=first_day.weekday())
            week_start = first_day + timedelta(weeks=week_num-1)
            return [week_start.strftime('%Y-%m-%d')]
        return []
        
    elif period_type == 'Monthly':
        # Assuming period_identifier is in 'MMM-YYYY' format
        try:
            date = datetime.strptime(period_identifier, '%b-%Y')
            start_month = date.replace(day=1)
            # Get all Mondays in the month
            weeks = []
            current = start_month - timedelta(days=start_month.weekday())  # First Monday before or on month start
            if current.month != start_month.month:
                current += timedelta(days=7)  # First Monday in the month
            
            while current.month == start_month.month:
                weeks.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=7)
            
            return weeks
        except ValueError:
            return []
            
    elif period_type == 'Quarterly':
        # Assuming period_identifier is in 'QX-YYYY' format
        try:
            quarter = int(period_identifier[1])
            year = int(period_identifier.split('-')[1])
            
            # Define the months in the quarter
            start_month = (quarter - 1) * 3 + 1
            months = [start_month, start_month + 1, start_month + 2]
            
            # Get all weeks for each month in the quarter
            weeks = []
            for month in months:
                start_date = datetime(year, month, 1)
                # Get all Mondays in the month
                current = start_date - timedelta(days=start_date.weekday())  # First Monday before or on month start
                if current.month != month:
                    current += timedelta(days=7)  # First Monday in the month
                
                end_date = (datetime(year, month+1, 1) if month < 12 else datetime(year+1, 1, 1)) - timedelta(days=1)
                
                while current.date() <= end_date.date():
                    weeks.append(current.strftime('%Y-%m-%d'))
                    current += timedelta(days=7)
            
            return weeks
        except (ValueError, IndexError):
            return []
            
    elif period_type == 'Yearly':
        # Assuming period_identifier is just the year
        try:
            year = int(period_identifier)
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            # Get all Mondays in the year
            weeks = []
            current = start_date - timedelta(days=start_date.weekday())  # First Monday before or on year start
            if current.year != year:
                current += timedelta(days=7)  # First Monday in the year
            
            while current.date() <= end_date.date():
                weeks.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=7)
            
            return weeks
        except ValueError:
            return []
            
    return []

def generate_performance_data(distributor_id, period_type, period_identifier, db, Actual, Target):
    """
    Generate performance data for a distributor in a specific period
    
    Args:
        distributor_id: ID of the distributor (None for all)
        period_type: 'Weekly', 'Monthly', 'Quarterly', 'Yearly'
        period_identifier: The specific period
        db: Database session
        Actual, Target: Database models
        
    Returns:
        dict: Performance data with actual, target, achievement values
    """
    
    # Get total target
    total_target = db.session.query(func.sum(Target.target_value)).filter(
        Target.period_type == period_type,
        Target.period_identifier == period_identifier
    )
    
    if distributor_id:
        total_target = total_target.filter(Target.distributor_id == distributor_id)
    
    total_target = total_target.scalar() or 0
    
    # For 'Monthly' period type (most common), extract the month and financial year
    if period_type == 'Monthly' and '-' in period_identifier:
        month, financial_year = period_identifier.split('-', 1)
        
        # Get total actual by using a more flexible query that searches all records for the month
        total_actual_query = db.session.query(func.sum(Actual.actual_sales))
        
        if distributor_id:
            total_actual_query = total_actual_query.filter(Actual.distributor_id == distributor_id)
        
        # Use both the month field and date-based filtering (just like the dashboard)
        total_actual_query = total_actual_query.filter(
            (Actual.month == period_identifier) | 
            (Actual.month.like(f"{month}%") & Actual.year.like(f"%{financial_year[2:]}"))
        )
        
        # Parse the financial year to get calendar dates
        try:
            fy_start_year = int("20" + financial_year[2:4])
            
            # Map months to their calendar values
            month_map = {
                'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 
                'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3
            }
            
            # Determine the year for this month
            month_num = month_map.get(month, 1)
            year = fy_start_year if month_num >= 4 else fy_start_year + 1
            
            # Create date range for the entire month
            if month_num in [4, 6, 9, 11]:  # 30 days
                last_day = 30
            elif month_num == 2:  # February - simplified, not handling leap years
                last_day = 28
            else:  # 31 days
                last_day = 31
            
            start_date = f"{year}-{month_num:02d}-01"  # First day of month
            end_date = f"{year}-{month_num:02d}-{last_day}"  # Last day of month
            
            # Also try date-based filtering for weekly data within this month
            date_filtered_actual = db.session.query(func.sum(Actual.actual_sales)).filter(
                Actual.distributor_id == distributor_id if distributor_id else True,
                Actual.week_start_date >= start_date,
                Actual.week_end_date <= end_date
            ).scalar() or 0
            
            # Use date-filtered value if it's greater (meaning we found more records)
            if date_filtered_actual > 0:
                total_actual = date_filtered_actual
            else:
                total_actual = total_actual_query.scalar() or 0
        except Exception as e:
            # Fallback to simple filtering if date parsing fails
            total_actual = total_actual_query.scalar() or 0
            
    # Default filtering for other period types
    else:
        total_actual_query = db.session.query(func.sum(Actual.actual_sales))
        
        if distributor_id:
            total_actual_query = total_actual_query.filter(Actual.distributor_id == distributor_id)
        
        if period_type == 'Weekly':
            week_date = get_period_weeks(period_type, period_identifier)[0] if get_period_weeks(period_type, period_identifier) else None
            if week_date:
                total_actual_query = total_actual_query.filter(Actual.week_start_date == week_date)
            else:
                total_actual_query = total_actual_query.filter(Actual.id == -1)  # No results if invalid
        elif period_type == 'Monthly':
            total_actual_query = total_actual_query.filter(Actual.month == period_identifier)
        elif period_type == 'Quarterly':
            total_actual_query = total_actual_query.filter(Actual.quarter == period_identifier)
        elif period_type == 'Yearly':
            total_actual_query = total_actual_query.filter(Actual.year == period_identifier)
        
        total_actual = total_actual_query.scalar() or 0
    
    # Calculate achievement
    achievement_amount = total_actual
    achievement_percent = (total_actual / total_target * 100) if total_target > 0 else 0
    shortfall = total_target - total_actual if total_actual < total_target else 0
    
    return {
        'target': total_target,
        'actual': total_actual,
        'achievement_amount': achievement_amount,
        'achievement_percent': achievement_percent,
        'shortfall': shortfall
    }

def generate_summary_pdf(distributors, db, Actual, Target):
    """Generates a summary PDF for all distributors for the current financial year."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Distributor Summary Report")
    
    # Get current financial year
    current_fin_year = get_financial_year()
    
    # Report Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, 750, f"Distributor Performance Summary ({current_fin_year})")
    
    # Table Header
    pdf.setFont("Helvetica-Bold", 12)
    y_position = 700
    pdf.drawString(72, y_position, "Name")
    pdf.drawString(250, y_position, "Target")
    pdf.drawString(400, y_position, "Actual")
    pdf.drawString(500, y_position, "Ach %") # Added Achievement %
    
    # Table Content
    pdf.setFont("Helvetica", 10) # Smaller font for more data
    y_position -= 30
    
    for distributor in distributors:
        # Calculate Target for the financial year
        distributor_target = db.session.query(func.sum(Target.target_value)).filter(
            Target.distributor_id == distributor.id,
            Target.period_type == 'Monthly',
            Target.period_identifier.like(f"%-{current_fin_year}")
        ).scalar() or 0
        
        # Calculate Actual for the financial year
        distributor_actual = db.session.query(func.sum(Actual.actual_sales)).filter(
            Actual.distributor_id == distributor.id,
            Actual.year == current_fin_year
        ).scalar() or 0
        
        # Calculate Achievement Percentage
        achievement_percent = (distributor_actual / distributor_target * 100) if distributor_target > 0 else 0
        
        # Draw row
        pdf.drawString(72, y_position, distributor.name)
        pdf.drawString(250, y_position, f"{int(distributor_target):,}")
        pdf.drawString(400, y_position, f"{int(distributor_actual):,}")
        pdf.drawString(500, y_position, f"{achievement_percent:.1f}%")
        
        y_position -= 20
        if y_position < 100: # Check if page break needed
            pdf.showPage()
            # Redraw headers on new page
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(72, 750, f"Distributor Performance Summary ({current_fin_year}) (cont.)")
            pdf.setFont("Helvetica-Bold", 12)
            y_position = 700
            pdf.drawString(72, y_position, "Name")
            pdf.drawString(250, y_position, "Target")
            pdf.drawString(400, y_position, "Actual")
            pdf.drawString(500, y_position, "Ach %")
            pdf.setFont("Helvetica", 10)
            y_position -= 30
            
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()

def generate_bulk_pdf(distributors, db, Actual, Target):
    """Generates a combined PDF with individual reports for all distributors for the current financial year."""
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Bulk Distributor Reports")
    
    # Get current financial year
    current_fin_year = get_financial_year()
    
    first_page = True
    for distributor in distributors:
        if not first_page:
            pdf.showPage() # New page for each distributor
        else:
            first_page = False
            
        # Calculate Target for the financial year
        distributor_target = db.session.query(func.sum(Target.target_value)).filter(
            Target.distributor_id == distributor.id,
            Target.period_type == 'Monthly',
            Target.period_identifier.like(f"%-{current_fin_year}")
        ).scalar() or 0
        
        # Calculate Actual for the financial year
        distributor_actual = db.session.query(func.sum(Actual.actual_sales)).filter(
            Actual.distributor_id == distributor.id,
            Actual.year == current_fin_year
        ).scalar() or 0
            
        # Calculate Achievement Percentage
        achievement_percent = (distributor_actual / distributor_target * 100) if distributor_target > 0 else 0
        shortfall = max(0, distributor_target - distributor_actual)

        # --- Start Drawing Distributor Page ---
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(72, 750, f"Performance Report: {distributor.name}")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(72, 730, f"Financial Year: {current_fin_year}")
        
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(72, 690, "Metric")
        pdf.drawString(250, 690, "Value")
        pdf.line(72, 685, 550, 685) # Underline header
        
        pdf.setFont("Helvetica", 12)
        y = 665
        pdf.drawString(72, y, "Target")
        pdf.drawString(250, y, f"{int(distributor_target):,} cases")
        y -= 20
        pdf.drawString(72, y, "Actual")
        pdf.drawString(250, y, f"{int(distributor_actual):,} cases")
        y -= 20
        pdf.drawString(72, y, "Achievement")
        pdf.drawString(250, y, f"{achievement_percent:.1f}%")
        y -= 20
        pdf.drawString(72, y, "Shortfall")
        pdf.drawString(250, y, f"{int(shortfall):,} cases")
        # --- End Drawing Distributor Page ---

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue() # Return the single PDF buffer

def generate_pdf_report(distributor_name, period_type, period_identifier, performance_data):
    """
    Generate PDF report for distributor performance
    
    Args:
        distributor_name (str): Name of the distributor
        period_type (str): Type of period (Weekly, Monthly, Quarterly, Yearly)
        period_identifier (str): Specific period identifier
        performance_data (dict): Performance metrics
        
    Returns:
        bytes: PDF file contents
    """
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = f"Performance Report: {distributor_name}"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Period information
    period_info = f"Period: {period_type} {period_identifier}"
    elements.append(Paragraph(period_info, styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Report date
    report_date = f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    elements.append(Paragraph(report_date, styles['Normal']))
    elements.append(Spacer(1, 24))
    
    # Performance data table
    data = [
        ['Metric', 'Value'],
        ['Target', f"{int(performance_data['target']):,} cases"],
        ['Actual', f"{int(performance_data['actual']):,} cases"],
        ['Achievement', f"{int(performance_data['achievement_percent'])}%"],
        ['Shortfall', f"{int(performance_data['shortfall']):,} cases"]
    ]
    
    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 24))
    
    # Additional notes
    elements.append(Paragraph("Notes:", styles['Heading3']))
    elements.append(Paragraph("- Achievement percentage is calculated as (Actual/Target) * 100%", styles['Normal']))
    elements.append(Paragraph("- Shortfall is calculated as Target - Actual when Actual < Target", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF from buffer
    buffer.seek(0)
    return buffer.getvalue()

def generate_excel_report(distributor_name, period_type, period_identifier, performance_data):
    """
    Generate Excel report for distributor performance
    
    Args:
        distributor_name (str): Name of the distributor
        period_type (str): Type of period (Weekly, Monthly, Quarterly, Yearly)
        period_identifier (str): Specific period identifier
        performance_data (dict): Performance metrics
        
    Returns:
        bytes: Excel file contents
    """
    buffer = io.BytesIO()
    
    # Create DataFrame
    df = pd.DataFrame({
        'Metric': ['Target', 'Actual', 'Achievement Percent', 'Shortfall'],
        'Value': [
            f"{int(performance_data['target']):,} cases",
            f"{int(performance_data['actual']):,} cases",
            f"{int(performance_data['achievement_percent'])}%",
            f"{int(performance_data['shortfall']):,} cases"
        ]
    })
    
    # Create Excel writer
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write data to Excel
        df.to_excel(writer, sheet_name='Performance', index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Performance']
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#DDDDDD',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1
        })
        
        # Apply formatting
        worksheet.set_column('A:A', 20, cell_format)
        worksheet.set_column('B:B', 25, cell_format)
        worksheet.set_row(0, None, header_format)
        
        # Add title
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16
        })
        
        worksheet.write('D1', f'Distributor: {distributor_name}', title_format)
        worksheet.write('D2', f'Period: {period_type} {period_identifier}', title_format)
        worksheet.write('D3', f'Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', title_format)
        
        # Add chart
        chart = workbook.add_chart({'type': 'column'})
        
        # Configure chart
        chart.add_series({
            'name': 'Performance',
            'categories': ['Performance', 1, 0, 2, 0],  # Metrics (excluding shortfall)
            'values': '=Performance!$B$2:$B$3',  # Values for Target and Actual
            'data_labels': {'value': True}
        })
        
        chart.set_title({'name': 'Target vs. Actual Performance'})
        chart.set_legend({'position': 'top'})
        
        # Insert chart
        worksheet.insert_chart('D5', chart, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})
    
    # Get Excel file from buffer
    buffer.seek(0)
    return buffer.getvalue()

def send_email_report(recipient_email, distributor_name, period_type, period_identifier, pdf_data, excel_data=None):
    """
    Send performance report via email
    
    Args:
        recipient_email (str): Email address of recipient
        distributor_name (str): Name of the distributor
        period_type (str): Type of period
        period_identifier (str): Specific period identifier
        pdf_data (bytes): PDF report as bytes
        excel_data (bytes, optional): Excel report as bytes
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('EMAIL_FROM', 'noreply@example.com')
        msg['To'] = recipient_email
        msg['Subject'] = f"Performance Report: {distributor_name} - {period_type} {period_identifier}"
        
        # Add body text
        body = f"""
        Dear {distributor_name},
        
        Please find attached your performance report for {period_type} {period_identifier}.
        
        Thank you,
        Distributor Tracking System
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF report
        pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename=f"{distributor_name}_Report_{period_identifier}.pdf")
        msg.attach(pdf_attachment)
        
        # Attach Excel report if provided
        if excel_data:
            excel_attachment = MIMEApplication(excel_data, _subtype='xlsx')
            excel_attachment.add_header('Content-Disposition', 'attachment', filename=f"{distributor_name}_Report_{period_identifier}.xlsx")
            msg.attach(excel_attachment)
        
        # Connect to mail server and send
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            # Only login if credentials are provided
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logging.info(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

def get_financial_year(date=None):
    """
    Get the financial year for a given date (April to March)
    Financial year is represented as FY24-25 for April 2024 to March 2025
    
    Args:
        date (datetime, optional): Date to calculate financial year for. Defaults to current date.
        
    Returns:
        str: Financial year in format "FY24-25"
    """
    if date is None:
        date = datetime.now()
    
    if date.month >= 4:  # April onwards is next financial year
        fy_start = date.year
    else:
        fy_start = date.year - 1
    
    # Format as FY24-25
    return f"FY{str(fy_start)[-2:]}-{str(fy_start+1)[-2:]}"

def get_financial_quarter(date=None):
    """
    Get the financial quarter for a given date
    Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar
    
    Args:
        date (datetime, optional): Date to calculate financial quarter for. Defaults to current date.
        
    Returns:
        str: Financial quarter in format "Q1-FY24-25"
    """
    if date is None:
        date = datetime.now()
    
    # Financial year quarters
    if date.month >= 4 and date.month <= 6:
        quarter = 1
    elif date.month >= 7 and date.month <= 9:
        quarter = 2
    elif date.month >= 10 and date.month <= 12:
        quarter = 3
    else:  # Jan-Mar
        quarter = 4
    
    fy = get_financial_year(date)
    return f"Q{quarter}-{fy}"

def get_financial_month(date=None):
    """
    Get the financial month for a given date with financial year
    
    Args:
        date (datetime, optional): Date to calculate financial month for. Defaults to current date.
        
    Returns:
        str: Financial month in format "Apr-FY24-25"
    """
    if date is None:
        date = datetime.now()
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_name = month_names[date.month - 1]
    
    fy = get_financial_year(date)
    return f"{month_name}-{fy}"

def get_all_financial_years(start_year=None, end_year=2035):
    """
    Get a list of all financial years from start year to end year
    
    Args:
        start_year (int, optional): Start year. Defaults to 3 years ago.
        end_year (int, optional): End year. Defaults to 2035.
        
    Returns:
        list: List of financial years in format "FY24-25"
    """
    if start_year is None:
        # Start 3 years ago by default
        start_year = datetime.now().year - 3
    
    financial_years = []
    for year in range(start_year, end_year + 1):
        financial_years.append(f"FY{str(year)[-2:]}-{str(year+1)[-2:]}")
    
    return financial_years

def get_financial_quarter_dates(fy_quarter):
    """
    Get the start and end dates for a financial quarter
    
    Args:
        fy_quarter (str): Financial quarter in format "Q1-FY24-25"
        
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    parts = fy_quarter.split('-')
    quarter = int(parts[0][1])
    fy_start = int('20' + parts[1][2:4])  # Convert FY24-25 to year 2024
    
    if quarter == 1:  # Apr-Jun
        return (
            datetime(fy_start, 4, 1),
            datetime(fy_start, 6, 30)
        )
    elif quarter == 2:  # Jul-Sep
        return (
            datetime(fy_start, 7, 1),
            datetime(fy_start, 9, 30)
        )
    elif quarter == 3:  # Oct-Dec
        return (
            datetime(fy_start, 10, 1),
            datetime(fy_start, 12, 31)
        )
    else:  # Q4: Jan-Mar
        return (
            datetime(fy_start + 1, 1, 1),
            datetime(fy_start + 1, 3, 31)
        )

def test_email_config():
    """
    Test the email configuration by checking if required environment variables are set
    
    Returns:
        dict: Email configuration status with keys:
            - is_configured: bool indicating if email is configured
            - smtp_server: SMTP server address
            - smtp_port: SMTP port
            - username: Username for SMTP (partially masked)
            - error: Error message if any
    """
    result = {
        'is_configured': False,
        'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': os.environ.get('SMTP_PORT', 587),
        'username': None,
        'error': None
    }
    
    # Check if credentials are set
    smtp_username = os.environ.get('SMTP_USERNAME', '')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    
    if not smtp_username or not smtp_password:
        result['error'] = "Email credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables."
        return result
    
    # Mask the username for security (show first 3 chars and domain)
    if '@' in smtp_username:
        user, domain = smtp_username.split('@', 1)
        if len(user) > 3:
            masked_user = user[:3] + '*' * (len(user) - 3)
        else:
            masked_user = user
        result['username'] = f"{masked_user}@{domain}"
    else:
        result['username'] = smtp_username[:3] + '*' * (len(smtp_username) - 3) if len(smtp_username) > 3 else smtp_username
    
    # Try to connect to the SMTP server
    try:
        with smtplib.SMTP(result['smtp_server'], int(result['smtp_port'])) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_username, smtp_password)
            result['is_configured'] = True
    except Exception as e:
        result['error'] = f"Error connecting to SMTP server: {str(e)}"
    
    return result

def send_test_email(recipient_email):
    """
    Send a test email to verify email configuration
    
    Args:
        recipient_email (str): Email address to send test to
        
    Returns:
        dict: Result with keys:
            - success: bool indicating if email sent successfully
            - message: Status message
    """
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('EMAIL_FROM', 'noreply@example.com')
        msg['To'] = recipient_email
        msg['Subject'] = f"Test Email from Sales Management System"
        
        # Add body text
        body = f"""
        This is a test email from the Sales Management System.
        
        If you received this email, your email configuration is working correctly.
        
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to mail server and send
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME', '')
        smtp_password = os.environ.get('SMTP_PASSWORD', '')
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            # Only login if credentials are provided
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logging.info(f"Test email sent successfully to {recipient_email}")
        return {
            'success': True,
            'message': f"Test email sent successfully to {recipient_email}"
        }
    except Exception as e:
        error_msg = f"Failed to send test email: {str(e)}"
        logging.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }
