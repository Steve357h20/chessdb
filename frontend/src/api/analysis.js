import request from './request'

export function startAnalysis(gameId, params) {
  return request.post(`/analysis/game/${gameId}/start`, params)
}

export function getAnalysisStatus(gameId) {
  return request.get(`/analysis/game/${gameId}/status`)
}

export function getAnalysisResult(gameId) {
  return request.get(`/analysis/game/${gameId}`)
}

export function getMoveAnalysis(gameId, moveNumber) {
  return request.get(`/analysis/game/${gameId}/move/${moveNumber}`)
}

export function getTaskStatus(taskId) {
  return request.get(`/analysis/tasks/${taskId}`)
}

export function listAnalysisTasks() {
  return request.get('/analysis/tasks')
}

export function cancelAnalysisTask(taskId) {
  return request.delete(`/analysis/tasks/${taskId}`)
}

export function getEngineInfo() {
  return request.get('/analysis/engines')
}
