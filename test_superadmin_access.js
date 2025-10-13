// Test script to verify superadmin access across all API endpoints
const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

const BASE_URL = 'http://localhost:8000/api';
let token = '';

async function testEndpoint(method, endpoint, data = null) {
  const config = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    },
    ...(data && { body: JSON.stringify(data) })
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, config);
    const result = await response.json();
    
    console.log(`${method} ${endpoint}: ${response.status}`);
    if (response.ok) {
      console.log('✅ SUCCESS');
    } else {
      console.log('❌ FAILED:', result.detail || 'Unknown error');
    }
    return response.ok;
  } catch (error) {
    console.log(`${method} ${endpoint}: ERROR - ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('🧪 Testing Superadmin Access...\n');

  // Test 1: Login as superadmin
  console.log('1. Testing Login...');
  const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({
      username: 'superadmin',
      password: 'super123'
    }),
  });

  if (loginResponse.ok) {
    const loginData = await loginResponse.json();
    token = loginData.access_token;
    console.log('✅ Login successful');
    console.log(`   User: ${loginData.user.username}, Role: ${loginData.user.role}`);
  } else {
    console.log('❌ Login failed');
    return;
  }

  console.log('\n2. Testing API Endpoints...');

  // Test authentication endpoints
  await testEndpoint('GET', '/auth/me');

  // Test document endpoints
  await testEndpoint('GET', '/documents/');
  await testEndpoint('POST', '/documents/upload');

  // Test admin endpoints
  await testEndpoint('GET', '/admin/users');
  await testEndpoint('GET', '/admin/stats');

  // Test chat endpoints
  await testEndpoint('GET', '/chat/history');
  await testEndpoint('POST', '/chat', { message: 'test query', document_ids: [] });

  console.log('\n🎯 Testing Complete!');
}

runTests().catch(console.error);