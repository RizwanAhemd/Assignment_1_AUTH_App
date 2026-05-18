const API_BASE = 'http://127.0.0.1:8000/api/v1';

// State Management
let state = {
  token: localStorage.getItem('access_token'),
  user: null
};

// DOM Elements
const authSection = document.getElementById('auth-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const authMessage = document.getElementById('auth-message');
const userEmailDisplay = document.getElementById('user-email-display');
const logoutBtn = document.getElementById('logout-btn');

// --- Helper Functions ---

function showMessage(text, type = 'success') {
  authMessage.textContent = text;
  authMessage.className = `message ${type}`;
  setTimeout(() => { authMessage.className = 'message'; }, 5000);
}

function updateUI() {
  if (state.token) {
    authSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    if (state.user) {
      userEmailDisplay.textContent = state.user.email;
    }
  } else {
    authSection.classList.remove('hidden');
    dashboardSection.classList.add('hidden');
  }
}

// --- API Calls ---

async function fetchWithAuth(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };

  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  
  if (response.status === 401 && state.token) {
      // Simple logout on unauthorized
      logout();
      throw new Error('Session expired');
  }
  
  return response;
}

async function login(email, password) {
  try {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) throw new Error(data.detail || 'Login failed');

    localStorage.setItem('access_token', data.access_token);
    state.token = data.access_token;
    await fetchCurrentUser();
    updateUI();
    showMessage('Successfully logged in!');
  } catch (err) {
    showMessage(err.message, 'error');
  }
}

async function register(email, password) {
  try {
    const response = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) throw new Error(data.detail || 'Registration failed');

    showMessage('Registration successful! Please login.');
    switchToLogin();
  } catch (err) {
    showMessage(err.message, 'error');
  }
}

async function fetchCurrentUser() {
  try {
    const response = await fetchWithAuth('/users/me');
    const data = await response.json();
    if (response.ok) {
      state.user = data;
      userEmailDisplay.textContent = data.email;
    }
  } catch (err) {
    console.error('Failed to fetch user', err);
  }
}

function logout() {
  localStorage.removeItem('access_token');
  state.token = null;
  state.user = null;
  updateUI();
}

// --- Event Listeners ---

loginTab.addEventListener('click', switchToLogin);
registerTab.addEventListener('click', switchToRegister);

function switchToLogin() {
  loginTab.classList.add('active');
  registerTab.classList.remove('active');
  loginForm.classList.remove('hidden');
  registerForm.classList.add('hidden');
}

function switchToRegister() {
  registerTab.classList.add('active');
  loginTab.classList.remove('active');
  registerForm.classList.remove('hidden');
  loginForm.classList.add('hidden');
}

loginForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  login(email, password);
});

registerForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  register(email, password);
});

logoutBtn.addEventListener('click', logout);

// --- Initialization ---

if (state.token) {
  fetchCurrentUser().then(updateUI);
} else {
  updateUI();
}
