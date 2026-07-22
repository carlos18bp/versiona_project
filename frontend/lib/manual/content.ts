import { BookOpen } from 'lucide-react';

import type { ManualSection } from './types';

export const MANUAL_SECTIONS: ManualSection[] = [
  {
    id: 'getting-started',
    title: { es: 'Primeros pasos', en: 'Getting started' },
    icon: BookOpen,
    processes: [
      {
        id: 'create-account',
        title: { es: 'Crea tu cuenta', en: 'Create your account' },
        summary: {
          es: 'Regístrate con tu correo o con Google para empezar a versionar documentos.',
          en: 'Sign up with your email or Google account to start versioning documents.',
        },
        why: {
          es: 'Tu cuenta es la llave de tu organización: en ella viven tus proyectos, versiones y aprobaciones.',
          en: 'Your account is the key to your organization: your projects, versions and approvals live there.',
        },
        steps: {
          es: [
            'Abre la página de inicio y presiona "Crear cuenta gratis".',
            'Completa tu correo y una contraseña de al menos 8 caracteres, o usa el botón de Google.',
            'Resuelve el captcha si se solicita.',
            'Al entrar quedarás en tu panel, listo para el asistente de bienvenida.',
          ],
          en: [
            'Open the landing page and press "Crear cuenta gratis".',
            'Fill in your email and a password of at least 8 characters, or use the Google button.',
            'Solve the captcha if prompted.',
            'You will land on your panel, ready for the onboarding assistant.',
          ],
        },
        route: '/sign-up',
        tips: {
          es: ['Si ya tienes cuenta, usa "Iniciar sesión" en el encabezado.'],
          en: ['If you already have an account, use "Iniciar sesión" in the header.'],
        },
        keywords: [
          'cuenta',
          'account',
          'registro',
          'sign up',
          'google',
          'crear',
          'signup',
          'registrarse',
        ],
      },
      {
        id: 'sign-in-recover',
        title: { es: 'Inicia sesión o recupera tu contraseña', en: 'Sign in or recover your password' },
        summary: {
          es: 'Entra con tus credenciales y, si olvidaste la contraseña, recupérala con un código por correo.',
          en: 'Sign in with your credentials and, if you forgot the password, recover it with an email code.',
        },
        why: {
          es: 'Sin sesión activa no puedes ver proyectos ni aprobar versiones.',
          en: 'Without an active session you cannot see projects or approve versions.',
        },
        steps: {
          es: [
            'Presiona "Iniciar sesión" en el encabezado.',
            'Ingresa tu correo y contraseña, o usa Google.',
            'Si olvidaste la contraseña, usa el enlace de recuperación.',
            'Recibirás un código de 6 dígitos por correo, válido por 15 minutos.',
            'Ingresa el código y define tu nueva contraseña.',
          ],
          en: [
            'Press "Iniciar sesión" in the header.',
            'Enter your email and password, or use Google.',
            'If you forgot the password, use the recovery link.',
            'You will receive a 6-digit code by email, valid for 15 minutes.',
            'Enter the code and set your new password.',
          ],
        },
        route: '/sign-in',
        tips: {
          es: ['El código de recuperación expira: pide uno nuevo si tardaste más de 15 minutos.'],
          en: ['The recovery code expires: request a new one if more than 15 minutes passed.'],
        },
        keywords: [
          'login',
          'iniciar sesión',
          'password',
          'contraseña',
          'recuperar',
          'recover',
          'código',
          'code',
          'olvidé',
        ],
      },
      {
        id: 'panel-overview',
        title: { es: 'Conoce tu panel', en: 'Tour your panel' },
        summary: {
          es: 'El panel será tu tablero de proyectos: estados de un vistazo, búsqueda y acceso a cada documento.',
          en: 'The panel will be your projects board: at-a-glance states, search and access to each document.',
        },
        why: {
          es: 'Desde el tablero verás qué está en revisión, qué tiene observaciones y qué ya fue aprobado.',
          en: 'From the board you will see what is in review, what has observations and what is already approved.',
        },
        steps: {
          es: [
            'Inicia sesión y presiona "Panel" en el encabezado.',
            'Muy pronto: crea proyectos, sube tu PDF y mira tu primera comparación en minutos.',
          ],
          en: [
            'Sign in and press "Panel" in the header.',
            'Coming soon: create projects, upload your PDF and see your first comparison in minutes.',
          ],
        },
        route: '/dashboard',
        tips: {
          es: ['Esta guía crecerá con cada iteración: versiones, comparación, observaciones y sellos.'],
          en: ['This guide grows with each iteration: versions, comparison, observations and seals.'],
        },
        keywords: [
          'panel',
          'dashboard',
          'proyectos',
          'projects',
          'tablero',
          'board',
          'inicio',
        ],
      },
    ],
  },
];
