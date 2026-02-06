<script setup>
import { ref } from 'vue'
import api from '../api/client'

const props = defineProps({
  directoryId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['uploaded'])

const uploading = ref(false)
const progress = ref(0)
const error = ref('')
const fileInput = ref(null)

async function calculateSHA256(file) {
  const buffer = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

async function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return
  
  error.value = ''
  uploading.value = true
  progress.value = 0
  
  try {
    // Step 1: Request presigned URL
    progress.value = 10
    const urlResponse = await api.post('/files/upload-url', {
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      size: file.size,
      directory_id: props.directoryId
    })
    
    const { presigned_url, file_id } = urlResponse.data
    progress.value = 20
    
    // Step 2: Calculate SHA256
    const sha256 = await calculateSHA256(file)
    progress.value = 40
    
    // Step 3: Upload file directly to S3
    await fetch(presigned_url, {
      method: 'PUT',
      headers: {
        'Content-Type': file.type || 'application/octet-stream'
      },
      body: file
    })
    progress.value = 80
    
    // Step 4: Confirm upload
    await api.post(`/files/${file_id}/confirm`, { sha256 })
    progress.value = 100
    
    emit('uploaded')
    
    // Reset after short delay
    setTimeout(() => {
      uploading.value = false
      progress.value = 0
    }, 500)
    
  } catch (err) {
    error.value = err.response?.data?.detail || 'Upload failed'
    uploading.value = false
    progress.value = 0
  }
  
  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function triggerFileSelect() {
  fileInput.value?.click()
}
</script>

<template>
  <div class="file-upload">
    <input
      ref="fileInput"
      type="file"
      @change="handleFileSelect"
      style="display: none"
    />
    
    <button
      @click="triggerFileSelect"
      class="upload-btn"
      :disabled="uploading"
    >
      <svg v-if="!uploading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
      <div v-else class="upload-spinner"></div>
      {{ uploading ? `Uploading ${progress}%` : 'Upload File' }}
    </button>
    
    <div v-if="error" class="upload-error">{{ error }}</div>
  </div>
</template>

<style scoped>
.file-upload {
  position: relative;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--primary);
  color: white;
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.upload-btn:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.upload-btn:disabled {
  opacity: 0.8;
  cursor: wait;
}

.upload-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.upload-error {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  background: var(--danger);
  color: white;
  font-size: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  white-space: nowrap;
}
</style>
