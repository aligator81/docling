// Test script to verify Super Admin access
// Run this in browser console while logged in as admin

(async function() {
  console.log('🔍 Testing Super Admin Access...');

  // Check current user data
  const { AuthService } = await import('/_next/static/chunks/lib/auth.js');
  const user = AuthService.getUser();

  console.log('Current user:', user);
  console.log('User role:', user?.role);

  // Test permissions
  console.log('isAdmin():', AuthService.isAdmin());
  console.log('isSuperAdmin():', AuthService.isSuperAdmin());
  console.log('hasPermissions(["admin", "system"]):', AuthService.hasPermissions(['admin', 'system']));
  console.log('hasPermissions(["users"]):', AuthService.hasPermissions(['users']));

  if (user?.role === 'super_admin') {
    console.log('✅ Super Admin role detected!');
    console.log('');
    console.log('🎯 You should now see:');
    console.log('  - Users and Settings in navigation menu');
    console.log('  - "Super Admin" badge in top-right');
    console.log('  - "Administrator Dashboard" title');
    console.log('');
    console.log('🔗 Try these URLs:');
    console.log('  - /admin/users (User Management)');
    console.log('  - /admin/settings (System Settings)');
    console.log('  - /admin/database (Database Tools)');

    // Force page reload to ensure UI updates
    console.log('🔄 Reloading page to update navigation...');
    window.location.reload();
  } else {
    console.log('❌ Super Admin role not detected');
    console.log('🔧 Try running the cache clear script first');
  }
})();