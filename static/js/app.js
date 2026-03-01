(function () {
  'use strict';

  const API_BASE = '';

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

  // System info
  get('/api/system_info').then(function (info) {
    var el = document.getElementById('system-version');
    if (el) el.textContent = 'v' + (info.version || '');
    var qwen = document.getElementById('qwen-status');
    if (qwen) qwen.classList.toggle('on', !!info.qwen_enabled);
  }).catch(function () {});

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
      post('/api/search_jobs', { keyword: keyword, city: city, page: 1 })
        .then(function (data) {
          btnSearch.disabled = false;
          if (!data.jobs || data.jobs.length === 0) {
            searchResult.className = 'result-box empty';
            searchResult.innerHTML = '未找到相关职位，可更换关键词或城市重试。';
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
          searchResult.textContent = err.message || '搜索失败';
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
})();
