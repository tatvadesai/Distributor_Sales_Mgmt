# Running Tests for Distributor Tracker

This guide explains how to run the automated tests for the Distributor Tracker application.

## Prerequisites

Make sure you have installed the required test dependencies:

```bash
pip install -r local_requirements.txt
```

## Running All Tests

To run all tests:

```bash
python -m pytest
```

## Running Specific Test Files

To run tests from a specific file:

```bash
python -m pytest tests/test_auth.py
```

## Running Specific Tests

To run a specific test:

```bash
python -m pytest tests/test_auth.py::test_login_success
```

## Generating Test Coverage Report

To generate a coverage report:

```bash
pip install pytest-cov
python -m pytest --cov=.
```

For a more detailed HTML report:

```bash
python -m pytest --cov=. --cov-report=html
```

This will create a directory called `htmlcov` with an HTML report of your code coverage.

## Understanding the Tests

The test suite is organized into several files:

1. **test_auth.py**: Tests for authentication functionality (login, logout)
2. **test_models.py**: Tests for database models (User, Distributor, Target, Actual)
3. **test_routes.py**: Tests for application routes (pages and form submissions)
4. **test_utils.py**: Tests for utility functions

## Writing New Tests

To write a new test:

1. Decide which file it belongs in based on what you're testing
2. Create a new function with a name starting with `test_`
3. Use assertions to verify expected behavior:
   ```python
   def test_something_works():
       result = my_function()
       assert result == expected_value
   ```

## Using Test Fixtures

The `conftest.py` file defines several useful fixtures:

- `app`: The Flask application configured for testing
- `client`: A test client for making requests
- `db`: The test database
- `session`: A database session for each test
- `logged_in_client`: A test client that's already logged in

Use these fixtures in your tests by adding them as parameters:

```python
def test_my_feature(logged_in_client, session):
    # Your test code using the fixtures
    pass
```

## Common Issues

1. **Database errors**: Make sure your model imports are correct and the database is properly initialized
2. **Authentication errors**: Some tests require a logged-in user; use the `logged_in_client` fixture
3. **CSRF errors**: Set `WTF_CSRF_ENABLED = False` in test configuration to bypass CSRF protection 