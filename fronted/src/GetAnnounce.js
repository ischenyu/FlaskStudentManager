// GetAnnounce.js
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { api } from './index.js'
import dayjs from 'dayjs'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

export function useAnnounce() {
  const announceVisible = ref(false)
  const announceData = ref(null)

  const formatDate = (dateString) => {
    return dayjs(dateString).format('YYYY-MM-DD HH:mm')
  }

  const parseMarkdown = (rawText) => {
  const unsafeHtml = marked.parse(rawText || '') // 解析Markdown
  return DOMPurify.sanitize(unsafeHtml) // 安全过滤
}

  const fetchAnnouncement = async () => {
    try {
      const res = await api.get('/deductions/announce')
      if (res.data?.code === 200 && res.data.data) {
        announceData.value = {
          text: res.data.data.text,
          time: res.data.data.time
        }
        announceVisible.value = true
      }
    } catch (error) {
      message.error('公告加载失败')
    }
  }

  onMounted(() => {
    fetchAnnouncement()
  })

  return {
    announceVisible,
    announceData,
    formatDate,
    parseMarkdown
  }
}