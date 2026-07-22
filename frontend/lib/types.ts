/** Versiona domain types (mirror of docs/plan/03 serializers — It1 slice). */

export interface OrgSummary {
  public_id: string;
  name: string;
  slug: string;
  kind: 'personal' | 'team';
  role: 'owner' | 'admin' | 'member';
}

export type ProjectRole = 'admin' | 'editor' | 'reviewer' | 'viewer';

export interface ProjectSummary {
  public_id: string;
  name: string;
  slug: string;
  description: string;
  status: 'active' | 'archived';
  is_sample: boolean;
  document_count: number;
  effective_role: ProjectRole | null;
  created_at: string;
  updated_at: string;
}

export interface VersionSummary {
  public_id: string;
  number: number;
  message: string;
  sha256: string;
  size_bytes: number;
  page_count: number;
  source_scenario: 'text_native' | 'scanned_ocr' | 'mixed';
  analysis_status: 'pending' | 'processing' | 'ready' | 'failed';
  error_detail: string;
  is_approved: boolean;
  is_draft: boolean;
  is_trashed: boolean;
  author_email: string | null;
  thumb_url: string | null;
  check_summary?: CheckSummary | null;
  created_at: string;
}

export interface SectionInfo {
  stable_key: string;
  heading_text: string;
  level: number;
  order_index: number;
  page_start: number;
  page_end: number;
  bboxes: Array<{ page: number; x0: number; y0: number; x1: number; y1: number }>;
  body_hash: string;
  char_count: number;
}

export interface CheckSummary {
  pass: number;
  warn: number;
  fail: number;
}

export interface VersionDetail extends VersionSummary {
  sections: SectionInfo[];
  /** Injected by the endpoint so the screen can hide role-gated actions. */
  effective_role?: ProjectRole;
}

export interface DocumentSummary {
  public_id: string;
  title: string;
  slug: string;
  latest_number: number;
  latest_version: VersionSummary | null;
  created_at: string;
  updated_at: string;
}

export interface EngineJobStatus {
  public_id: string;
  job_type: string;
  status: 'pending' | 'running' | 'done' | 'failed';
  attempts: number;
  error: string | null;
  result: Record<string, unknown> | null;
  version_id: string | null;
}

export interface TrashItem {
  type: 'project' | 'document' | 'version';
  public_id: string;
  name: string;
  context: string;
  deleted_at: string;
  deleted_by: string | null;
  purge_after: string | null;
}

export interface Profile {
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  language: 'es' | 'en';
  timezone: string;
}
