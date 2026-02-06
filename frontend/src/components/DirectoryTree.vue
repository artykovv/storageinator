<script setup>
defineProps({
  directories: {
    type: Array,
    required: true
  },
  selectedId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['select', 'delete', 'edit'])
</script>

<template>
  <div class="directory-tree">
    <div
      v-for="dir in directories"
      :key="dir.id"
      class="directory-item"
    >
      <div
        class="directory-row"
        :class="{ selected: dir.id === selectedId }"
        @click="emit('select', dir)"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="directory-name">{{ dir.name }}</span>
        <button
          class="edit-btn"
          @click.stop="emit('edit', dir)"
          title="Edit directory"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
        <button
          class="delete-btn"
          @click.stop="emit('delete', dir.id)"
          title="Delete directory"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>
      </div>
      
      <div v-if="dir.children && dir.children.length > 0" class="children">
        <DirectoryTree
          :directories="dir.children"
          :selected-id="selectedId"
          @select="emit('select', $event)"
          @delete="emit('delete', $event)"
          @edit="emit('edit', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.directory-tree {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.directory-item {
  display: flex;
  flex-direction: column;
}

.directory-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--text-secondary);
}

.directory-row:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.directory-row.selected {
  background: var(--primary);
  color: white;
}

.directory-row.selected:hover {
  background: var(--primary-hover);
}

.directory-name {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.edit-btn,
.delete-btn {
  opacity: 0;
  padding: 0.25rem;
  background: transparent;
  border-radius: 0.25rem;
  color: var(--text-muted);
  transition: all 0.15s ease;
}

.directory-row:hover .edit-btn,
.directory-row:hover .delete-btn {
  opacity: 1;
}

.edit-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  color: var(--primary);
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}

.directory-row.selected .edit-btn,
.directory-row.selected .delete-btn {
  color: rgba(255, 255, 255, 0.7);
}

.directory-row.selected .edit-btn:hover,
.directory-row.selected .delete-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.children {
  padding-left: 1.25rem;
  border-left: 1px solid var(--border);
  margin-left: 0.625rem;
}
</style>
