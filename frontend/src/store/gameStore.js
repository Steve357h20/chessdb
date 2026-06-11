import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getGame, getGameMoves, getGameAnalysis, analyzeGame } from '@/api/games'

export const useGameStore = defineStore('game', () => {
  const currentGame = ref(null)
  const currentMove = ref(0)
  const isPlaying = ref(false)
  const playSpeed = ref(1000)
  const moves = ref([])
  const analysisData = ref(null)
  const loading = ref(false)

  let playTimer = null

  const totalMoves = computed(() => Math.max(0, moves.value.length - 1))

  const currentFen = computed(() => {
    if (!moves.value.length) return 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    const idx = Math.min(currentMove.value, moves.value.length - 1)
    return moves.value[idx]?.fen || moves.value[0]?.fen
  })

  const currentLastMove = computed(() => {
    if (!moves.value.length || currentMove.value <= 0) return null
    const idx = Math.min(currentMove.value, moves.value.length - 1)
    const pos = moves.value[idx]
    return pos?.from && pos?.to ? { from: pos.from, to: pos.to } : null
  })

  const currentTurn = computed(() => {
    const fen = currentFen.value
    if (!fen) return 'white'
    return fen.includes(' w ') ? 'white' : 'black'
  })

  const currentEvalScore = computed(() => {
    if (!analysisData.value?.length) return null
    const idx = Math.min(currentMove.value, analysisData.value.length - 1)
    if (idx < 0) return null
    return analysisData.value[idx]?.score ?? null
  })

  const currentMoveEval = computed(() => {
    if (!moves.value.length || currentMove.value <= 0) return null
    const idx = Math.min(currentMove.value, moves.value.length - 1)
    const pos = moves.value[idx]
    if (!pos) return null
    return {
      move: pos.san || '',
      score: pos.score ?? null,
      win_rate: pos.win_rate ?? null,
      best_move: pos.best_move || null,
      best_score: pos.best_score ?? null,
      evaluation: pos.evaluation || null,
      nag: pos.nag ?? null,
      pv: pos.pv || null,
      comment: pos.comment || null,
    }
  })

  const displayMoves = computed(() => {
    if (!moves.value.length) return []
    const result = []
    for (let i = 1; i < moves.value.length; i++) {
      const pos = moves.value[i]
      const moveNum = Math.ceil(i / 2)
      if (i % 2 === 1) {
        result.push({
          move_number: moveNum,
          white: pos.san || '...',
          black: '',
          white_eval: pos.eval_data || null,
          black_eval: null,
        })
      } else {
        if (result.length) {
          result[result.length - 1].black = pos.san || '...'
          result[result.length - 1].black_eval = pos.eval_data || null
        }
      }
    }
    return result
  })

  async function loadGame(gameId) {
    loading.value = true
    try {
      const res = await getGame(gameId)
      const data = res.data || res
      currentGame.value = data

      if (data.moves && Array.isArray(data.moves)) {
        moves.value = [
          { fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' },
          ...data.moves,
        ]
      } else if (data.pgn) {
        moves.value = parsePgn(data.pgn)
      } else {
        moves.value = [{ fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' }]
      }

      currentMove.value = 0
      isPlaying.value = false

      try {
        const analysisRes = await getGameAnalysis(gameId)
        analysisData.value = (analysisRes.data || analysisRes) || null
      } catch {
        analysisData.value = null
      }
    } finally {
      loading.value = false
    }
  }

  function parsePgn(pgn) {
    if (!pgn) return [{ fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' }]
    const fens = [{ fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' }]
    const moveRegex = /\d+\.\s*([a-h1-8KQRBNO][\w\-+=#!?]+)\s*([a-h1-8KQRBNO][\w\-+=#!?]*)?/g
    let match
    while ((match = moveRegex.exec(pgn)) !== null) {
      if (match[1]) fens.push({ fen: '', san: match[1], eval_data: null })
      if (match[2]) fens.push({ fen: '', san: match[2], eval_data: null })
    }
    return fens
  }

  function nextMove() {
    if (currentMove.value < totalMoves.value) {
      currentMove.value++
    }
  }

  function prevMove() {
    if (currentMove.value > 0) {
      currentMove.value--
    }
  }

  function jumpToMove(n) {
    currentMove.value = Math.max(0, Math.min(totalMoves.value, n))
  }

  function startAutoPlay() {
    stopAutoPlay()
    isPlaying.value = true
    playTimer = setInterval(() => {
      if (currentMove.value < totalMoves.value) {
        currentMove.value++
      } else {
        stopAutoPlay()
      }
    }, playSpeed.value)
  }

  function stopAutoPlay() {
    if (playTimer) {
      clearInterval(playTimer)
      playTimer = null
    }
    isPlaying.value = false
  }

  function setSpeed(speed) {
    playSpeed.value = speed
    if (isPlaying.value) {
      stopAutoPlay()
      startAutoPlay()
    }
  }

  async function requestAnalysis(gameId, params) {
    return analyzeGame(gameId, params)
  }

  function reset() {
    currentGame.value = null
    currentMove.value = 0
    isPlaying.value = false
    moves.value = []
    analysisData.value = null
    stopAutoPlay()
  }

  return {
    currentGame,
    currentMove,
    isPlaying,
    playSpeed,
    moves,
    analysisData,
    loading,
    totalMoves,
    currentFen,
    currentLastMove,
    currentTurn,
    currentEvalScore,
    currentMoveEval,
    displayMoves,
    loadGame,
    nextMove,
    prevMove,
    jumpToMove,
    startAutoPlay,
    stopAutoPlay,
    setSpeed,
    requestAnalysis,
    reset,
  }
})
