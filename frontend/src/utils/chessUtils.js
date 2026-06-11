const PIECE_MAP = {
  p: 'pawn', n: 'knight', b: 'bishop', r: 'rook', q: 'queen', k: 'king',
}

const FILES = 'abcdefgh'
const RANKS = '87654321'

const NAG_SYMBOLS = {
  1: '!',
  2: '?',
  3: '!!',
  4: '??',
  5: '!?',
  6: '?!',
  7: '□',
  10: '=',
  13: '∞',
  14: '+=',
  15: '=+',
  16: '±',
  17: '∓',
  18: '+-',
  19: '-+',
  22: '⨀',
  23: '⨀',
  26: '△',
  32: '↑',
  36: '↑↑',
  40: '→',
  44: '⇗',
  132: '⇓',
  138: '⇓⇓',
  146: '⊥',
}

export function parseFEN(fen) {
  if (!fen) return []
  const parts = fen.split(' ')
  const rows = parts[0].split('/')
  const board = []

  for (let r = 0; r < 8; r++) {
    const row = []
    for (const ch of rows[r]) {
      if (ch >= '1' && ch <= '8') {
        for (let i = 0; i < parseInt(ch); i++) row.push(null)
      } else {
        const color = ch === ch.toUpperCase() ? 'w' : 'b'
        const type = PIECE_MAP[ch.toLowerCase()]
        row.push({ color, type, char: ch })
      }
    }
    board.push(row)
  }

  return {
    board,
    turn: parts[1] || 'w',
    castling: parts[2] || '-',
    enPassant: parts[3] || '-',
    halfmove: parseInt(parts[4]) || 0,
    fullmove: parseInt(parts[5]) || 1,
  }
}

export function getPieceAt(fen, square) {
  const { board } = parseFEN(fen)
  const coords = squareToCoords(square)
  if (!coords) return null
  return board[coords.row]?.[coords.col] || null
}

export function isLightSquare(square) {
  if (!square || square.length !== 2) return true
  const col = square.charCodeAt(0) - 97
  const row = parseInt(square[1])
  return (col + row) % 2 === 0
}

export function squareToCoords(square) {
  if (!square || square.length !== 2) return null
  const col = square.charCodeAt(0) - 97
  const row = 8 - parseInt(square[1])
  if (col < 0 || col > 7 || row < 0 || row > 7) return null
  return { col, row }
}

export function coordsToSquare(col, row) {
  if (col < 0 || col > 7 || row < 0 || row > 7) return ''
  return String.fromCharCode(97 + col) + String(8 - row)
}

export function sanToCoords(san) {
  if (!san) return null

  let move = san.replace(/[+#!?]/g, '')

  let promotion = null
  const promoMatch = move.match(/=([QRBN])$/i)
  if (promoMatch) {
    promotion = promoMatch[1].toLowerCase()
    move = move.replace(/=[QRBN]/i, '')
  }

  if (move === 'O-O' || move === '0-0') {
    return { from: 'e1', to: 'g1', promotion, castling: 'kingside' }
  }
  if (move === 'O-O-O' || move === '0-0-0') {
    return { from: 'e1', to: 'c1', promotion, castling: 'queenside' }
  }

  const toSquare = move.slice(-2)
  if (!/^[a-h][1-8]$/.test(toSquare)) return null

  const piece = /^[A-Z]/.test(move) ? move[0].toLowerCase() : 'p'
  const rest = piece === 'p' ? move.slice(0, -2) : move.slice(1, -2)

  let fromFile = null
  let fromRank = null
  for (const ch of rest) {
    if (ch >= 'a' && ch <= 'h') fromFile = ch
    else if (ch >= '1' && ch <= '8') fromRank = ch
  }

  return {
    from: fromFile && fromRank ? `${fromFile}${fromRank}` : null,
    to: toSquare,
    piece,
    fromFile,
    fromRank,
    promotion,
    castling: null,
  }
}

export function coordsToSan(from, to, promotion) {
  let san = from + to
  if (promotion) san += '=' + promotion.toUpperCase()
  return san
}

export function uciToCoords(uci) {
  if (!uci || uci.length < 4) return null
  const from = uci.slice(0, 2)
  const to = uci.slice(2, 4)
  const promotion = uci.length > 4 ? uci[4] : null

  if (!/^[a-h][1-8]$/.test(from) || !/^[a-h][1-8]$/.test(to)) return null

  return { from, to, promotion }
}

export function parseMove(san, fen) {
  const result = sanToCoords(san)
  if (!result) return null

  if (result.from) return result

  if (!fen) return result

  const { board, turn } = parseFEN(fen)
  const piece = result.piece
  const toCol = result.to.charCodeAt(0) - 97
  const toRow = 8 - parseInt(result.to[1])

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const p = board[r][c]
      if (!p) continue
      if (p.color !== turn) continue
      if (p.type !== piece) continue
      if (result.fromFile && FILES[c] !== result.fromFile) continue
      if (result.fromRank && RANKS[r] !== result.fromRank) continue

      return { ...result, from: coordsToSquare(c, r) }
    }
  }

  return result
}

export function getLegalMoves(fen) {
  const { board, turn, castling, enPassant } = parseFEN(fen)
  const moves = []

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const piece = board[r][c]
      if (!piece || piece.color !== turn) continue

      const from = coordsToSquare(c, r)

      switch (piece.type) {
        case 'pawn':
          addPawnMoves(board, r, c, turn, enPassant, from, moves)
          break
        case 'knight':
          addKnightMoves(board, r, c, turn, from, moves)
          break
        case 'bishop':
          addSlidingMoves(board, r, c, turn, from, [[-1, -1], [-1, 1], [1, -1], [1, 1]], moves)
          break
        case 'rook':
          addSlidingMoves(board, r, c, turn, from, [[-1, 0], [1, 0], [0, -1], [0, 1]], moves)
          break
        case 'queen':
          addSlidingMoves(board, r, c, turn, from, [[-1, -1], [-1, 1], [1, -1], [1, 1], [-1, 0], [1, 0], [0, -1], [0, 1]], moves)
          break
        case 'king':
          addKingMoves(board, r, c, turn, from, moves)
          break
      }
    }
  }

  addCastlingMoves(board, turn, castling, moves)

  return moves
}

function addPawnMoves(board, r, c, turn, enPassant, from, moves) {
  const dir = turn === 'w' ? -1 : 1
  const startRow = turn === 'w' ? 6 : 1
  const promoRow = turn === 'w' ? 0 : 7

  const nr = r + dir
  if (nr >= 0 && nr < 8 && !board[nr][c]) {
    if (nr === promoRow) {
      for (const p of ['q', 'r', 'b', 'n']) {
        moves.push({ from, to: coordsToSquare(c, nr), promotion: p })
      }
    } else {
      moves.push({ from, to: coordsToSquare(c, nr) })
      if (r === startRow && !board[r + 2 * dir][c]) {
        moves.push({ from, to: coordsToSquare(c, r + 2 * dir) })
      }
    }
  }

  for (const dc of [-1, 1]) {
    const nc = c + dc
    if (nc < 0 || nc > 7 || nr < 0 || nr > 7) continue
    const target = board[nr][nc]
    const epSquare = enPassant !== '-' ? enPassant : null
    if ((target && target.color !== turn) || (epSquare && coordsToSquare(nc, nr) === epSquare)) {
      if (nr === promoRow) {
        for (const p of ['q', 'r', 'b', 'n']) {
          moves.push({ from, to: coordsToSquare(nc, nr), promotion: p })
        }
      } else {
        moves.push({ from, to: coordsToSquare(nc, nr) })
      }
    }
  }
}

function addKnightMoves(board, r, c, turn, from, moves) {
  const offsets = [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]]
  for (const [dr, dc] of offsets) {
    const nr = r + dr, nc = c + dc
    if (nr < 0 || nr > 7 || nc < 0 || nc > 7) continue
    const target = board[nr][nc]
    if (!target || target.color !== turn) {
      moves.push({ from, to: coordsToSquare(nc, nr) })
    }
  }
}

function addSlidingMoves(board, r, c, turn, from, directions, moves) {
  for (const [dr, dc] of directions) {
    let nr = r + dr, nc = c + dc
    while (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
      const target = board[nr][nc]
      if (!target) {
        moves.push({ from, to: coordsToSquare(nc, nr) })
      } else {
        if (target.color !== turn) moves.push({ from, to: coordsToSquare(nc, nr) })
        break
      }
      nr += dr
      nc += dc
    }
  }
}

function addKingMoves(board, r, c, turn, from, moves) {
  for (let dr = -1; dr <= 1; dr++) {
    for (let dc = -1; dc <= 1; dc++) {
      if (dr === 0 && dc === 0) continue
      const nr = r + dr, nc = c + dc
      if (nr < 0 || nr > 7 || nc < 0 || nc > 7) continue
      const target = board[nr][nc]
      if (!target || target.color !== turn) {
        moves.push({ from, to: coordsToSquare(nc, nr) })
      }
    }
  }
}

function addCastlingMoves(board, turn, castling, moves) {
  const row = turn === 'w' ? 7 : 0
  if (turn === 'w' && castling.includes('K') && !board[row][5] && !board[row][6]) {
    moves.push({ from: 'e1', to: 'g1', castling: 'kingside' })
  }
  if (turn === 'w' && castling.includes('Q') && !board[row][1] && !board[row][2] && !board[row][3]) {
    moves.push({ from: 'e1', to: 'c1', castling: 'queenside' })
  }
  if (turn === 'b' && castling.includes('k') && !board[row][5] && !board[row][6]) {
    moves.push({ from: 'e8', to: 'g8', castling: 'kingside' })
  }
  if (turn === 'b' && castling.includes('q') && !board[row][1] && !board[row][2] && !board[row][3]) {
    moves.push({ from: 'e8', to: 'c8', castling: 'queenside' })
  }
}

export function scoreToWinRate(score) {
  if (score == null) return 50
  return Math.round(100 / (1 + Math.exp(-score / 200)))
}

export function nagToSymbol(nag) {
  if (nag == null) return ''
  return NAG_SYMBOLS[nag] || ''
}

export function formatScore(score, type = 'cp') {
  if (score == null) return '-'
  if (type === 'mate') {
    return score > 0 ? `M${score}` : `-M${Math.abs(score)}`
  }
  return (score / 100).toFixed(2)
}

export function formatEval(evalCp, evalType = 'cp') {
  if (evalCp == null) return '-'
  if (evalType === 'mate') {
    return evalCp > 0 ? `M${evalCp}` : `-M${Math.abs(evalCp)}`
  }
  return (evalCp / 100).toFixed(2)
}

export function classifyMove(evalDelta, isBestMove = false, positionComplexity = 'normal') {
  if (evalDelta == null) return ''
  const abs = Math.abs(evalDelta)
  
  // 如果实际着法等于AI首选，给予最高评价
  if (isBestMove) {
    if (positionComplexity === 'complex' && abs < 30) return 'brilliant'  // !!
    return 'great'  // !
  }
  
  // 根据分数差距评价
  if (abs < 15) return 'great'        // !   几乎最佳
  if (abs < 35) return 'good'         // 正常好着
  if (abs < 60) return 'interesting'  // !?  有趣尝试
  if (abs < 100) return 'inaccuracy'  // ?!  不精确
  if (abs < 200) return 'mistake'     // ?   失误
  return 'blunder'                    // ??  严重失误
}

export function resultLabel(result) {
  const map = { '1-0': '白胜', '0-1': '黑胜', '1/2-1/2': '和棋', '*': '进行中' }
  return map[result] || result
}

export function debounce(fn, delay) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

export function throttle(fn, delay) {
  let last = 0
  return function (...args) {
    const now = Date.now()
    if (now - last >= delay) {
      last = now
      fn.apply(this, args)
    }
  }
}

export function formatDate(date) {
  if (!date) return ''
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

export function truncate(str, length) {
  if (!str) return ''
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}
