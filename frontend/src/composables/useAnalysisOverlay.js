import { ref, watch } from 'vue'

export function useAnalysisOverlay() {
  const overlayVisible = ref(true)

  function dismissOverlay() {
    overlayVisible.value = false
  }

  function resetOverlay() {
    overlayVisible.value = true
  }

  function watchAnalyzing(analyzingRef) {
    watch(analyzingRef, (val) => {
      resetOverlay()
    })
  }

  return {
    overlayVisible,
    dismissOverlay,
    resetOverlay,
    watchAnalyzing,
  }
}
