(function () {
  'use strict';

  const API_BASE = '';
  let currentCaptchaTask = null;

  // 关闭通知功能
  function initNoticeClose() {
    const closeBtn = document.getElementById('close-notice');
    const notice = document.getElementById('lagou-notice');
    
    if (closeBtn && notice) {
      closeBtn.addEventListener('click', function() {
        notice.style.display = 'none';
        // 可以选择将状态保存到localStorage
        try {
          localStorage.setItem('lagouNoticeClosed', 'true');
        } catch (e) {
          // localStorage不可用时忽略
        }
      });
      
      // 检查是否之前关闭过
      try {
        if (localStorage.getItem('lagouNoticeClosed') === 'true') {
          notice.style.display = 'none';
        }
      } catch (e) {
        // localStorage不可用时忽略
      }
    }
  }

  // 页面加载完成后初始化
  document.addEventListener('DOMContentLoaded', function() {
    initNoticeClose();
    initCaptchaModal();
    startCaptchaPolling();
  });

  function request(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body && (method === 'POST' || method === 'PUT')) opts.body = JSON.stringify(body);
    return fetch(API_BASE + path, opts).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) throw new Error(data.error || '请求失败');
        return data;
      });
    });
  }

  function get(path) {
    return request('GET', path);
  }

  function post(path, body) {
    return request('POST', path, body);
  }

  // Tabs
  var tabs = document.querySelectorAll('.tab');
  var panels = document.querySelectorAll('.panel');
  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var id = this.getAttribute('data-tab');
      tabs.forEach(function (t) { t.classList.toggle('active', t === tab); });
      panels.forEach(function (p) {
        p.classList.toggle('active', p.id === 'panel-' + id);
      });
    });
  });

  // System info and source initialization
  Promise.all([
    get('/api/system_info'),
    get('/api/job_sources')
  ]).then(function (results) {
    var info = results[0];
    var sources = results[1];
    
    // Update system info
    var el = document.getElementById('system-version');
    if (el) el.textContent = 'v' + (info.version || '');
    var qwen = document.getElementById('qwen-status');
    if (qwen) qwen.classList.toggle('on', !!info.qwen_enabled);
    
    // Initialize source checkboxes
    initSourceCheckboxes(sources);
  }).catch(function (error) {
    console.error('Failed to initialize:', error);
  });
  
  // Initialize source checkboxes
  function initSourceCheckboxes(sourcesData) {
    var container = document.getElementById('source-checkboxes');
    if (!container) return;
    
    var availableSources = sourcesData.available || [];
    var enabledSources = sourcesData.enabled || [];
    
    // Clear existing content
    container.innerHTML = '';
    
    // Create checkbox for each source
    availableSources.forEach(function(sourceId) {
      var sourceName = getSourceDisplayName(sourceId);
      var isChecked = enabledSources.includes(sourceId);
      
      var checkboxDiv = document.createElement('div');
      checkboxDiv.className = 'source-checkbox ' + (isChecked ? 'checked' : '');
      checkboxDiv.innerHTML = `
        <input type="checkbox" id="source-${sourceId}" value="${sourceId}" ${isChecked ? 'checked' : ''}>
        <span>${sourceName}</span>
        <span class="source-status status-pending" id="status-${sourceId}">
          <span class="loading-spinner"></span>
        </span>
      `;
      
      // Add click handler
      checkboxDiv.addEventListener('click', function(e) {
        if (e.target.type !== 'checkbox') {
          var checkbox = checkboxDiv.querySelector('input[type="checkbox"]');
          checkbox.checked = !checkbox.checked;
          checkbox.dispatchEvent(new Event('change'));
        }
      });
      
      // Add change handler
      var checkbox = checkboxDiv.querySelector('input[type="checkbox"]');
      checkbox.addEventListener('change', function() {
        checkboxDiv.classList.toggle('checked', this.checked);
        checkSourceStatus(sourceId);
      });
      
      container.appendChild(checkboxDiv);
      
      // Check initial status
      checkSourceStatus(sourceId);
    });
  }
  
  // Get display name for source
  function getSourceDisplayName(sourceId) {
    var names = {
      'lagou': '拉勾网',
      'boss': 'BOSS直聘',
      'zhaopin': '智联招聘'
    };
    return names[sourceId] || sourceId;
  }
  
  // Check source status
  function checkSourceStatus(sourceId) {
    var statusElement = document.getElementById('status-' + sourceId);
    if (!statusElement) return;
    
    // Set to pending state
    statusElement.className = 'source-status status-pending';
    statusElement.innerHTML = '<span class="loading-spinner"></span>';
    
    // Simulate status check (in real implementation, this would call an API)
    setTimeout(function() {
      var isAvailable = getSourceAvailability(sourceId);
      updateSourceStatus(sourceId, isAvailable);
    }, 800);
  }
  
  // Get source availability (mock implementation)
  function getSourceAvailability(sourceId) {
    // In a real implementation, this would check actual source status
    var unavailableSources = ['boss', 'zhaopin']; // These are placeholders
    return !unavailableSources.includes(sourceId);
  }
  
  // Update source status display
  function updateSourceStatus(sourceId, isAvailable) {
    var statusElement = document.getElementById('status-' + sourceId);
    if (!statusElement) return;
    
    if (isAvailable) {
      statusElement.className = 'source-status status-available';
      statusElement.innerHTML = '✓';
      statusElement.title = '源可用';
    } else {
      statusElement.className = 'source-status status-unavailable';
      statusElement.innerHTML = '✗';
      statusElement.title = '源不可用';
    }
  }
  
  // Get selected sources
  function getSelectedSources() {
    var checkboxes = document.querySelectorAll('#source-checkboxes input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
  }

  // Search jobs
  var searchResult = document.getElementById('search-result');
  var btnSearch = document.getElementById('btn-search');
  if (btnSearch) {
    btnSearch.addEventListener('click', function () {
      var keyword = document.getElementById('search-keyword').value.trim();
      var city = document.getElementById('search-city').value.trim() || '全国';
      if (!keyword) {
        searchResult.className = 'result-box error';
        searchResult.textContent = '请输入职位关键词';
        return;
      }
      searchResult.className = 'result-box loading';
      searchResult.textContent = '正在搜索…';
      btnSearch.disabled = true;
      var selectedSources = getSelectedSources();
      if (selectedSources.length === 0) {
        searchResult.className = 'result-box error';
        searchResult.innerHTML = `
          <div class="notice-banner notice-error">
            <div class="notice-content">
              <span class="notice-icon">⚠️</span>
              <div class="notice-text">
                <strong>请选择至少一个招聘网站</strong>
                <br>请在上方选择要搜索的招聘网站
              </div>
            </div>
          </div>
        `;
        btnSearch.disabled = false;
        return;
      }
      
      post('/api/search_jobs', { 
        keyword: keyword, 
        city: city, 
        page: 1,
        sources: selectedSources
      })
        .then(function (data) {
          btnSearch.disabled = false;
          if (!data.jobs || data.jobs.length === 0) {
            searchResult.className = 'result-box warning';
            searchResult.innerHTML = `
              <div class="source-unavailable-notice">
                <strong>未找到职位数据</strong>
                <br>可能是由于以下原因：
                <ul>
                  ${selectedSources.map(source => `<li>${getSourceDisplayName(source)}: 暂无相关职位或源不可用</li>`).join('')}
                </ul>
                <br>建议：<br>
                • 尝试更换关键词<br>
                • 选择其他招聘网站<br>
                • 稍后再试
              </div>
            `;
            return;
          }
          searchResult.className = 'result-box';
          searchResult.innerHTML = '<ul class="job-list">' + data.jobs.map(function (job) {
            return (
              '<li class="job-card">' +
              '<h3>' + escapeHtml(job.title || '') + '</h3>' +
              '<div class="job-meta">' + escapeHtml(job.company || '') +
              ' <span class="salary">' + escapeHtml(job.salary || '') + '</span></div>' +
              (job.description ? '<div class="job-desc">' + escapeHtml(job.description).slice(0, 150) + '…</div>' : '') +
              '</li>'
            );
          }).join('') + '</ul>';
        })
        .catch(function (err) {
          btnSearch.disabled = false;
          searchResult.className = 'result-box error';
          searchResult.innerHTML = `
            <div class="notice-banner notice-error">
              <div class="notice-content">
                <span class="notice-icon">❌</span>
                <div class="notice-text">
                  <strong>搜索遇到问题</strong>
                  <br>${escapeHtml(err.message || '搜索失败')}<br><br>
                  <small>如果您持续遇到此问题，请联系技术支持。</small>
                </div>
              </div>
            </div>
          `;
        });
    });
  }

  // Match resume
  var matchResult = document.getElementById('match-result');
  var btnMatch = document.getElementById('btn-match');
  if (btnMatch) {
    btnMatch.addEventListener('click', function () {
      var resume = document.getElementById('match-resume').value.trim();
      var keyword = document.getElementById('match-keyword').value.trim();
      var city = document.getElementById('match-city').value.trim() || '全国';
      if (!resume || !keyword) {
        matchResult.className = 'result-box error';
        matchResult.textContent = '请填写简历内容与目标职位关键词';
        return;
      }
      matchResult.className = 'result-box loading';
      matchResult.textContent = '正在匹配…';
      btnMatch.disabled = true;
      post('/api/match_resume', { resume: resume, keyword: keyword, city: city })
        .then(function (data) {
          btnMatch.disabled = false;
          var jobs = data.matched_jobs || [];
          if (jobs.length === 0) {
            matchResult.className = 'result-box empty';
            matchResult.innerHTML = '暂无匹配职位，请调整关键词或简历内容。';
            return;
          }
          matchResult.className = 'result-box';
          matchResult.innerHTML = '<ul class="job-list">' + jobs.map(function (job) {
            return (
              '<li class="job-card">' +
              '<h3>' + escapeHtml(job.title || '') + '</h3>' +
              '<div class="job-meta">' + escapeHtml(job.company || '') +
              ' <span class="salary">' + escapeHtml(job.salary || '') + '</span></div>' +
              '<span class="match-score">匹配度 ' + (job.match_score != null ? job.match_score : '—') + '%</span>' +
              (job.description ? '<div class="job-desc">' + escapeHtml(job.description).slice(0, 120) + '…</div>' : '') +
              '</li>'
            );
          }).join('') + '</ul>';
        })
        .catch(function (err) {
          btnMatch.disabled = false;
          matchResult.className = 'result-box error';
          matchResult.textContent = err.message || '匹配失败';
        });
    });
  }

  // Optimize resume
  var optimizeResult = document.getElementById('optimize-result');
  var btnOptimize = document.getElementById('btn-optimize');
  if (btnOptimize) {
    btnOptimize.addEventListener('click', function () {
      var resume = document.getElementById('optimize-resume').value.trim();
      var keyword = document.getElementById('optimize-keyword').value.trim();
      var city = document.getElementById('optimize-city').value.trim() || '全国';
      if (!resume || !keyword) {
        optimizeResult.className = 'result-box error';
        optimizeResult.textContent = '请填写简历内容与目标职位关键词';
        return;
      }
      optimizeResult.className = 'result-box loading';
      optimizeResult.textContent = '正在生成优化建议…';
      btnOptimize.disabled = true;
      post('/api/optimize_resume', { resume: resume, keyword: keyword, city: city })
        .then(function (data) {
          btnOptimize.disabled = false;
          var suggestions = data.suggestions || [];
          var optimized = data.optimized_resume || '';
          optimizeResult.className = 'result-box';
          var html = '';
          if (suggestions.length) {
            html += '<h4 style="margin:0 0 0.5rem; font-size:0.9rem;">优化建议</h4>';
            html += '<ul class="suggestions-list">' + suggestions.map(function (s) {
              return '<li>' + escapeHtml(s) + '</li>';
            }).join('') + '</ul>';
          }
          if (optimized) {
            html += '<div class="optimized-block"><h4>优化后简历</h4>' + escapeHtml(optimized) + '</div>';
          }
          if (!html) html = '<p class="empty">暂无优化内容</p>';
          optimizeResult.innerHTML = html;
        })
        .catch(function (err) {
          btnOptimize.disabled = false;
          optimizeResult.className = 'result-box error';
          optimizeResult.textContent = err.message || '优化失败';
        });
    });
  }

  function escapeHtml(s) {
    if (s == null) return '';
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }
  
  // 验证码处理功能
  function initCaptchaModal() {
    const modal = document.getElementById('captcha-modal');
    const closeBtn = document.getElementById('close-captcha-modal');
    const submitBtn = document.getElementById('submit-captcha');
    const solutionInput = document.getElementById('captcha-solution');
    
    if (!modal || !closeBtn || !submitBtn) return;
    
    // 关闭模态框
    closeBtn.addEventListener('click', function() {
      closeModal();
    });
    
    // 点击背景关闭
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeModal();
      }
    });
    
    // 提交验证码
    submitBtn.addEventListener('click', submitCaptchaSolution);
    
    // 回车提交
    solutionInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        submitCaptchaSolution();
      }
    });
    
    function closeModal() {
      modal.style.display = 'none';
      currentCaptchaTask = null;
      solutionInput.value = '';
    }
    
    function submitCaptchaSolution() {
      if (!currentCaptchaTask || !solutionInput.value.trim()) return;
      
      submitBtn.disabled = true;
      submitBtn.textContent = '提交中...';
      
      post('/api/captcha/submit', {
        captcha_id: currentCaptchaTask.id,
        solution: solutionInput.value.trim()
      })
      .then(function(response) {
        if (response.success) {
          showNotification('✅ 验证码提交成功', 'success');
          closeModal();
        } else {
          showNotification('❌ 验证码提交失败: ' + response.message, 'error');
        }
      })
      .catch(function(error) {
        showNotification('❌ 提交失败: ' + error.message, 'error');
      })
      .finally(function() {
        submitBtn.disabled = false;
        submitBtn.textContent = '提交';
      });
    }
  }
  
  function startCaptchaPolling() {
    // 每5秒检查一次待处理的验证码
    setInterval(checkPendingCaptchas, 5000);
    // 立即检查一次
    setTimeout(checkPendingCaptchas, 1000);
  }
  
  function checkPendingCaptchas() {
    get('/api/captcha/pending')
    .then(function(response) {
      if (response.count > 0) {
        showCaptchaModal(response.pending_captchas[0]);
      }
    })
    .catch(function(error) {
      // 静默处理，避免过多错误提示
      console.debug('检查验证码失败:', error);
    });
  }
  
  function showCaptchaModal(captchaTask) {
    const modal = document.getElementById('captcha-modal');
    const container = document.getElementById('captcha-container');
    const solutionInput = document.getElementById('captcha-solution');
    
    if (!modal || !container) return;
    
    currentCaptchaTask = captchaTask;
    
    // 显示验证码内容
    let captchaHtml = '';
    
    // 处理滑动验证码的特殊显示
    if (captchaTask.type === 'slide' || captchaTask.enhanced_type === 'slide_with_images') {
      captchaHtml += renderSlideCaptcha(captchaTask);
    } else {
      // 其他类型验证码的显示
      if (captchaTask.image) {
        captchaHtml += `<img src="data:image/png;base64,${captchaTask.image}" 
                        class="captcha-image" 
                        alt="验证码图片">`;
      }
    }
    
    captchaHtml += `<div class="captcha-type-info">
                      验证码类型: ${getCaptchaTypeName(captchaTask.type)}
                    </div>`;
    
    // 根据验证码类型添加操作提示
    const operationTips = getCaptchaOperationTip(captchaTask.type);
    if (operationTips) {
      captchaHtml += `<div class="captcha-operation-tip">
                        ${operationTips}
                      </div>`;
    }
    
    container.innerHTML = captchaHtml;
    solutionInput.value = '';
    
    // 显示模态框
    modal.style.display = 'block';
    
    // 聚焦到输入框
    setTimeout(function() {
      solutionInput.focus();
    }, 100);
  }
  
  function getCaptchaTypeName(type) {
    const names = {
      'slide': '滑动验证码',
      'text_input': '文本验证码',
      'image_text': '图片数字验证码',
      'click': '点选验证码',
      'geetest': '极验验证码',
      'unknown': '未知类型验证码'
    };
    return names[type] || names['unknown'];
  }
  
  function getCaptchaOperationTip(type) {
    const tips = {
      'slide': '请在下方的滑动区域中拖动滑块到正确位置',
      'text_input': '请在下方输入框中输入看到的验证码文字',
      'image_text': '请观察上方图片中的数字或文字，在下方输入框中输入答案',
      'click': '请在下方输入框中输入点击坐标（格式：x1,y1;x2,y2），或直接在图片上点击',
      'geetest': '请按照极验验证码的要求完成验证操作',
      'unknown': '请根据图片提示完成相应的验证操作'
    };
    return tips[type];
  }
  
  function renderSlideCaptcha(captchaTask) {
    let html = '';
    
    // 获取验证码图片信息
    const captchaImages = captchaTask.captcha_images || {};
    
    // 显示背景图片
    if (captchaImages.background) {
      html += `
        <div class="slide-captcha-container">
          <div class="slide-background">
            <img src="${captchaImages.background}" alt="滑动验证码背景" class="captcha-bg-image">
          </div>
          
          <!-- 滑动轨道 -->
          <div class="slide-track" id="slide-track-${captchaTask.id}">
            <div class="slide-slider" id="slide-slider-${captchaTask.id}">
              <span class="slider-icon">→</span>
            </div>
            <div class="slide-progress" id="slide-progress-${captchaTask.id}"></div>
          </div>
          
          <!-- 滑块图片 -->
          ${captchaImages.slider ? 
            `<div class="slide-piece">
               <img src="${captchaImages.slider}" alt="滑块" class="captcha-slider-image">
             </div>` : ''
          }
        </div>
      `;
      
      // 添加滑动事件监听
      setTimeout(() => {
        initSlideInteraction(captchaTask.id);
      }, 100);
    } else if (captchaImages.full_captcha) {
      // 如果只有完整截图，显示完整图片
      html += `
        <div class="slide-captcha-full">
          <img src="data:image/png;base64,${captchaImages.full_captcha}" 
               alt="滑动验证码" 
               class="captcha-full-image">
          <div class="slide-overlay" id="slide-overlay-${captchaTask.id}">
            <div class="slide-handle" id="slide-handle-${captchaTask.id}">拖动滑块</div>
          </div>
        </div>
      `;
      
      // 添加拖动事件
      setTimeout(() => {
        initFullImageSlide(captchaTask.id);
      }, 100);
    }
    
    return html;
  }
  
  function initSlideInteraction(captchaId) {
    const slider = document.getElementById(`slide-slider-${captchaId}`);
    const track = document.getElementById(`slide-track-${captchaId}`);
    const progress = document.getElementById(`slide-progress-${captchaId}`);
    
    if (!slider || !track) return;
    
    let isDragging = false;
    let startX = 0;
    let startLeft = 0;
    
    slider.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
    
    slider.addEventListener('touchstart', startDrag, { passive: false });
    document.addEventListener('touchmove', drag, { passive: false });
    document.addEventListener('touchend', stopDrag);
    
    function startDrag(e) {
      e.preventDefault();
      isDragging = true;
      startX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
      startLeft = parseInt(getComputedStyle(slider).left) || 0;
      slider.classList.add('dragging');
    }
    
    function drag(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      const currentX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
      const deltaX = currentX - startX;
      
      const maxLeft = track.offsetWidth - slider.offsetWidth;
      let newLeft = Math.max(0, Math.min(maxLeft, startLeft + deltaX));
      
      slider.style.left = newLeft + 'px';
      progress.style.width = newLeft + 'px';
      
      // 实时更新输入框的值
      const solutionInput = document.getElementById('captcha-solution');
      if (solutionInput) {
        const percentage = (newLeft / maxLeft) * 100;
        solutionInput.value = Math.round(percentage);
      }
    }
    
    function stopDrag() {
      if (isDragging) {
        isDragging = false;
        slider.classList.remove('dragging');
        
        // 检查是否完成验证
        const sliderPos = parseInt(getComputedStyle(slider).left);
        const trackWidth = track.offsetWidth - slider.offsetWidth;
        
        if (sliderPos >= trackWidth * 0.8) { // 80%以上认为完成
          showNotification('✅ 滑动验证完成，请提交', 'success');
        }
      }
    }
  }
  
  function initFullImageSlide(captchaId) {
    const overlay = document.getElementById(`slide-overlay-${captchaId}`);
    const handle = document.getElementById(`slide-handle-${captchaId}`);
    
    if (!overlay || !handle) return;
    
    let isDragging = false;
    let startX = 0;
    let startLeft = 0;
    
    handle.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
    
    function startDrag(e) {
      e.preventDefault();
      isDragging = true;
      startX = e.clientX;
      startLeft = parseInt(getComputedStyle(handle).left) || 0;
      handle.classList.add('dragging');
    }
    
    function drag(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      const deltaX = e.clientX - startX;
      const maxLeft = overlay.offsetWidth - handle.offsetWidth;
      let newLeft = Math.max(0, Math.min(maxLeft, startLeft + deltaX));
      
      handle.style.left = newLeft + 'px';
      
      // 更新输入框值
      const solutionInput = document.getElementById('captcha-solution');
      if (solutionInput) {
        const percentage = (newLeft / maxLeft) * 100;
        solutionInput.value = Math.round(percentage);
      }
    }
    
    function stopDrag() {
      if (isDragging) {
        isDragging = false;
        handle.classList.remove('dragging');
      }
    }
  }
  
  function showNotification(message, type = 'info') {
    // 简单的通知显示
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 8px;
      color: white;
      font-size: 14px;
      z-index: 1001;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      ${type === 'success' ? 'background: #10b981;' : ''}
      ${type === 'error' ? 'background: #ef4444;' : ''}
      ${type === 'info' ? 'background: #3b82f6;' : ''}
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动消失
    setTimeout(function() {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 3000);
  }

  // 页面加载完成后初始化通知关闭功能
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNoticeClose);
  } else {
    initNoticeClose();
  }
})();
