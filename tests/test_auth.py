def test_login_page(client):
    """Test that the login page loads correctly"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_success(client):
    """Test that a user can log in successfully"""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data

def test_login_failure(client):
    """Test that login fails with incorrect credentials"""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data

def test_logout(logged_in_client):
    """Test that a user can log out"""
    response = logged_in_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_protected_route_redirect(client):
    """Test that protected routes redirect to login when not authenticated"""
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data 