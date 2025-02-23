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

import { GithubOutlined } from '@ant-design/icons-vue'
import LineChart from './components/LineChart.vue'
import { useDeductionSystem } from './index.js'

const {
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
  showModal_warning
} = useDeductionSystem()

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
