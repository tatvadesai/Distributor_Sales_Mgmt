from models import User, Distributor, Target, Actual
from datetime import datetime

def test_user_model(session):
    """Test User model creation and password checking"""
    user = User(username='newuser')
    user.set_password('password123')
    session.add(user)
    session.commit()
    
    retrieved_user = session.query(User).filter_by(username='newuser').first()
    assert retrieved_user is not None
    assert retrieved_user.check_password('password123')
    assert not retrieved_user.check_password('wrongpassword')

def test_distributor_model(session):
    """Test Distributor model creation and relationships"""
    distributor = Distributor(
        name='Test Distributor',
        email='test@example.com',
        whatsapp='+1234567890',
        area='Test Area'
    )
    session.add(distributor)
    session.commit()
    
    retrieved_distributor = session.query(Distributor).filter_by(name='Test Distributor').first()
    assert retrieved_distributor is not None
    assert retrieved_distributor.email == 'test@example.com'
    assert retrieved_distributor.whatsapp == '+1234567890'
    assert retrieved_distributor.area == 'Test Area'

def test_target_model(session):
    """Test Target model creation and relationships"""
    # Create a distributor first
    distributor = Distributor(name='Target Test Distributor')
    session.add(distributor)
    session.commit()
    
    target = Target(
        distributor_id=distributor.id,
        period_type='Monthly',
        period_identifier='2023-01',
        target_value=1000.0
    )
    session.add(target)
    session.commit()
    
    retrieved_target = session.query(Target).filter_by(period_identifier='2023-01').first()
    assert retrieved_target is not None
    assert retrieved_target.target_value == 1000.0
    assert retrieved_target.distributor.name == 'Target Test Distributor'

def test_actual_model(session):
    """Test Actual sales model creation and relationships"""
    # Create a distributor first
    distributor = Distributor(name='Actual Test Distributor')
    session.add(distributor)
    session.commit()
    
    # Create a weekly sales record
    start_date = datetime.strptime('2023-01-01', '%Y-%m-%d').date()
    end_date = datetime.strptime('2023-01-07', '%Y-%m-%d').date()
    
    actual = Actual(
        distributor_id=distributor.id,
        week_start_date=start_date,
        week_end_date=end_date,
        actual_sales=750.0
    )
    session.add(actual)
    session.commit()
    
    retrieved_actual = session.query(Actual).filter_by(distributor_id=distributor.id).first()
    assert retrieved_actual is not None
    assert retrieved_actual.actual_sales == 750.0
    assert retrieved_actual.distributor.name == 'Actual Test Distributor'
    assert retrieved_actual.week_start_date == start_date
    assert retrieved_actual.week_end_date == end_date 