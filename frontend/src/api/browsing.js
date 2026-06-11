import request from './request'

export function getBrowsingHistory(params) {
  return request.get('/browsing', { params })
}

export function recordBrowsing(gameId) {
  return request.post('/browsing', { game_id: gameId })
}

export function deleteBrowsing(gameId) {
  return request.delete(`/browsing/${gameId}`)
}

export function clearBrowsing() {
  return request.post('/browsing/clear')
}
