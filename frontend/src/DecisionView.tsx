import { useState } from 'react'
import { evaluateDecision } from './decisions'
import type { ConstraintEvidence, WorkloadDecision, WorkloadTargets } from './decisions'
import type { NormalizedWorkbook } from './workbooks'

const quantity = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 })
const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 4,
})

const metricNames = {
  throughput: 'Total capacity',
  generation_speed: 'Response speed per person',
  ttft: 'Time until the response starts',
  context: 'Conversation size',
  cost: 'Hardware cost at full projected use',
}

const statusPresentation = {
  go: {
    title: 'Go for this projected workload',
    detail: 'At least one workbook configuration meets every requested check.',
    badge: 'GO',
    announcement: 'Go decision ready',
  },
  no_go: {
    title: 'No go for this projected workload',
    detail: 'Every matching configuration misses at least one requested limit.',
    badge: 'NO GO',
    announcement: 'No go decision ready',
  },
  insufficient_data: {
    title: 'More information needed',
    detail: 'The available projection cannot confirm a pass for every requested check.',
    badge: 'NEEDS DATA',
    announcement: 'More information needed for this decision',
  },
}

function evidenceExplanation(item: ConstraintEvidence) {
  if (item.outcome === 'unknown') {
    if (item.metric === 'context')
      return 'The supported context window was not supplied, so this size check cannot be confirmed.'
    if (item.metric === 'cost')
      return 'A box-hour price and usable projected capacity per box are needed to estimate hardware cost.'
    return 'The workbook has no projected value for this check.'
  }
  if (item.metric === 'throughput')
    return 'This is projected total capacity across requests, not one person’s response speed.'
  if (item.metric === 'generation_speed')
    return 'This is the projected pace of generated tokens for one person.'
  if (item.metric === 'ttft')
    return 'This is the projected wait before the first response token appears.'
  if (item.metric === 'context')
    return 'The required window covers the larger of your minimum and this workload’s input plus output tokens.'
  return 'Hardware-only estimate at sustained projected capacity; idle time and other costs are excluded.'
}

function assumptionCopy(assumption: string) {
  if (assumption.startsWith('Projections are capacity estimates'))
    return 'Workbook projections are capacity estimates and do not guarantee production service levels.'
  if (assumption.startsWith('Supported context window is a caller assumption of'))
    return assumption.replace(
      'Supported context window is a caller assumption of',
      'You supplied a supported context window of',
    )
  if (assumption.startsWith('Context window limit not supplied'))
    return 'No supported context window was supplied, so the context check remains unknown.'
  if (assumption.startsWith('Hardware-only cost per million')) {
    const price = assumption.match(/Caller-supplied price: (\$[\d.]+)\/box-hour/)
    return `You supplied a hardware price of ${price?.[1] ?? 'the stated amount'} per box-hour. The estimate divides that hourly price by projected tokens per box per hour, assuming sustained use and excluding idle time and other costs.`
  }
  if (assumption.startsWith('Hardware box-hour cost not supplied'))
    return 'No hardware price per box-hour was supplied, so the cost check remains unknown.'
  return assumption
}

function selectionCopy(result: WorkloadDecision) {
  if (!result.selected_record) return 'No projected configuration matches this workload.'
  if (result.status === 'go')
    return 'The first matching configuration that meets every check is shown below.'
  if (result.status === 'no_go')
    return 'The configuration with the fewest missed limits is shown below. Review all matching configurations for the full evidence.'
  return 'This configuration has no known failure, but missing facts could change the outcome.'
}

function formatValue(evidence: ConstraintEvidence, value: number | null) {
  if (value === null) return 'Not available'
  if (evidence.metric === 'cost') return `${currency.format(value)} per million tokens`
  if (evidence.metric === 'ttft') return `${quantity.format(value)} ms`
  if (evidence.metric === 'context') return `${quantity.format(value)} tokens`
  if (evidence.metric === 'generation_speed')
    return `${quantity.format(value)} tokens/sec per person`
  return `${quantity.format(value)} tokens/sec total`
}

function EvidenceList({ evidence }: { evidence: ConstraintEvidence[] }) {
  return (
    <ul className="evidence-list">
      {evidence.map((item) => (
        <li key={item.metric} className={`evidence-item evidence-${item.outcome}`}>
          <div className="evidence-topline">
            <strong>{metricNames[item.metric]}</strong>
            <span>
              {item.outcome === 'met'
                ? 'Meets target'
                : item.outcome === 'unmet'
                  ? 'Misses target'
                  : 'Unknown'}
            </span>
          </div>
          <p>
            {formatValue(item, item.actual)} <span aria-hidden="true">·</span>{' '}
            {item.metric === 'context' ? 'Required window' : 'Your limit'}:{' '}
            {formatValue(item, item.target)}
          </p>
          <p className="evidence-explanation">{evidenceExplanation(item)}</p>
        </li>
      ))}
    </ul>
  )
}

function DecisionResult({ result }: { result: WorkloadDecision }) {
  const copy = statusPresentation[result.status]

  return (
    <section className="decision-result" aria-labelledby="decision-title">
      <div className={`verdict verdict-${result.status}`}>
        <div>
          <div className="eyebrow">
            Customer decision · {result.model_name} / Profile {result.profile_id}
          </div>
          <h3 id="decision-title">{copy.title}</h3>
          <p>{copy.detail}</p>
          <p className="verdict-reason">{selectionCopy(result)}</p>
        </div>
        <span className="verdict-status">{copy.badge}</span>
      </div>

      {result.selected_record && (
        <div className="chosen-configuration">
          <span className="eyebrow">Configuration shown</span>
          <strong>Batch size {result.selected_record.batch_size}</strong>
          <span>
            {quantity.format(result.selected_record.input_length)} input tokens ·{' '}
            {quantity.format(result.selected_record.output_length)} output tokens ·{' '}
            {quantity.format(result.selected_record.cache_percentage * 100)}% cached
          </span>
        </div>
      )}

      <div className="decision-columns">
        <div className="panel">
          <div className="eyebrow">Why this result</div>
          <h3>Checks against your limits</h3>
          {result.evidence.length ? (
            <EvidenceList evidence={result.evidence} />
          ) : (
            <p className="decision-empty">
              Add at least one performance or cost limit to assess this workbook.
            </p>
          )}
        </div>
        <aside className="panel decision-assumptions" aria-label="Assumptions and limitations">
          <div className="eyebrow">Read before deciding</div>
          <h3>Assumptions and limits</h3>
          <ul>
            {result.assumptions.map((assumption) => (
              <li key={assumption}>{assumptionCopy(assumption)}</li>
            ))}
          </ul>
          <p>
            Throughput is total capacity; response speed is what one person may see. The cost
            estimate uses hardware cost at sustained projected capacity. It is not a customer price.
          </p>
        </aside>
      </div>

      {result.evaluated_configurations.length > 0 && (
        <details className="configuration-details">
          <summary>
            Review all {result.evaluated_configurations.length} matching configurations
          </summary>
          <div className="configuration-list">
            {result.evaluated_configurations.map((configuration, index) => (
              <article className="configuration-card" key={index}>
                <h4>Batch size {configuration.record.batch_size}</h4>
                <p>
                  {configuration.unmet_constraints.length} unmet ·{' '}
                  {configuration.unknown_constraints.length} unknown
                </p>
                <EvidenceList evidence={configuration.evidence} />
              </article>
            ))}
          </div>
        </details>
      )}
    </section>
  )
}

function numeric(form: FormData, name: string): number | undefined {
  const value = String(form.get(name) ?? '').trim()
  return value === '' ? undefined : Number(value)
}

export default function DecisionView({
  workbook,
  allWorkbooks = [workbook],
}: {
  workbook: NormalizedWorkbook
  allWorkbooks?: NormalizedWorkbook[]
}) {
  const [results, setResults] = useState<WorkloadDecision[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const peers = allWorkbooks.filter((candidate) => candidate.profile_id === workbook.profile_id)
  const selectedResult = results?.find((result) => result.model_name === workbook.model_name)
  const scenarios = [
    ...new Map(
      workbook.records.map((record) => [
        `${record.input_length}:${record.output_length}:${record.cache_percentage}`,
        record,
      ]),
    ).values(),
  ]

  async function submit(form: HTMLFormElement) {
    const data = new FormData(form)
    const scenarioIndex = String(data.get('scenario') ?? '')
    const scenario = scenarioIndex === '' ? undefined : scenarios[Number(scenarioIndex)]
    const targets: WorkloadTargets = {
      ...(scenario && {
        input_tokens: scenario.input_length,
        output_tokens: scenario.output_length,
        cache_fraction: scenario.cache_percentage,
      }),
      min_throughput_tps: numeric(data, 'throughput'),
      min_generation_speed_tps_per_user: numeric(data, 'generation'),
      max_ttft_ms: numeric(data, 'ttft'),
      min_context_window_tokens: numeric(data, 'context'),
      max_cost_usd_per_million_tokens: numeric(data, 'cost'),
    }
    if (
      !Object.entries(targets).some(
        ([name, value]) =>
          !['input_tokens', 'output_tokens', 'cache_fraction'].includes(name) &&
          value !== undefined,
      )
    ) {
      setError('Enter at least one target to make a customer decision.')
      return
    }
    if (peers.length > 1 && !scenario) {
      setError('Choose a projected workload to compare models against the same scenario.')
      return
    }
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const assumptions = {
        context_window_tokens: numeric(data, 'supported-context'),
        hardware_cost_usd_per_box_hour: numeric(data, 'box-price'),
      }
      setResults(
        await Promise.all(
          peers.map((candidate) => evaluateDecision(candidate, targets, assumptions)),
        ),
      )
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The decision could not be evaluated.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="decision-section" aria-labelledby="workload-title">
      <div className="section-index">03 / DECISION</div>
      <div className="decision-heading">
        <div>
          <h2 id="workload-title">Will it work for your customers?</h2>
          <p>
            Set the limits that matter. We’ll check each model in this profile against the same
            workload and assumptions.
          </p>
        </div>
        <span className="decision-hint">Blank fields stay unknown or unchecked</span>
      </div>
      <form
        className="decision-form panel"
        onChange={() => {
          setResults(null)
          setError(null)
        }}
        onSubmit={(event) => {
          event.preventDefault()
          void submit(event.currentTarget)
        }}
      >
        <fieldset className="decision-fields" disabled={loading}>
          <legend className="sr-only">Customer workload, limits, and assumptions</legend>
          <div className="form-group">
            <h3>1. Choose the workload</h3>
            <p>
              {peers.length > 1
                ? 'Pick one projected scenario so every model is checked against the same workload.'
                : 'Pick a workbook scenario, or look for a fit among any projected configuration.'}
            </p>
            <label htmlFor="scenario">Projected workload</label>
            <select id="scenario" name="scenario" defaultValue="">
              <option value="">
                {peers.length > 1 ? 'Choose a workload' : 'Any projected workload'}
              </option>
              {scenarios.map((scenario, index) => (
                <option
                  value={index}
                  key={`${scenario.input_length}-${scenario.output_length}-${scenario.cache_percentage}`}
                >
                  {quantity.format(scenario.input_length)} input ·{' '}
                  {quantity.format(scenario.output_length)} output ·{' '}
                  {quantity.format(scenario.cache_percentage * 100)}% cached
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <h3>2. Set your limits</h3>
            <p>Enter only the requirements you need to check.</p>
            <div className="form-grid">
              <label>
                Minimum total capacity <span>tokens per second</span>
                <input
                  name="throughput"
                  type="number"
                  min="0.001"
                  step="any"
                  placeholder="e.g. 400000"
                />
              </label>
              <label>
                Minimum response speed <span>tokens per second per person</span>
                <input
                  name="generation"
                  type="number"
                  min="0.001"
                  step="any"
                  placeholder="e.g. 1200"
                />
              </label>
              <label>
                Maximum time until response starts <span>milliseconds</span>
                <input name="ttft" type="number" min="0.001" step="any" placeholder="e.g. 10" />
              </label>
              <label>
                Minimum context window <span>tokens</span>
                <input name="context" type="number" min="1" step="1" placeholder="e.g. 32000" />
              </label>
              <label>
                Maximum hardware cost <span>USD per million projected tokens</span>
                <input name="cost" type="number" min="0.001" step="any" placeholder="e.g. 2.50" />
              </label>
            </div>
          </div>
          <div className="form-group">
            <h3>3. Add known facts</h3>
            <p>These are supplied assumptions, not facts established by the workbook.</p>
            <div className="form-grid">
              <label>
                Supported context window <span>tokens</span>
                <input
                  name="supported-context"
                  type="number"
                  min="1"
                  step="1"
                  placeholder="If known"
                />
              </label>
              <label>
                Hardware price <span>USD per box-hour</span>
                <input name="box-price" type="number" min="0" step="any" placeholder="If known" />
              </label>
            </div>
          </div>
        </fieldset>
        <div className="decision-actions">
          <button type="submit" disabled={loading}>
            {loading ? 'Checking workload…' : 'Check customer fit'}
          </button>
          <span>Results use workbook projections, not production measurements.</span>
        </div>
      </form>
      {error && (
        <div role="alert" className="error-banner">
          <strong>{error}</strong>
        </div>
      )}
      {loading && (
        <p role="status" className="decision-loading">
          Checking your limits against the decision API…
        </p>
      )}
      <div role="status" aria-live="polite" className="sr-only">
        {results ? `${results.length} customer decisions ready` : ''}
      </div>
      {results && results.length > 1 && (
        <div className="panel decision-comparison">
          <h3>Customer fit across models</h3>
          <p className="panel-description">
            The same scenario, limits, and supplied assumptions were checked for every model in
            profile {workbook.profile_id}. A missing projected row remains “needs data.”
          </p>
          <div className="table-scroll">
            <table aria-label="Customer decision comparison">
              <thead>
                <tr>
                  <th scope="col">Model</th>
                  <th scope="col">Decision</th>
                  <th scope="col">Configuration</th>
                  <th scope="col">Unmet checks</th>
                  <th scope="col">Unknown checks</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result) => (
                  <tr key={`${result.model_name}-${result.profile_id}`}>
                    <th scope="row">{result.model_name}</th>
                    <td>{statusPresentation[result.status].badge}</td>
                    <td>
                      {result.selected_record
                        ? `Batch ${result.selected_record.batch_size}`
                        : 'No matching row'}
                    </td>
                    <td>{result.unmet_constraints.join(', ') || 'None'}</td>
                    <td>{result.unknown_constraints.join(', ') || 'None'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {selectedResult && <DecisionResult result={selectedResult} />}
    </section>
  )
}
