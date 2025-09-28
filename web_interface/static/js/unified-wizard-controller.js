/**
 * 统一向导控制器 - 所有向导页面的通用逻辑
 */

class UnifiedWizardController {
    constructor(config) {
        this.config = Object.assign({
            totalSteps: 4,
            currentStep: 1,
            steps: [],
            validationRules: {},
            navigationFunctions: {
                next: 'nextStep',
                prev: 'prevStep',
                restart: 'restartWizard'
            }
        }, config);
        
        this.wizardData = {
            currentStep: this.config.currentStep,
            data: {},
            validation: {}
        };
        
        this.init();
    }
    
    /**
     * 初始化向导
     */
    init() {
        this.updateWizardUI();
        this.updateNavigationButtons();
        this.bindEvents();
        this.loadWizardData();
    }
    
    /**
     * 更新向导UI
     */
    updateWizardUI() {
        // 更新步骤指示器
        document.querySelectorAll('.wizard-steps .step').forEach((step, index) => {
            step.classList.toggle('active', index + 1 === this.wizardData.currentStep);
        });
        
        // 更新步骤内容 - 支持多种选择器
        const stepSelectors = [
            '.wizard-step',
            '.step-content',
            '[id^="step-"]'
        ];
        
        stepSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach((step, index) => {
                if (step.id && step.id.includes('step-')) {
                    // 通过ID匹配步骤
                    const stepNumber = parseInt(step.id.split('-')[1]);
                    step.classList.toggle('active', stepNumber === this.wizardData.currentStep);
                } else {
                    // 通过索引匹配步骤
                    step.classList.toggle('active', index + 1 === this.wizardData.currentStep);
                }
            });
        });
        
        // 更新步骤指示器文本
        const stepIndicator = document.querySelector('.step-indicator');
        if (stepIndicator) {
            stepIndicator.textContent = `步骤 ${this.wizardData.currentStep} / ${this.config.totalSteps}`;
        }
        
        console.log(`Updated wizard UI to step ${this.wizardData.currentStep}`);
    }
    
    /**
     * 更新导航按钮状态
     */
    updateNavigationButtons() {
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        
        if (prevBtn) {
            prevBtn.disabled = this.wizardData.currentStep === 1;
        }
        
        if (nextBtn) {
            const canProceed = this.canProceedToNextStep(this.wizardData.currentStep);
            nextBtn.disabled = !canProceed || this.wizardData.currentStep === this.config.totalSteps;
        }
    }
    
    /**
     * 检查是否可以进入下一步
     */
    canProceedToNextStep(step) {
        if (this.config.validationRules && this.config.validationRules[step]) {
            return this.config.validationRules[step](this.wizardData);
        }
        return true;
    }
    
    /**
     * 下一步
     */
    nextStep() {
        if (this.canProceedToNextStep(this.wizardData.currentStep)) {
            if (this.wizardData.currentStep < this.config.totalSteps) {
                this.wizardData.currentStep++;
                this.updateWizardUI();
                this.updateNavigationButtons();
                this.saveWizardData();
                this.onStepChange(this.wizardData.currentStep);
            }
        }
    }
    
    /**
     * 上一步
     */
    prevStep() {
        if (this.wizardData.currentStep > 1) {
            this.wizardData.currentStep--;
            this.updateWizardUI();
            this.updateNavigationButtons();
            this.saveWizardData();
            this.onStepChange(this.wizardData.currentStep);
        }
    }
    
    /**
     * 跳转到指定步骤
     */
    goToStep(step) {
        if (step >= 1 && step <= this.config.totalSteps) {
            this.wizardData.currentStep = step;
            this.updateWizardUI();
            this.updateNavigationButtons();
            this.saveWizardData();
            this.onStepChange(this.wizardData.currentStep);
        }
    }
    
    /**
     * 重启向导
     */
    restartWizard() {
        this.wizardData.currentStep = 1;
        this.wizardData.data = {};
        this.wizardData.validation = {};
        this.updateWizardUI();
        this.updateNavigationButtons();
        this.saveWizardData();
        this.onWizardRestart();
    }
    
    /**
     * 设置向导数据
     */
    setWizardData(key, value) {
        this.wizardData.data[key] = value;
        this.saveWizardData();
    }
    
    /**
     * 获取向导数据
     */
    getWizardData(key) {
        return this.wizardData.data[key];
    }
    
    /**
     * 保存向导数据到localStorage
     */
    saveWizardData() {
        const key = `wizard_${this.config.wizardId || 'default'}_data`;
        localStorage.setItem(key, JSON.stringify(this.wizardData));
    }
    
    /**
     * 从localStorage加载向导数据
     */
    loadWizardData() {
        const key = `wizard_${this.config.wizardId || 'default'}_data`;
        const saved = localStorage.getItem(key);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                this.wizardData = { ...this.wizardData, ...data };
            } catch (e) {
                console.warn('Failed to load wizard data:', e);
            }
        }
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 步骤指示器点击事件
        document.querySelectorAll('.wizard-steps .step').forEach((step, index) => {
            step.addEventListener('click', () => {
                if (index + 1 <= this.wizardData.currentStep) {
                    this.goToStep(index + 1);
                }
            });
        });
        
        // 键盘导航
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && e.ctrlKey) {
                e.preventDefault();
                this.prevStep();
            } else if (e.key === 'ArrowRight' && e.ctrlKey) {
                e.preventDefault();
                this.nextStep();
            }
        });
    }
    
    /**
     * 步骤变化回调
     */
    onStepChange(step) {
        // 子类可以重写此方法
        console.log(`Wizard step changed to: ${step}`);
    }
    
    /**
     * 向导重启回调
     */
    onWizardRestart() {
        // 子类可以重写此方法
        console.log('Wizard restarted');
    }
}

// 全局向导控制器实例
let globalWizardController = null;

// 全局导航函数
window.nextStep = function() {
    if (globalWizardController) {
        globalWizardController.nextStep();
    } else {
        console.warn('No global wizard controller found');
    }
};

window.prevStep = function() {
    if (globalWizardController) {
        globalWizardController.prevStep();
    } else {
        console.warn('No global wizard controller found');
    }
};

window.goToStep = function(step) {
    if (globalWizardController) {
        globalWizardController.goToStep(step);
    } else {
        console.warn('No global wizard controller found');
    }
};

// 设置全局向导控制器
window.setGlobalWizardController = function(controller) {
    globalWizardController = controller;
};

/**
 * 统一文件上传控制器
 */
class UnifiedFileUploadController {
    constructor(options) {
        this.options = {
            allowedTypes: ['.csv', '.xlsx', '.xls'],
            maxFileSize: 10 * 1024 * 1024, // 10MB
            multiple: false,
            ...options
        };
        
        this.files = [];
        this.init();
    }
    
    /**
     * 初始化文件上传
     */
    init() {
        this.bindEvents();
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 拖拽上传事件
        document.querySelectorAll('.upload-box').forEach(box => {
            box.addEventListener('dragover', this.handleDragOver.bind(this));
            box.addEventListener('dragleave', this.handleDragLeave.bind(this));
            box.addEventListener('drop', this.handleDrop.bind(this));
            box.addEventListener('click', this.handleClick.bind(this));
        });
        
        // 文件输入事件
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', this.handleFileSelect.bind(this));
        });
    }
    
    /**
     * 处理拖拽悬停
     */
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }
    
    /**
     * 处理拖拽离开
     */
    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
    }
    
    /**
     * 处理文件拖拽
     */
    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }
    
    /**
     * 处理点击上传
     */
    handleClick(e) {
        const input = e.currentTarget.querySelector('input[type="file"]');
        if (input) {
            input.click();
        }
    }
    
    /**
     * 处理文件选择
     */
    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.processFiles(files);
    }
    
    /**
     * 处理文件
     */
    processFiles(files) {
        files.forEach(file => {
            if (this.validateFile(file)) {
                this.addFile(file);
            }
        });
    }
    
    /**
     * 验证文件
     */
    validateFile(file) {
        // 检查文件类型
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        if (!this.options.allowedTypes.includes(fileExtension)) {
            this.showAlert(`不支持的文件类型: ${fileExtension}`, 'error');
            return false;
        }
        
        // 检查文件大小
        if (file.size > this.options.maxFileSize) {
            this.showAlert(`文件大小超过限制: ${this.formatFileSize(this.options.maxFileSize)}`, 'error');
            return false;
        }
        
        return true;
    }
    
    /**
     * 添加文件
     */
    addFile(file) {
        if (!this.options.multiple) {
            this.files = [];
        }
        
        this.files.push(file);
        this.displayFileInfo(file);
        this.onFileAdded(file);
    }
    
    /**
     * 显示文件信息
     */
    displayFileInfo(file) {
        const uploadBox = document.querySelector('.upload-box');
        const fileInfo = document.querySelector('.file-info');
        
        if (uploadBox) {
            uploadBox.style.display = 'none';
        }
        
        if (fileInfo) {
            fileInfo.classList.add('show');
            
            const fileIcon = fileInfo.querySelector('.file-icon');
            const fileName = fileInfo.querySelector('.file-details-info h5');
            const fileSize = fileInfo.querySelector('.file-details-info p');
            
            if (fileIcon) {
                const iconClass = this.getFileIconClass(file.name);
                fileIcon.innerHTML = `<i class="fas ${iconClass}"></i>`;
            }
            
            if (fileName) {
                fileName.textContent = file.name;
            }
            
            if (fileSize) {
                fileSize.textContent = `${this.formatFileSize(file.size)} • ${this.getFileTypeName(file.name)}`;
            }
        }
    }
    
    /**
     * 获取文件图标类
     */
    getFileIconClass(filename) {
        const ext = filename.toLowerCase().split('.').pop();
        switch (ext) {
            case 'csv':
                return 'fa-file-csv';
            case 'xlsx':
            case 'xls':
                return 'fa-file-excel';
            default:
                return 'fa-file-alt';
        }
    }
    
    /**
     * 获取文件类型名称
     */
    getFileTypeName(filename) {
        const ext = filename.toLowerCase().split('.').pop();
        switch (ext) {
            case 'csv':
                return 'CSV文件';
            case 'xlsx':
                return 'Excel文件';
            case 'xls':
                return 'Excel文件';
            default:
                return '数据文件';
        }
    }
    
    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * 移除文件
     */
    removeFile(index) {
        this.files.splice(index, 1);
        this.updateFileDisplay();
        this.onFileRemoved(index);
    }
    
    /**
     * 更新文件显示
     */
    updateFileDisplay() {
        if (this.files.length === 0) {
            const uploadBox = document.querySelector('.upload-box');
            const fileInfo = document.querySelector('.file-info');
            
            if (uploadBox) {
                uploadBox.style.display = 'flex';
            }
            
            if (fileInfo) {
                fileInfo.classList.remove('show');
            }
        }
    }
    
    /**
     * 文件添加回调
     */
    onFileAdded(file) {
        console.log('File added:', file.name);
    }
    
    /**
     * 文件移除回调
     */
    onFileRemoved(index) {
        console.log('File removed at index:', index);
    }
    
    /**
     * 显示提示信息
     */
    showAlert(message, type = 'info') {
        // 这里可以集成统一的提示组件
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

/**
 * 统一表单验证器
 */
class UnifiedFormValidator {
    constructor(rules) {
        this.rules = rules || {};
        this.errors = {};
    }
    
    /**
     * 验证表单
     */
    validate(formData) {
        this.errors = {};
        
        for (const field in this.rules) {
            const value = formData[field];
            const rule = this.rules[field];
            
            if (rule.required && (!value || value.toString().trim() === '')) {
                this.errors[field] = rule.message || `${field}是必填项`;
                continue;
            }
            
            if (value && rule.pattern && !rule.pattern.test(value)) {
                this.errors[field] = rule.message || `${field}格式不正确`;
                continue;
            }
            
            if (value && rule.minLength && value.length < rule.minLength) {
                this.errors[field] = rule.message || `${field}长度不能少于${rule.minLength}个字符`;
                continue;
            }
            
            if (value && rule.maxLength && value.length > rule.maxLength) {
                this.errors[field] = rule.message || `${field}长度不能超过${rule.maxLength}个字符`;
                continue;
            }
        }
        
        return Object.keys(this.errors).length === 0;
    }
    
    /**
     * 获取错误信息
     */
    getErrors() {
        return this.errors;
    }
    
    /**
     * 获取字段错误信息
     */
    getFieldError(field) {
        return this.errors[field];
    }
}

// 全局实例
window.UnifiedWizardController = UnifiedWizardController;
window.UnifiedFileUploadController = UnifiedFileUploadController;
window.UnifiedFormValidator = UnifiedFormValidator;