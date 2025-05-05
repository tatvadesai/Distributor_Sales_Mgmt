from app import app, db
from models import Distributor

DISTRIBUTORS = [
    'Prit Enterprise Retail',
    'Firdos Colddrinks',
    'Ammary Agency',
    'Maa Ashapura Marketing',
    'Shivam Enterprise',
    'Burhani Agency',
    'Patel Colddrinks'
]

@app.cli.command('init-db')
def initialize_database():
    """Create tables and seed initial data"""
    with app.app_context():
        db.create_all()
        
        # Seed distributors
        existing = {d.name for d in Distributor.query.all()}
        for name in DISTRIBUTORS:
            if name not in existing:
                db.session.add(Distributor(name=name))
                print(f'Added distributor: {name}')
        
        db.session.commit()
        print('Database initialization complete')