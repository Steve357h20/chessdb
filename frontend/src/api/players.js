import request from './request'

export function getPlayers(params) {
  return request.get('/players', { params })
}

export function getPlayerFilters() {
  return request.get('/players/filters')
}

export function getPlayer(id) {
  return request.get(`/players/${id}`)
}

export function getPlayerGames(id, params) {
  return request.get(`/players/${id}/games`, { params })
}

export function getPlayerStats(id) {
  return request.get(`/players/${id}/stats`)
}
