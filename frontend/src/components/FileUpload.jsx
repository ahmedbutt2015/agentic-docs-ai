import { useEffect, useRef, useState } from 'react';
import {
  CheckCircleIcon,
  PlusIcon,
  SettingsIcon,
  ShieldCheckIcon,
  UploadIcon,
} from './Icons';
import { PROCESSING_OPTIONS } from '../processingOptions';

function createRow(file, index) {
  const extension = file.name.split('.').pop()?.toLowerCase() || 'file';
  const kind = extension === 'pdf' ? 'pdf' : extension === 'docx' ? 'docx' : extension === 'xlsx' ? 'xlsx' : extension === 'txt' ? 'txt' : 'png';

  return {
    id: `${Date.now()}-${index}-${file.name}`,
    file,
    extension,
    kind,
    name: file.name,
    sizeLabel: file.size ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : '—',
    progress: 0,
    statusLabel: 'Uploading',
    badgeClass: 'badge-blue',
  };
}

function FileUpload({ apiBase, backendOnline, demoRunId, onDemoComplete, onToast, onUploadSuccess }) {
  const inputRef = useRef(null);
  const [uploadRows, setUploadRows] = useState([]);
  const [error, setError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [optionState, setOptionState] = useState(
    PROCESSING_OPTIONS.reduce((accumulator, option) => ({ ...accumulator, [option.key]: option.enabled }), {}),
  );
  const [availableFrameworks, setAvailableFrameworks] = useState([]);
  const [frameworkState, setFrameworkState] = useState({});
  const complianceScoringEnabled = Boolean(optionState.run_compliance_check);

  useEffect(() => {
    if (!backendOnline) {
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch(`${apiBase}/frameworks`);
        if (!response.ok) return;
        const data = await response.json();
        if (cancelled) return;
        const list = Array.isArray(data?.frameworks) ? data.frameworks : [];
        setAvailableFrameworks(list);
        setFrameworkState((current) => {
          const next = {};
          list.forEach((name) => {
            next[name] = current[name] !== undefined ? current[name] : true;
          });
          return next;
        });
      } catch (err) {
        // backend probably offline; the inline warning will show
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBase, backendOnline]);

  const selectedFrameworks = Object.entries(frameworkState)
    .filter(([, isActive]) => isActive)
    .map(([name]) => name);

  const updateRow = (rowId, patch) => {
    setUploadRows((rows) => rows.map((row) => (row.id === rowId ? { ...row, ...patch } : row)));
  };

  const getUploadErrorMessage = async (response, uploadError) => {
    if (response) {
      try {
        const payload = await response.json();
        if (payload?.detail) {
          return typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail);
        }
      } catch {
        // Fall back to plain text below.
      }

      try {
        const text = await response.text();
        if (text) {
          return text;
        }
      } catch {
        // Ignore and use generic fallback below.
      }

      return `Upload failed with status ${response.status}.`;
    }

    if (uploadError instanceof TypeError) {
      return `Backend is not reachable at ${apiBase}. Start the FastAPI server and try again.`;
    }

    return uploadError?.message || 'Upload failed.';
  };

  const uploadFile = async (row) => {
    let progress = 0;
    const progressInterval = window.setInterval(() => {
      progress = Math.min(progress + Math.random() * 18 + 4, 92);
      updateRow(row.id, { progress });
    }, 120);

    try {
      const formData = new FormData();
      formData.append('file', row.file);
      formData.append('processing_options', JSON.stringify(optionState));
      if (complianceScoringEnabled && selectedFrameworks.length) {
        formData.append('frameworks', selectedFrameworks.join(','));
      }

      const response = await fetch(`${apiBase}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const message = await getUploadErrorMessage(response);
        throw new Error(message);
      }

      const data = await response.json();
      window.clearInterval(progressInterval);
      updateRow(row.id, {
        progress: 100,
        statusLabel: 'Done',
        badgeClass: 'badge-green',
      });
      onToast('info', `Processing started for ${row.name}`);
      onUploadSuccess({ id: data.id, fileName: row.name });
    } catch (uploadError) {
      window.clearInterval(progressInterval);
      updateRow(row.id, {
        progress: 100,
        statusLabel: 'Failed',
        badgeClass: 'badge-red',
      });
      const message = await getUploadErrorMessage(null, uploadError);
      setError(message);
      onToast('error', `Upload failed for ${row.name}`);
    }
  };

  const queueFiles = async (files) => {
    if (!files.length) {
      return;
    }

    setError('');
    const newRows = files.map((file, index) => createRow(file, index));
    setUploadRows((rows) => [...rows, ...newRows]);

    for (const row of newRows) {
      // eslint-disable-next-line no-await-in-loop
      await uploadFile(row);
    }
  };

  const handleSelectedFiles = (fileList) => {
    if (!backendOnline) {
      setError(`Backend is not reachable at ${apiBase}. Start the FastAPI server and try again.`);
      return;
    }

    const files = Array.from(fileList || []);
    void queueFiles(files);
  };

  useEffect(() => {
    if (!demoRunId) {
      return;
    }

    const demoRow = {
      id: `demo-${demoRunId}`,
      file: null,
      extension: 'pdf',
      kind: 'pdf',
      name: 'contract_q1_2026.pdf',
      sizeLabel: '2.3 MB · Demo file',
      progress: 0,
      statusLabel: 'Uploading',
      badgeClass: 'badge-blue',
    };

    setError('');
    setUploadRows([demoRow]);

    let progress = 0;
    const intervalId = window.setInterval(() => {
      progress = Math.min(progress + 14, 100);
      setUploadRows((rows) =>
        rows.map((row) =>
          row.id === demoRow.id
            ? {
                ...row,
                progress,
                statusLabel: progress >= 100 ? 'Done' : 'Uploading',
                badgeClass: progress >= 100 ? 'badge-green' : 'badge-blue',
              }
            : row,
        ),
      );

      if (progress >= 100) {
        window.clearInterval(intervalId);
        onDemoComplete();
      }
    }, 100);

    return () => window.clearInterval(intervalId);
  }, [demoRunId, onDemoComplete]);

  return (
    <div className="upload-layout">
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <UploadIcon color="var(--cyan-bright)" />
            Upload Documents
          </div>
          <button
            className="btn btn-secondary"
            type="button"
            disabled={!backendOnline}
            onClick={() => inputRef.current?.click()}
          >
            Browse Files
          </button>
          <input
            ref={inputRef}
            accept=".pdf,.docx,.xlsx,.png,.txt,.jpg,.jpeg"
            disabled={!backendOnline}
            hidden
            multiple
            type="file"
            onChange={(event) => {
              handleSelectedFiles(event.target.files);
              event.target.value = '';
            }}
          />
        </div>

        <div className="card-body">
          <button
            className={`upload-zone ${isDragging ? 'drag-over' : ''} ${backendOnline ? '' : 'disabled'}`}
            id="dropZone"
            type="button"
            onClick={() => {
              if (backendOnline) {
                inputRef.current?.click();
              }
            }}
            onDragOver={(event) => {
              if (!backendOnline) {
                return;
              }
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              if (backendOnline) {
                handleSelectedFiles(event.dataTransfer.files);
              }
            }}
          >
            <div className="upload-icon">
              <UploadIcon width={28} height={28} color="#60a5fa" strokeWidth={1.5} />
            </div>
            <div className="upload-title">Drop documents here</div>
            <div className="upload-sub">
              or <strong>click to browse</strong> · up to 50 MB per file
            </div>
            <div className="file-types">
              <span className="file-type-pill pill-pdf">PDF</span>
              <span className="file-type-pill pill-docx">DOCX</span>
              <span className="file-type-pill pill-xlsx">XLSX</span>
              <span className="file-type-pill pill-png">PNG</span>
              <span className="file-type-pill pill-txt">TXT</span>
            </div>
          </button>

          {!backendOnline ? (
            <p className="error-text upload-inline-warning">
              Backend is offline. Start `make backend` or `make dev` before uploading.
            </p>
          ) : null}

          <div className={`upload-progress ${uploadRows.length ? 'visible' : ''}`}>
            <div className="upload-list-spacer"></div>
            <div id="uploadList">
              {uploadRows.map((row) => (
                <div key={row.id} className="upload-file-row">
                  <div className={`file-icon-wrap ${row.kind}`}>{row.extension.toUpperCase()}</div>
                  <div className="file-info">
                    <div className="file-name">{row.name}</div>
                    <div className="file-meta">{row.sizeLabel}</div>
                  </div>
                  <div className="progress-bar-wrap upload-progress-bar">
                    <div className="progress-bar-fill" style={{ width: `${row.progress}%` }}></div>
                  </div>
                  <span className={`badge ${row.badgeClass}`}>{row.statusLabel}</span>
                </div>
              ))}
            </div>
          </div>

          {error ? <p className="error-text">{error}</p> : null}
        </div>
      </div>

      <div className="two-col">
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <SettingsIcon color="var(--cyan-bright)" />
              Processing Options
            </div>
          </div>
          <div className="card-body option-list">
            {PROCESSING_OPTIONS.map((option) => (
              <label key={option.key} className="option-row">
                <span className="option-label">{option.label}</span>
                <button
                  type="button"
                  className={`toggle ${optionState[option.key] ? 'on' : ''}`}
                  onClick={() =>
                    setOptionState((currentState) => ({
                      ...currentState,
                      [option.key]: !currentState[option.key],
                    }))
                  }
                />
              </label>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <ShieldCheckIcon color="var(--cyan-bright)" />
              Compliance Frameworks
            </div>
          </div>
          <div className="card-body framework-list">
            {!complianceScoringEnabled ? (
              <p className="framework-hint">
                Compliance scoring is off, so framework selection is currently skipped for this upload.
              </p>
            ) : null}
            {availableFrameworks.length === 0 ? (
              <p className="framework-hint">
                {backendOnline
                  ? 'No compliance rules defined yet. Open the Rules page to add some, or restore defaults.'
                  : 'Backend offline — frameworks will appear once the API is reachable.'}
              </p>
            ) : (
              <>
                {availableFrameworks.map((name) => {
                  const isActive = Boolean(frameworkState[name]);
                  return (
                    <button
                      key={name}
                      type="button"
                      className={`framework-chip ${isActive ? 'framework-chip-active' : 'framework-chip-muted'}`}
                      disabled={!complianceScoringEnabled}
                      onClick={() =>
                        setFrameworkState((current) => ({ ...current, [name]: !current[name] }))
                      }
                      aria-pressed={isActive}
                    >
                      {isActive ? (
                        <CheckCircleIcon width={14} height={14} color="var(--cyan-bright)" />
                      ) : (
                        <PlusIcon width={14} height={14} color="var(--text-muted)" />
                      )}
                      <span>{name}</span>
                    </button>
                  );
                })}
                {complianceScoringEnabled && selectedFrameworks.length === 0 ? (
                  <p className="framework-hint">
                    No frameworks selected — the backend will evaluate every framework with at least one enabled rule.
                  </p>
                ) : null}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default FileUpload;
