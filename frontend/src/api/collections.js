import request from './request'

export function getCollections(params) {
  return request.get('/collections', { params })
}

export function addCollection(gameId, note = '') {
  return request.post('/collections', { game_id: gameId, note })
}

export function removeCollection(collectionId) {
  return request.delete(`/collections/${collectionId}`)
}

export function checkCollection(gameId) {
  return request.get(`/collections/check/${gameId}`)
}

export function updateCollectionNote(collectionId, note) {
  return request.put(`/collections/${collectionId}`, { note })
}
