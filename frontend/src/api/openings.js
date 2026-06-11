import request from './request'

export function getOpenings(params) {
  return request.get('/openings', { params })
}

export function getOpening(id) {
  return request.get(`/openings/${id}`)
}

export function identifyOpening(moves) {
  return request.post('/openings/identify', { moves })
}

export function getOpeningTree(eco) {
  return request.get('/openings/tree', { params: { eco } })
}
