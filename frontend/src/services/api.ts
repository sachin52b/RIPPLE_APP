import type {
  DatasetUploadPayload,
  CriticalityRequestPayload,
  CriticalityResponse,
  CommitInterventionPayload,
  CommitInterventionResponse,
  InterventionEvaluationPayload,
  InterventionEvaluationResponse,
  HealthResponse,
  NetworkResponse,
  ShockPayload,
  SimulationStateResponse,
  SaveRunPayload,
  SaveRunResponse,
} from './types'

// Development requests are proxied by Vite; production requests are served by
// FastAPI from the same public origin. An override remains available if needed.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...init?.headers,
      },
    })
  } catch {
    throw new ApiError('Unable to reach the backend service.')
  }

  const contentType = response.headers.get('content-type') ?? ''
  const data: unknown = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const detail =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String(data.detail)
        : `Request failed with status ${response.status}.`
    throw new ApiError(detail, response.status)
  }

  return data as T
}

export function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

export function loadDemoNetwork(): Promise<NetworkResponse> {
  return request<NetworkResponse>('/api/network/demo')
}

export function simulateShock(payload: ShockPayload): Promise<SimulationStateResponse> {
  const { network_id, ...shock } = payload
  return request<SimulationStateResponse>('/api/simulation/shock', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ network_id, shock }),
  })
}

export function fetchCriticalityRankings(
  payload: CriticalityRequestPayload,
): Promise<CriticalityResponse> {
  return request<CriticalityResponse>('/api/intervention/criticality', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function evaluatePolicies(
  payload: InterventionEvaluationPayload,
): Promise<InterventionEvaluationResponse> {
  return request<InterventionEvaluationResponse>('/api/intervention/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function commitIntervention(
  payload: CommitInterventionPayload,
): Promise<CommitInterventionResponse> {
  return request<CommitInterventionResponse>('/api/intervention/commit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function saveRun(payload: SaveRunPayload): Promise<SaveRunResponse> {
  return request<SaveRunResponse>('/api/persistence/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

/**
 * Upload a JSON dataset containing the backend's borrower/relationship arrays.
 * CSV and Excel mapping/parsing are intentionally deferred to the upload UI phase.
 */
export async function uploadDataset(file: File): Promise<NetworkResponse> {
  if (!file.name.toLowerCase().endsWith('.json')) {
    throw new ApiError(
      'This Phase 1 client accepts JSON datasets. CSV/Excel mapping will be added with the upload UI.',
    )
  }

  let payload: DatasetUploadPayload
  try {
    payload = JSON.parse(await file.text()) as DatasetUploadPayload
  } catch {
    throw new ApiError('The selected file is not valid JSON.')
  }

  return request<NetworkResponse>('/api/network/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
