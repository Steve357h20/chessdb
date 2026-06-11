import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { Chess } from 'chess.js'
import {
  startPractice,
  makeMove,
  undoMove,
  getHint,
  resignPractice,
  getPuzzles,
} from '@/api/practice'

function _handleSessionExpired(error, store) {
  if (error?._sessionExpired || error?.response?.status === 410) {
    store.sessionExpired = true
  }
}

export const usePracticeStore = defineStore('practice', () => {
  const sessionId = ref(null)
  const currentFen = ref('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
  const isUserTurn = ref(true)
  const userColor = ref('white')
  const difficulty = ref('medium')
  const mode = ref(null)
  const puzzleInfo = ref(null)
  const startFen = ref('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
  const moveHistory = ref([])
  const isGameOver = ref(false)
  const result = ref(null)
  const lastAiMove = ref(null)
  const lastMoveFromTo = ref(null)
  const hintsUsed = ref(0)
  const undoCount = ref(0)
  const startTime = ref(null)
  const hintData = ref(null)
  const showHint = ref(false)
  const loading = ref(false)
  const aiThinking = ref(false)
  const error = ref(null)
  const puzzles = ref([])
  const sessionExpired = ref(false)

  const currentTurn = computed(() => {
    if (!currentFen.value) return 'white'
    return currentFen.value.includes(' w ') ? 'white' : 'black'
  })

  const positions = computed(() => {
    const result = [{ fen: startFen.value }]
    try {
      const chess = new Chess(startFen.value)
      for (const entry of moveHistory.value) {
        chess.move(entry.san)
        result.push({ fen: chess.fen(), san: entry.san, color: entry.color })
      }
    } catch {
      for (const entry of moveHistory.value) {
        result.push({ fen: '', san: entry.san, color: entry.color })
      }
    }
    return result
  })

  function _initSession(data) {
    sessionId.value = data.session_id
    currentFen.value = data.fen || data.start_fen || startFen.value
    startFen.value = data.fen || data.start_fen || startFen.value
    isUserTurn.value = data.is_user_turn ?? true
    userColor.value = data.user_color || 'white'
    difficulty.value = data.difficulty || 'medium'
    mode.value = data.mode || mode.value
    puzzleInfo.value = data.puzzle_info || null
    moveHistory.value = []
    isGameOver.value = false
    result.value = null
    lastAiMove.value = null
    lastMoveFromTo.value = null
    hintsUsed.value = 0
    undoCount.value = 0
    hintData.value = null
    showHint.value = false
    startTime.value = Date.now()
    sessionExpired.value = false
  }

  async function loadPuzzles(params) {
    try {
      const res = await getPuzzles(params)
      const data = res.data || res
      puzzles.value = data.puzzles || []
    } catch (e) {
      error.value = e.message || '加载残局列表失败'
    }
  }

  async function startFromPuzzle(puzzleId, color = 'white', diff = 'medium') {
    loading.value = true
    error.value = null
    try {
      const res = await startPractice({
        mode: 'puzzle',
        puzzle_id: puzzleId,
        user_color: color,
        difficulty: diff,
      })
      const data = res.data || res
      _initSession(data)
    } catch (e) {
      error.value = e.message || '启动残局练习失败'
    } finally {
      loading.value = false
    }
  }

  async function startFromGame(gameId, fromMove = 0, color = 'white', diff = 'medium') {
    loading.value = true
    error.value = null
    try {
      const res = await startPractice({
        mode: 'from_game',
        game_id: gameId,
        from_move: fromMove,
        user_color: color,
        difficulty: diff,
      })
      const data = res.data || res
      _initSession(data)
    } catch (e) {
      error.value = e.message || '启动对局练习失败'
    } finally {
      loading.value = false
    }
  }

  async function startCustom(fen = '', color = 'white', diff = 'medium') {
    loading.value = true
    error.value = null
    try {
      const res = await startPractice({
        mode: 'custom',
        custom_fen: fen,
        user_color: color,
        difficulty: diff,
      })
      const data = res.data || res
      _initSession(data)
    } catch (e) {
      error.value = e.message || '启动自定义练习失败'
    } finally {
      loading.value = false
    }
  }

  async function submitMove(san) {
    if (!isUserTurn.value || isGameOver.value || aiThinking.value) return
    aiThinking.value = true
    error.value = null
    try {
      const res = await makeMove({ session_id: sessionId.value, move: san })
      const data = res.data || res

      try {
        const preMoveChess = new Chess(currentFen.value)
        const userMoveObj = preMoveChess.move(san)
        if (userMoveObj) {
          lastMoveFromTo.value = { from: userMoveObj.from, to: userMoveObj.to, isAi: false }
        }
      } catch { /* ignore */ }

      moveHistory.value.push({ san, color: 'user' })

      if (data.user_fen) {
        currentFen.value = data.user_fen
      }

      if (data.ai_move) {
        const delay = Math.floor(Math.random() * 800) + 400
        await new Promise(resolve => setTimeout(resolve, delay))
        moveHistory.value.push({ san: data.ai_move, color: 'ai' })
        lastAiMove.value = data.ai_move
        try {
          const preAiChess = new Chess(data.user_fen || currentFen.value)
          const aiMoveObj = preAiChess.move(data.ai_move)
          if (aiMoveObj) {
            lastMoveFromTo.value = { from: aiMoveObj.from, to: aiMoveObj.to, isAi: true }
          }
        } catch { /* ignore */ }
        currentFen.value = data.fen || currentFen.value
      } else {
        currentFen.value = data.fen || currentFen.value
      }

      isUserTurn.value = data.is_user_turn ?? true
      isGameOver.value = data.is_game_over ?? false
      result.value = data.result || null

      showHint.value = false
      hintData.value = null
    } catch (e) {
      _handleSessionExpired(e, { sessionExpired })
      if (sessionExpired.value) {
        isGameOver.value = true
        result.value = '*'
      }
      error.value = e.message || '走棋失败'
    } finally {
      aiThinking.value = false
    }
  }

  async function undo() {
    if (moveHistory.value.length < 2) return
    error.value = null
    try {
      const res = await undoMove({ session_id: sessionId.value })
      const data = res.data || res

      moveHistory.value.pop()
      moveHistory.value.pop()

      try {
        const chess = new Chess(startFen.value)
        for (const entry of moveHistory.value) {
          chess.move(entry.san)
        }
        currentFen.value = chess.fen()
      } catch {
        currentFen.value = data.fen || currentFen.value
      }

      undoCount.value++
      isUserTurn.value = true
      isGameOver.value = false
      result.value = null

      if (moveHistory.value.length > 0) {
        const lastEntry = moveHistory.value[moveHistory.value.length - 1]
        try {
          const chess = new Chess(startFen.value)
          for (let i = 0; i < moveHistory.value.length - 1; i++) {
            chess.move(moveHistory.value[i].san)
          }
          const moveObj = chess.move(lastEntry.san)
          if (moveObj) {
            lastMoveFromTo.value = { from: moveObj.from, to: moveObj.to, isAi: lastEntry.color === 'ai' }
          } else {
            lastMoveFromTo.value = null
          }
        } catch {
          lastMoveFromTo.value = null
        }
      } else {
        lastMoveFromTo.value = null
      }
    } catch (e) {
      _handleSessionExpired(e, { sessionExpired })
      if (sessionExpired.value) {
        isGameOver.value = true
      }
      error.value = e.message || '悔棋失败'
    }
  }

  async function requestHint() {
    error.value = null
    try {
      const res = await getHint({ session_id: sessionId.value })
      const data = res.data || res
      hintData.value = data
      showHint.value = true
      hintsUsed.value++
    } catch (e) {
      _handleSessionExpired(e, { sessionExpired })
      if (sessionExpired.value) {
        isGameOver.value = true
      }
      error.value = e.message || '获取提示失败'
    }
  }

  async function resign() {
    error.value = null
    try {
      await resignPractice({ session_id: sessionId.value })
      isGameOver.value = true
      result.value = userColor.value === 'white' ? '0-1' : '1-0'
    } catch (e) {
      _handleSessionExpired(e, { sessionExpired })
      if (sessionExpired.value) {
        isGameOver.value = true
        result.value = userColor.value === 'white' ? '0-1' : '1-0'
      }
      error.value = e.message || '认输失败'
    }
  }

  function reset() {
    sessionId.value = null
    currentFen.value = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    isUserTurn.value = true
    userColor.value = 'white'
    difficulty.value = 'medium'
    mode.value = null
    puzzleInfo.value = null
    startFen.value = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    moveHistory.value = []
    isGameOver.value = false
    result.value = null
    lastAiMove.value = null
    lastMoveFromTo.value = null
    hintsUsed.value = 0
    undoCount.value = 0
    startTime.value = null
    hintData.value = null
    showHint.value = false
    loading.value = false
    aiThinking.value = false
    error.value = null
    sessionExpired.value = false
  }

  return {
    sessionId,
    currentFen,
    isUserTurn,
    userColor,
    difficulty,
    mode,
    puzzleInfo,
    startFen,
    moveHistory,
    isGameOver,
    result,
    lastAiMove,
    lastMoveFromTo,
    hintsUsed,
    undoCount,
    startTime,
    hintData,
    showHint,
    loading,
    aiThinking,
    error,
    puzzles,
    sessionExpired,
    currentTurn,
    positions,
    loadPuzzles,
    startFromPuzzle,
    startFromGame,
    startCustom,
    submitMove,
    undo,
    requestHint,
    resign,
    reset,
  }
})
