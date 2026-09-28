import { useState } from 'react'
import { loadSampleWorkbook, normalizeWorkbook } from './workbooks'
import type { NormalizedWorkbook, PerformanceRecord } from './workbooks'

const whole = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const decimal = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 })

function Icon({
  name,
  size = 20,
}: {
  name: 'spark' | 'upload' | 'arrow' | 'file' | 'check' | 'warning'
  size?: number
}) {
  const paths = {
    spark: (
      <>
        <path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z" />
        <path d="m19 17 .7 2.3L22 20l-2.3.7L19 23l-.7-2.3L16 20l2.3-.7L19 17Z" />
      </>
    ),
    upload: (
      <>
        <path d="M12 16V3m0 0L7 8m5-5 5 5" />
        <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
      </>
    ),
    arrow: (
      <>
        <path d="M4 12h16m-7-7 7 7-7 7" />
      </>
    ),
    file: (
      <>
        <path d="M7 2h7l5 5v13a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z" />
        <path d="M14 2v6h5M8 13h8m-8 4h8" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    warning: (
      <>
        <path d="M12 3 2 21h20L12 3Z" />
        <path d="M12 9v5m0 3h.01" />
      </>
    ),
  }
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  )
}

function MetricCard({
  label,
  value,
  unit,
  note,
  tone,
}: {
  label: string
  value: string
  unit: string
  note: string
  tone?: 'accent'
}) {
  return (
    <div className={`metric-card ${tone === 'accent' ? 'metric-card-accent' : ''}`}>
      <span className="metric-label">{label}</span>
      <div className="metric-value">
        {value}
        <span>{unit}</span>
      </div>
      <p>{note}</p>
    </div>
  )
}

function RecordTable({ records }: { records: PerformanceRecord[] }) {
  const maxThroughput = Math.max(...records.map((record) => record.throughput), 1)
  return (
    <div className="table-scroll">
      <table aria-label="Normalized configurations">
        <thead>
          <tr>
            <th scope="col">Batch</th>
            <th scope="col">
              Throughput <span>tokens/s</span>
            </th>
            <th scope="col">
              Per box <span>tokens/s</span>
            </th>
            <th scope="col">
              TTFT <span>ms</span>
            </th>
            <th scope="col">
              Gen speed <span>tokens/s/user</span>
            </th>
            <th scope="col">
              Requests <span>/ minute</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {records.map((record, index) => (
            <tr key={`${record.batch_size}-${index}`}>
              <th scope="row">
                <span className="batch-pill">{record.batch_size}</span>
              </th>
              <td>
                <div className="bar-cell">
                  <span className="bar-track" aria-hidden="true">
                    <span
                      style={{
                        width: `${Math.max(4, (record.throughput / maxThroughput) * 100)}%`,
                      }}
                    />
                  </span>
                  <strong>{whole.format(record.throughput)}</strong>
                </div>
              </td>
              <td>{whole.format(record.throughput_per_box)}</td>
              <td>{whole.format(record.ttft_ms)}</td>
              <td>{decimal.format(record.gen_speed)}</td>
              <td>{whole.format(record.rpm)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function WorkbookPreview({ data, source }: { data: NormalizedWorkbook; source: string }) {
  const records = data.records
  const peak = records.reduce(
    (best, record) => (record.throughput > best.throughput ? record : best),
    records[0],
  )
  const fastestStart = Math.min(...records.map((record) => record.ttft_ms))
  const topGeneration = Math.max(...records.map((record) => record.gen_speed))
  const inputLengths = [...new Set(records.map((record) => record.input_length))]
  const outputLengths = [...new Set(records.map((record) => record.output_length))]
  const cacheLevels = [...new Set(records.map((record) => record.cache_percentage))]

  return (
    <section className="preview" aria-labelledby="preview-title">
      <div className="preview-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" /> Normalized preview
          </div>
          <h2 id="preview-title">{data.model_name}</h2>
          <div className="preview-meta">
            <span className="profile-badge">Profile {data.profile_id}</span>
            <span>{data.record_count} configurations</span>
            <span className="meta-divider" aria-hidden="true" />
            <span title={source}>{source}</span>
          </div>
        </div>
        <span className="success-badge">
          <Icon name="check" size={15} /> Workbook ready
        </span>
      </div>

      <div className="metrics-grid">
        <MetricCard
          label="Peak throughput"
          value={whole.format(peak.throughput)}
          unit="tok/s"
          note={`At batch size ${peak.batch_size}`}
          tone="accent"
        />
        <MetricCard
          label="Fastest first token"
          value={whole.format(fastestStart)}
          unit="ms"
          note="Lowest projected TTFT"
        />
        <MetricCard
          label="Generation speed"
          value={decimal.format(topGeneration)}
          unit="tok/s"
          note="Fastest per user"
        />
      </div>

      <div className="details-grid">
        <div className="panel configuration-panel">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">Performance by configuration</div>
              <h3>Batch size changes the picture</h3>
            </div>
            <span className="panel-count">{records.length} rows</span>
          </div>
          <p className="panel-description">
            Compare projected throughput, response start, and generation speed across the normalized
            rows.
          </p>
          <RecordTable records={records} />
        </div>
        <aside className="panel context-panel" aria-label="Workbook context">
          <div className="eyebrow">Workbook context</div>
          <h3>What this projection covers</h3>
          <dl>
            <div>
              <dt>Input length</dt>
              <dd>{inputLengths.map((value) => whole.format(value)).join(', ')} tokens</dd>
            </div>
            <div>
              <dt>Output length</dt>
              <dd>{outputLengths.map((value) => whole.format(value)).join(', ')} tokens</dd>
            </div>
            <div>
              <dt>Cache share</dt>
              <dd>{cacheLevels.map((value) => `${decimal.format(value * 100)}%`).join(', ')}</dd>
            </div>
            <div>
              <dt>Batch sizes</dt>
              <dd>{records.map((record) => record.batch_size).join(' · ')}</dd>
            </div>
          </dl>
          <div className="projection-note">
            <span className="note-icon">
              <Icon name="warning" size={17} />
            </span>
            <p>
              These are workbook projections, not measured production results. Compare
              configurations before using them in a customer decision.
            </p>
          </div>
        </aside>
      </div>
    </section>
  )
}

export default function App() {
  const [workbook, setWorkbook] = useState<NormalizedWorkbook | null>(null)
  const [source, setSource] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function loadWorkbook(getFile: () => Promise<File>) {
    setError(null)
    setWorkbook(null)
    setSource('')
    setLoading(true)
    try {
      const file = await getFile()
      const result = await normalizeWorkbook(file)
      setWorkbook(result)
      setSource(file.name)
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Something went wrong while loading this workbook.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="header-inner">
          <a className="brand" href="/" aria-label="Performance Studio home">
            <span className="brand-mark">
              <Icon name="spark" size={20} />
            </span>
            <span>
              PERFORMANCE<span className="brand-light">/STUDIO</span>
            </span>
          </a>
          <span className="header-tag">
            MODEL INTELLIGENCE <span className="tag-dot" /> 01
          </span>
        </div>
      </header>

      <main>
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-glow" aria-hidden="true" />
          <div className="hero-inner">
            <div className="hero-copy">
              <div className="hero-kicker">
                <span className="pulse-dot" /> WORKBOOK ANALYSIS, SIMPLIFIED
              </div>
              <h1 id="hero-title">
                From raw projections
                <br />
                to <em>real clarity.</em>
              </h1>
              <p>
                Upload a performance workbook and see the numbers that matter. Explore throughput,
                latency, and workload shape in one clear view.
              </p>
              <div className="hero-rule">
                <span>01</span>
                <span>Upload a workbook</span>
                <Icon name="arrow" size={16} />
                <span>02</span>
                <span>Explore the projection</span>
              </div>
            </div>
            <div className="hero-graphic" aria-hidden="true">
              <div className="graphic-grid" />
              <div className="graphic-orbit orbit-one" />
              <div className="graphic-orbit orbit-two" />
              <div className="graphic-core">
                <span>PERF</span>
                <strong>↗</strong>
              </div>
              <span className="graphic-label label-top">THROUGHPUT / TOK·S</span>
              <span className="graphic-label label-bottom">LATENCY / MS</span>
            </div>
          </div>
        </section>

        <div className="content-wrap">
          <section className="upload-section" aria-labelledby="upload-title">
            <div className="section-index">01 / INPUT</div>
            <div className="upload-layout">
              <div className="section-copy">
                <h2 id="upload-title">Start with a sweep.</h2>
                <p>
                  Choose an Excel workbook from your device, or explore the sample. Both are
                  analyzed through the same API.
                </p>
                <div className="format-hint">
                  <Icon name="file" size={17} />
                  <span>Accepts .xlsx performance workbooks</span>
                </div>
              </div>
              <div className="upload-card">
                <div className="upload-card-top">
                  <span className="upload-icon">
                    <Icon name="upload" size={26} />
                  </span>
                  <span className="step-label">SINGLE WORKBOOK · LIVE ANALYSIS</span>
                </div>
                <h3>Bring your data in</h3>
                <p>Your workbook is validated and normalized as soon as you choose it.</p>
                <label
                  className={`file-picker ${loading ? 'is-loading' : ''}`}
                  htmlFor="workbook-file"
                >
                  <Icon name="upload" size={18} />
                  {loading ? 'Analyzing workbook…' : 'Choose an Excel workbook'}
                  <input
                    id="workbook-file"
                    type="file"
                    accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    disabled={loading}
                    onChange={(event) => {
                      const file = event.currentTarget.files?.[0]
                      event.currentTarget.value = ''
                      if (file) void loadWorkbook(async () => file)
                    }}
                  />
                </label>
                <div className="upload-divider">
                  <span>or</span>
                </div>
                <button
                  className="sample-button"
                  type="button"
                  disabled={loading}
                  onClick={() => void loadWorkbook(loadSampleWorkbook)}
                >
                  Load sample workbook <Icon name="arrow" size={17} />
                </button>
                <div className="upload-footnote">Sample: Model A · Profile 1</div>
              </div>
            </div>
          </section>

          <div role="status" aria-live="polite" className="sr-only">
            {loading
              ? 'Analyzing workbook'
              : workbook
                ? `${workbook.model_name} workbook ready`
                : ''}
          </div>
          {error && (
            <div className="error-banner" role="alert">
              <span className="error-icon">
                <Icon name="warning" size={19} />
              </span>
              <div>
                <strong>We couldn’t load that workbook</strong>
                <p>{error}</p>
              </div>
              <button type="button" onClick={() => setError(null)} aria-label="Dismiss error">
                ×
              </button>
            </div>
          )}
          {loading && (
            <section className="loading-panel" aria-label="Loading workbook">
              <span className="loading-spinner" aria-hidden="true" />
              <div>
                <h2>Analyzing your workbook</h2>
                <p>Validating columns and normalizing performance records…</p>
              </div>
            </section>
          )}
          {workbook ? (
            <WorkbookPreview data={workbook} source={source} />
          ) : (
            !loading && (
              <section className="empty-panel" aria-labelledby="empty-title">
                <span className="empty-visual">
                  <Icon name="file" size={30} />
                </span>
                <div className="eyebrow">Your workspace is ready</div>
                <h2 id="empty-title">No workbook loaded</h2>
                <p>
                  Upload a performance sweep or load the sample to see its normalized summary here.
                </p>
              </section>
            )
          )}
        </div>
      </main>
      <footer className="site-footer">
        <span>PERFORMANCE / STUDIO</span>
        <span>Projection data should be validated before making deployment decisions.</span>
      </footer>
    </div>
  )
}
