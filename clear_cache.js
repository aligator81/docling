// Script to clear cached user data and force fresh login
// Run this in the browser console on the login page

// Clear localStorage
localStorage.removeItem('auth_token');
localStorage.removeItem('user_data');

// Clear sessionStorage as well
sessionStorage.clear();

// Clear any cookies (optional)
document.cookie.split(";").forEach(cookie => {
  const eqPos = cookie.indexOf("=");
  const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
  document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/";
});

console.log('Cache cleared! Please login again to get fresh user data.');
console.log('Login with:');
console.log('Username: admin');
console.log('Password: admin123');
console.log('You should now see Super Admin role and access to admin features.');