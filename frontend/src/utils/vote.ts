import type { VoteStat } from '@/types/share'

export function getVoteCount(voteStats: VoteStat[], index: number): number {
  const stat = voteStats.find((s) => s.plan_index === index)
  return stat?.count || 0
}

export function getTotalVotes(voteStats: VoteStat[]): number {
  return voteStats.reduce((sum, s) => sum + s.count, 0)
}

export function getVotePercentage(voteStats: VoteStat[], index: number): number {
  const total = getTotalVotes(voteStats)
  if (total === 0) return 0
  return Math.round((getVoteCount(voteStats, index) / total) * 100)
}

export function getWinnerIndex(voteStats: VoteStat[]): number {
  let maxVotes = 0
  let winner = 0
  voteStats.forEach((s) => {
    if (s.count > maxVotes) {
      maxVotes = s.count
      winner = s.plan_index
    }
  })
  return winner
}
