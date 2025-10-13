import sys
sys.path.append('backend')
from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.auth import check_role_permission

db = SessionLocal()
admin_user = db.query(User).filter(User.username == 'admin').first()
print(f'Admin user role in database: {admin_user.role}')

# Test permission checking
print(f'check_role_permission("super_admin", ["admin", "system"]): {check_role_permission("super_admin", ["admin", "system"])}')
print(f'check_role_permission("super_admin", ["users"]): {check_role_permission("super_admin", ["users"])}')

db.close()