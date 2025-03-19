<template>
  <a-layout>
    <!-- 头部导航 -->
    <a-layout-header style="background: #fff; padding: 0 24px; display: flex; align-items: center;">
      <h2 style="margin: 0">学生扣分管理系统</h2>
      <div style="margin-left: auto; display: flex; gap: 16px">
    </div>
    <a-button @click="showModal">新增扣分</a-button>
      <a-button
          class="mobile-menu-button"
          type="primary"
          @click="showModal"
      >
        新增扣分
      </a-button>
    </a-layout-header>

    <!-- 新增公告弹窗 -->
    <a-modal
      v-model:open="announceVisible"
      title="系统公告"
      :footer="null"
      class="announce-modal"
    >
      <div v-if="announceData">
    <div
      class="markdown-body"
      v-html="parseMarkdown(announceData.text)"
    ></div>
    <div class="announce-time">
      {{ formatAnnounceDate(announceData.time) }}
    </div>
  </div>
    <a-empty v-else description="暂无公告" />
  </a-modal>

    <!-- 修改后的微信提示层 -->
    <div v-if="showWechatWarning" class="wechat-warning">
      <a-result
        status="warning"
        title="兼容性提示"
        sub-title="微信浏览器可能影响功能体验"
      >
      <template #extra>
      <div class="browser-guide">
      <p>(如css样式文件无法正常加载导致的界面错乱)</p>
        <p>如果正常，可留在微信</p>
      <p>点击右上角 <span class="icon-more">...</span> 选择「在浏览器打开」</p>
    </div>


    <div class="action-buttons">
      <a-button
        type="primary"
        @click="closeWechatWarning"
        class="continue-btn"
      >
      继续访问
      </a-button>
      <a-button
        @click="showModal_warning('请使用Safari/Chrome浏览器访问')"
        class="open-browser-btn"
      >
      仍要打开浏览器
      </a-button>
    </div>
    </template>
    </a-result>
    </div>

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
            <!-- 新增扣分原因列的特殊处理 -->
            <template v-if="column.dataIndex === 'reason'">
              <div class="reason-cell">
                <span class="reason-content">{{ record.reason }}</span>
              </div>
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
          v-model:open="modalVisible"
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
              @dropdownVisibleChange="(open) => open && handleDropdownSearch()"
              :loading="studentLoading"
              @blur="handleFormValidate"
            >
              <a-select-option
                  v-for="student in studentList"
                  :key="student.id"
                  :value="student.id"
              >
                {{ student.name }}(当前扣分：{{ student.total_deduction }})
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

  <!-- 新增状态栏 -->
    <a-layout-footer class="status-footer">
      <div v-if="systemInfo" class="status-container">
        <a-tooltip title="服务器时间">
          <div class="status-item">
            <clock-circle-outlined />
            {{ formatServerTime(systemInfo.current) }}
          </div>
        </a-tooltip>

        <a-tooltip title="CPU使用率">
          <div class="status-item">
            <dashboard-outlined />
            {{ systemInfo.cpu.toFixed(1) }}%
          </div>
        </a-tooltip>

        <a-tooltip title="内存使用率">
          <div class="status-item">
            <pie-chart-outlined />
            {{ systemInfo.memory.toFixed(1) }}%
          </div>
        </a-tooltip>

        <a-tooltip title="系统负载">
          <div class="status-item">
            <line-chart-outlined />
            {{ formatLoad(systemInfo.load) }}
          </div>
        </a-tooltip>

        <a-tooltip title="运行时间">
          <div class="status-item">
            <poweroff-outlined />
            {{ formatUptime(systemInfo.uptime) }}
          </div>
        </a-tooltip>
      </div>

      <div v-else class="status-loading">
        <a-spin size="small" />
        正在获取服务器状态...
      </div>
    </a-layout-footer>

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

import { GithubOutlined, WarningFilled } from '@ant-design/icons-vue'
import LineChart from './components/LineChart.vue'
import {
  ClockCircleOutlined,
  DashboardOutlined,
  PieChartOutlined,
  LineChartOutlined,
  PoweroffOutlined
} from '@ant-design/icons-vue'
import { useDeductionSystem } from './index.js'
import { useServerStatus } from './GetServerStatus'
import { useAnnounce } from './GetAnnounce.js'
import './assets/index.css'

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
  formRules,
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
  handleDropdownSearch
} = useDeductionSystem()

const {
  systemInfo,
  formatServerTime,
  formatLoad,
  formatUptime
} = useServerStatus()

const {
  announceVisible,
  announceData,
  parseMarkdown,
  formatDate: formatAnnounceDate
} = useAnnounce()


</script>

<style>
@import 'https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css';
</style>
