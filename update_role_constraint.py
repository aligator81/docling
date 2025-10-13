import sys
sys.path.append('backend')
from backend.app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Update the check constraint to include super_admin
    db.execute(text("""
        ALTER TABLE users DROP CONSTRAINT users_role_check;
    """))

    db.execute(text("""
        ALTER TABLE users ADD CONSTRAINT users_role_check
        CHECK (role = ANY (ARRAY['user'::text, 'admin'::text, 'super_admin'::text]));
    """))

    db.commit()
    print('Successfully updated users_role_check constraint to include super_admin')

except Exception as e:
    print(f'Error updating constraint: {e}')
    db.rollback()
finally:
    db.close()