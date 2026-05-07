export const DEMO_FILE_NAME = 'contract_q1_2026.pdf';

export const DASHBOARD_STATS = [
  {
    label: 'Docs Processed',
    value: '1,284',
    change: '+48 this week',
    changeType: 'up',
    accent: 'linear-gradient(90deg,#3b82f6,#06b6d4)',
    iconBackground: 'rgba(59,130,246,0.1)',
    iconColor: '#60a5fa',
    iconKey: 'document',
    valueColor: 'var(--blue-bright)',
  },
  {
    label: 'Compliance Rate',
    value: '94.2%',
    change: '+2.1% vs last month',
    changeType: 'up',
    accent: 'linear-gradient(90deg,#10b981,#34d399)',
    iconBackground: 'rgba(16,185,129,0.1)',
    iconColor: '#34d399',
    iconKey: 'check',
    valueColor: 'var(--green-bright)',
  },
  {
    label: 'Open Issues',
    value: '17',
    change: '-5 from last week',
    changeType: 'down',
    accent: 'linear-gradient(90deg,#f59e0b,#fcd34d)',
    iconBackground: 'rgba(245,158,11,0.1)',
    iconColor: '#fcd34d',
    iconKey: 'alert',
    valueColor: '#fcd34d',
  },
  {
    label: 'Avg. Processing',
    value: '3.4s',
    change: '12% faster',
    changeType: 'up',
    accent: 'linear-gradient(90deg,#6b21a8,#a855f7)',
    iconBackground: 'rgba(168,85,247,0.1)',
    iconColor: '#c4b5fd',
    iconKey: 'pulse',
    valueColor: '#c4b5fd',
  },
];

export const RECENT_ACTIVITY = [
  {
    title: 'NDA_vendor_2026.pdf',
    description: 'passed compliance check',
    time: '2 minutes ago · Score: 98%',
    color: 'var(--green-bright)',
  },
  {
    title: 'employment_contract.docx',
    description: 'flagged — 2 issues',
    time: '18 minutes ago · Score: 76%',
    color: 'var(--amber)',
  },
  {
    title: 'Q1 audit batch',
    description: 'started — 12 documents',
    time: '1 hour ago',
    color: 'var(--blue-bright)',
  },
  {
    title: 'lease_agreement_NY.pdf',
    description: 'failed — GDPR violation',
    time: '3 hours ago · Score: 41%',
    color: 'var(--red)',
  },
  {
    title: 'Terms of Service v3',
    description: 'passed all checks',
    time: 'Yesterday · Score: 100%',
    color: 'var(--green-bright)',
  },
];

export const INITIAL_LOGS = [
  {
    time: 'Idle',
    type: 'info',
    message: 'Waiting for a document upload to start the pipeline.',
  },
];

export const ACTIVE_LOGS = [
  {
    time: '09:41:02',
    type: 'info',
    message: '[INGEST]  contract_q1_2026.pdf received (2.3 MB)',
  },
  {
    time: '09:41:03',
    type: 'proc',
    message: '[OCR]     Tesseract v5 — 4 pages detected',
  },
  {
    time: '09:41:05',
    type: 'success',
    message: '[OCR]     Extraction complete — 1,847 tokens',
  },
  {
    time: '09:41:06',
    type: 'info',
    message: '[REASON]  Sending to claude-haiku-4-5 for entity extraction…',
  },
];

export const LIVE_LOG_TAIL = [
  {
    time: '09:41:07',
    type: 'info',
    message: '[REASON]  Entities: 12 found (3 ORG, 1 PERSON, 2 DATE, 1 AMOUNT, 2 CLAUSE)',
  },
  {
    time: '09:41:09',
    type: 'proc',
    message: '[REASON]  Running compliance rules against GDPR, SOC2, ISO27001…',
  },
  {
    time: '09:41:11',
    type: 'warn',
    message: '[COMPLY]  WARN: GDPR-Art.28 — DPA missing for sub-processor relationship',
  },
  {
    time: '09:41:12',
    type: 'success',
    message: '[COMPLY]  PASS: GDPR-Art.13 — Privacy notice references present',
  },
  {
    time: '09:41:13',
    type: 'warn',
    message: '[COMPLY]  WARN: SOC2-CC6.1 — Encryption standard not specified',
  },
  {
    time: '09:41:14',
    type: 'success',
    message: '[COMPLY]  PASS: ISO-A.18.1 — Applicable legislation identified',
  },
  {
    time: '09:41:15',
    type: 'info',
    message: '[REPORT]  Generating compliance report… score 89/100',
  },
  {
    time: '09:41:16',
    type: 'success',
    message: '[DONE]    Analysis complete — 3 issues, 89/100',
  },
];

export const PROCESSING_OPTIONS = [
  { label: 'Enable OCR', enabled: true },
  { label: 'Entity Extraction', enabled: true },
  { label: 'Compliance Scoring', enabled: true },
  { label: 'GDPR Mode', enabled: false },
  { label: 'Auto-archive Results', enabled: true },
];

export const FRAMEWORKS = [
  { name: 'GDPR (EU 2016/679)', code: 'GDPR', active: true },
  { name: 'SOC 2 Type II', code: 'SOC2', active: true },
  { name: 'ISO 27001', code: 'ISO27001', active: true },
  { name: 'Add framework…', code: null, active: false, readOnly: true },
];

export const COMPLIANCE_ISSUES = [
  {
    severity: 'High',
    severity_class: 'sev-high',
    rule: 'GDPR-Art.28',
    description: 'Data Processing Agreement missing — required for sub-processors',
  },
  {
    severity: 'Medium',
    severity_class: 'sev-medium',
    rule: 'SOC2-CC6.1',
    description: 'No mention of encryption standards for data at rest',
  },
  {
    severity: 'Low',
    severity_class: 'sev-low',
    rule: 'ISO-A.9.4',
    description: 'Access control policy reference is outdated (v2.1 required)',
  },
];

export const DEMO_RESULT = {
  text: `This Service Agreement ("Agreement") is entered into as of January 1, 2026, by and between Acme Corporation, a Delaware corporation ("Service Provider"), and GlobalTech Ltd., a United Kingdom company ("Client").

1. SERVICES. Acme Corporation agrees to provide software development and consulting services as described in Schedule A. Payment terms are $45,000 USD per month, payable within 30 days of invoice.

2. CONFIDENTIALITY. Dr. Sarah Chen, as designated DPO for GlobalTech Ltd., shall oversee all data processing activities in accordance with Article 13 GDPR. Personal data of EU citizens shall not be transferred outside the EEA without appropriate safeguards.

3. TERM. This Agreement shall commence on January 1, 2026 and continue through December 31, 2026, unless earlier terminated by either party with 30 days' written notice.`,
  entities: {
    provider_company: 'Acme Corporation',
    client_company: 'GlobalTech Ltd.',
    designated_person: 'Dr. Sarah Chen',
    payment_amount: '$45,000 USD per month',
    effective_date: 'January 1, 2026',
    expiration_date: 'December 31, 2026',
    gdpr_clause: 'Article 13 GDPR',
    termination_notice: "30 days' written notice",
  },
  metadata: {
    filename: 'contract_q1_2026.pdf',
    extension: '.pdf',
    mime_type: 'application/pdf',
    file_size_bytes: 2411724,
    file_size_label: '2.3 MB',
    text_source: 'demo-pdf',
    uploaded_at: '2026-05-03T09:41:00Z',
    processed_at: '2026-05-03T09:41:16Z',
    character_count: 739,
    word_count: 108,
    line_count: 8,
    page_count: 4,
  },
  score: {
    value: 89,
    label: 'Ready',
    summary: 'The demo document includes extractable text, identified entities, and a small set of rule-based issues.',
    frameworks: [
      { name: 'Upload Metadata', status: 'complete' },
      { name: 'Text Extraction', status: 'complete' },
      { name: 'Entity Detection', status: 'complete' },
      { name: 'Deferred OCR/AI', status: 'pending' },
    ],
  },
  issues: COMPLIANCE_ISSUES,
};
