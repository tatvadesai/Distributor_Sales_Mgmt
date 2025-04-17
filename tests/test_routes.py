def test_dashboard_access(logged_in_client):
    """Test that an authenticated user can access the dashboard"""
    response = logged_in_client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_distributors_page(logged_in_client):
    """Test that the distributors page loads correctly"""
    response = logged_in_client.get('/distributors')
    assert response.status_code == 200
    assert b'Distributors' in response.data

def test_targets_page(logged_in_client):
    """Test that the targets page loads correctly"""
    response = logged_in_client.get('/targets')
    assert response.status_code == 200
    assert b'Targets' in response.data

def test_actuals_page(logged_in_client):
    """Test that the actuals page loads correctly"""
    response = logged_in_client.get('/actuals')
    assert response.status_code == 200
    assert b'Sales' in response.data

def test_reports_page(logged_in_client):
    """Test that the reports page loads correctly"""
    response = logged_in_client.get('/reports')
    assert response.status_code == 200
    assert b'Reports' in response.data

def test_new_distributor_form(logged_in_client):
    """Test that the new distributor form loads correctly"""
    response = logged_in_client.get('/distributors/new')
    assert response.status_code == 200
    assert b'Add Distributor' in response.data

def test_create_distributor(logged_in_client, session):
    """Test creating a new distributor"""
    response = logged_in_client.post('/distributors/new', data={
        'name': 'New Test Distributor',
        'email': 'newtest@example.com',
        'whatsapp': '+9876543210',
        'area': 'Test Area 2'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Distributor added successfully' in response.data
    assert b'New Test Distributor' in response.data 