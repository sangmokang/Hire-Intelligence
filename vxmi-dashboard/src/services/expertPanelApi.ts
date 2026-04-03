/**
 * Expert Panel API 클라이언트
 */
import { apiClient } from './apiClient';

// --- Types ---

export interface QueryClassification {
  axis: 'TASK' | 'FACT';
  specificity: 'AMBIGUOUS' | 'CONCRETE';
  confidence: number;
  routingStrategy: string;
}

export interface ExpertResponseItem {
  expert: string;
  expertName: string;
  answer: string;
  confidence: number;
  suggestedActions: { priority: string; text: string; cta?: string; ctaUrl?: string }[] | null;
  relatedViews: string[];
}

export interface AskResponse {
  classification: QueryClassification;
  responses: ExpertResponseItem[];
  sessionId: string;
  isAiGenerated: boolean;
}

export interface AskRequest {
  query: string;
  view?: string;
  expertHint?: string;
  contextData?: Record<string, unknown>;
}

export interface FeedbackRequest {
  sessionId: string;
  expertType: string;
  feedbackType: 'HELPFUL' | 'NOT_HELPFUL' | 'FOLLOW_UP' | 'COPY';
  rating?: number;
  feedbackText?: string;
}

export interface SessionSummary {
  id: string;
  query: string;
  view: string | null;
  classificationAxis: string;
  classificationSpecificity: string;
  selectedExperts: string[];
  routingStrategy: string;
  responseTimeMs: number | null;
  createdAt: string;
}

// --- API Functions ---

export async function askExpert(request: AskRequest): Promise<AskResponse> {
  const { data } = await apiClient.post<{ data: AskResponse }>('/api/v1/expert-panel/ask', request);
  return data.data;
}

export async function submitFeedback(request: FeedbackRequest): Promise<void> {
  await apiClient.post('/api/v1/expert-panel/feedback', request);
}

export async function getSessions(limit = 20): Promise<SessionSummary[]> {
  const { data } = await apiClient.get<{ data: SessionSummary[] }>('/api/v1/expert-panel/sessions', {
    params: { limit },
  });
  return data.data;
}
