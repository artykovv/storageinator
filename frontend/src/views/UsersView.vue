<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api/client'

const router = useRouter()
const authStore = useAuthStore()

const users = ref([])
const loading = ref(true)
const error = ref('')
const editingUser = ref(null)
const editRole = ref('')
const editActive = ref(true)
const editEmail = ref('')
const editPassword = ref('')
const isSuperAdmin = computed(() => authStore.user?.role === 'super_admin')

const currentUser = computed(() => authStore.user)
const isAdmin = computed(() => ['admin', 'super_admin'].includes(authStore.user?.role))

onMounted(async () => {
  if (!isAdmin.value) {
    router.push('/')
    return
  }
  await loadUsers()
})

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get('/users')
    users.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load users'
  } finally {
    loading.value = false
  }
}

function startEdit(user) {
  editingUser.value = user
  editRole.value = user.role
  editActive.value = user.is_active
  editEmail.value = user.email
  editPassword.value = ''
}

function cancelEdit() {
  editingUser.value = null
}

async function saveUser() {
  if (!editingUser.value) return
  
  try {
    const payload = {
      role: editRole.value,
      is_active: editActive.value
    }
    
    // Only send email/password if super_admin and fields are changed/provided
    if (isSuperAdmin.value) {
      if (editEmail.value !== editingUser.value.email) {
        payload.email = editEmail.value
      }
      if (editPassword.value) {
        payload.password = editPassword.value
      }
    }

    await api.patch(`/users/${editingUser.value.id}`, payload)
    await loadUsers()
    editingUser.value = null
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to update user'
  }
}

async function deleteUser(userId) {
  if (!confirm('Are you sure you want to delete this user?')) return
  
  try {
    await api.delete(`/users/${userId}`)
    await loadUsers()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete user'
  }
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="users-view">
    <header class="header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Back
        </button>
        <h1>👥 User Management</h1>
      </div>
    </header>

    <main class="main">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <span>Loading users...</span>
      </div>

      <div v-else-if="error" class="error">{{ error }}</div>

      <div v-else class="users-table-wrapper">
        <table class="users-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id" :class="{ current: user.id === currentUser?.id }">
              <td class="email-cell">
                {{ user.email }}
                <span v-if="user.id === currentUser?.id" class="you-badge">You</span>
              </td>
              <td>
                <span class="role-badge" :class="user.role">{{ user.role }}</span>
              </td>
              <td>
                <span class="status-badge" :class="{ active: user.is_active, inactive: !user.is_active }">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="date-cell">{{ formatDate(user.created_at) }}</td>
              <td class="actions-cell">
                <button 
                  class="action-btn edit" 
                  @click="startEdit(user)"
                  :disabled="user.id === currentUser?.id"
                  title="Edit"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </button>
                <button 
                  class="action-btn delete" 
                  @click="deleteUser(user.id)"
                  :disabled="user.id === currentUser?.id"
                  title="Delete"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <!-- Edit Modal -->
    <div v-if="editingUser" class="modal-overlay" @click.self="cancelEdit">
      <div class="modal">
        <h2>Edit User</h2>
        <div v-if="isSuperAdmin" class="form-group">
          <label>Email</label>
          <input v-model="editEmail" type="email" placeholder="Email address" />
        </div>
        <p v-else class="modal-email">{{ editingUser.email }}</p>
        
        <div class="form-group">
          <label>Role</label>
          <select v-model="editRole">
            <option value="super_admin">Super Admin</option>
            <option value="admin">Admin</option>
            <option value="user">User</option>
            <option value="pending">Pending</option>
          </select>
        </div>
        
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="editActive" />
            <span>Active</span>
          </label>
        </div>
        
        <div v-if="isSuperAdmin" class="form-group">
          <label>New Password (Optional)</label>
          <input v-model="editPassword" type="password" placeholder="Leave empty to keep current" />
        </div>
        
        <div class="modal-actions">
          <button class="btn-secondary" @click="cancelEdit">Cancel</button>
          <button class="btn-primary" @click="saveUser">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.users-view {
  min-height: 100vh;
  background: var(--bg-primary);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.header h1 {
  font-size: 1.25rem;
  font-weight: 600;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--bg-tertiary);
  border-radius: 0.5rem;
  color: var(--text-secondary);
  transition: all 0.15s;
}

.back-btn:hover {
  background: var(--primary);
  color: white;
}

.main {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: var(--text-muted);
  gap: 1rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  background: rgba(239, 68, 68, 0.15);
  color: var(--danger);
  padding: 1rem;
  border-radius: 0.5rem;
  text-align: center;
}

.users-table-wrapper {
  background: var(--bg-secondary);
  border-radius: 0.75rem;
  border: 1px solid var(--border);
  overflow: hidden;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th,
.users-table td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.users-table th {
  background: var(--bg-tertiary);
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.users-table tr:last-child td {
  border-bottom: none;
}

.users-table tr.current {
  background: rgba(99, 102, 241, 0.1);
}

.email-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.you-badge {
  font-size: 0.625rem;
  padding: 0.125rem 0.375rem;
  background: var(--primary);
  color: white;
  border-radius: 9999px;
  font-weight: 600;
}

.role-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.role-badge.super_admin {
  background: rgba(234, 179, 8, 0.2);
  color: #facc15;
}

.role-badge.admin {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.role-badge.user {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.role-badge.pending {
  background: rgba(249, 115, 22, 0.2);
  color: #fb923c;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-badge.active {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.status-badge.inactive {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.date-cell {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  padding: 0.5rem;
  background: transparent;
  border-radius: 0.375rem;
  color: var(--text-muted);
  transition: all 0.15s;
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
}

.action-btn.edit:hover:not(:disabled) {
  color: var(--primary);
}

.action-btn.delete:hover:not(:disabled) {
  color: var(--danger);
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--bg-secondary);
  padding: 2rem;
  border-radius: 1rem;
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--border);
}

.modal h2 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.modal-email {
  color: var(--text-muted);
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.form-group select,
.form-group input[type="email"],
.form-group input[type="password"] {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  color: var(--text-primary);
  font-size: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-label input {
  width: 1.25rem;
  height: 1.25rem;
  accent-color: var(--primary);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.btn-secondary,
.btn-primary {
  flex: 1;
  padding: 0.75rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.15s;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background: var(--border);
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover {
  background: var(--primary-hover);
}
</style>
