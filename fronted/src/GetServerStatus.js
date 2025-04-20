import axios from 'axios'
import { ref, onMounted, onUnmounted } from 'vue'
import dayjs from "dayjs"

// API配置
export const api = axios.create({
  baseURL: import.meta.env.PROD
      ? '/api'
      : 'http://192.168.10.115:5000/api'
})

// 改为导出函数形式
export function useServerStatus() {
  const systemInfo = ref(null)
  let updateTimer = null

  const fetchSystemInfo = async () => {
    try {
      const res = await api.get('system/status')  //('https://api.alistnas.top/system_info')
      systemInfo.value = res.data
    } catch (error) {
      console.error('获取服务器状态失败:', error)
    }
  }

  const formatServerTime = (timeStr) => {
    return dayjs(timeStr).format('YYYY-MM-DD HH:mm:ss')
  }

  const formatLoad = (load) => {
    return load.map(n => n.toFixed(2)).join(' / ')
  }

  const formatUptime = (uptimeStr) => {
    const cleaned = uptimeStr.split('.')[0]
    return cleaned
      .replace('days', '天')
      .replace('day', '天')
      .replace(/(\d+):(\d+):(\d+)/, (_, h, m, s) => `${h}小时${m}分`)
  }

  onMounted(() => {
    fetchSystemInfo()
    updateTimer = setInterval(fetchSystemInfo, 3000)
  })

  onUnmounted(() => {
    clearInterval(updateTimer)
  })

  // 返回需要暴露的内容
  return {
    systemInfo,
    formatServerTime,
    formatLoad,
    formatUptime
  }
}