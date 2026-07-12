/**
 * Flow tag constants for consistent E2E test tagging.
 *
 * Each constant bundles @flow:, @module:, and @priority: tags.
 * Use spread syntax to compose tags in tests:
 *
 *   import { AUTH_LOGIN_INVALID } from '../helpers/flow-tags';
 *   test('...', { tag: [...AUTH_LOGIN_INVALID] }, async ({ page }) => { ... });
 *
 * Source of truth: e2e/flow-definitions.json (v2.0.0 — Versiona MVP flows,
 * one per artifact flow id A1..F1; see docs/plan/06 §5).
 */

// ── Home / landing ──
export const HOME_LOADS = ['@flow:home-loads', '@module:home', '@priority:P1'];

// ── Auth (kept from the template; real pages already work) ──
export const AUTH_SIGN_IN_FORM = ['@flow:auth-sign-in-form', '@module:auth', '@priority:P2'];
export const AUTH_SIGN_UP_FORM = ['@flow:auth-sign-up-form', '@module:auth', '@priority:P1'];
export const AUTH_LOGIN_INVALID = ['@flow:auth-login-invalid', '@module:auth', '@priority:P1'];
export const AUTH_PROTECTED_REDIRECT = ['@flow:auth-protected-redirect', '@module:auth', '@priority:P1'];
export const AUTH_FORGOT_PASSWORD_FORM = ['@flow:auth-forgot-password-form', '@module:auth', '@priority:P2'];

// ── Versiona MVP flows (specs land with their vertical iteration, docs/plan/09) ──
export const A1_ONBOARDING_WOW = ['@flow:a1-onboarding-wow', '@module:onboarding', '@priority:P1'];
export const A2_INVITE_TEAM = ['@flow:a2-invite-team', '@module:org', '@priority:P1'];
export const B1_CREATE_PROJECT = ['@flow:b1-create-project', '@module:projects', '@priority:P1'];
export const B2_PROJECTS_BOARD = ['@flow:b2-projects-board', '@module:projects', '@priority:P2'];
export const B3_PROJECT_SETTINGS = ['@flow:b3-project-settings', '@module:projects', '@priority:P2'];
export const C1_UPLOAD_FIRST = ['@flow:c1-upload-first', '@module:documents', '@priority:P1'];
export const C2_UPLOAD_VERSION = ['@flow:c2-upload-version', '@module:documents', '@priority:P1'];
export const C3_HISTORY = ['@flow:c3-history', '@module:documents', '@priority:P2'];
export const D1_REQUEST_REVIEW = ['@flow:d1-request-review', '@module:review', '@priority:P1'];
export const D2_ASSISTED_REVIEW = ['@flow:d2-assisted-review', '@module:review', '@priority:P1'];
export const D3_OBSERVATIONS = ['@flow:d3-anchored-observations', '@module:review', '@priority:P1'];
export const D4_SEAL_APPROVE = ['@flow:d4-seal-approve', '@module:review', '@priority:P1'];
export const D5_SELECTIVE_INVALIDATION = ['@flow:d5-selective-invalidation', '@module:review', '@priority:P1'];
export const E1_COMPARE = ['@flow:e1-compare', '@module:compare', '@priority:P1'];
export const E3_CHECKS = ['@flow:e3-configurable-checks', '@module:compare', '@priority:P2'];
export const F1_BILLING = ['@flow:f1-billing', '@module:billing', '@priority:P2'];

// ── Versiona It1+ additions (v2.1.0) ──
export const C4_DELETE_DRAFT = ['@flow:c4-delete-draft', '@module:documents', '@priority:P2'];
export const AUTH_SIGN_IN_SUCCESS = ['@flow:auth-sign-in-success', '@module:auth', '@priority:P1'];
export const AUTH_SIGN_OUT = ['@flow:auth-sign-out', '@module:auth', '@priority:P2'];
export const A3_ACCOUNT_SECURITY = ['@flow:a3-account-security', '@module:auth', '@priority:P2'];
export const E2_SAVED_COMPARISONS = ['@flow:e2-saved-comparisons', '@module:compare', '@priority:P2'];
export const F2_USAGE_PANEL = ['@flow:f2-usage-panel', '@module:billing', '@priority:P2'];
export const E4_CONSTANCIA = ['@flow:e4-constancia', '@module:review', '@priority:P2'];
export const MASTER_JOURNEY = ['@flow:master-e2e-journey', '@module:master', '@priority:P1'];
