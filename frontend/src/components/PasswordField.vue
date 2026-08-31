<template>
  <div class="password-wrap">
    <input
      :value="modelValue"
      :type="visible ? 'text' : 'password'"
      :autocomplete="autocomplete"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :minlength="minlength"
      :name="name"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button
      type="button"
      class="password-toggle"
      :aria-label="visible ? 'Hide password' : 'Show password'"
      :aria-pressed="visible"
      :disabled="disabled"
      @click="visible = !visible"
    >
      <EyeOff v-if="visible" :size="18" :stroke-width="1.75" />
      <Eye v-else :size="18" :stroke-width="1.75" />
    </button>
  </div>
</template>

<script setup>
import { Eye, EyeOff } from '@lucide/vue'
import { ref } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  autocomplete: { type: String, default: 'current-password' },
  placeholder: { type: String, default: '••••••••' },
  disabled: { type: Boolean, default: false },
  required: { type: Boolean, default: false },
  minlength: { type: [Number, String], default: undefined },
  name: { type: String, default: undefined },
})

defineEmits(['update:modelValue'])

const visible = ref(false)
</script>

<style scoped>
.password-wrap {
  position: relative;
  display: block;
  width: 100%;
}

.password-wrap input {
  width: 100%;
  box-sizing: border-box;
  font-family: var(--font-body);
  font-size: 1rem;
  padding: 0.65rem 2.65rem 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  text-transform: none;
  letter-spacing: normal;
}

.password-wrap input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.password-wrap input:disabled {
  opacity: 0.6;
}

.password-toggle {
  position: absolute;
  right: 0.3rem;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0;
}

.password-toggle:hover:not(:disabled) {
  color: var(--color-text);
  background: rgba(196, 163, 90, 0.12);
}

.password-toggle:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
