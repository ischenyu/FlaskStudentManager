// LineChart.vue 修改建议
<script setup>
import {ref, onMounted, watch, nextTick, onBeforeUnmount} from 'vue';
import * as echarts from 'echarts';

const props = defineProps(['data']);
const chart = ref(null);
let myChart = null;

// 添加调试输出
console.log('初始数据:', props.data);

// 优化数据监听
watch(() => [...props.data], async () => {
  console.log('数据变化:', props.data);
  await nextTick();
  updateChart();
});

onMounted(() => {
  console.log('图表挂载完成');
  initChart();
});

// 销毁图表实例
const destroyChart = () => {
  if (myChart) {
    myChart.dispose();
    myChart = null;
  }
};

const initChart = () => {
  destroyChart();

  if (!chart.value) return;

  window.addEventListener('resize', handleChartResize);

  myChart = echarts.init(chart.value);
  updateChart();
};

const updateChart = () => {
  console.log('更新图表数据:', props.data);

  if (!myChart || !props.data?.length) {
    console.warn('图表未初始化或数据为空');
    return;
  }

  // 验证数据格式
  const isValidData = props.data.every(item =>
      'date' in item && 'count' in item && 'points' in item
  );

  if (!isValidData) {
    console.error('无效数据格式，需要包含date/count/points字段');
    return;
  }

  const option = {
    xAxis: {
      type: 'category',
      data: props.data.map(d => d.date)
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '扣分次数',
        type: 'line',
        data: props.data.map(d => d.count)
      },
      {
        name: '扣分总分',
        type: 'line',
        data: props.data.map(d => Number(d.points)) // 确保数值类型
      }
    ],
    tooltip: { trigger: 'axis' }
  };

  myChart.setOption(option);
  myChart.resize(); // 添加自适应
};

const handleChartResize = () => {
  if (myChart) {
    myChart.resize();
  }
}

// 组件卸载时移除监听
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize);
  destroyChart();
});

</script>

<template>
  <div ref="chart" class="chart-container"></div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 400px;

  @media (max-width: 768px) {
    height: 300px;
  }

  @media (max-width: 480px) {
    height: 250px;
  }
}
</style>