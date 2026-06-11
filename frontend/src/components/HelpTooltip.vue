<template>
  <el-tooltip :content="content" :placement="placement" :effect="effect">
    <el-icon class="ht-icon" :style="{ fontSize: size + 'px' }">
      <QuestionFilled />
    </el-icon>
  </el-tooltip>
</template>

<script setup>
import { QuestionFilled } from '@element-plus/icons-vue'

defineProps({
  content: { type: String, required: true },
  placement: { type: String, default: 'top' },
  effect: { type: String, default: 'dark' },
  size: { type: Number, default: 14 },
})
</script>

<style scoped>
.ht-icon {
  color: var(--text-color-secondary);
  cursor: help;
  vertical-align: middle;
  margin-left: 2px;
}

.ht-icon:hover {
  color: #409eff;
}
</style>
