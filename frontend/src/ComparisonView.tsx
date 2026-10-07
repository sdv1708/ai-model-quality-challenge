import { useState } from 'react'
import TableScroll from './TableScroll'
import type { AlignedConfiguration, ComparisonResponse } from './comparisons'

const number = new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 })

function configurationLabel(configuration: AlignedConfiguration) {
  const { input_length, output_length, cache_percentage, batch_size } = configuration.key
  return `${number.format(input_length)} input · ${number.format(output_length)} output · ${number.format(cache_percentage * 100)}% cached · batch ${batch_size}`
}

interface ComparisonViewProps {
  data: ComparisonResponse
  selectedWorkbookIndex: number
  onSelectWorkbook: (index: number) => void
}

export default function ComparisonView({
  data,
  selectedWorkbookIndex,
  onSelectWorkbook,
}: ComparisonViewProps) {
  const profiles = [...new Set(data.configurations.map((item) => item.key.profile_id))].sort(
    (a, b) => a.localeCompare(b, undefined, { numeric: true }),
  )
  const [profile, setProfile] = useState(profiles[0] ?? '')
  const [configurationIndex, setConfigurationIndex] = useState(0)
  const configurations = data.configurations.filter((item) => item.key.profile_id === profile)
  const selected = configurations[configurationIndex] ?? configurations[0]
  const comparableCount = data.configurations.filter((item) => item.is_comparable).length

  return (
    <section className="comparison-section" aria-labelledby="comparison-title">
      <div className="section-index">02 / COMPARISON</div>
      <div className="comparison-heading">
        <div>
          <h2 id="comparison-title">Compare the same workload</h2>
          <p>
            Rows align only when profile, input and output length, cache share, and batch size
            match. Missing projections stay visible.
          </p>
        </div>
        <span className="profile-badge">
          {data.models.length} {data.models.length === 1 ? 'model' : 'models'} · {comparableCount}{' '}
          shared configurations
        </span>
      </div>

      {data.diagnostics.length > 0 && (
        <div className="panel comparison-diagnostics" role="region" aria-label="Upload diagnostics">
          <h3>Upload notes</h3>
          <ul>
            {data.diagnostics.map((diagnostic, index) => (
              <li key={`${diagnostic.code}-${diagnostic.filename ?? ''}-${index}`}>
                <strong>{diagnostic.filename ?? diagnostic.model_name ?? diagnostic.code}:</strong>{' '}
                {diagnostic.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.models.length === 1 && (
        <p className="comparison-note">
          One model is loaded. Add another workbook to compare projected configurations.
        </p>
      )}

      <div className="panel comparison-panel">
        <div className="comparison-controls">
          <label>
            Traffic profile
            <select
              value={profile}
              onChange={(event) => {
                setProfile(event.target.value)
                setConfigurationIndex(0)
              }}
            >
              {profiles.map((id) => (
                <option key={id} value={id}>
                  Profile {id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Projected configuration
            <select
              value={configurationIndex}
              onChange={(event) => setConfigurationIndex(Number(event.target.value))}
            >
              {configurations.map((configuration, index) => (
                <option key={index} value={index}>
                  {configurationLabel(configuration)}
                </option>
              ))}
            </select>
          </label>
        </div>

        {selected && (
          <>
            <div className="comparison-status">
              <strong>
                {selected.is_comparable ? 'Direct comparison available' : 'No direct comparison'}
              </strong>
              <span>
                {selected.members.length} of {data.models.length} uploaded models have this exact
                configuration.
              </span>
            </div>
            {selected.missing_models.length > 0 && (
              <p className="comparison-note">
                No matching projection: {selected.missing_models.join(', ')}.
              </p>
            )}

            <h3>Customer view</h3>
            <p className="panel-description">
              These are projections for one matched configuration, not a go/no-go decision or
              measured production performance.
            </p>
            <TableScroll label="Customer model comparison">
              <table aria-label="Customer model comparison">
                <thead>
                  <tr>
                    <th scope="col">Model</th>
                    <th scope="col">Total capacity (tok/s)</th>
                    <th scope="col">Generation speed (tok/s/user)</th>
                    <th scope="col">Time to first token (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.models.map((model) => {
                    const member = selected.members.find((item) => item.model_name === model)
                    return (
                      <tr key={model}>
                        <th scope="row">{model}</th>
                        <td>
                          {member ? number.format(member.record.throughput) : 'No projection'}
                        </td>
                        <td>{member ? number.format(member.record.gen_speed) : 'No projection'}</td>
                        <td>{member ? number.format(member.record.ttft_ms) : 'No projection'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </TableScroll>

            <h3>Engineering view</h3>
            <p className="panel-description">
              Per-box capacity and cache-sensitive throughput help check deployment assumptions.
            </p>
            <TableScroll label="Engineering model comparison">
              <table aria-label="Engineering model comparison">
                <thead>
                  <tr>
                    <th scope="col">Model</th>
                    <th scope="col">Per box (tok/s)</th>
                    <th scope="col">Cached (tok/s)</th>
                    <th scope="col">Uncached (tok/s)</th>
                    <th scope="col">Requests/min</th>
                  </tr>
                </thead>
                <tbody>
                  {data.models.map((model) => {
                    const member = selected.members.find((item) => item.model_name === model)
                    return (
                      <tr key={model}>
                        <th scope="row">{model}</th>
                        <td>
                          {member
                            ? number.format(member.record.throughput_per_box)
                            : 'No projection'}
                        </td>
                        <td>
                          {member
                            ? number.format(member.record.cached_throughput)
                            : 'No projection'}
                        </td>
                        <td>
                          {member
                            ? number.format(member.record.uncached_throughput)
                            : 'No projection'}
                        </td>
                        <td>{member ? number.format(member.record.rpm) : 'No projection'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </TableScroll>
          </>
        )}
      </div>

      <div className="comparison-workbook-choice">
        <label htmlFor="selected-workbook">Inspect one sweep and test customer targets</label>
        <select
          id="selected-workbook"
          value={selectedWorkbookIndex}
          onChange={(event) => onSelectWorkbook(Number(event.target.value))}
        >
          {data.workbooks.map((workbook, index) => (
            <option key={`${workbook.model_name}-${workbook.profile_id}-${index}`} value={index}>
              {workbook.model_name} · Profile {workbook.profile_id}
            </option>
          ))}
        </select>
      </div>
    </section>
  )
}
