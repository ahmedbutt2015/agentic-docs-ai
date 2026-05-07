import { useCallback, useEffect, useState } from 'react';
import Chat from './components/Chat';
import FileUpload from './components/FileUpload';
import ResultDisplay from './components/ResultDisplay';
import Rules from './components/Rules';
import {
  ActivityPulseIcon,
  AlertCircleIcon,
  AppGridIcon,
  BellIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentIcon,
  FileTextIcon,
  LogoSparkIcon,
  MessageCircleIcon,
  PlayIcon,
  PulseLineIcon,
  SettingsIcon,
  ShieldCheckIcon,
  TeamIcon,
  UploadIcon,
} from './components/Icons';
import {
  ACTIVE_LOGS,
  DEMO_FILE_NAME,
  DEMO_RESULT,
  INITIAL_LOGS,
  LIVE_LOG_TAIL,
} from './mockData';
import './styles.css';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const STATUS_COLORS = {
  completed: 'var(--green-bright)',
  processing: 'var(--blue-bright)',
  pending: '#fcd34d',
  failed: 'var(--red)',
};

function formatTimestamp(value) {
  if (!value) {
    return 'Waiting for processing';
  }

  const date = new Date(value);
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatRelativeTime(value) {
  if (!value) {
    return 'just now';
  }

  const now = Date.now();
  const target = new Date(value).getTime();
  const diffSeconds = Math.max(Math.round((now - target) / 1000), 0);

  if (diffSeconds < 60) {
    return 'just now';
  }

  const diffMinutes = Math.round(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  }

  const diffDays = Math.round(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
}

function App() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);
  const [resultMeta, setResultMeta] = useState(null);
  const [message, setMessage] = useState('');
  const [section, setSection] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(false);
  const [activeFileName, setActiveFileName] = useState('');
  const [isDarkToggleOn, setIsDarkToggleOn] = useState(true);
  const [demoRunId, setDemoRunId] = useState(0);
  const [toasts, setToasts] = useState([]);
  const [logLines, setLogLines] = useState(INITIAL_LOGS);
  const [dashboard, setDashboard] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');
  const [chatPreselectedJobId, setChatPreselectedJobId] = useState(null);

  const handleOpenChatForDocument = useCallback(
    (targetJobId) => {
      setChatPreselectedJobId(targetJobId || null);
      setSection('chat');
    },
    [],
  );

  const clearChatPreselectedJobId = useCallback(() => {
    setChatPreselectedJobId(null);
  }, []);
  const hasActiveWorkflow = Boolean(jobId) || isLoading || status === 'processing' || status === 'pending';

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      if (!response.ok) {
        setBackendStatus('offline');
        return;
      }

      setBackendStatus('online');
    } catch (error) {
      setBackendStatus('offline');
    }
  };

  const fetchDashboardSummary = async () => {
    try {
      const response = await fetch(`${API_BASE}/dashboard`);
      if (!response.ok) {
        setBackendStatus('offline');
        return;
      }

      const data = await response.json();
      setDashboard(data);
      setBackendStatus('online');
    } catch (error) {
      setBackendStatus('offline');
    }
  };

  useEffect(() => {
    if (!hasActiveWorkflow) {
      setLogLines(INITIAL_LOGS);
      return undefined;
    }

    setLogLines(ACTIVE_LOGS);
    let index = 0;
    const intervalId = window.setInterval(() => {
      if (index >= LIVE_LOG_TAIL.length) {
        window.clearInterval(intervalId);
        return;
      }

      setLogLines((currentLines) => [...currentLines, LIVE_LOG_TAIL[index]]);
      index += 1;
    }, 1800);

    return () => window.clearInterval(intervalId);
  }, [hasActiveWorkflow]);

  useEffect(() => {
    void checkBackendHealth();
    void fetchDashboardSummary();
    const intervalId = window.setInterval(() => {
      void checkBackendHealth();
    }, 15000);

    return () => window.clearInterval(intervalId);
  }, []);

  const pushToast = (type, toastMessage) => {
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setToasts((currentToasts) => [...currentToasts, { id, type, message: toastMessage }]);

    window.setTimeout(() => {
      setToasts((currentToasts) => currentToasts.filter((toast) => toast.id !== id));
    }, 3800);
  };

  const handleUploadSuccess = ({ id, fileName }) => {
    setJobId(id);
    setStatus('pending');
    setActiveFileName(fileName);
    setMessage('Queued for processing');
    setResult(null);
    setResultMeta(null);
    setIsLoading(true);
    setSection('results');
    pushToast('success', `${fileName} uploaded — analysis queued`);
    void fetchDashboardSummary();
    pollStatus(id);
  };

  const pollStatus = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/status/${id}`);
      const data = await response.json();
      setStatus(data.status);
      setMessage(data.message);
      setActiveFileName(data.filename);

      if (data.status === 'completed') {
        const resultResponse = await fetch(`${API_BASE}/result/${id}`);
        const resultData = await resultResponse.json();
        setResult(resultData.result);
        setResultMeta({
          filename: resultData.filename,
          createdAt: resultData.created_at,
          updatedAt: resultData.updated_at,
        });
        setActiveFileName(resultData.filename);
        setIsLoading(false);
        pushToast('success', 'Processing complete — results ready');
        void fetchDashboardSummary();
      } else if (data.status === 'processing' || data.status === 'pending') {
        window.setTimeout(() => pollStatus(id), 1200);
      }
    } catch (error) {
      setMessage('Unable to reach backend. Check that the API is running.');
      setIsLoading(false);
      pushToast('error', 'Unable to reach backend');
    }
  };

  const runDemo = () => {
    setSection('upload');
    setJobId('demo-contract-q1-2026');
    setStatus('processing');
    setMessage('Loading demo workflow');
    setResult(null);
    setResultMeta(null);
    setIsLoading(true);
    setActiveFileName(DEMO_FILE_NAME);
    setDemoRunId((current) => current + 1);
    setLogLines(ACTIVE_LOGS);
    pushToast('info', `Loading demo document: ${DEMO_FILE_NAME}`);
  };

  const handleDemoComplete = () => {
    setJobId('demo-contract-q1-2026');
    setStatus('processing');
    setMessage('OCR complete — analyzing compliance rules');

    window.setTimeout(() => {
      pushToast('success', 'Upload complete — starting analysis pipeline');
    }, 150);

    window.setTimeout(() => {
      pushToast('info', 'OCR complete — 1,847 tokens extracted');
    }, 1500);

    window.setTimeout(() => {
      setResult(DEMO_RESULT);
      setResultMeta({
        filename: DEMO_RESULT.metadata.filename,
        createdAt: DEMO_RESULT.metadata.uploaded_at,
        updatedAt: DEMO_RESULT.metadata.processed_at,
      });
      setStatus('completed');
      setMessage('Compliance check finished — score: 89/100');
      setIsLoading(false);
      setSection('results');
      pushToast('success', 'Compliance check finished — score: 89/100');
    }, 3400);
  };

  const handleExportReport = () => {
    if (!result) {
      pushToast('error', 'No result available to export');
      return;
    }

    const compliance = result.compliance;
    const reportLines = [
      'Regulus AI Compliance Report',
      `Document: ${activeFileName}`,
      `Status: ${status || 'completed'}`,
      '',
      'Extracted Text',
      result.text,
      '',
      'Entities',
      ...Object.entries(result.entities || {}).map(([key, value]) => `${key}: ${String(value)}`),
      '',
      'Metadata',
      ...Object.entries(result.metadata || {}).map(([key, value]) => `${key}: ${String(value ?? '')}`),
      '',
      'Issues',
      ...(result.issues || []).map((issue) => `${issue.severity} ${issue.rule}: ${issue.description}`),
    ];

    if (compliance) {
      reportLines.push(
        '',
        `Compliance Score: ${compliance.score}/100 — ${compliance.label}`,
        `Summary: ${compliance.summary}`,
        `Generated by: ${compliance.llm_provider}${compliance.llm_model ? ` (${compliance.llm_model})` : ''}`,
        '',
        'Compliance Findings',
        ...(compliance.findings || []).map((finding) =>
          `[${finding.status?.toUpperCase()}] ${finding.severity} ${finding.rule_id} (${finding.framework}): ${finding.explanation}`,
        ),
      );
    }

    const reportText = reportLines.join('\n');

    const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${activeFileName.replace(/\.[^.]+$/, '') || 'regulus-report'}-report.txt`;
    anchor.click();
    URL.revokeObjectURL(url);
    pushToast('success', 'Compliance report exported');
  };

  const handleReanalyze = () => {
    setSection('upload');
    pushToast('info', 'Ready for another analysis run');
  };

  const navItems = [
    { key: 'dashboard', label: 'Dashboard', icon: <AppGridIcon /> },
    { key: 'upload', label: 'Ingest', icon: <UploadIcon /> },
    { key: 'rules', label: 'Rules', icon: <ShieldCheckIcon /> },
    { key: 'chat', label: 'Chat', icon: <MessageCircleIcon /> },
    { key: 'results', label: 'Results', icon: <FileTextIcon /> },
  ];

  const sidebarSections = [
    {
      label: 'Workspace',
      items: [
        { key: 'dashboard', label: 'Overview', icon: <AppGridIcon /> },
        { key: 'upload', label: 'Document Ingest', icon: <UploadIcon /> },
        { key: 'rules', label: 'Compliance Rules', icon: <ShieldCheckIcon /> },
        { key: 'chat', label: 'Document Chat', icon: <MessageCircleIcon /> },
        { key: 'results', label: 'Results', icon: <FileTextIcon />, badge: '3' },
      ],
    },
    {
      label: 'Analytics',
      items: [
        { key: null, label: 'Audit Trail', icon: <PulseLineIcon /> },
        { key: null, label: 'Reports', icon: <ActivityPulseIcon /> },
        { key: null, label: 'Alerts', icon: <AlertCircleIcon />, badge: '3' },
      ],
    },
    {
      label: 'Settings',
      items: [
        { key: null, label: 'Configuration', icon: <SettingsIcon /> },
        { key: null, label: 'Team', icon: <TeamIcon /> },
      ],
    },
  ];

  const statIcons = {
    document: DocumentIcon,
    check: CheckCircleIcon,
    alert: AlertCircleIcon,
    pulse: PulseLineIcon,
  };

  const dashboardStats = [
    {
      label: 'Docs Processed',
      value: String(dashboard?.total_jobs ?? 0),
      change: `${dashboard?.completed_jobs ?? 0} completed`,
      changeType: 'up',
      accent: 'linear-gradient(90deg,#3b82f6,#06b6d4)',
      iconBackground: 'rgba(59,130,246,0.1)',
      iconColor: '#60a5fa',
      iconKey: 'document',
      valueColor: 'var(--blue-bright)',
    },
    {
      label: 'Avg. Score',
      value: `${dashboard?.average_score ?? 0}%`,
      change: `${dashboard?.processing_jobs ?? 0} processing now`,
      changeType: 'up',
      accent: 'linear-gradient(90deg,#10b981,#34d399)',
      iconBackground: 'rgba(16,185,129,0.1)',
      iconColor: '#34d399',
      iconKey: 'check',
      valueColor: 'var(--green-bright)',
    },
    {
      label: 'Detected Issues',
      value: String(dashboard?.total_issues ?? 0),
      change: `${dashboard?.failed_jobs ?? 0} failed`,
      changeType: 'down',
      accent: 'linear-gradient(90deg,#f59e0b,#fcd34d)',
      iconBackground: 'rgba(245,158,11,0.1)',
      iconColor: '#fcd34d',
      iconKey: 'alert',
      valueColor: '#fcd34d',
    },
    {
      label: 'Pending Jobs',
      value: String((dashboard?.pending_jobs ?? 0) + (dashboard?.processing_jobs ?? 0)),
      change: `${dashboard?.pending_jobs ?? 0} queued`,
      changeType: 'up',
      accent: 'linear-gradient(90deg,#6b21a8,#a855f7)',
      iconBackground: 'rgba(168,85,247,0.1)',
      iconColor: '#c4b5fd',
      iconKey: 'pulse',
      valueColor: '#c4b5fd',
    },
  ];

  const recentActivity = (dashboard?.recent_jobs || []).map((job) => {
    const color = STATUS_COLORS[job.status] || 'var(--blue-bright)';
    const description =
      job.status === 'completed'
        ? `completed — ${job.issue_count} issue${job.issue_count === 1 ? '' : 's'}`
        : job.status === 'processing'
          ? 'is processing'
          : job.status === 'pending'
            ? 'is queued'
            : 'requires attention';
    const scoreText = job.score != null ? ` · Score: ${job.score}%` : '';

    return {
      title: job.filename,
      description,
      time: `${formatRelativeTime(job.updated_at || job.created_at)}${scoreText}`,
      color,
    };
  });

  return (
    <div id="app" className="app-container">
      <header>
        <a className="logo" href="#" onClick={(event) => event.preventDefault()}>
          <div className="logo-mark">
            <LogoSparkIcon width={20} height={20} />
          </div>
          <span className="logo-text">
            Regulus<span>AI</span>
          </span>
        </a>

        <nav className="header-nav" aria-label="Primary">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={`nav-item ${section === item.key ? 'active' : ''}`}
              onClick={() => setSection(item.key)}
              type="button"
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="header-right">
          <div className="status-pill">
            <div className={`status-dot status-dot-${backendStatus}`}></div>
            {backendStatus === 'online'
              ? 'Backend Connected'
              : backendStatus === 'offline'
                ? 'Backend Offline'
                : 'Checking Backend'}
          </div>

          <div className="toggle-wrap">
            <span className="toggle-label">Dark</span>
            <button
              type="button"
              className={`toggle ${isDarkToggleOn ? 'on' : ''}`}
              id="darkToggle"
              aria-label="Toggle dark mode appearance"
              onClick={() => setIsDarkToggleOn((current) => !current)}
            />
          </div>

          <button
            type="button"
            className="icon-btn"
            title="Notifications"
            aria-label="Show notifications"
            onClick={() => pushToast('info', 'You have 3 new compliance alerts.')}
          >
            <BellIcon />
          </button>

          <div className="avatar" title="Regulus AI">
            RA
          </div>
        </div>
      </header>

      <div className="body-wrap">
        <aside>
          {sidebarSections.map((sidebarSection) => (
            <div key={sidebarSection.label}>
              <div className="sidebar-section-label">{sidebarSection.label}</div>
              {sidebarSection.items.map((item) => {
                const isInteractive = Boolean(item.key);
                const isActive = item.key && section === item.key;

                return (
                  <button
                    key={`${sidebarSection.label}-${item.label}`}
                    className={`sidebar-item ${isActive ? 'active' : ''}`}
                    onClick={() => {
                      if (isInteractive) {
                        setSection(item.key);
                      }
                    }}
                    type="button"
                  >
                    {item.icon}
                    {item.label}
                    {item.badge ? <span className="sidebar-badge">{item.badge}</span> : null}
                  </button>
                );
              })}
            </div>
          ))}
        </aside>

        <main>
          {backendStatus === 'offline' ? (
            <div className="health-banner">
              Backend is offline. Start FastAPI on `http://127.0.0.1:8000` before uploading files.
            </div>
          ) : null}

          {section === 'dashboard' ? (
            <section id="section-dashboard">
              <div className="page-header">
                <div>
                  <div className="page-title">Compliance Overview</div>
                  <div className="page-subtitle">
                    Last updated {formatTimestamp(new Date().toISOString())} ·{' '}
                    {(dashboard?.pending_jobs ?? 0) + (dashboard?.processing_jobs ?? 0)} documents queued
                  </div>
                </div>

                <div className="page-actions">
                  <button className="btn btn-secondary" type="button" onClick={() => setSection('upload')}>
                    <UploadIcon />
                    Upload Document
                  </button>
                  <button className="btn btn-primary" type="button" onClick={runDemo}>
                    <PlayIcon />
                    Run Demo
                  </button>
                </div>
              </div>

              <div className="stats-row">
                {dashboardStats.map((stat) => {
                  const IconComponent = statIcons[stat.iconKey];

                  return (
                    <div key={stat.label} className="stat-card" style={{ '--accent-line': stat.accent }}>
                      <div className="stat-icon" style={{ background: stat.iconBackground }}>
                        <IconComponent color={stat.iconColor} />
                      </div>
                      <div className="stat-label">{stat.label}</div>
                      <div className="stat-value" style={{ color: stat.valueColor }}>
                        {stat.value}
                      </div>
                      <div className={`stat-change ${stat.changeType}`}>
                        {stat.changeType === 'up' ? <CheckCircleIcon width={12} height={12} /> : <ClockIcon width={12} height={12} />}
                        {stat.change}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="two-col">
                <div className="card">
                  <div className="card-header">
                    <div className="card-title">
                      <ClockIcon color="var(--cyan-bright)" />
                      Agent Workflow
                    </div>
                    <span className={`badge ${hasActiveWorkflow ? 'badge-green' : 'badge-muted'}`}>
                      {hasActiveWorkflow ? 'Live' : 'Idle'}
                    </span>
                  </div>
                  <div className="card-body">
                    <div className="pipeline-viz">
                      <div className={`pipeline-step ${hasActiveWorkflow ? 'done' : ''}`}>
                        <div className="step-node">
                          <UploadIcon color="#22d3ee" />
                        </div>
                        <div className="step-label">Ingest</div>
                      </div>
                      <div className={`pipeline-step ${hasActiveWorkflow ? 'done' : ''}`}>
                        <div className="step-node">
                          <DocumentIcon color="#22d3ee" />
                        </div>
                        <div className="step-label">OCR</div>
                      </div>
                      <div className={`pipeline-step ${hasActiveWorkflow ? 'active' : ''}`}>
                        <div className="step-node">
                          {hasActiveWorkflow ? <div className="spinner"></div> : <ClockIcon color="var(--text-muted)" />}
                        </div>
                        <div className="step-label">Reasoning</div>
                      </div>
                      <div className="pipeline-step">
                        <div className="step-node">
                          <CheckCircleIcon color="var(--text-muted)" />
                        </div>
                        <div className="step-label">Compliance</div>
                      </div>
                      <div className="pipeline-step">
                        <div className="step-node">
                          <FileTextIcon color="var(--text-muted)" />
                        </div>
                        <div className="step-label">Report</div>
                      </div>
                    </div>

                    <div className="process-log" id="liveLog">
                      {logLines.map((line) => (
                        <div key={`${line.time}-${line.message}`} className="log-line">
                          <span className="log-time">{line.time}</span>
                          <span className={`log-msg ${line.type}`}>{line.message}</span>
                        </div>
                      ))}
                    </div>

                    {jobId ? (
                      <div className="job-status-grid">
                        <div className="job-status-item">
                          <span className="job-status-label">Job ID</span>
                          <span className="job-status-value">{jobId}</span>
                        </div>
                        <div className="job-status-item">
                          <span className="job-status-label">Status</span>
                          <span className="job-status-value text-capitalize">{status || 'idle'}</span>
                        </div>
                        <div className="job-status-item job-status-wide">
                          <span className="job-status-label">Message</span>
                          <span className="job-status-value">{message || 'Waiting for the next document run'}</span>
                        </div>
                      </div>
                    ) : (
                      <div className="job-status-grid">
                        <div className="job-status-item job-status-wide">
                          <span className="job-status-label">Status</span>
                          <span className="job-status-value">No active document run. Upload a file to start processing.</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="card">
                  <div className="card-header">
                    <div className="card-title">
                      <PulseLineIcon color="var(--cyan-bright)" />
                      Recent Activity
                    </div>
                  </div>
                  <div className="activity-list">
                    {(recentActivity.length ? recentActivity : []).map((activity) => (
                      <div key={`${activity.title}-${activity.time}`} className="activity-item">
                        <div className="activity-dot" style={{ background: activity.color }}></div>
                        <div className="activity-content">
                          <div className="activity-text">
                            <strong>{activity.title}</strong> {activity.description}
                          </div>
                          <div className="activity-time">{activity.time}</div>
                        </div>
                      </div>
                    ))}
                    {!recentActivity.length ? (
                      <div className="activity-item">
                        <div className="activity-dot" style={{ background: 'var(--text-muted)' }}></div>
                        <div className="activity-content">
                          <div className="activity-text">
                            <strong>No backend jobs yet</strong> Upload a document to populate live activity.
                          </div>
                          <div className="activity-time">Waiting for first document</div>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            </section>
          ) : null}

          {section === 'upload' ? (
            <section id="section-upload">
              <div className="page-header">
                <div>
                  <div className="page-title">Document Ingest</div>
                  <div className="page-subtitle">
                    Upload contracts, reports, or legal documents for compliance analysis
                  </div>
                </div>
              </div>

              <FileUpload
                apiBase={API_BASE}
                backendOnline={backendStatus === 'online'}
                demoRunId={demoRunId}
                onDemoComplete={handleDemoComplete}
                onToast={pushToast}
                onUploadSuccess={handleUploadSuccess}
              />
            </section>
          ) : null}

          {section === 'rules' ? (
            <section id="section-rules">
              <Rules
                apiBase={API_BASE}
                backendOnline={backendStatus === 'online'}
                onToast={pushToast}
              />
            </section>
          ) : null}

          {section === 'chat' ? (
            <section id="section-chat">
              <Chat
                apiBase={API_BASE}
                backendOnline={backendStatus === 'online'}
                defaultJobId={chatPreselectedJobId}
                onClearDefaultJobId={clearChatPreselectedJobId}
              />
            </section>
          ) : null}

          {section === 'results' ? (
            <section id="section-results">
              <div className="page-header">
                <div>
                  <div className="page-title">Analysis Results</div>
                  <div className="page-subtitle">
                    {activeFileName || 'No document selected'} · Processed {formatTimestamp(resultMeta?.updatedAt)}
                  </div>
                </div>
              </div>

              {isLoading ? (
                <div className="card">
                  <div className="card-body loading-card">
                    <div className="spinner spinner-lg"></div>
                    <p>{message || 'Running OCR, extraction, and compliance scoring...'}</p>
                  </div>
                </div>
              ) : result ? (
                <ResultDisplay
                  fileName={activeFileName}
                  result={result}
                  status={status}
                  jobId={jobId}
                  onExportReport={handleExportReport}
                  onReanalyze={handleReanalyze}
                  onChatAboutDocument={handleOpenChatForDocument}
                />
              ) : (
                <div className="card">
                  <div className="card-body empty-card">
                    <p>No results yet. Upload a document or run the demo to begin processing.</p>
                  </div>
                </div>
              )}
            </section>
          ) : null}
        </main>
      </div>

      <div id="toast-container">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast-${toast.type}`}>
            <div className="toast-icon">
              {toast.type === 'success' ? (
                <CheckCircleIcon color="#34d399" width={14} height={14} />
              ) : toast.type === 'error' ? (
                <AlertCircleIcon color="#fca5a5" width={14} height={14} />
              ) : (
                <BellIcon color="#60a5fa" width={14} height={14} />
              )}
            </div>
            <span>{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
