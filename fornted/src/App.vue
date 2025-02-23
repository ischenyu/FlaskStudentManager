<template>
  <a-layout>
    <!-- 头部导航 -->
    <a-layout-header style="background: #fff; padding: 0 24px; display: flex; align-items: center;">
      <h2 style="margin: 0">学生扣分管理系统</h2>
      <a-button
          class="mobile-menu-button"
          type="primary"
          @click="showModal"
      >
        新增扣分
      </a-button>
    </a-layout-header>

    <a-layout-content class="content-wrapper">
      <!-- 统计卡片 -->
      <a-row :gutter="24" style="margin-bottom: 24px;">
        <a-col :span="12" :xs="24" :sm="24" :md="12" :lg="12">
          <a-card title="扣分趋势">
            <template v-if="trendDataLoading">
              <a-skeleton active />
            </template>
            <template v-else>
              <LineChart
                  v-if="trendData.length > 0"
                  :data="trendData"
              />
              <a-empty v-else description="暂无数据" />
            </template>
          </a-card>
        </a-col>
        <a-col :span="12" :xs="24" :sm="24" :md="12" :lg="12">
          <a-card title="扣分TOP榜">
            <template v-if="topStudentsLoading">
              <a-skeleton active />
            </template>
            <a-list
                v-else
                item-layout="horizontal"
                :data-source="topStudents"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :description="`总扣分：${item.points}分`">
                    <template #title>
                      {{ item.name }}
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
              <template v-if="topStudents.length === 0">
                <a-empty description="暂无数据" />
              </template>
            </a-list>
          </a-card>
        </a-col>
      </a-row>

      <!-- 操作区域 -->
      <a-card>
        <div style="display: flex; justify-content: space-between; margin-bottom: 24px;">
          <a-input-search
              v-model:value="searchText"
              placeholder="搜索学生或原因"
              style="width: 300px"
              @search="handleSearch"
          />
          <a-button type="primary" @click="showModal">新增扣分</a-button>
        </div>

        <!-- 数据表格 -->
        <a-table
            :columns="columns"
            :data-source="deductions"
            :pagination="tablePagination"
            :loading="tableLoading"
            bordered
            @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'created_at'">
              {{ formatDate(record.created_at) }}
            </template>
            <template v-if="column.dataIndex === 'action'">
              <a-popconfirm
                  title="确定要删除这条记录吗？"
                  @confirm="deleteRecord(record.id)"
              >
                <a-button type="link" danger>删除</a-button>
              </a-popconfirm>
            </template>
          </template>
        </a-table>
      </a-card>

      <!-- 新增扣分模态框 -->
      <a-modal
          v-model:visible="modalVisible"
          title="新增扣分记录"
          :confirm-loading="modalLoading"
          :ok-button-props="{ disabled: hasFormError }"
          @ok="handleSubmit"
          @cancel="resetForm"
      >
        <a-form
            ref="formRef"
            :model="formState"
            :rules="formRules"
            @values-change="handleFormValidate"
            layout="vertical"
        >
          <a-form-item label="学生" name="student_id">
            <a-select
                v-model:value="formState.student_id"
                show-search
                placeholder="请选择学生"
                :filter-option="false"
                :not-found-content="studentLoading ? undefined : '暂无数据'"
                @search="debouncedSearch"
                :loading="studentLoading"
                @blur="handleFormValidate"
            >
              <a-select-option
                  v-for="student in studentList"
                  :key="student.id"
                  :value="student.id"
              >
                {{ student.name }}（当前扣分：{{ student.total_deduction }}）
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="扣分分值" name="points">
            <a-input-number
                v-model:value="formState.points"
                @blur="handleFormValidate"
                :min="1"
                style="width: 100%"
            />
          </a-form-item>

          <a-form-item label="扣分原因" name="reason">
            <a-textarea
                v-model:value="formState.reason"
                @blur="handleFormValidate"
                placeholder="请输入扣分原因"
                :rows="4"
            />
          </a-form-item>

          <a-form-item label="操作人" name="operator">
            <a-input
                v-model:value="formState.operator"
                @blur="handleFormValidate"
                placeholder="请输入操作人姓名"
            />
          </a-form-item>

          <a-form-item label="密钥" name="password">
            <a-input type="password"
                placeholder="请输入Key"
                @blur="handleFormValidate"
                v-model:value="formState.password"
            />
          </a-form-item>
        </a-form>
      </a-modal>
    </a-layout-content>
  </a-layout>



  <a-layout-footer style="text-align: center; padding: 10px">
    <div style="color: rgba(0, 0, 0, 0.65)">
      Developed by
      <a
          href="https://github.com/ischenyu"
          target="_blank"
          rel="noopener noreferrer"
          style="color: inherit; margin-left: 8px"
      >
        Shan Chenyu <github-outlined />
      </a>
    </div>
  </a-layout-footer>



</template>

<script setup>

import { GithubOutlined } from '@ant-design/icons-vue';
import { useDebounceFn } from '@vueuse/core';
import { ref, reactive, onMounted, computed, nextTick } from 'vue';
import 'ant-design-vue/dist/reset.css';
import { message } from 'ant-design-vue';
import { Modal } from 'ant-design-vue';
import axios from 'axios';
import dayjs from 'dayjs';
import LineChart from './components/LineChart.vue';


// 密码输入状态
const globalPassword = ref(localStorage.getItem('tempKey') || '');

// API配置
const api = axios.create({
  baseURL: import.meta.env.PROD
      ? 'https://student.alistnas.top/api'
      : 'http://192.168.10.115:5000/api'
});

// 表格列配置
const columns = [
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
];

// 响应式数据
const deductions = ref([]);
const searchText = ref('');
const modalVisible = ref(false);
const modalLoading = ref(false);
const tableLoading = ref(false);
const studentLoading = ref(false);
const trendDataLoading = ref(false);
const topStudentsLoading = ref(false);

const tablePagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: ['5', '10', '20', '50'],
  showTotal: total => `共 ${total} 条记录`
});

const formState = reactive({
  student_id: undefined,
  points: 1,
  reason: '',
  operator: '',
  password: ''
});

const studentList = ref([]);
const topStudents = ref([]);
const trendData = ref([]);

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
    trigger: 'blur'  // 增加触发时机
  }],
  operator: [{
    required: true,
    message: '请输入操作人姓名',
    trigger: 'blur'
  }],
  password: [{  // 新增密码验证规则
    required: true,
    message: '请输入有效密钥',
    trigger: 'blur'
  }]
};

// 初始化加载数据
onMounted(() => {
  fetchDeductions();
  fetchStatistics();
});

// 获取扣分记录
// 获取统计信息
const fetchDeductions = async () => {
  try {
    // 初始化加载状态
    tableLoading.value = true;

    // 添加请求取消功能
    const controller = new AbortController();
    const signal = controller.signal;

    // 请求参数处理
    const params = {
      page: tablePagination.current,
      size: tablePagination.pageSize,  // 根据API文档确认参数名
      keyword: searchText.value.trim() // 统一后端搜索参数命名
    };

    // 带API Key的请求配置
    const res = await api.get('/deductions', {
      params,
      signal,
      headers: {
        'X-API-KEY': localStorage.getItem('apiKey') || ''
      }
    });

    // 深度响应式数据更新（根据实际API结构调整）
    if (res.data?.code === 200) {
      deductions.value = res.data.data?.items || []; // 假设数据在data字段下
      tablePagination.total = res.data.data?.total || 0;

      // 检查分页合理性
      if (tablePagination.current > 1 && deductions.value.length === 0) {
        tablePagination.current = 1;
        return fetchDeductions(); // 自动重新请求第一页
      }
    } else {
      throw new Error(res.data?.message || 'Invalid response structure');
    }
  } catch (error) {
    // 细化错误处理
    if (error.name !== 'CanceledError') {
      const errorMessage = error.response?.data?.message
          || error.message
          || '未知错误';

      message.error(`数据加载失败: ${errorMessage}`);
      console.error('扣分记录请求错误:', error);

      // 重置分页数据
      deductions.value = [];
      tablePagination.total = 0;
    }
  } finally {
    tableLoading.value = false;
  }
};

// 表格分页/排序变化
const handleTableChange = (pag) => {
  tablePagination.current = pag.current;
  tablePagination.pageSize = pag.pageSize;
  fetchDeductions();
};

// 删除记录
const deleteRecord = async (id) => {
  if (!formState.password) {
    message.error('请先在密码框中输入密钥');
    return;
  }
  try {
    await api.delete(`/deductions/${id}`, {
      headers: { 'X-API-KEY': formState.password }
    });
    message.success('删除成功');
    fetchDeductions();
    fetchStatistics();
  } catch (error) {
    message.error('删除失败');
  }
};

// 在setup中
const debouncedSearch = useDebounceFn(async (name) => {
  try {
    studentLoading.value = true;
    const res = await api.get('/students', {
      params: {
        search: name.trim(),
        page: 1,
        size: 10
      }
    });
    studentList.value = res.data?.data?.items || [];
  } catch (error) {
    message.error(`学生搜索失败：${error.response?.data?.message || error.message}`);
  } finally {
    studentLoading.value = false;
  }
}, 300);


// 搜索学生
const handleStudentSearch = useDebounceFn(async (name) => {
  try {
    studentLoading.value = true;

    const res = await api.get('/students', {
      params: {
        search: name.trim(),  // 保持与文档一致的参数名
        page: 1,            // 明确分页参数
        size: 10            // 控制返回结果数量
      }
    });

    // 修正数据路径为 res.data.data.items ✅
    studentList.value = res.data?.data?.items || [];

    // 调试输出（开发环境使用）
    if (import.meta.env.DEV) {
      console.log('搜索学生结果:', {
        params: { search: name },
        response: res.data,
        list: studentList.value
      });
    }
  } catch (error) {
    message.error(`学生搜索失败：${error.response?.data?.message || error.message}`);
    console.error('学生搜索请求错误:', error);
  } finally {
    studentLoading.value = false;
  }
}, 300); // 300毫秒防抖

// 在setup()中
const formRef = ref(null);
const formValid = ref(false);

// 计算表单错误状态
const hasFormError = computed(() => {
  // 检查是否存在未通过验证的字段
  return !formValid.value
});

// 修改表单验证处理逻辑，移除可能导致循环的验证逻辑
const handleFormValidate = () => {
  if (!formRef.value) return;

  formRef.value
      .validateFields()
      .then(() => {
        formValid.value = true;
        console.log('表单验证通过'); // 调试用
      })
      .catch((errors) => {
        formValid.value = false;
        console.log('验证错误:', errors); // 调试用
      });
};

// 提交表单
const handleSubmit = async () => {
  try {
    modalLoading.value = true;
    // 正确等待并获取响应结果
    const response = await api.post('/deductions', formState, {
      headers: { 'X-API-KEY': formState.password }
    });

    // 直接从响应数据中解构需要的信息
    const { code, message: responseMessage } = response.data;

    // 根据状态码进行逻辑处理
    if (code === 200) {
      message.success('扣分记录添加成功');
      modalVisible.value = false;
      resetForm();
      await fetchDeductions();
      await fetchStatistics();
    } else if (code === 403) {
      showModal_warning(responseMessage);  // 显示具体的权限错误提示
    }
  } catch (error) {
    // 处理网络异常或服务端返回的HTTP错误状态码
    const errorCode = error.response?.data?.code;
    const errorMessage = error.response?.data?.message || '提交失败';

    // 特别处理403状态码（HTTP层面的权限错误）
    if (errorCode === 403 || error.response?.status === 403) {
      showModal_warning(errorMessage);
    } else {
      message.error(errorMessage);
    }
    console.error('提交出错:', error);
  } finally {
    modalLoading.value = false;
  }
};

// 重置表单
const resetForm = () => {
  formState.student_id = undefined;
  formState.points = 1;
  formState.reason = '';
  formState.operator = '';
};

// 日期格式化
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 显示模态框
// 在显示模态框时重置验证状态
const showModal = () => {
  modalVisible.value = true;
  // 等待DOM更新后重置验证状态
  nextTick(() => {
    formValid.value = false;
    formRef.value?.clearValidate();
    // 调试输出
    if (import.meta.env.DEV) {
      console.log('表单初始验证状态:', formValid.value);
    }
  });
};


// 处理搜索
const handleSearch = () => {
  tablePagination.current = 1;
  fetchDeductions();
};

// 获取统计信息
const fetchStatistics = async () => {
  try {
    trendDataLoading.value = true;
    topStudentsLoading.value = true;

    const res = await api.get('/deductions/statistics', {
      headers: {
        'X-API-KEY': localStorage.getItem('apiKey') || ''
      }
    });

    if (res.data?.code === 200) {
      trendData.value = res.data.data?.trend || [];
      // 修改为 + 字段转换
      topStudents.value = (res.data.data?.top_students || []).map(item => ({
        name: item.name,
        points: Number(item.total_points) || 0 // 转换字段名并确保数值类型
      }));
    } else {
      throw new Error(res.data?.message || 'Invalid response structure');
    }
  } catch (error) {
    message.error(`统计信息加载失败: ${error.response?.data?.message || error.message}`);
    console.error('统计信息请求错误:', error);
  } finally {
    trendDataLoading.value = false;
    topStudentsLoading.value = false;
  }
};


const open = ref(false);
const showModal_warning = (message) => {
  Modal.warning({
    title: '提交失败',
    content: message,
  });
};


</script>

<style scoped>
.content-wrapper {
  padding: 24px;
  margin: 0 auto;
  max-width: 1200px;

  @media (max-width: 768px) {
    padding: 12px;
    max-width: 100%;
  }
}

/* 卡片容器响应式 */
.ant-row {
  @media (max-width: 576px) {
    margin-left: -8px !important;
    margin-right: -8px !important;

    .ant-col {
      padding-left: 8px !important;
      padding-right: 8px !important;
    }
  }
}

/* 表格响应式 */
.ant-table-wrapper {
  overflow-x: auto;

  .ant-table {
    min-width: 800px;

    @media (max-width: 768px) {
      font-size: 14px;
    }
  }
}

/* 搜索框区域响应式 */
.ant-card .ant-input-search {
  @media (max-width: 576px) {
    width: 100% !important;
    margin-bottom: 12px;
  }
}


</style>

<style scoped>
.mobile-menu-button {
  display: none;
  margin-left: auto;

  @media (max-width: 576px) {
    display: block;
  }
}

/* 隐藏PC端按钮 */
.ant-card .ant-btn-primary {
  @media (max-width: 576px) {
    display: none;
  }
}

.ant-modal {
  @media (max-width: 576px) {
    width: 95% !important;
    max-width: none;
    margin: 8px;

    .ant-modal-content {
      padding: 16px;
    }
  }
}

/* 固定底部定位 */
.ant-layout-footer {
  position: sticky;
  bottom: 0;
  z-index: 1;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}

/* 响应式处理 */
@media (max-width: 768px) {
  .ant-layout-footer {
    font-size: 14px;
    padding: 16px;
  }
}

</style>
