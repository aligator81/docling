import sys
sys.path.append('backend')
from backend.app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Query to check constraints on users table
    result = db.execute(text("""
        SELECT constraint_name, check_clause
        FROM information_schema.check_constraints
        WHERE constraint_schema = 'public' AND constraint_name LIKE '%users%'
    """))
    constraints = result.fetchall()
    print('Check constraints on users table:')
    for constraint in constraints:
        print(f'Name: {constraint.constraint_name}')
        print(f'Clause: {constraint.check_clause}')
        print('---')

    if not constraints:
        print('No check constraints found on users table')

except Exception as e:
    print(f'Error querying constraints: {e}')
finally:
    db.close()