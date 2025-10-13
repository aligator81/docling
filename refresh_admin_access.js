// Script to refresh Super Admin access and force UI update
// Run this in the browser console while logged in as admin

// Force refresh user data from server
(async function() {
  console.log('🔄 Refreshing user data and UI state...');

  try {
    // Import AuthService and refresh user data
    const { AuthService } = await import('/_next/static/chunks/lib/auth.js');
    const freshUser = await AuthService.refreshUserData();

    if (freshUser) {
      console.log('✅ Fresh user data loaded:', freshUser);

      if (freshUser.role === 'super_admin') {
        console.log('🎉 Super Admin role confirmed!');
        console.log('🔐 Full access granted to:');
        console.log('  - Users management');
        console.log('  - System settings');
        console.log('  - Database tools');
        console.log('  - All admin features');

        // Force page reload to update UI
        console.log('🔄 Reloading page to update navigation...');
        window.location.reload();
      } else {
        console.log('⚠️ Role is not super_admin:', freshUser.role);
      }
    } else {
      console.log('❌ Could not refresh user data');
    }
  } catch (error) {
    console.error('Error refreshing user data:', error);

    // Fallback: manual refresh
    console.log('🔄 Attempting manual refresh...');
    window.location.reload();
  }
})();