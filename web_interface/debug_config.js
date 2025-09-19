// DeepSeek本地模型配置调试脚本
console.log('=== DeepSeek本地模型配置调试 ===');

// 测试保存配置
function testSaveConfig() {
    console.log('测试保存配置...');
    
    const testConfig = {
        url: 'http://192.168.210.209:11434/api/generate',
        model: 'deepseek-r1',
        timeout: 30,
        timestamp: new Date().toISOString()
    };
    
    try {
        localStorage.setItem('local_config', JSON.stringify(testConfig));
        console.log('✅ 配置保存成功:', testConfig);
        return true;
    } catch (error) {
        console.error('❌ 配置保存失败:', error);
        return false;
    }
}

// 测试加载配置
function testLoadConfig() {
    console.log('测试加载配置...');
    
    try {
        const config = localStorage.getItem('local_config');
        if (config) {
            const parsedConfig = JSON.parse(config);
            console.log('✅ 配置加载成功:', parsedConfig);
            return parsedConfig;
        } else {
            console.log('⚠️ 没有找到保存的配置');
            return null;
        }
    } catch (error) {
        console.error('❌ 配置加载失败:', error);
        return null;
    }
}

// 测试localStorage可用性
function testLocalStorage() {
    console.log('测试localStorage可用性...');
    
    try {
        const testKey = 'test_key_' + Date.now();
        const testValue = 'test_value';
        
        localStorage.setItem(testKey, testValue);
        const retrieved = localStorage.getItem(testKey);
        localStorage.removeItem(testKey);
        
        if (retrieved === testValue) {
            console.log('✅ localStorage工作正常');
            return true;
        } else {
            console.error('❌ localStorage数据不一致');
            return false;
        }
    } catch (error) {
        console.error('❌ localStorage不可用:', error);
        return false;
    }
}

// 检查当前页面中的配置元素
function checkConfigElements() {
    console.log('检查配置元素...');
    
    const elements = {
        'local-url': document.getElementById('local-url'),
        'local-model': document.getElementById('local-model'),
        'local-timeout': document.getElementById('local-timeout')
    };
    
    for (const [id, element] of Object.entries(elements)) {
        if (element) {
            console.log(`✅ 找到元素 ${id}:`, element.value);
        } else {
            console.error(`❌ 未找到元素 ${id}`);
        }
    }
    
    return elements;
}

// 模拟配置保存过程
function simulateSaveProcess() {
    console.log('模拟配置保存过程...');
    
    const config = {
        url: document.getElementById('local-url')?.value || '',
        model: document.getElementById('local-model')?.value || '',
        timeout: document.getElementById('local-timeout')?.value || '30'
    };
    
    console.log('准备保存的配置:', config);
    
    try {
        localStorage.setItem('local_config', JSON.stringify(config));
        console.log('✅ 模拟保存成功');
        return true;
    } catch (error) {
        console.error('❌ 模拟保存失败:', error);
        return false;
    }
}

// 模拟配置加载过程
function simulateLoadProcess() {
    console.log('模拟配置加载过程...');
    
    try {
        const config = localStorage.getItem('local_config');
        if (config) {
            const parsedConfig = JSON.parse(config);
            console.log('加载的配置:', parsedConfig);
            
            // 模拟填充表单
            const urlElement = document.getElementById('local-url');
            const modelElement = document.getElementById('local-model');
            const timeoutElement = document.getElementById('local-timeout');
            
            if (urlElement) urlElement.value = parsedConfig.url || '';
            if (modelElement) modelElement.value = parsedConfig.model || '';
            if (timeoutElement) timeoutElement.value = parsedConfig.timeout || 30;
            
            console.log('✅ 模拟加载成功');
            return true;
        } else {
            console.log('⚠️ 没有配置可加载');
            return false;
        }
    } catch (error) {
        console.error('❌ 模拟加载失败:', error);
        return false;
    }
}

// 运行所有测试
function runAllTests() {
    console.log('开始运行所有测试...');
    
    const results = {
        localStorage: testLocalStorage(),
        saveConfig: testSaveConfig(),
        loadConfig: testLoadConfig(),
        elements: checkConfigElements(),
        simulateSave: simulateSaveProcess(),
        simulateLoad: simulateLoadProcess()
    };
    
    console.log('=== 测试结果汇总 ===');
    console.log(results);
    
    return results;
}

// 如果在浏览器环境中，自动运行测试
if (typeof window !== 'undefined') {
    console.log('在浏览器环境中，准备运行测试...');
    // 等待页面加载完成
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runAllTests);
    } else {
        runAllTests();
    }
}

// 导出函数供外部调用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        testSaveConfig,
        testLoadConfig,
        testLocalStorage,
        checkConfigElements,
        simulateSaveProcess,
        simulateLoadProcess,
        runAllTests
    };
}
