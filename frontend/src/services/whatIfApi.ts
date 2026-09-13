import { api } from './api';
import type {
  WhatIfSimulationRequest,
  WhatIfSimulationResponse,
} from '../types';

/**
 * Phase 7 — What-If Academic Simulator API client.
 * The frontend ONLY consumes backend results. No ML logic lives here.
 */
export const whatIfApi = {
  runSimulation: async (payload: WhatIfSimulationRequest): Promise<WhatIfSimulationResponse> => {
    const res = await api.post<WhatIfSimulationResponse>('/predictions/what-if', payload);
    return res.data;
  },
};