import { useEffect, useMemo, useRef, useState } from 'react';
import {
  EditIcon,
  ListIcon,
  PlusIcon,
  RotateCounterClockwiseIcon,
  ShieldCheckIcon,
  TrashIcon,
} from './Icons';

const SEVERITY_OPTIONS = ['High', 'Medium', 'Low'];

const SEVERITY_BADGE_CLASS = {
  High: 'badge-red',
  Medium: 'badge-amber',
  Low: 'badge-green',
};

const EMPTY_FORM = {
  rule_id: '',
  framework: '',
  title: '',
  check: '',
  severity: 'Medium',
  is_enabled: true,
};

function Rules({ apiBase, backendOnline, onToast, demoMode = false, demoRules = null }) {
  const [rules, setRules] = useState(null);
  const [frameworkOptions, setFrameworkOptions] = useState([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingFrameworks, setIsLoadingFrameworks] = useState(false);
  const [filter, setFilter] = useState('all');
  const [editing, setEditing] = useState(null);
  const datalistId = useRef(`framework-suggestions-${Math.random().toString(36).slice(2)}`);

  const usingDemoRules = Boolean(demoMode && Array.isArray(demoRules) && demoRules.length);
  const effectiveRules = usingDemoRules ? demoRules : rules;

  const loadRules = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch(`${apiBase}/rules`);
      if (!response.ok) {
        throw new Error(`Failed to load rules (${response.status})`);
      }
      const data = await response.json();
      setRules(data);
    } catch (err) {
      setError(err.message || 'Could not load rules.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadFrameworks = async () => {
    setIsLoadingFrameworks(true);
    try {
      const response = await fetch(`${apiBase}/frameworks`);
      if (!response.ok) {
        throw new Error(`Failed to load frameworks (${response.status})`);
      }
      const data = await response.json();
      setFrameworkOptions(Array.isArray(data.frameworks) ? data.frameworks : []);
    } catch (err) {
      console.warn(err);
      setFrameworkOptions([]);
    } finally {
      setIsLoadingFrameworks(false);
    }
  };

  useEffect(() => {
    if (usingDemoRules) {
      return;
    }
    if (!backendOnline) {
      return;
    }
    void loadRules();
    void loadFrameworks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendOnline, usingDemoRules]);

  const frameworks = useMemo(() => {
    if (usingDemoRules || !backendOnline || frameworkOptions.length === 0) {
      if (!effectiveRules) return [];
      return Array.from(new Set(effectiveRules.map((rule) => rule.framework))).sort();
    }
    return frameworkOptions;
  }, [backendOnline, effectiveRules, frameworkOptions, usingDemoRules]);

  const filteredRules = useMemo(() => {
    if (!effectiveRules) return [];
    if (filter === 'all') return effectiveRules;
    return effectiveRules.filter((rule) => rule.framework === filter);
  }, [effectiveRules, filter]);

  const stats = useMemo(() => {
    if (!effectiveRules) return { total: 0, enabled: 0, defaults: 0, custom: 0 };
    return {
      total: effectiveRules.length,
      enabled: effectiveRules.filter((r) => r.is_enabled).length,
      defaults: effectiveRules.filter((r) => r.is_default).length,
      custom: effectiveRules.filter((r) => !r.is_default).length,
    };
  }, [effectiveRules]);

  const startCreate = () => {
    setEditing({ ...EMPTY_FORM, mode: 'create' });
  };

  const startEdit = (rule) => {
    setEditing({
      mode: 'edit',
      id: rule.id,
      rule_id: rule.rule_id,
      framework: rule.framework,
      title: rule.title,
      check: rule.check,
      severity: rule.severity,
      is_enabled: rule.is_enabled,
    });
  };

  const closeModal = () => setEditing(null);

  const handleSave = async (formValue) => {
    try {
      const url = formValue.mode === 'edit' ? `${apiBase}/rules/${formValue.id}` : `${apiBase}/rules`;
      const method = formValue.mode === 'edit' ? 'PUT' : 'POST';
      const body = {
        rule_id: formValue.rule_id,
        framework: formValue.framework,
        title: formValue.title,
        check: formValue.check,
        severity: formValue.severity,
        is_enabled: formValue.is_enabled,
      };

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        throw new Error(detail?.detail || `Save failed (${response.status})`);
      }

      onToast?.('success', formValue.mode === 'edit' ? 'Rule updated' : 'Rule created');
      closeModal();
      await loadRules();
    } catch (err) {
      onToast?.('error', err.message || 'Could not save rule');
    }
  };

  const handleDelete = async (rule) => {
    if (!window.confirm(`Delete rule "${rule.rule_id}"?`)) {
      return;
    }
    try {
      const response = await fetch(`${apiBase}/rules/${rule.id}`, { method: 'DELETE' });
      if (!response.ok && response.status !== 204) {
        throw new Error(`Delete failed (${response.status})`);
      }
      onToast?.('info', `Deleted ${rule.rule_id}`);
      await loadRules();
    } catch (err) {
      onToast?.('error', err.message || 'Could not delete rule');
    }
  };

  const handleToggleEnabled = async (rule) => {
    try {
      const response = await fetch(`${apiBase}/rules/${rule.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_enabled: !rule.is_enabled }),
      });
      if (!response.ok) {
        throw new Error(`Toggle failed (${response.status})`);
      }
      await loadRules();
    } catch (err) {
      onToast?.('error', err.message || 'Could not toggle rule');
    }
  };

  const handleRestoreDefaults = async () => {
    try {
      const response = await fetch(`${apiBase}/rules/restore-defaults`, { method: 'POST' });
      if (!response.ok) {
        throw new Error(`Restore failed (${response.status})`);
      }
      const data = await response.json();
      if (data.restored === 0) {
        onToast?.('info', 'All default rules already present');
      } else {
        onToast?.('success', `Restored ${data.restored} default rule(s)`);
      }
      await loadRules();
    } catch (err) {
      onToast?.('error', err.message || 'Could not restore defaults');
    }
  };

  return (
    <div className="rules-shell">
      <div className="page-header">
        <div>
          <div className="page-title">Compliance Rules</div>
          <div className="page-subtitle">
            Define what the agent checks for. Add custom rules, edit defaults, or wipe and restore.
          </div>
        </div>
        <div className="page-actions">
          <button
            className="btn btn-secondary"
            type="button"
            onClick={handleRestoreDefaults}
            disabled={!backendOnline || usingDemoRules}
          >
            <RotateCounterClockwiseIcon />
            Restore Defaults
          </button>
          <button className="btn btn-primary" type="button" onClick={startCreate} disabled={!backendOnline || usingDemoRules}>
            <PlusIcon />
            Add Rule
          </button>
        </div>
      </div>

      {usingDemoRules ? (
        <div className="card demo-callout">
          <div className="card-body">
            <strong>Demo rules preview</strong> These are the active checks used in the demo run. The real app loads editable rules from the backend, but the demo uses a stable local set so the walkthrough can show Rules, Results, and Chat together.
          </div>
        </div>
      ) : null}

      <div className="rules-stats">
        <div className="rules-stat">
          <span className="rules-stat-label">Total</span>
          <span className="rules-stat-value">{stats.total}</span>
        </div>
        <div className="rules-stat">
          <span className="rules-stat-label">Enabled</span>
          <span className="rules-stat-value" style={{ color: 'var(--green-bright)' }}>{stats.enabled}</span>
        </div>
        <div className="rules-stat">
          <span className="rules-stat-label">Defaults</span>
          <span className="rules-stat-value" style={{ color: 'var(--blue-bright)' }}>{stats.defaults}</span>
        </div>
        <div className="rules-stat">
          <span className="rules-stat-label">Custom</span>
          <span className="rules-stat-value" style={{ color: 'var(--cyan-bright)' }}>{stats.custom}</span>
        </div>
      </div>

      <div className="card">
        <div className="card-header rules-table-header">
          <div className="card-title">
            <ListIcon color="var(--cyan-bright)" />
            Rule Catalog
            <span className="badge badge-blue">{filteredRules.length}</span>
          </div>
          <div className="rules-filters">
            <button
              type="button"
              className={`framework-chip ${filter === 'all' ? 'framework-chip-active' : 'framework-chip-muted'}`}
              onClick={() => setFilter('all')}
            >
              <span>All</span>
            </button>
            {frameworks.map((framework) => (
              <button
                key={framework}
                type="button"
                className={`framework-chip ${filter === framework ? 'framework-chip-active' : 'framework-chip-muted'}`}
                onClick={() => setFilter(framework)}
              >
                <span>{framework}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="card-body">
          {error ? <p className="error-text">{error}</p> : null}

          {isLoading && !effectiveRules ? (
            <div className="loading-card">
              <div className="spinner spinner-lg" />
              <p>Loading rules…</p>
            </div>
          ) : null}

          {effectiveRules && filteredRules.length === 0 ? (
            <div className="empty-card">
              <p>No rules{filter !== 'all' ? ` in ${filter}` : ''} yet. Add one or restore defaults to get started.</p>
            </div>
          ) : null}

          {effectiveRules && filteredRules.length > 0 ? (
            <table className="issues-table rules-table">
              <thead>
                <tr>
                  <th>Enabled</th>
                  <th>Framework</th>
                  <th>Rule</th>
                  <th>Title</th>
                  <th>Severity</th>
                  <th>Type</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {filteredRules.map((rule) => (
                  <tr key={rule.id} className={rule.is_enabled ? '' : 'rule-row-disabled'}>
                    <td>
                      <button
                        type="button"
                          className={`toggle ${rule.is_enabled ? 'on' : ''}`}
                          onClick={() => handleToggleEnabled(rule)}
                          aria-label={`${rule.is_enabled ? 'Disable' : 'Enable'} ${rule.rule_id}`}
                          disabled={usingDemoRules}
                      />
                    </td>
                    <td>
                      <span className="framework-chip framework-chip-active rules-framework-chip">
                        <span>{rule.framework}</span>
                      </span>
                    </td>
                    <td>
                      <code className="rule-code">{rule.rule_id}</code>
                    </td>
                    <td className="issue-description rule-title-cell">{rule.title}</td>
                    <td>
                      <span className={`badge ${SEVERITY_BADGE_CLASS[rule.severity] || 'badge-muted'}`}>
                        {rule.severity}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${rule.is_default ? 'badge-blue' : 'badge-muted'}`}>
                        {rule.is_default ? 'Default' : 'Custom'}
                      </span>
                    </td>
                    <td>
                      <div className="rules-row-actions">
                        <button
                          className="icon-btn"
                          type="button"
                          title="Edit rule"
                          aria-label={`Edit ${rule.rule_id}`}
                          onClick={() => startEdit(rule)}
                          disabled={usingDemoRules}
                        >
                          <EditIcon width={16} height={16} />
                        </button>
                        <button
                          className="icon-btn icon-btn-danger"
                          type="button"
                          title="Delete rule"
                          aria-label={`Delete ${rule.rule_id}`}
                          onClick={() => handleDelete(rule)}
                          disabled={usingDemoRules}
                        >
                          <TrashIcon width={16} height={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </div>
      </div>

      {editing ? (
        <RuleModal
          formValue={editing}
          frameworks={frameworks}
          datalistId={datalistId.current}
          onCancel={closeModal}
          onSave={handleSave}
        />
      ) : null}
    </div>
  );
}

function RuleModal({ formValue, frameworks, datalistId, onCancel, onSave }) {
  const [draft, setDraft] = useState(formValue);
  const [submitting, setSubmitting] = useState(false);

  const updateField = (field, value) => {
    setDraft((current) => ({ ...current, [field]: value }));
  };

  const isValid = Boolean(
    draft.rule_id?.trim() && draft.framework?.trim() && draft.title?.trim() && draft.check?.trim(),
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!isValid) return;
    setSubmitting(true);
    try {
      await onSave(draft);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" onClick={onCancel}>
      <div className="modal-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <div className="card-title">
            <ShieldCheckIcon color="var(--cyan-bright)" />
            {draft.mode === 'edit' ? `Edit ${formValue.rule_id}` : 'New Rule'}
          </div>
          <button
            type="button"
            className="icon-btn"
            aria-label="Close modal"
            onClick={onCancel}
          >
            ✕
          </button>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          <label className="form-field">
            <span className="form-label">Rule ID</span>
            <input
              type="text"
              className="form-input"
              value={draft.rule_id}
              onChange={(event) => updateField('rule_id', event.target.value)}
              placeholder="e.g. HIPAA-164.312"
              required
              autoFocus={draft.mode === 'create'}
            />
          </label>

          <label className="form-field">
            <span className="form-label">Framework</span>
            <input
              type="text"
              className="form-input"
              list={datalistId}
              value={draft.framework}
              onChange={(event) => updateField('framework', event.target.value)}
              placeholder="e.g. GDPR, SOC2, HIPAA, Internal Policy"
              required
            />
            <datalist id={datalistId}>
              {frameworks.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </label>

          <label className="form-field">
            <span className="form-label">Title</span>
            <input
              type="text"
              className="form-input"
              value={draft.title}
              onChange={(event) => updateField('title', event.target.value)}
              placeholder="One-line rule name"
              required
            />
          </label>

          <label className="form-field">
            <span className="form-label">Check</span>
            <textarea
              className="form-input form-textarea"
              value={draft.check}
              onChange={(event) => updateField('check', event.target.value)}
              placeholder="Describe what the LLM should look for in the document. The clearer the check, the better the result."
              rows={4}
              required
            />
          </label>

          <div className="form-row">
            <label className="form-field">
              <span className="form-label">Severity</span>
              <select
                className="form-input"
                value={draft.severity}
                onChange={(event) => updateField('severity', event.target.value)}
              >
                {SEVERITY_OPTIONS.map((value) => (
                  <option key={value} value={value}>{value}</option>
                ))}
              </select>
            </label>

            <label className="form-field form-field-toggle">
              <span className="form-label">Enabled</span>
              <button
                type="button"
                className={`toggle ${draft.is_enabled ? 'on' : ''}`}
                onClick={() => updateField('is_enabled', !draft.is_enabled)}
                aria-label="Toggle enabled"
              />
            </label>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={!isValid || submitting}>
              {submitting ? 'Saving…' : draft.mode === 'edit' ? 'Save Changes' : 'Create Rule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Rules;
