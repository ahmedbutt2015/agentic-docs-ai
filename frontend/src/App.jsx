import { useEffect, useState } from 'react';
import FileUpload from './components/FileUpload';
import ResultDisplay from './components/ResultDisplay';
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
  PlayIcon,
  PulseLineIcon,
  SettingsIcon,
  TeamIcon,
  UploadIcon,
} from './components/Icons';
import {
  DASHBOARD_STATS,
  DEMO_FILE_NAME,
  DEMO_RESULT,
  INITIAL_LOGS,
  LIVE_LOG_TAIL,
  RECENT_ACTIVITY,
} from './mockData';
import './styles.css';

const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

function App() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('');
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState('');
  const [section, setSection] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(false);
  const [activeFileName, setActiveFileName] = useState(DEMO_FILE_NAME);
  const [isDarkToggleOn, setIsDarkToggleOn] = useState(true);
  const [demoRunId, setDemoRunId] = useState(0);
  const [toasts, setToasts] = useState([]);
  const [logLines, setLogLines] = useState(INITIAL_LOGS);

  useEffect(() => {
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
    setIsLoading(true);
    setSection('results');
    pushToast('success', `${fileName} uploaded — analysis queued`);
    pollStatus(id);
  };

  const pollStatus = async (id) => {
    try {
      const response = await fetch(`${API_BASE}/status/${id}`);
      const data = await response.json();
      setStatus(data.status);
      setMessage(data.message);

      if (data.status === 'completed') {
        const resultResponse = await fetch(`${API_BASE}/result/${id}`);
        const resultData = await resultResponse.json();
        setResult(resultData.result);
        setIsLoading(false);
        pushToast('success', 'Processing complete — results ready');
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
    setIsLoading(true);
    setActiveFileName(DEMO_FILE_NAME);
    setDemoRunId((current) => current + 1);
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

    const reportText = [
      'Regulus AI Compliance Report',
      `Document: ${activeFileName}`,
      `Status: ${status || 'completed'}`,
      '',
      'Extracted Text',
      result.text,
      '',
      'Entities',
      ...Object.entries(result.entities || {}).map(([key, value]) => `${key}: ${String(value)}`),
    ].join('\n');

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
    { key: 'results', label: 'Results', icon: <FileTextIcon /> },
  ];

  const sidebarSections = [
    {
      label: 'Workspace',
      items: [
        { key: 'dashboard', label: 'Overview', icon: <AppGridIcon /> },
        { key: 'upload', label: 'Document Ingest', icon: <UploadIcon /> },
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
            <div className="status-dot"></div>
            Backend Connected
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
          {section === 'dashboard' ? (
            <section id="section-dashboard">
              <div className="page-header">
                <div>
                  <div className="page-title">Compliance Overview</div>
                  <div className="page-subtitle">Last updated May 3, 2026 · 3 documents queued</div>
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
                {DASHBOARD_STATS.map((stat) => {
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
                    <span className="badge badge-green">Live</span>
                  </div>
                  <div className="card-body">
                    <div className="pipeline-viz">
                      <div className="pipeline-step done">
                        <div className="step-node">
                          <UploadIcon color="#22d3ee" />
                        </div>
                        <div className="step-label">Ingest</div>
                      </div>
                      <div className="pipeline-step done">
                        <div className="step-node">
                          <DocumentIcon color="#22d3ee" />
                        </div>
                        <div className="step-label">OCR</div>
                      </div>
                      <div className="pipeline-step active">
                        <div className="step-node">
                          <div className="spinner"></div>
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
                    ) : null}
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
                    {RECENT_ACTIVITY.map((activity) => (
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
                demoRunId={demoRunId}
                onDemoComplete={handleDemoComplete}
                onToast={pushToast}
                onUploadSuccess={handleUploadSuccess}
              />
            </section>
          ) : null}

          {section === 'results' ? (
            <section id="section-results">
              <div className="page-header">
                <div>
                  <div className="page-title">Analysis Results</div>
                  <div className="page-subtitle">
                    {activeFileName} · Processed May 3, 2026 at 09:41 UTC
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
                  onExportReport={handleExportReport}
                  onReanalyze={handleReanalyze}
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
