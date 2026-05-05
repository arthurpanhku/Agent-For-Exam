import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { flashcardService } from '../services/flashcardService'

export const useFlashcardStore = defineStore('flashcards', () => {
  const cards = ref([])
  const stats = ref({ total: 0, due: 0, mastered: 0, new: 0 })
  const loading = ref(false)
  const generating = ref(false)
  const currentSubjectId = ref(null)

  const dueCards = computed(() => {
    const now = new Date()
    return cards.value.filter(c => new Date(c.next_review) <= now)
  })

  async function loadCards(subjectId) {
    currentSubjectId.value = subjectId
    loading.value = true
    try {
      cards.value = await flashcardService.list(subjectId)
      await loadStats(subjectId)
    } finally {
      loading.value = false
    }
  }

  async function loadStats(subjectId) {
    stats.value = await flashcardService.stats(subjectId)
  }

  async function generate(subjectId, n = 15) {
    generating.value = true
    try {
      const newCards = await flashcardService.generate(subjectId, n)
      cards.value = [...cards.value, ...newCards]
      await loadStats(subjectId)
      return newCards
    } finally {
      generating.value = false
    }
  }

  async function reviewCard(subjectId, cardId, quality) {
    const updated = await flashcardService.review(subjectId, cardId, quality)
    const idx = cards.value.findIndex(c => c.card_id === cardId)
    if (idx !== -1) cards.value[idx] = updated
    await loadStats(subjectId)
    return updated
  }

  async function deleteAll(subjectId) {
    await flashcardService.deleteAll(subjectId)
    cards.value = []
    stats.value = { total: 0, due: 0, mastered: 0, new: 0 }
  }

  return {
    cards, stats, loading, generating, dueCards, currentSubjectId,
    loadCards, loadStats, generate, reviewCard, deleteAll,
  }
})
