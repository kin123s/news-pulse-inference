<template>
  <div class="app-container">
    <header class="header">
      <h1>📰 실시간 뉴스 분석 시스템</h1>
      <div class="status-bar">
        <span :class="['status-indicator', connectionStatus]">
          {{ connectionStatus === 'connected' ? '🟢 연결됨' : '🔴 연결 끊김' }}
        </span>
        <span class="stats">총 뉴스: {{ totalNews }}</span>
      </div>
    </header>

    <main class="main-content">
      <!-- Filter Section -->
      <div class="filter-section">
        <button 
          :class="['filter-btn', { active: currentView === 'realtime' }]"
          @click="currentView = 'realtime'"
        >
          ⚡ 실시간 피드
        </button>
        <button 
          :class="['filter-btn', { active: currentView === 'recent' }]"
          @click="loadRecentNews"
        >
          📋 최근 뉴스
        </button>
        <button 
          :class="['filter-btn', { active: currentView === 'top' }]"
          @click="loadTopNews"
        >
          ⭐ 중요 뉴스
        </button>
      </div>

      <!-- News Feed -->
      <div class="news-feed">
        <div 
          v-for="news in displayedNews" 
          :key="news.id"
          class="news-card"
          :data-sentiment="news.analysis.sentiment"
        >
          <div class="news-header">
            <span class="news-source">{{ news.source }}</span>
            <span :class="['sentiment-badge', news.analysis.sentiment]">
              {{ getSentimentEmoji(news.analysis.sentiment) }}
              {{ news.analysis.sentiment }}
            </span>
          </div>
          
          <h3 class="news-title">{{ news.title }}</h3>
          <p class="news-description">{{ news.description }}</p>
          
          <div class="news-meta">
            <div class="keywords">
              <span 
                v-for="keyword in news.analysis.keywords" 
                :key="keyword"
                class="keyword-tag"
              >
                #{{ keyword }}
              </span>
            </div>
            <div class="news-score">
              중요도: {{ news.analysis.importance_score.toFixed(1) }}/10
            </div>
          </div>
          
          <div class="news-footer">
            <span class="news-time">{{ formatTime(news.publishedAt) }}</span>
            <a :href="news.url" target="_blank" class="read-more">
              전체 기사 보기 →
            </a>
          </div>
        </div>

        <div v-if="displayedNews.length === 0" class="empty-state">
          <p>{{ currentView === 'realtime' ? '실시간 뉴스를 기다리는 중...' : '뉴스가 없습니다.' }}</p>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    const ws = ref(null)
    const connectionStatus = ref('disconnected')
    const currentView = ref('realtime')
    const realtimeNews = ref([])
    const recentNews = ref([])
    const topNews = ref([])
    const totalNews = ref(0)

    const displayedNews = computed(() => {
      switch (currentView.value) {
        case 'realtime':
          return realtimeNews.value
        case 'recent':
          return recentNews.value
        case 'top':
          return topNews.value
        default:
          return []
      }
    })

    const connectWebSocket = () => {
      const wsUrl = 'ws://localhost:8002/ws'
      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log('WebSocket connected')
        connectionStatus.value = 'connected'
      }

      ws.value.onmessage = (event) => {
        const message = JSON.parse(event.data)
        
        if (message.type === 'initial_data') {
          realtimeNews.value = message.data
          totalNews.value = message.data.length
        } else if (message.type === 'new_analysis') {
          realtimeNews.value.unshift(message.data)
          if (realtimeNews.value.length > 50) {
            realtimeNews.value.pop()
          }
          totalNews.value = realtimeNews.value.length
        }
      }

      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        connectionStatus.value = 'disconnected'
      }

      ws.value.onclose = () => {
        console.log('WebSocket disconnected')
        connectionStatus.value = 'disconnected'
        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000)
      }
    }

    const loadRecentNews = async () => {
      currentView.value = 'recent'
      try {
        const response = await axios.get('/api/news/recent?limit=20')
        recentNews.value = response.data.news
      } catch (error) {
        console.error('Error loading recent news:', error)
      }
    }

    const loadTopNews = async () => {
      currentView.value = 'top'
      try {
        const response = await axios.get('/api/news/top?limit=10')
        topNews.value = response.data.news
      } catch (error) {
        console.error('Error loading top news:', error)
      }
    }

    const getSentimentEmoji = (sentiment) => {
      const emojis = {
        positive: '😊',
        neutral: '😐',
        negative: '😞'
      }
      return emojis[sentiment] || '❓'
    }

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const now = new Date()
      const diff = Math.floor((now - date) / 1000)

      if (diff < 60) return `${diff}초 전`
      if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
      if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
      return date.toLocaleDateString('ko-KR')
    }

    onMounted(() => {
      connectWebSocket()
    })

    onUnmounted(() => {
      if (ws.value) {
        ws.value.close()
      }
    })

    return {
      connectionStatus,
      currentView,
      displayedNews,
      totalNews,
      loadRecentNews,
      loadTopNews,
      getSentimentEmoji,
      formatTime
    }
  }
}
</script>

<style scoped>
.app-container {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.header h1 {
  font-size: 28px;
  color: #2d3748;
  margin-bottom: 12px;
}

.status-bar {
  display: flex;
  gap: 20px;
  align-items: center;
  font-size: 14px;
}

.status-indicator {
  padding: 6px 12px;
  border-radius: 20px;
  font-weight: 500;
}

.status-indicator.connected {
  background: #c6f6d5;
  color: #22543d;
}

.status-indicator.disconnected {
  background: #fed7d7;
  color: #742a2a;
}

.stats {
  color: #718096;
  font-weight: 500;
}

.filter-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.filter-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: white;
  color: #4a5568;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.filter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.filter-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.news-feed {
  display: grid;
  gap: 20px;
}

.news-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  border-left: 4px solid #cbd5e0;
}

.news-card[data-sentiment="positive"] {
  border-left-color: #48bb78;
}

.news-card[data-sentiment="negative"] {
  border-left-color: #f56565;
}

.news-card[data-sentiment="neutral"] {
  border-left-color: #a0aec0;
}

.news-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.news-source {
  font-size: 12px;
  font-weight: 600;
  color: #667eea;
  text-transform: uppercase;
}

.sentiment-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.sentiment-badge.positive {
  background: #c6f6d5;
  color: #22543d;
}

.sentiment-badge.negative {
  background: #fed7d7;
  color: #742a2a;
}

.sentiment-badge.neutral {
  background: #e2e8f0;
  color: #2d3748;
}

.news-title {
  font-size: 20px;
  color: #2d3748;
  margin-bottom: 12px;
  line-height: 1.4;
}

.news-description {
  color: #4a5568;
  line-height: 1.6;
  margin-bottom: 16px;
}

.news-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.keywords {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.keyword-tag {
  padding: 4px 10px;
  background: #edf2f7;
  color: #4a5568;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.news-score {
  font-size: 13px;
  font-weight: 600;
  color: #ed8936;
}

.news-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.news-time {
  color: #a0aec0;
}

.read-more {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s;
}

.read-more:hover {
  color: #764ba2;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: white;
  font-size: 18px;
  opacity: 0.8;
}
</style>
