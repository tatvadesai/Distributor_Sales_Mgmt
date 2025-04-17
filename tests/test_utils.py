import pytest
from datetime import datetime, date, timedelta
from utils import (
    get_current_week_start,
    get_current_week_end,
    get_period_weeks,
    calculate_periods
)

def test_get_current_week_dates():
    """Test that get_current_week_start and get_current_week_end return correct dates"""
    start_date = datetime.strptime(get_current_week_start(), '%Y-%m-%d').date()
    end_date = datetime.strptime(get_current_week_end(), '%Y-%m-%d').date()
    
    # Verify that start_date is a Monday
    assert start_date.weekday() == 0
    
    # Verify that end_date is a Sunday
    assert end_date.weekday() == 6
    
    # Verify that the difference is 6 days (making it a week)
    assert (end_date - start_date).days == 6

def test_get_period_weeks():
    """Test that get_period_weeks returns correct data for different period types"""
    # Test for Monthly period
    monthly_weeks = get_period_weeks('Monthly', 'Jan-2023')
    
    # Should contain some weeks
    assert len(monthly_weeks) >= 4
    
    # First week should be in January 2023
    first_week = datetime.strptime(monthly_weeks[0], '%Y-%m-%d')
    assert first_week.year == 2023
    assert first_week.month == 1
    
    # Test for Quarterly period
    quarterly_weeks = get_period_weeks('Quarterly', 'Q1-2023')
    
    # Q1 should have approximately 13 weeks
    assert len(quarterly_weeks) >= 12
    
    # First week should be in Q1 2023
    first_week = datetime.strptime(quarterly_weeks[0], '%Y-%m-%d')
    assert first_week.year == 2023
    assert first_week.month <= 3  # Q1 = Jan-Mar

def test_calculate_periods():
    """Test that calculate_periods returns correct period identifiers"""
    # Test with a specific date
    month, quarter, year = calculate_periods('2023-01-15')
    
    # The result will depend on your financial year settings
    # This is a basic check that we get three non-empty values
    assert month
    assert quarter
    assert year 