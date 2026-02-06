<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api/client'
import DirectoryTree from '../components/DirectoryTree.vue'
import FileList from '../components/FileList.vue'
import FileUpload from '../components/FileUpload.vue'

const router = useRouter()
const authStore = useAuthStore()

const emit = defineEmits(['download', 'delete', 'update'])

const previewFile = ref(null)
const previewUrl = ref('')
const previewLoading = ref(false)

const shareFile = ref(null)
const shareLink = ref('')
const isCopied = ref(false)

const directories = ref([])
const selectedDirectory = ref(null)
const files = ref([])
const loading = ref(false)
const showNewDirModal = ref(false)
const newDirName = ref('')
const newDirPublic = ref(false)
const newDirError = ref('')

// Editing directory state
const editingDirectory = ref(null)
const showEditDirModal = ref(false)
const editDirName = ref('')
const editDirPublic = ref(false)
const editDirError = ref('')

// Load directories
async function loadDirectories() {
  try {
    const response = await api.get('/directories')
    directories.value = response.data
  } catch (error) {
    console.error('Failed to load directories:', error)
  }
}

// Load files for selected directory
async function loadFiles(directoryId) {
  if (!directoryId) {
    files.value = []
    return
  }
  
  loading.value = true
  try {
    const response = await api.get(`/files/directory/${directoryId}`)
    files.value = response.data.files
  } catch (error) {
    console.error('Failed to load files:', error)
    files.value = []
  } finally {
    loading.value = false
  }
}

// Select directory
function selectDirectory(dir) {
  selectedDirectory.value = dir
  loadFiles(dir.id)
}

// Open edit modal
function openEditDirectory(dir) {
  editingDirectory.value = dir
  editDirName.value = dir.name
  editDirPublic.value = dir.is_public
  editDirError.value = ''
  showEditDirModal.value = true
}

// Update directory
async function updateDirectory() {
  if (!editDirName.value.trim()) {
    editDirError.value = 'Directory name is required'
    return
  }
  
  try {
    const payload = {
      name: editDirName.value,
      is_public: editDirPublic.value
    }
    
    await api.patch(`/directories/${editingDirectory.value.id}`, payload)
    
    // Update local state if needed (reload directories)
    await loadDirectories()
    
    // If we are currently inside the edited directory, update selectedDirectory
    if (selectedDirectory.value && selectedDirectory.value.id === editingDirectory.value.id) {
       // Refresh current view details
       // We can just rely on loadDirectories or fetch again.
       // For simplicity, let's just reload files to be safe if anything changed (though unlikely for rename)
    }
    
    showEditDirModal.value = false
    editingDirectory.value = null
  } catch (error) {
    editDirError.value = error.response?.data?.detail || 'Failed to update directory'
  }
}

// Create new directory
async function createDirectory() {
  if (!newDirName.value.trim()) {
    newDirError.value = 'Directory name is required'
    return
  }
  
  try {
    await api.post('/directories', {
      name: newDirName.value.trim(),
      parent_id: selectedDirectory.value?.id || null,
      is_public: newDirPublic.value
    })
    
    await loadDirectories()
    showNewDirModal.value = false
    newDirName.value = ''
    newDirPublic.value = false
    newDirError.value = ''
  } catch (error) {
    newDirError.value = error.response?.data?.detail || 'Failed to create directory'
  }
}

// Delete directory
async function deleteDirectory(dirId) {
  if (!confirm('Are you sure you want to delete this directory?')) return
  
  try {
    await api.delete(`/directories/${dirId}`)
    if (selectedDirectory.value?.id === dirId) {
      selectedDirectory.value = null
      files.value = []
    }
    await loadDirectories()
  } catch (error) {
    alert(error.response?.data?.detail || 'Failed to delete directory')
  }
}

async function openShare(file) {
  shareFile.value = file
  // Generate link based on current location protocol/host + api path
  // Since we are frontend, we want the link to point to backend public endpoint directly?
  // User asked for "file accessible to everyone".
  // The link should be the backend endpoint: domain/api/public/files/{id}
  // Or better: domain/shared/{id} if frontend handles it.
  // The plan said: `https://<domain>/api/public/files/<id>`.
  // Let's use window.location.origin to detect domain, but point to API URL.
  // API URL is usually localhost:8000 or similar.
  // Let's construct it from API client base URL or just relatively if proxied.
  // For now, let's assume API is at /api relative to current domain in prod, or localhost:8000 in dev.
  // Simpler: Use the API endpoint directly.
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
  shareLink.value = `${apiUrl}/public/files/${file.id}`
  isCopied.value = false
}

function closeShare() {
  shareFile.value = null
  isCopied.value = false
}

async function togglePublic() {
  if (!shareFile.value) return
  
  try {
    const newStatus = !shareFile.value.is_public
    const response = await api.patch(`/files/${shareFile.value.id}`, {
      is_public: newStatus
    })
    
    // Update local state
    shareFile.value = response.data
    // Emit update to parent to refresh list? Or just mutate prop (avoid prop mutation).
    // Better reload list or emit event.
    if (selectedDirectory.value) {
      await loadFiles(selectedDirectory.value.id)
    }
  } catch (error) {
    console.error('Failed to update public status:', error)
    alert('Failed to update status')
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(shareLink.value)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy', err)
  }
}

// Handle file uploaded
async function handleFileUploaded() {
  if (selectedDirectory.value) {
    await loadFiles(selectedDirectory.value.id)
  }
}

// Delete file
async function deleteFile(fileId) {
  if (!confirm('Are you sure you want to delete this file?')) return
  
  try {
    await api.delete(`/files/${fileId}`)
    await loadFiles(selectedDirectory.value.id)
  } catch (error) {
    alert(error.response?.data?.detail || 'Failed to delete file')
  }
}

// Download file
async function downloadFile(fileId, filename) {
  try {
    const response = await api.get(`/files/${fileId}/download-url`)
    const link = document.createElement('a')
    link.href = response.data.presigned_url
    link.download = filename
    link.click()
  } catch (error) {
    alert(error.response?.data?.detail || 'Failed to download file')
  }
}

// Logout
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadDirectories()
})
</script>

<template>
  <div class="files-page">
    <!-- Header -->
    <header class="header">
      <div class="header-content">
        <div class="header-left">
          <div class="logo-small">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h1>Storageinator</h1>
        </div>
        <div class="header-right">
          <span class="role-badge" :class="authStore.user?.role">{{ authStore.user?.role }}</span>
          <span class="user-email">{{ authStore.user?.email }}</span>
          <router-link v-if="['admin', 'super_admin'].includes(authStore.user?.role)" to="/users" class="btn-icon" title="Manage Users">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </router-link>
          <button @click="handleLogout" class="btn-secondary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Logout
          </button>
        </div>
      </div>
    </header>
    
    <!-- Main content -->
    <main class="main-content">
      <!-- Sidebar with directories -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h2>Directories</h2>
          <button @click="showNewDirModal = true" class="btn-icon" title="New directory">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>
        </div>
        
        <div class="directory-list">
          <div v-if="directories.length === 0" class="empty-state">
            <p>No directories yet</p>
            <button @click="showNewDirModal = true" class="btn-primary btn-sm">
              Create your first directory
            </button>
          </div>
          
          <DirectoryTree
            v-else
            :directories="directories"
            :selected-id="selectedDirectory?.id"
            @select="selectDirectory"
            @delete="deleteDirectory"
            @edit="openEditDirectory"
          />
        </div>
      </aside>
      
      <!-- Files area -->
      <section class="files-area">
        <div v-if="!selectedDirectory" class="no-selection">
          <div class="no-selection-content">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
            <h3>Select a directory</h3>
            <p>Choose a directory from the sidebar to view its files</p>
          </div>
        </div>
        
        <template v-else>
          <div class="files-header">
            <div class="files-header-info">
              <h2>{{ selectedDirectory.name }}</h2>
              <span class="path">{{ selectedDirectory.path }}</span>
            </div>
            <FileUpload
              :directory-id="selectedDirectory.id"
              @uploaded="handleFileUploaded"
            />
          </div>
          
          <FileList
            :files="files"
            :loading="loading"
            @download="downloadFile"
            @delete="deleteFile"
            @share="openShare"
          />
        </template>
      </section>
    </main>
    
    <!-- New directory modal -->
    <div v-if="showNewDirModal" class="modal-overlay" @click.self="showNewDirModal = false">
      <div class="modal">
        <h3>Create New Directory</h3>
        <p v-if="selectedDirectory" class="modal-subtitle">
          Inside: {{ selectedDirectory.path }}
        </p>
        
        <form @submit.prevent="createDirectory">
          <div v-if="newDirError" class="error-message">{{ newDirError }}</div>
          
          <div class="form-group">
            <label for="dirName">Directory Name</label>
            <input
              id="dirName"
              v-model="newDirName"
              type="text"
              placeholder="Enter directory name"
              autofocus
            />
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="newDirPublic" />
              <span>Public directory (accessible to all users)</span>
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="showNewDirModal = false" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Edit directory modal -->
    <div v-if="showEditDirModal" class="modal-overlay" @click.self="showEditDirModal = false">
      <div class="modal">
        <h3>Edit Directory</h3>
        
        <form @submit.prevent="updateDirectory">
          <div v-if="editDirError" class="error-message">{{ editDirError }}</div>
          
          <div class="form-group">
            <label for="editDirName">Directory Name</label>
            <input
              id="editDirName"
              v-model="editDirName"
              type="text"
              placeholder="Enter directory name"
              autofocus
            />
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="editDirPublic" />
              <span>Public directory (accessible to all users)</span>
            </label>
          </div>
          
          <div class="modal-actions">
            <button type="button" @click="showEditDirModal = false" class="btn-secondary">
              Cancel
            </button>
            <button type="submit" class="btn-primary">
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Share Modal -->
    <Teleport to="body">
      <div v-if="shareFile" class="modal-overlay" @click.self="closeShare">
        <div class="modal share-modal">
          <div class="modal-header">
            <h3>Share File</h3>
            <button class="close-btn" @click="closeShare">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
          
          <div class="modal-content">
            <div class="file-summary">
              <div class="file-icon small">
                 <!-- Simplified icon -->
                 <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                    <polyline points="13 2 13 9 20 9"/>
                 </svg>
              </div>
              <span class="filename">{{ shareFile.filename }}</span>
            </div>

            <div class="share-toggle">
              <label class="switch">
                <input type="checkbox" :checked="shareFile.is_public" @change="togglePublic">
                <span class="slider round"></span>
              </label>
              <div class="toggle-label">
                <span class="label-title">Public Access</span>
                <span class="label-desc">{{ shareFile.is_public ? 'Anyone with the link can view' : 'Only you can view' }}</span>
              </div>
            </div>

            <div v-if="shareFile.is_public" class="share-link-box">
              <input type="text" readonly :value="shareLink" />
              <button class="copy-btn" @click="copyLink">
                <span v-if="isCopied">Copied!</span>
                <span v-else>Copy</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.files-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  padding: 1rem 1.5rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-small {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
  border-radius: 0.5rem;
  color: white;
}

.header-left h1 {
  font-size: 1.25rem;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-email {
  color: var(--text-muted);
  font-size: 0.875rem;
}

.header-right .btn-secondary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.role-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
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

.header-right .btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--bg-tertiary);
  border-radius: 0.5rem;
  color: var(--text-muted);
  transition: all 0.15s;
}

.header-right .btn-icon:hover {
  background: var(--primary);
  color: white;
}

/* Main content */
.main-content {
  flex: 1;
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

/* Sidebar */
.sidebar {
  width: 300px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}

.sidebar-header h2 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.directory-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: var(--text-muted);
}

.empty-state p {
  margin-bottom: 1rem;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.8125rem;
}

/* Files area */
.files-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.no-selection {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-selection-content {
  text-align: center;
  color: var(--text-muted);
}

.no-selection-content svg {
  margin-bottom: 1rem;
  opacity: 0.5;
}

.no-selection-content h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.files-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg-primary);
}

.files-header-info h2 {
  font-size: 1.25rem;
  font-weight: 600;
}

.files-header-info .path {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 1.5rem;
  width: 100%;
  max-width: 400px;
  animation: slideUp 0.2s ease;
}

.modal h3 {
  font-size: 1.125rem;
  margin-bottom: 0.25rem;
}

.modal-subtitle {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.modal .form-group {
  margin-bottom: 1.25rem;
}

.modal .form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}
</style>
