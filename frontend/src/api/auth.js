import request from './request'

export function login(credentials) {
  return request.post('/auth/login', credentials)
}

export function register(data) {
  return request.post('/auth/register', data)
}

export function getProfile() {
  return request.get('/auth/profile')
}

export function updateProfile(data) {
  return request.put('/auth/profile', data)
}

export function logout() {
  return request.post('/auth/logout')
}
