import { useMemo, useState } from 'react';
import {
  AlertCircleIcon,
  ChevronDownIcon,
  DownloadIcon,
  FileTextIcon,
  RefreshIcon,
  ShieldCheckIcon,
  TagIcon,
} from './Icons';
import { COMPLIANCE_ISSUES } from '../mockData';

function getEntityType(key, value) {
  const content = `${key} ${String(value)}`.toLowerCase();

  if (content.includes('article') || content.includes('clause') || content.includes('notice')) {
    return 'CLAUSE';
  }
  if (content.includes('name') || content.includes('person') || content.includes('dpo')) {
    return 'PERSON';
  }
  if (content.includes('org') || content.includes('company') || content.includes('party') || content.includes('client')) {
    return 'ORG';
  }
  if (content.includes('date') || content.includes('term') || /\b\d{4}\b/.test(content)) {
    return 'DATE';
  }
  if (content.includes('amount') || content.includes('price') || content.includes('cost') || value.includes('$')) {
    return 'AMOUNT';
  }
  return 'ORG';
}

function getEntityTypeClass(type) {
  if (type === 'PERSON') return 'et-person';
  if (type === 'ORG') return 'et-org';
  if (type === 'DATE') return 'et-date';
  if (type === 'AMOUNT') return 'et-amount';
  if (type === 'CLAUSE') return 'et-clause';
  return 'et-org';
}

function getConfidence(type, index) {
  const base = {
    ORG: 99,
    PERSON: 97,
    AMOUNT: 100,
    DATE: 100,
    CLAUSE: 96,
  };

  return `${Math.max((base[type] || 95) - index, 92)}%`;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildHighlightedContent(text, entities) {
  if (!text) {
    return 'No extracted text available.';
  }

  const matches = [];

  entities.forEach((entity, entityIndex) => {
    const query = String(entity.value || '').trim();

    if (!query || query.length < 3) {
      return;
    }

    const regex = new RegExp(escapeRegExp(query), 'gi');
    let regexMatch = regex.exec(text);

    while (regexMatch) {
      matches.push({
        start: regexMatch.index,
        end: regexMatch.index + regexMatch[0].length,
        text: regexMatch[0],
        entity,
        order: entityIndex,
      });
      regexMatch = regex.exec(text);
    }
  });

  matches.sort((left, right) => {
    if (left.start !== right.start) {
      return left.start - right.start;
    }

    const leftLength = left.end - left.start;
    const rightLength = right.end - right.start;
    return rightLength - leftLength;
  });

  const selectedMatches = [];
  let lastEnd = 0;

  matches.forEach((match) => {
    if (match.start >= lastEnd) {
      selectedMatches.push(match);
      lastEnd = match.end;
    }
  });

  if (!selectedMatches.length) {
    return text;
  }

  const nodes = [];
  let cursor = 0;

  selectedMatches.forEach((match) => {
    if (match.start > cursor) {
      nodes.push(text.slice(cursor, match.start));
    }

    nodes.push(
      <span
        key={`${match.start}-${match.end}-${match.order}`}
        className={`highlight-${match.entity.type.toLowerCase()}`}
      >
        {text.slice(match.start, match.end)}
      </span>,
    );

    cursor = match.end;
  });

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return nodes;
}

function ResultDisplay({ fileName, onExportReport, onReanalyze, result }) {
  const [openSections, setOpenSections] = useState({
    text: true,
    issues: true,
  });

  const entities = useMemo(() => {
    return Object.entries(result?.entities || {}).map(([key, value], index) => {
      const type = getEntityType(key, String(value));

      return {
        id: key,
        key,
        value: String(value),
        type,
        typeClass: getEntityTypeClass(type),
        confidence: getConfidence(type, index),
      };
    });
  }, [result]);

  const highlightedText = useMemo(() => buildHighlightedContent(result?.text || '', entities), [entities, result?.text]);

  const score = 89;
  const scoreCircumference = 238.76;
  const scoreOffset = scoreCircumference - (scoreCircumference * score) / 100;

  const toggleSection = (sectionKey) => {
    setOpenSections((sections) => ({
      ...sections,
      [sectionKey]: !sections[sectionKey],
    }));
  };

  return (
    <div className="results-shell">
      <div className="page-actions results-actions">
        <button className="btn btn-secondary" type="button" onClick={onExportReport}>
          <DownloadIcon />
          Export Report
        </button>
        <button className="btn btn-primary" type="button" onClick={onReanalyze}>
          <RefreshIcon />
          Re-analyze
        </button>
      </div>

      <div className="three-col">
        <div className="results-left">
          <div className="card collapsible">
            <button
              className={`collapsible-toggle ${openSections.text ? 'open' : ''}`}
              type="button"
              onClick={() => toggleSection('text')}
            >
              <span className="collapsible-title">
                <FileTextIcon color="var(--cyan-bright)" />
                Extracted Text
              </span>
              <ChevronDownIcon className="chevron" />
            </button>
            <div className={`collapsible-body ${openSections.text ? 'open' : ''}`}>
              <div className="extracted-text">{highlightedText}</div>
            </div>
          </div>

          <div className="card collapsible">
            <button
              className={`collapsible-toggle ${openSections.issues ? 'open' : ''}`}
              type="button"
              onClick={() => toggleSection('issues')}
            >
              <span className="collapsible-title">
                <AlertCircleIcon color="#fcd34d" />
                Compliance Issues
                <span className="badge badge-amber">3 found</span>
              </span>
              <ChevronDownIcon className="chevron" />
            </button>
            <div className={`collapsible-body ${openSections.issues ? 'open' : ''}`}>
              <table className="issues-table">
                <thead>
                  <tr>
                    <th>Severity</th>
                    <th>Rule</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {COMPLIANCE_ISSUES.map((issue) => (
                    <tr key={issue.rule}>
                      <td>
                        <span className={`severity-dot ${issue.severityClass}`}>{issue.severity}</span>
                      </td>
                      <td>
                        <code className="rule-code">{issue.rule}</code>
                      </td>
                      <td className="issue-description">{issue.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="results-right">
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <ShieldCheckIcon color="var(--cyan-bright)" />
                Compliance Score
              </div>
            </div>
            <div className="compliance-score-ring">
              <div className="score-ring-wrap">
                <svg width="90" height="90" viewBox="0 0 90 90">
                  <circle cx="45" cy="45" r="38" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
                  <circle
                    cx="45"
                    cy="45"
                    r="38"
                    fill="none"
                    stroke="url(#scoreGrad)"
                    strokeWidth="8"
                    strokeDasharray={scoreCircumference}
                    strokeDashoffset={scoreOffset}
                    strokeLinecap="round"
                  />
                  <defs>
                    <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="100%" stopColor="#34d399" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="score-text">
                  <div className="score-num" style={{ color: 'var(--green-bright)' }}>
                    {score}
                  </div>
                  <div className="score-pct">/ 100</div>
                </div>
              </div>

              <div className="score-info">
                <div className="score-label">Mostly Compliant</div>
                <div className="score-sub">3 issues require attention before approval</div>
                <div className="score-badges">
                  <span className="badge badge-green">GDPR ✓</span>
                  <span className="badge badge-amber">SOC2 ~</span>
                  <span className="badge badge-green">ISO 27001 ✓</span>
                </div>
                <div className="result-file-name">{fileName}</div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <TagIcon color="var(--cyan-bright)" />
                Extracted Entities
                <span className="badge badge-blue">{entities.length}</span>
              </div>
            </div>
            <div className="entity-list">
              {entities.map((entity) => (
                <div key={entity.id} className="entity-row">
                  <span className={`entity-type ${entity.typeClass}`}>{entity.type}</span>
                  <div className="entity-main">
                    <div className="entity-value">{entity.value}</div>
                    <div className="entity-meta">{entity.key}</div>
                  </div>
                  <span className="entity-confidence">{entity.confidence}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResultDisplay;
