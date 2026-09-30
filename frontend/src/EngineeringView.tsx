import { useEffect, useState } from 'react'
import { analyzeEngineering } from './engineering'
import type {
  AnomalyFlag,
  ConfigurationDiagnostic,
  EngineeringAnalysisResponse,
  EngineeringMetric,
  SourceReference,
} from './engineering'
import type { NormalizedWorkbook } from './workbooks'

const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 })

function sourceKey(source: SourceReference) {
  return `${source.workbook_index}:${source.record_index}`
}

function sourceLabel(source: SourceReference) {
  return `${source.model_name} · Profile ${source.profile_id} · normalized row ${source.record_index + 1}`
}

function metricLabel(name: string) {
  const labels: Record<string, string> = {
    throughput: 'Aggregate throughput',
    throughput_per_box: 'Per-box throughput',
    cached_throughput: 'Cached component',
    uncached_throughput: 'Uncached component',
    cached_throughput_per_box: 'Cached per box',
    uncached_throughput_per_box: 'Uncached per box',
    ttft_ms: 'Time to first token',
    gen_speed: 'Generation speed per user',
    rpm: 'Requests per minute',
    cached_share: 'Cached contribution',
    uncached_share: 'Uncached contribution',
    implied_box_capacity_ratio: 'Implied aggregate/per-box ratio',
  }
  return labels[name] ?? name.replaceAll('_', ' ')
}

function formatMetric(metric: EngineeringMetric) {
  const value =
    metric.unit === 'ratio' && metric.name !== 'implied_box_capacity_ratio'
      ? `${number.format(metric.value * 100)}%`
      : number.format(metric.value)
  return `${value}${metric.unit === 'ratio' ? '' : ` ${metric.unit}`}`
}

function flagsFor(configuration: ConfigurationDiagnostic, anomalies: AnomalyFlag[]) {
  const key = sourceKey(configuration.source)
  return anomalies.filter((flag) => flag.sources.some((source) => sourceKey(source) === key))
}

interface EngineeringViewProps {
  data: EngineeringAnalysisResponse
}

export default function EngineeringView({ data }: EngineeringViewProps) {
  const workbookOptions = [
    ...new Map(
      data.configurations.map((configuration) => [
        configuration.source.workbook_index,
        configuration.source,
      ]),
    ).values(),
  ].sort((a, b) => a.workbook_index - b.workbook_index)
  const [workbookIndex, setWorkbookIndex] = useState(workbookOptions[0]?.workbook_index ?? 0)
  const [selectedKey, setSelectedKey] = useState('')
  const [trendDimension, setTrendDimension] = useState<'batch_size' | 'cache_percentage'>(
    'batch_size',
  )
  const configurations = data.configurations.filter(
    (configuration) => configuration.source.workbook_index === workbookIndex,
  )
  const selected =
    configurations.find((configuration) => sourceKey(configuration.source) === selectedKey) ??
    configurations[0]
  const trends = data.trends.filter(
    (trend) =>
      trend.baseline.workbook_index === workbookIndex && trend.dimension === trendDimension,
  )
  const anomalies = data.anomalies.filter((flag) =>
    flag.sources.some((source) => source.workbook_index === workbookIndex),
  )

  function inspectSource(source: SourceReference) {
    setWorkbookIndex(source.workbook_index)
    setSelectedKey(sourceKey(source))
  }

  return (
    <section className="engineering-section" aria-labelledby="engineering-title">
      <div className="section-index">04 / ENGINEERING</div>
      <div className="engineering-heading">
        <div>
          <h2 id="engineering-title">Inspect the projection</h2>
          <p>
            Check configuration behavior and review flags before relying on a projected result.
            These values are estimates, not production measurements.
          </p>
        </div>
        <span className="profile-badge">
          {data.anomalies.length} review {data.anomalies.length === 1 ? 'flag' : 'flags'} across all
          sweeps
        </span>
      </div>

      <div className="panel engineering-panel">
        <label className="engineering-control">
          Engineering sweep
          <select
            value={workbookIndex}
            onChange={(event) => {
              setWorkbookIndex(Number(event.target.value))
              setSelectedKey('')
            }}
          >
            {workbookOptions.map((source) => (
              <option key={source.workbook_index} value={source.workbook_index}>
                {source.model_name} · Profile {source.profile_id} · sweep{' '}
                {source.workbook_index + 1}
              </option>
            ))}
          </select>
        </label>

        <h3>Configuration evidence</h3>
        <p className="panel-description">
          Select a row to inspect all sourced metrics. Cached and uncached throughput are reported
          components; their ratio does not establish a cache speedup.
        </p>
        <div className="table-scroll">
          <table aria-label="Engineering configurations">
            <thead>
              <tr>
                <th scope="col">Configuration</th>
                <th scope="col">Batch</th>
                <th scope="col">Cache</th>
                <th scope="col">
                  Aggregate <span>t/s</span>
                </th>
                <th scope="col">
                  Per box <span>t/s/hardware</span>
                </th>
                <th scope="col">
                  Cached <span>t/s</span>
                </th>
                <th scope="col">
                  Uncached <span>t/s</span>
                </th>
                <th scope="col">
                  TTFT <span>ms</span>
                </th>
                <th scope="col">
                  Gen speed <span>t/s/user</span>
                </th>
                <th scope="col">Review flags</th>
              </tr>
            </thead>
            <tbody>
              {configurations.map((configuration) => {
                const { record, source } = configuration
                return (
                  <tr
                    key={sourceKey(source)}
                    className={
                      selected && sourceKey(source) === sourceKey(selected.source)
                        ? 'engineering-row-selected'
                        : ''
                    }
                  >
                    <th scope="row">
                      <button
                        type="button"
                        className="engineering-row-button"
                        onClick={() => inspectSource(source)}
                      >
                        Row {source.record_index + 1}
                      </button>
                    </th>
                    <td>{record.batch_size}</td>
                    <td>{number.format(record.cache_percentage * 100)}%</td>
                    <td>{number.format(record.throughput)}</td>
                    <td>{number.format(record.throughput_per_box)}</td>
                    <td>{number.format(record.cached_throughput)}</td>
                    <td>{number.format(record.uncached_throughput)}</td>
                    <td>{number.format(record.ttft_ms)}</td>
                    <td>{number.format(record.gen_speed)}</td>
                    <td>{flagsFor(configuration, data.anomalies).length}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {selected && (
          <div id="engineering-detail" className="engineering-detail" aria-live="polite">
            <div className="engineering-detail-heading">
              <div>
                <div className="eyebrow">Source evidence</div>
                <h3>{sourceLabel(selected.source)}</h3>
                <p>
                  {number.format(selected.record.input_length)} input ·{' '}
                  {number.format(selected.record.output_length)} output tokens · batch{' '}
                  {selected.record.batch_size} ·{' '}
                  {number.format(selected.record.cache_percentage * 100)}% cached
                </p>
              </div>
              <span className="panel-count">{flagsFor(selected, data.anomalies).length} flags</span>
            </div>
            <dl className="engineering-metrics">
              {selected.metrics.map((metric) => (
                <div key={metric.name}>
                  <dt>{metricLabel(metric.name)}</dt>
                  <dd>{formatMetric(metric)}</dd>
                  <p>{metric.explanation}</p>
                </div>
              ))}
            </dl>
          </div>
        )}
      </div>

      <div className="engineering-lower">
        <div className="panel engineering-trends">
          <h3>Controlled trends</h3>
          <p className="panel-description">
            The API compares rows only when the other workload dimensions match.
          </p>
          <label className="engineering-control">
            Change to inspect
            <select
              value={trendDimension}
              onChange={(event) =>
                setTrendDimension(event.target.value as 'batch_size' | 'cache_percentage')
              }
            >
              <option value="batch_size">Batch size</option>
              <option value="cache_percentage">Cache setting</option>
            </select>
          </label>
          {trends.length ? (
            <div className="engineering-trend-list" aria-label="Engineering trends">
              {trends.map((trend, index) => (
                <div
                  key={`${sourceKey(trend.baseline)}-${sourceKey(trend.candidate)}-${trend.metric_name}-${index}`}
                >
                  <strong>{metricLabel(trend.metric_name)}</strong>
                  <p>{trend.explanation}</p>
                  <span>
                    Rows {trend.baseline.record_index + 1} → {trend.candidate.record_index + 1}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="engineering-empty">
              No controlled {trendDimension === 'batch_size' ? 'batch-size' : 'cache-setting'} pair
              exists in this sweep.
            </p>
          )}
        </div>

        <div className="panel engineering-flags">
          <h3>Review signals</h3>
          <p className="panel-description">
            A flag asks for investigation; it does not discard the projection.
          </p>
          {anomalies.length ? (
            <ul>
              {anomalies.map((flag, index) => (
                <li key={`${flag.code}-${index}`}>
                  <strong>{flag.rule}</strong>
                  <p>{flag.explanation}</p>
                  <div className="engineering-sources">
                    {flag.sources.map((source) => (
                      <a
                        key={sourceKey(source)}
                        href="#engineering-detail"
                        onClick={() => inspectSource(source)}
                      >
                        Inspect {sourceLabel(source)}
                      </a>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="engineering-empty">
              No review flags for this sweep under the current rules.
            </p>
          )}
        </div>
      </div>

      <details className="engineering-limitations">
        <summary>Analysis limits and assumptions</summary>
        <ul>
          {data.limitations.map((limitation, index) => (
            <li key={index}>{limitation}</li>
          ))}
        </ul>
      </details>
    </section>
  )
}

export function EngineeringAnalysis({ workbooks }: { workbooks: NormalizedWorkbook[] }) {
  const [data, setData] = useState<EngineeringAnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    void analyzeEngineering(workbooks, controller.signal)
      .then(setData)
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setError(cause instanceof Error ? cause.message : 'Engineering analysis failed.')
        }
      })
    return () => controller.abort()
  }, [workbooks])

  if (error) {
    return (
      <section className="engineering-section" aria-label="Engineering analysis">
        <div className="error-banner" role="alert">
          <strong>Engineering analysis unavailable</strong>
          <p>{error}</p>
        </div>
      </section>
    )
  }
  if (!data) {
    return (
      <section className="engineering-section" aria-label="Engineering analysis" role="status">
        Loading engineering diagnostics…
      </section>
    )
  }
  return <EngineeringView data={data} />
}
