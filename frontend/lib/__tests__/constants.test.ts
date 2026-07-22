import { describe, it, expect } from '@jest/globals';

import { COOKIE_KEYS, PAGINATION, ROUTES } from '../constants';

describe('constants', () => {
  describe('ROUTES', () => {
    it('exposes HOME route as "/"', () => {
      expect(ROUTES.HOME).toBe('/');
    });

    it('exposes SIGN_IN route', () => {
      expect(ROUTES.SIGN_IN).toBe('/sign-in');
    });

    it('exposes DASHBOARD route', () => {
      expect(ROUTES.DASHBOARD).toBe('/dashboard');
    });

    it('exposes HELP route pointing to the manual', () => {
      expect(ROUTES.HELP).toBe('/manual');
    });
  });

  describe('COOKIE_KEYS', () => {
    it('exposes ACCESS_TOKEN key', () => {
      expect(COOKIE_KEYS.ACCESS_TOKEN).toBe('access_token');
    });

    it('exposes REFRESH_TOKEN key', () => {
      expect(COOKIE_KEYS.REFRESH_TOKEN).toBe('refresh_token');
    });
  });

  describe('PAGINATION', () => {
    it('exposes DEFAULT_PAGE_SIZE matching the DRF page size', () => {
      expect(PAGINATION.DEFAULT_PAGE_SIZE).toBe(25);
    });
  });
});
