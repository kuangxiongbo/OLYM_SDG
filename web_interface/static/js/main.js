// SDG多账号控制系统 - 主JavaScript文件

// 全局变量
let currentUser = null;
let apiBaseUrl = '/api';

// 页面加载完成后初始化
$(document).ready(function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    checkAuthStatus();
    setupEventListeners();
    setupTooltips();
}

// 检查认证状态
async function checkAuthStatus() {
    try {
        const response = await fetch('/auth/check-auth');
        
        // 检查响应状态
        if (!response.ok) {
            console.warn('认证状态检查失败，状态码:', response.status);
            updateUIForGuestUser();
            return;
        }
        
        // 检查响应内容类型
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            console.warn('认证状态API返回非JSON响应:', contentType);
            updateUIForGuestUser();
            return;
        }
        
        const result = await response.json();
        
        if (result.success && result.authenticated) {
            currentUser = result.user;
            updateUIForAuthenticatedUser();
        } else {
            updateUIForGuestUser();
        }
    } catch (error) {
        console.error('检查认证状态失败:', error);
        updateUIForGuestUser();
    }
}

// 更新已认证用户的UI
function updateUIForAuthenticatedUser() {
    // 显示用户菜单，隐藏登录/注册按钮
    $('.authenticated-menu').show();
    $('.guest-menu').hide();
    
    // 更新用户名显示
    if (currentUser) {
        $('.user-name').text(currentUser.username);
        $('.user-email').text(currentUser.email);
    }
}

// 更新访客用户的UI
function updateUIForGuestUser() {
    // 隐藏用户菜单，显示登录/注册按钮
    $('.authenticated-menu').hide();
    $('.guest-menu').show();
}

// 设置事件监听器
function setupEventListeners() {
    // 退出登录
    $(document).on('click', '.logout-btn', logout);
    
    // 表单提交
    $(document).on('submit', '.ajax-form', handleFormSubmit);
    
    // 确认删除
    $(document).on('click', '.delete-btn', confirmDelete);
    
    // 刷新数据
    $(document).on('click', '.refresh-btn', refreshData);
}

// 设置工具提示
function setupTooltips() {
    $('[data-bs-toggle="tooltip"]').tooltip();
}

// 退出登录
async function logout() {
    if (!confirm('确定要退出登录吗？')) {
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('退出登录成功', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showMessage('退出登录失败', 'error');
        }
    } catch (error) {
        console.error('退出登录失败:', error);
        showMessage('退出登录失败', 'error');
    } finally {
        hideLoading();
    }
}

// 处理表单提交
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = $(this);
    const formData = new FormData(form[0]);
    const url = form.attr('action');
    const method = form.attr('method') || 'POST';
    
    try {
        showLoading();
        
        const response = await fetch(url, {
            method: method,
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message || '操作成功', 'success');
            
            // 如果有回调函数，执行它
            if (form.data('callback')) {
                window[form.data('callback')](result);
            }
            
            // 如果是模态框表单，关闭模态框
            const modal = form.closest('.modal');
            if (modal.length) {
                modal.modal('hide');
            }
            
            // 刷新页面或特定区域
            if (form.data('refresh')) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showMessage(result.message || '操作失败', 'error');
        }
    } catch (error) {
        console.error('表单提交失败:', error);
        showMessage('操作失败，请稍后重试', 'error');
    } finally {
        hideLoading();
    }
}

// 确认删除
function confirmDelete(e) {
    e.preventDefault();
    
    const url = $(this).attr('href');
    const itemName = $(this).data('item-name') || '该项目';
    
    if (confirm(`确定要删除${itemName}吗？此操作不可撤销。`)) {
        deleteItem(url);
    }
}

// 删除项目
async function deleteItem(url) {
    try {
        showLoading();
        
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('删除成功', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showMessage(result.message || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除失败:', error);
        showMessage('删除失败，请稍后重试', 'error');
    } finally {
        hideLoading();
    }
}

// 刷新数据
async function refreshData() {
    const container = $(this).data('container');
    
    try {
        showLoading();
        
        // 这里可以根据需要实现具体的刷新逻辑
        setTimeout(() => {
            window.location.reload();
        }, 500);
    } catch (error) {
        console.error('刷新失败:', error);
        showMessage('刷新失败', 'error');
    } finally {
        hideLoading();
    }
}

// 显示加载状态
function showLoading(element) {
    if (element) {
        $(element).prop('disabled', true).html('<span class="loading"></span> 加载中...');
    } else {
        $('body').append('<div id="global-loading" class="position-fixed top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center" style="background: rgba(0,0,0,0.5); z-index: 9999;"><div class="spinner-border text-light" role="status"><span class="visually-hidden">加载中...</span></div></div>');
    }
}

// 隐藏加载状态
function hideLoading(element) {
    if (element) {
        $(element).prop('disabled', false).html('提交');
    } else {
        $('#global-loading').remove();
    }
}

// 显示消息
function showMessage(message, type = 'info', duration = 3000) {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const icon = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    }[type] || 'fas fa-info-circle';
    
    const alert = $(`
        <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
            <i class="${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    
    $('body').append(alert);
    
    // 自动隐藏
    setTimeout(() => {
        alert.alert('close');
    }, duration);
}

// API请求封装
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.message || '请求失败');
        }
        
        return result;
    } catch (error) {
        console.error('API请求失败:', error);
        throw error;
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化时间
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 验证邮箱格式
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 验证密码强度
function validatePassword(password) {
    if (password.length < 8) return false;
    
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasDigit = /\d/.test(password);
    const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password);
    
    return [hasUpper, hasLower, hasDigit, hasSpecial].filter(Boolean).length >= 3;
}

// 导出全局函数
window.logout = logout;
window.showMessage = showMessage;
window.apiRequest = apiRequest;
window.formatFileSize = formatFileSize;
window.formatTime = formatTime;
window.validateEmail = validateEmail;
window.validatePassword = validatePassword;
