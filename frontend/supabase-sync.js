(function (global) {
  'use strict';

  const TABLES = Object.freeze([
    'weekly_tasks',
    'pomodoro_sessions',
    'question_logs',
    'exam_results',
    'student_mistakes',
    'session_ledger',
    'weekly_parent_reports'
  ]);

  const ALLOWED_FIELDS = Object.freeze({
    weekly_tasks: ['id', 'tenant_id', 'student_id', 'title', 'subject', 'due_date', 'status', 'created_at', 'updated_at'],
    pomodoro_sessions: ['id', 'tenant_id', 'student_id', 'subject', 'duration_minutes', 'completed_at'],
    question_logs: ['id', 'tenant_id', 'student_id', 'subject', 'topic', 'correct_count', 'wrong_count', 'blank_count', 'logged_at'],
    exam_results: ['id', 'tenant_id', 'student_id', 'exam_name', 'exam_type', 'total_net', 'taken_at', 'created_at'],
    student_mistakes: ['id', 'tenant_id', 'student_id', 'subject', 'topic', 'note', 'resolved', 'created_at'],
    session_ledger: ['id', 'tenant_id', 'coach_id', 'student_id', 'delta_sessions', 'reason', 'recorded_at'],
    weekly_parent_reports: ['id', 'tenant_id', 'student_id', 'week_start', 'summary', 'total_questions', 'total_pomodoro_minutes', 'created_at']
  });

  const memoryStore = new Map();
  TABLES.forEach(function (t) {
    memoryStore.set(t, []);
  });
  const pendingQueue = [];

  function pickAllowed(table, record) {
    const fields = ALLOWED_FIELDS[table] || [];
    const src = record && typeof record === 'object' ? record : {};
    const out = {};
    for (let i = 0; i < fields.length; i += 1) {
      const key = fields[i];
      if (Object.prototype.hasOwnProperty.call(src, key) && src[key] !== undefined) {
        out[key] = src[key];
      }
    }
    return out;
  }

  function isOnline() {
    return typeof navigator === 'undefined' || navigator.onLine !== false;
  }

  function getSupabaseClient() {
    const client = global.__adimplanSupabase;
    if (client && typeof client.from === 'function') {
      return client;
    }
    return null;
  }

  function upsertMemory(table, items) {
    const list = memoryStore.get(table) || [];
    const next = list.slice();
    for (let i = 0; i < items.length; i += 1) {
      const item = items[i];
      const idx = item.id !== undefined ? next.findIndex(function (x) { return x.id === item.id; }) : -1;
      if (idx >= 0) {
        next[idx] = Object.assign({}, next[idx], item);
      } else {
        next.push(item);
      }
    }
    memoryStore.set(table, next);
  }

  async function writeRecord(table, payload, mode) {
    const items = Array.isArray(payload)
      ? payload.map(function (r) { return pickAllowed(table, r); })
      : [pickAllowed(table, payload)];

    upsertMemory(table, items);

    const client = getSupabaseClient();
    if (!client || !isOnline()) {
      pendingQueue.push({ table: table, mode: mode, payload: items, queuedAt: new Date().toISOString() });
      return { ok: true, offline: true, data: Array.isArray(payload) ? items : items[0] };
    }

    try {
      const query = mode === 'upsert'
        ? client.from(table).upsert(items).select()
        : client.from(table).insert(items).select();
      const res = await query;
      if (res && res.error) {
        pendingQueue.push({ table: table, mode: mode, payload: items, queuedAt: new Date().toISOString() });
        return { ok: true, offline: true, error: res.error.message || 'sync_queued', data: Array.isArray(payload) ? items : items[0] };
      }
      const rows = res && Array.isArray(res.data) ? res.data : items;
      upsertMemory(table, rows);
      return { ok: true, offline: false, data: Array.isArray(payload) ? rows : rows[0] };
    } catch (err) {
      pendingQueue.push({ table: table, mode: mode, payload: items, queuedAt: new Date().toISOString() });
      return { ok: true, offline: true, error: err && err.message ? err.message : 'network_error', data: Array.isArray(payload) ? items : items[0] };
    }
  }

  async function fetchTasks(filters) {
    const opts = filters && typeof filters === 'object' ? filters : {};
    const client = getSupabaseClient();
    if (client && isOnline()) {
      try {
        let query = client.from('weekly_tasks').select('*');
        if (opts.student_id) {
          query = query.eq('student_id', String(opts.student_id));
        }
        if (opts.tenant_id) {
          query = query.eq('tenant_id', String(opts.tenant_id));
        }
        if (opts.status) {
          query = query.eq('status', String(opts.status));
        }
        const res = await query;
        if (res && !res.error && Array.isArray(res.data)) {
          memoryStore.set('weekly_tasks', res.data.slice());
          return { ok: true, offline: false, data: res.data };
        }
      } catch (_err) {
        // Fallback to in-memory cache
      }
    }

    const cached = (memoryStore.get('weekly_tasks') || []).filter(function (row) {
      if (opts.student_id && row.student_id !== opts.student_id) return false;
      if (opts.tenant_id && row.tenant_id !== opts.tenant_id) return false;
      if (opts.status && row.status !== opts.status) return false;
      return true;
    });
    return { ok: true, offline: true, data: cached };
  }

  async function flushQueue() {
    const client = getSupabaseClient();
    if (!client || !isOnline() || pendingQueue.length === 0) {
      return { flushed: 0, remaining: pendingQueue.length };
    }
    let flushed = 0;
    const remaining = [];
    while (pendingQueue.length > 0) {
      const entry = pendingQueue.shift();
      try {
        const res = entry.mode === 'upsert'
          ? await client.from(entry.table).upsert(entry.payload)
          : await client.from(entry.table).insert(entry.payload);
        if (res && res.error) {
          remaining.push(entry);
        } else {
          flushed += 1;
        }
      } catch (_err) {
        remaining.push(entry);
      }
    }
    for (let i = 0; i < remaining.length; i += 1) {
      pendingQueue.push(remaining[i]);
    }
    return { flushed: flushed, remaining: pendingQueue.length };
  }

  function sanitizeApiBase(rawBase) {
    if (typeof rawBase !== 'string') return null;
    const trimmed = rawBase.trim().replace(/\/+$/, '');
    if (!trimmed) return null;
    if (trimmed.startsWith('/')) return trimmed;
    try {
      const parsed = new URL(trimmed);
      if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
        return parsed.origin + parsed.pathname.replace(/\/+$/, '');
      }
    } catch (_err) {
      return null;
    }
    return null;
  }

  async function postJson(path, body, fallbackFn) {
    const base = sanitizeApiBase(global.__adimplanApiBase);
    if (!base || !isOnline() || typeof fetch !== 'function') {
      return fallbackFn(body);
    }
    try {
      const response = await fetch(base + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {})
      });
      if (!response.ok) {
        return fallbackFn(body);
      }
      const data = await response.json();
      return Object.assign({ ok: true, fallback: false }, data);
    } catch (_err) {
      return fallbackFn(body);
    }
  }

  function fallbackSuggestPlan(input) {
    const data = input && typeof input === 'object' ? input : {};
    const subject = typeof data.subject === 'string' && data.subject.trim() ? data.subject.trim() : 'Matematik';
    const dailyMinutes = Number(data.daily_minutes) > 0 ? Number(data.daily_minutes) : 90;
    return {
      ok: true,
      fallback: true,
      plan: [
        { day: 'Pazartesi', subject: subject, task: 'Konu tekrar + 20 soru', minutes: dailyMinutes },
        { day: 'Çarşamba', subject: subject, task: 'Deneme analizi + eksik kapatma', minutes: dailyMinutes },
        { day: 'Cuma', subject: subject, task: 'Zamanlı karma test', minutes: dailyMinutes }
      ]
    };
  }

  function fallbackWeeklyParentReport(input) {
    const data = input && typeof input === 'object' ? input : {};
    const totalQuestions = Number(data.total_questions) || 0;
    const totalPomodoro = Number(data.total_pomodoro_minutes) || 0;
    return {
      ok: true,
      fallback: true,
      week_start: data.week_start || new Date().toISOString().slice(0, 10),
      total_questions: totalQuestions,
      total_pomodoro_minutes: totalPomodoro,
      summary: 'Haftalık özet: ' + totalQuestions + ' soru, ' + totalPomodoro + ' dakika odaklanma kaydedildi.'
    };
  }

  function fallbackSessionLedger(input) {
    const data = input && typeof input === 'object' ? input : {};
    const delta = Number(data.delta_sessions) || 0;
    return {
      ok: true,
      fallback: true,
      delta_sessions: delta,
      reason: typeof data.reason === 'string' ? data.reason : 'offline_record',
      recorded_at: new Date().toISOString()
    };
  }

  global.AdimplanSync = Object.freeze({
    tables: TABLES,
    upsertTasks: function (tasks) { return writeRecord('weekly_tasks', tasks, 'upsert'); },
    fetchTasks: fetchTasks,
    logPomodoro: function (session) { return writeRecord('pomodoro_sessions', session, 'insert'); },
    logQuestions: function (entry) { return writeRecord('question_logs', entry, 'insert'); },
    saveExamResult: function (result) { return writeRecord('exam_results', result, 'insert'); },
    saveMistake: function (mistake) { return writeRecord('student_mistakes', mistake, 'insert'); },
    recordSessionDelta: function (entry) { return writeRecord('session_ledger', entry, 'insert'); },
    saveWeeklyReport: function (report) { return writeRecord('weekly_parent_reports', report, 'upsert'); },
    flushQueue: flushQueue,
    getPendingQueue: function () { return pendingQueue.slice(); }
  });

  global.AdimplanAPI = Object.freeze({
    suggestPlan: function (payload) {
      return postJson('/api/v1/ai/suggest-plan', payload, fallbackSuggestPlan);
    },
    getWeeklyParentReport: function (payload) {
      return postJson('/api/v1/reports/weekly-parent', payload, fallbackWeeklyParentReport);
    },
    recordSessionLedger: function (payload) {
      return postJson('/api/v1/sessions/ledger', payload, fallbackSessionLedger);
    }
  });
})(typeof window !== 'undefined' ? window : globalThis);
