// electron/main.cjs

const API_BASE = process.env.API_BASE || 'http://192.168.10.115:5000'

const { app, BrowserWindow, session } = require('electron');
const path = require('path');


// 全局异常捕获
process.on('uncaughtException', (err) => {
  console.error('【主进程异常】', err);
});

function createWindow() {
  // 创建浏览器窗口配置
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      webSecurity: false,          // 禁用同源策略
      nodeIntegration: true,       // 允许Node集成
      contextIsolation: false,     // 与Vue兼容
      allowRunningInsecureContent: true // 允许HTTP内容
    }
  });

  // 开发模式配置
  if (process.env.NODE_ENV === 'development') {
    console.log('🚀 开发模式启动');
    win.loadURL('http://localhost:3000').catch(err => {
      console.error('⚠️ 加载开发服务器失败:', err);
    });
    win.webContents.openDevTools(); // 自动打开开发者工具
  } else {
    console.log('📦 生产模式启动');
    win.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // 窗口加载完成事件
  win.webContents.on('did-finish-load', () => {
    console.log('✅ 窗口内容加载完成');
  });

  // 窗口关闭事件
  win.on('closed', () => {
    console.log('⏹️ 窗口已关闭');
  });
}

// 设置全局CORS策略
app.whenReady().then(() => {
  console.log('🔧 配置CORS策略');

  // 新增请求拦截逻辑
  session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
  const parsed = new URL(details.url);

  // 调试输出原始请求信息
  console.log('原始请求:', {
    protocol: parsed.protocol,
    pathname: parsed.pathname,
    fullUrl: details.url
  });

  // 匹配所有包含/api的file协议请求
  if (parsed.protocol === 'file:' && parsed.pathname.includes('/api')) {
    // 提取API路径（兼容Windows和Unix路径）
    const apiPath = parsed.pathname.split('/api').pop() || '';
    const newUrl = new URL(`${API_BASE}/api${apiPath}`);

    // 保留原始查询参数
    newUrl.search = parsed.search;

    console.log('重定向至:', newUrl.toString());
    return callback({ redirectURL: newUrl.toString() });
  }

  callback({ cancel: false });
});

  createWindow();
});

// macOS窗口管理
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

// 网络超时处理
app.on('web-contents-created', (event, contents) => {
  contents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`❌ 加载失败 (${errorCode}): ${errorDescription}`);
  });
});


