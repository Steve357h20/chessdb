import request from './request'

export function getPuzzles(params) {
  return request.get('/practice/puzzles', { params })
}

export function getPuzzle(puzzleId) {
  return request.get(`/practice/puzzles/${puzzleId}`)
}

export function createPuzzle(data) {
  return request.post('/practice/puzzles', data)
}

export function deletePuzzle(puzzleId) {
  return request.delete(`/practice/puzzles/${puzzleId}`)
}

export function startPractice(data) {
  return request.post('/practice/start', data)
}

export function makeMove(data) {
  return request.post('/practice/move', data)
}

export function undoMove(data) {
  return request.post('/practice/undo', data)
}

export function getHint(data) {
  return request.post('/practice/hint', data)
}

export function resignPractice(data) {
  return request.post('/practice/resign', data)
}

export function getPracticeStatus(sessionId) {
  return request.get(`/practice/status/${sessionId}`)
}

export function getPracticeHistory(params) {
  return request.get('/practice/history', { params })
}

export function getPracticeDetail(practiceId) {
  return request.get(`/practice/history/${practiceId}`)
}

export function searchGames(params) {
  return request.get('/practice/search_games', { params })
}

export function startPracticeAnalysis(practiceId) {
  return request.post(`/practice/analyze/${practiceId}`)
}

export function getPracticeAnalysisStatus(practiceId) {
  return request.get(`/practice/analyze/${practiceId}/status`)
}

export function getPracticeAnalysisResult(practiceId) {
  return request.get(`/practice/analyze/${practiceId}/result`)
}
