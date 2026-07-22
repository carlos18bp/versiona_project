export const ROUTES = {
  HOME: '/',
  SIGN_IN: '/sign-in',
  SIGN_UP: '/sign-up',
  FORGOT_PASSWORD: '/forgot-password',
  DASHBOARD: '/dashboard',
  HELP: '/manual',
  PRECIOS: '/precios',
  COMPARAR: '/comparar',
  ORG_USAGE: '/org/usage',
} as const;

export const COOKIE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
} as const;

export const PAGINATION = {
  // Mirrors the DRF PAGE_SIZE (backend settings.REST_FRAMEWORK).
  DEFAULT_PAGE_SIZE: 25,
} as const;
