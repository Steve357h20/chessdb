import { createPinia } from 'pinia'
import { useGameStore } from './gameStore'
import { useUserStore } from './userStore'
import { useUiStore } from './uiStore'
import { usePracticeStore } from './practiceStore'
import { useThemeStore } from './themeStore'

const pinia = createPinia()

export default pinia

export { useGameStore, useUserStore, useUiStore, usePracticeStore, useThemeStore }
