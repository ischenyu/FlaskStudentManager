
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import axios from 'axios'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'
import { Modal } from 'ant-design-vue'

// API配置
export const api = axios.create({
    baseURL: import.meta.env.PROD
        ? '/api'
        : 'http://192.168.10.115:5000/api'
})

// 表格列配置
export const columns = [
    { title: '学生姓名', dataIndex: 'student_name' },
    { title: '扣分分值', dataIndex: 'points' },
    { title: '扣分原因', dataIndex: 'reason' },
    {
        title: '操作时间',
        dataIndex: 'created_at',
        sorter: true
    },
    { title: '操作人', dataIndex: 'operator' },
    {
        title: '操作',
        dataIndex: 'action',
        width: 100
    }
]

export function useDeductionSystem() {
    // 响应式数据
    const deductions = ref([])
    const searchText = ref('')
    const modalVisible = ref(false)
    const modalLoading = ref(false)
    const tableLoading = ref(false)
    const studentLoading = ref(false)
    const trendDataLoading = ref(false)
    const topStudentsLoading = ref(false)

    const tablePagination = reactive({
        current: 1,
        pageSize: 20,
        total: 0,
        showSizeChanger: true,
        showQuickJumper: true,
        pageSizeOptions: ['5', '10', '20', '50'],
        showTotal: total => `共 ${total} 条记录`
    })

    const formState = reactive({
        student_id: undefined,
        points: 1,
        reason: '',
        operator: '',
        password: ''
    })

    const studentList = ref([])
    const topStudents = ref([])
    const trendData = ref([])
    const formRef = ref(null)
    const formValid = ref(false)
    const globalPassword = ref(localStorage.getItem('tempKey') || '')

    // 表单验证规则
    const formRules = {
        student_id: [{
            required: true,
            message: '请选择学生',
            trigger: 'change'
        }],
        points: [
            { required: true, message: '请输入扣分分值' },
            { type: 'number', min: 1, message: '分值必须大于0' }
        ],
        reason: [{
            required: true,
            message: '请输入扣分原因',
            trigger: 'blur'
        }],
        operator: [{
            required: true,
            message: '请输入操作人姓名',
            trigger: 'blur'
        }],
        password: [{
            required: true,
            message: '请输入有效密钥',
            trigger: 'blur'
        }]
    }

    // 计算属性
    const hasFormError = computed(() => !formValid.value)

    // 生命周期钩子
    onMounted(() => {
        fetchDeductions()
        fetchStatistics()
    })

    // 方法定义
    const fetchDeductions = async () => {
        try {
            tableLoading.value = true
            const params = {
                page: tablePagination.current,
                size: tablePagination.pageSize,
                keyword: searchText.value.trim()
            }
    
            const res = await api.get('/deductions', {
                params,
                headers: {
                    'X-API-KEY': localStorage.getItem('apiKey') || ''
                }
            })
    
            if (res.data?.code === 200) {
                deductions.value = res.data.data?.items || []
                tablePagination.total = res.data.data?.pagination?.total || 0
    
                // 校正当前页码
                const totalPages = Math.ceil(tablePagination.total / tablePagination.pageSize)
                if (tablePagination.current > totalPages) {
                    tablePagination.current = totalPages || 1
                    return fetchDeductions()
                }
    
                if (deductions.value.length === 0 && tablePagination.current > 1) {
                    tablePagination.current = 1
                    return fetchDeductions()
                }
            }
        } catch (error) {
            message.error(`数据加载失败: ${error.response?.data?.message || error.message}`)
        } finally {
            tableLoading.value = false
        }
    }

    const handleTableChange = (pag) => {
        tablePagination.current = pag.current
        tablePagination.pageSize = pag.pageSize
        fetchDeductions()
    }

    const deleteRecord = async (id) => {
        try {
            await api.delete(`/deductions/${id}`, {
                headers: { 'X-API-KEY': formState.password }
            })
            message.success('删除成功')
            fetchDeductions()
            fetchStatistics()
        } catch (error) {
            message.error('删除失败')
        }
    }

    const debouncedSearch = useDebounceFn(async (name) => {
        try {
            studentLoading.value = true
            const res = await api.get('/students', {
                params: {
                    search: name.trim(),
                    page: 1,
                    size: 10
                }
            })
            studentList.value = res.data?.data?.items || []
        } catch (error) {
            message.error(`学生搜索失败：${error.response?.data?.message || error.message}`)
        } finally {
            studentLoading.value = false
        }
    }, 300)

    // 无防抖搜索
    const handleDropdownSearch = async () => {
        try {
            studentLoading.value = true;
            const res = await api.get('/students', {
                params: {
                search: '', // 空搜索参数
                page: 1,
                size: 10
                }
            });
            studentList.value = res.data?.data?.items || [];
        } catch (error) {
        message.error(`学生加载失败：${error.response?.data?.message || error.message}`);
        } finally {
            studentLoading.value = false;
        }
    };



    const handleFormValidate = () => {
        formRef.value?.validateFields()
            .then(() => formValid.value = true)
            .catch(() => formValid.value = false)
    }

    const handleSubmit = async () => {
        try {
            modalLoading.value = true
            const response = await api.post('/deductions', formState, {
                headers: { 'X-API-KEY': formState.password }
            })

            if (response.data?.code === 200) {
                message.success('扣分记录添加成功')
                modalVisible.value = false
                resetForm()
                await fetchDeductions()
                await fetchStatistics()
            }
        } catch (error) {
            message.error(error.response?.data?.message || '提交失败')
        } finally {
            modalLoading.value = false
        }
    }

    const resetForm = () => {
        formState.student_id = undefined
        formState.points = 1
        formState.reason = ''
        formState.operator = ''
    }

    const formatDate = (dateString) => {
        return dayjs(dateString).format('YYYY-MM-DD HH:mm')
    }

    const showModal = () => {
        modalVisible.value = true
        nextTick(() => {
            formValid.value = false
            formRef.value?.clearValidate()
        })
    }

    const handleSearch = () => {
        tablePagination.current = 1
        fetchDeductions()
    }

    const fetchStatistics = async () => {
        try {
            trendDataLoading.value = true
            topStudentsLoading.value = true

            const res = await api.get('/deductions/statistics', {
                headers: {
                    'X-API-KEY': localStorage.getItem('apiKey') || ''
                }
            })

            if (res.data?.code === 200) {
                trendData.value = res.data.data?.trend || []
                topStudents.value = (res.data.data?.top_students || []).map(item => ({
                    name: item.name,
                    points: Number(item.total_points) || 0
                }))
            }
        } catch (error) {
            message.error(`统计信息加载失败: ${error.response?.data?.message || error.message}`)
        } finally {
            trendDataLoading.value = false
            topStudentsLoading.value = false
        }
    }

    const showModal_warning = (message) => {
        Modal.warning({
            title: '提交失败',
            content: message,
        })
    }

    const isWeChat = computed(() => {
      return /micromessenger/i.test(navigator.userAgent)
    })

    // 控制提示显示
    const showWechatWarning = ref(
        isWeChat.value && !localStorage.getItem('dismissWechatWarning')
    )

    // 关闭提示方法
    const closeWechatWarning = () => {
      showWechatWarning.value = false
      localStorage.setItem('dismissWechatWarning', 'true')
    }

    const exportLoading = ref(false)
  
    // 导出处理方法
    const handleExport = async () => {
        try {
          exportLoading.value = true
          const response = await api.get('/deductions/export', {
            responseType: 'blob',
            headers: { 'X-API-KEY': formState.password }
          })
      
          // 安全获取文件名
          const disposition = response.headers['content-disposition'] || ''
          let filename = 'deduction_report.xlsx' // 默认文件名
          
          const filenameMatch = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (filenameMatch && filenameMatch[1]) { 
            filename = decodeURIComponent(filenameMatch[1].replace(/['"]/g, ''))
          }
      
          // 创建下载链接
          const url = window.URL.createObjectURL(new Blob([response.data]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', filename)
          document.body.appendChild(link)
          link.click()
          
          // 清理DOM
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
      
          message.success('报表下载已开始')
        } catch (error) {
          console.error('导出失败详情:', error)
          let errorMsg = error.response?.data?.message || error.message
          if (error.response?.status === 403) {
            errorMsg = '导出权限不足，请联系管理员'
          }
          message.error(`导出失败: ${errorMsg}`)
        } finally {
          exportLoading.value = false
        }
      }
      

    return {
        // 响应式数据
        columns,
        deductions,
        searchText,
        modalVisible,
        modalLoading,
        tableLoading,
        studentLoading,
        trendDataLoading,
        topStudentsLoading,
        tablePagination,
        formState,
        studentList,
        topStudents,
        trendData,
        formRef,
        formRules,
        isWeChat,
        showWechatWarning,
        closeWechatWarning,

        // 计算属性
        hasFormError,

        // 方法
        showModal,
        handleSearch,
        handleTableChange,
        deleteRecord,
        formatDate,
        resetForm,
        handleSubmit,
        debouncedSearch,
        handleFormValidate,
        fetchStatistics,
        showModal_warning,
        handleDropdownSearch,
        exportLoading,
        handleExport,
    }
}
