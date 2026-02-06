<script setup>
import { ref, computed } from 'vue'
import api from '../api/client'

const props = defineProps({
  files: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['download', 'delete', 'share'])

const previewFile = ref(null)
const previewUrl = ref('')
const previewLoading = ref(false)

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function getFileIcon(contentType) {
  if (contentType.startsWith('image/')) return 'image'
  if (contentType.startsWith('video/')) return 'video'
  if (contentType.startsWith('audio/')) return 'audio'
  if (contentType === 'application/pdf') return 'pdf'
  if (contentType.includes('zip') || contentType.includes('compressed')) return 'archive'
  return 'file'
}

function isPreviewable(contentType) {
  return contentType.startsWith('image/') ||
         contentType.startsWith('video/') ||
         contentType === 'application/pdf'
}

function getPreviewType(contentType) {
  if (contentType.startsWith('image/')) return 'image'
  if (contentType.startsWith('video/')) return 'video'
  if (contentType === 'application/pdf') return 'pdf'
  return null
}

async function openPreview(file) {
  if (!isPreviewable(file.content_type)) {
    // Not previewable, just download
    emit('download', file.id, file.filename)
    return
  }
  
  previewFile.value = file
  previewLoading.value = true
  
  try {
    const response = await api.get(`/files/${file.id}/preview-url`)
    previewUrl.value = response.data.presigned_url
  } catch (error) {
    console.error('Failed to get preview URL:', error)
    previewFile.value = null
  } finally {
    previewLoading.value = false
  }
}

function closePreview() {
  previewFile.value = null
  previewUrl.value = ''
}

function handleDownloadFromPreview() {
  if (previewFile.value) {
    emit('download', previewFile.value.id, previewFile.value.filename)
  }
}
</script>

<template>
  <div class="file-list">
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>Loading files...</span>
    </div>
    
    <div v-else-if="files.length === 0" class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <p>No files in this directory</p>
    </div>
    
    <div v-else class="files-grid">
      <div
        v-for="file in files"
        :key="file.id"
        class="file-card"
        :class="{ clickable: isPreviewable(file.content_type) }"
        @click="openPreview(file)"
      >
        <div class="file-icon" :class="getFileIcon(file.content_type)">
          <!-- Image icon -->
          <svg v-if="getFileIcon(file.content_type) === 'image'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
          <!-- Video icon -->
          <svg v-else-if="getFileIcon(file.content_type) === 'video'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          <!-- PDF icon -->
          <svg v-else-if="getFileIcon(file.content_type) === 'pdf'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <path d="M10 12h4"/>
            <path d="M10 16h4"/>
          </svg>
          <!-- Archive icon -->
          <svg v-else-if="getFileIcon(file.content_type) === 'archive'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 8v13H3V8"/>
            <path d="M1 3h22v5H1z"/>
            <path d="M10 12h4"/>
          </svg>
          <!-- Default file icon -->
          <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        
        <div class="file-info">
          <h4 class="file-name" :title="file.filename">{{ file.filename }}</h4>
          <div class="file-meta">
            <span>{{ formatSize(file.size) }}</span>
            <span>•</span>
            <span>{{ formatDate(file.created_at) }}</span>
          </div>
        </div>
        
        <div class="file-actions" @click.stop>
          <button
            v-if="isPreviewable(file.content_type)"
            class="action-btn preview"
            @click.stop="openPreview(file)"
            title="Preview"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
          <button
            class="action-btn download"
            @click.stop="emit('download', file.id, file.filename)"
            title="Download"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </button>
          <button
            class="action-btn share"
            @click.stop="emit('share', file)"
            title="Share"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
              <polyline points="16 6 12 2 8 6"/>
              <line x1="12" y1="2" x2="12" y2="15"/>
            </svg>
          </button>
          <button
            class="action-btn delete"
            @click.stop="emit('delete', file.id)"
            title="Delete"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Preview Modal -->
    <Teleport to="body">
      <div v-if="previewFile" class="preview-overlay" @click="closePreview">
        <div class="preview-modal" @click.stop>
          <div class="preview-header">
            <h3>{{ previewFile.filename }}</h3>
            <div class="preview-actions">
              <button class="preview-btn" @click="handleDownloadFromPreview" title="Download">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
              </button>
              <button class="preview-btn close" @click="closePreview" title="Close">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div class="preview-content">
            <div v-if="previewLoading" class="preview-loading">
              <div class="spinner"></div>
              <span>Loading preview...</span>
            </div>
            
            <template v-else-if="previewUrl">
              <!-- Image Preview -->
              <img 
                v-if="getPreviewType(previewFile.content_type) === 'image'"
                :src="previewUrl"
                :alt="previewFile.filename"
                class="preview-image"
              />
              
              <!-- Video Preview -->
              <video 
                v-else-if="getPreviewType(previewFile.content_type) === 'video'"
                :src="previewUrl"
                controls
                autoplay
                class="preview-video"
              >
                Your browser does not support video playback.
              </video>
              
              <!-- PDF Preview -->
              <iframe 
                v-else-if="getPreviewType(previewFile.content_type) === 'pdf'"
                :src="previewUrl"
                class="preview-pdf"
              />
            </template>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.file-list {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
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

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.file-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  transition: all 0.2s ease;
}

.file-card.clickable {
  cursor: pointer;
}

.file-card:hover {
  border-color: var(--primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px var(--shadow);
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 0.5rem;
  background: var(--bg-tertiary);
  color: var(--text-muted);
  flex-shrink: 0;
}

.file-icon.image {
  background: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
}

.file-icon.video {
  background: rgba(236, 72, 153, 0.15);
  color: #ec4899;
}

.file-icon.pdf {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.file-icon.archive {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 0.25rem;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.file-actions {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  padding: 0.5rem;
  background: transparent;
  border-radius: 0.375rem;
  color: var(--text-muted);
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: var(--bg-tertiary);
}

.action-btn.preview:hover {
  color: #22c55e;
}

.action-btn.download:hover {
  color: var(--primary);
}

.action-btn.delete:hover {
  color: var(--danger);
}

/* Preview Modal */
.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.preview-modal {
  background: var(--bg-secondary);
  border-radius: 1rem;
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border);
}

.preview-header h3 {
  font-size: 1rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-actions {
  display: flex;
  gap: 0.5rem;
}

.preview-btn {
  padding: 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 0.5rem;
  color: var(--text-muted);
  transition: all 0.15s;
}

.preview-btn:hover {
  color: var(--primary);
}

.preview-btn.close:hover {
  color: var(--danger);
}

.preview-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #000;
  min-height: 400px;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: var(--text-muted);
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

.preview-video {
  max-width: 100%;
  max-height: 80vh;
}

.preview-pdf {
  width: 100%;
  height: 80vh;
  border: none;
}
</style>
