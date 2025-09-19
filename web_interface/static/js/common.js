/**
 * SDG Web界面通用JavaScript函数
 */

// 显示警告消息
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container');
    
    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" id="${alertId}" role="alert">
            <i class="fas fa-${getAlertIcon(type)}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // 自动隐藏
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

// 获取警告图标
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化数字
function formatNumber(num, decimals = 2) {
    if (isNaN(num)) return '-';
    return parseFloat(num).toFixed(decimals);
}

// 格式化百分比
function formatPercentage(num, decimals = 1) {
    if (isNaN(num)) return '-';
    return parseFloat(num).toFixed(decimals) + '%';
}

// 验证文件类型
function validateFileType(file, allowedTypes = ['csv', 'xlsx', 'xls']) {
    const extension = file.name.split('.').pop().toLowerCase();
    return allowedTypes.includes(extension);
}

// 验证文件大小
function validateFileSize(file, maxSizeMB = 50) {
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    return file.size <= maxSizeBytes;
}

// 显示加载状态
function showLoading(element, text = '加载中...') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="text-center">
                <i class="fas fa-spinner fa-spin fa-2x text-primary mb-3"></i>
                <p class="text-muted">${text}</p>
            </div>
        `;
    }
}

// 隐藏加载状态
function hideLoading(element, content = '') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = content;
    }
}

// 显示空状态
function showEmptyState(element, message = '暂无数据', icon = 'inbox') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-${icon}"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

// 显示错误状态
function showErrorState(element, message = '加载失败', icon = 'exclamation-triangle') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="error-state">
                <i class="fas fa-${icon}"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

// 显示成功状态
function showSuccessState(element, message = '操作成功', icon = 'check-circle') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="success-state">
                <i class="fas fa-${icon}"></i>
                <p>${message}</p>
            </div>
        `;
    }
}

// 创建数据表格
function createDataTable(container, data, columns = null) {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    
    if (!container || !data || data.length === 0) {
        showEmptyState(container, '暂无数据');
        return;
    }
    
    // 如果没有指定列，使用第一行数据的键
    if (!columns) {
        columns = Object.keys(data[0]);
    }
    
    let tableHTML = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        ${columns.map(col => `<th>${col}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.map(row => `
                        <tr>
                            ${columns.map(col => `<td>${row[col] || '-'}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHTML;
}

// 创建统计卡片
function createStatCard(container, title, value, icon = 'chart-bar', color = 'primary') {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    
    if (container) {
        container.innerHTML = `
            <div class="stat-card bg-${color}">
                <i class="fas fa-${icon} fa-2x mb-3"></i>
                <h3>${value}</h3>
                <p>${title}</p>
            </div>
        `;
    }
}

// 创建进度条
function createProgressBar(container, value, max = 100, label = '') {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    
    if (container) {
        const percentage = (value / max) * 100;
        const colorClass = percentage >= 80 ? 'success' : percentage >= 60 ? 'warning' : 'danger';
        
        container.innerHTML = `
            <div class="progress mb-2">
                <div class="progress-bar bg-${colorClass}" role="progressbar" 
                     style="width: ${percentage}%"></div>
            </div>
            <div class="d-flex justify-content-between">
                <span>${label}</span>
                <span>${formatNumber(value)}/${formatNumber(max)}</span>
            </div>
        `;
    }
}

// 复制到剪贴板
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showAlert('已复制到剪贴板', 'success');
        }).catch(() => {
            showAlert('复制失败', 'danger');
        });
    } else {
        // 兼容旧浏览器
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showAlert('已复制到剪贴板', 'success');
        } catch (err) {
            showAlert('复制失败', 'danger');
        }
        document.body.removeChild(textArea);
    }
}

// 下载文件
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 格式化日期
function formatDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
    if (!date) return '-';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return '-';
    
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

// 生成随机ID
function generateId(prefix = 'id') {
    return prefix + '_' + Math.random().toString(36).substr(2, 9);
}

// 检查是否为移动设备
function isMobile() {
    return window.innerWidth <= 768;
}

// 平滑滚动到元素
function scrollToElement(element, offset = 0) {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
}

// 获取URL参数
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 设置URL参数
function setUrlParameter(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.replaceState({}, '', url);
}

// 移除URL参数
function removeUrlParameter(name) {
    const url = new URL(window.location);
    url.searchParams.delete(name);
    window.history.replaceState({}, '', url);
}

// 验证邮箱
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 验证URL
function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// 本地存储操作
const storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('存储失败:', e);
            return false;
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('读取失败:', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('删除失败:', e);
            return false;
        }
    },
    
    clear: function() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.error('清空失败:', e);
            return false;
        }
    }
};

// 会话存储操作
const sessionStorage = {
    set: function(key, value) {
        try {
            window.sessionStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('会话存储失败:', e);
            return false;
        }
    },
    
    get: function(key, defaultValue = null) {
        try {
            const item = window.sessionStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('会话读取失败:', e);
            return defaultValue;
        }
    },
    
    remove: function(key) {
        try {
            window.sessionStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('会话删除失败:', e);
            return false;
        }
    }
};

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化弹出框
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 添加页面加载动画
    document.body.classList.add('loaded');
});

// 页面卸载时清理
window.addEventListener('beforeunload', function() {
    // 清理定时器等资源
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const bsAlert = bootstrap.Alert.getInstance(alert);
        if (bsAlert) {
            bsAlert.close();
        }
    });
});
