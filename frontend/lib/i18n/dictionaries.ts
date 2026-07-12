/**
 * UI dictionaries (kit 7 — operator decision 2026-07-12: es/en functional).
 * Every new screen ships BOTH languages; `useDict(namespace)` resolves the
 * active locale from the persisted user preference (localeStore, synced with
 * the backend profile). Never hardcode user-facing strings in components.
 */

import { useEffect, useState } from 'react';

import { useLocaleStore } from '@/lib/stores/localeStore';

const DICTIONARIES = {
  common: {
    es: {
      loading: 'Cargando…',
      retry: 'Reintentar',
      cancel: 'Cancelar',
      confirm: 'Confirmar',
      save: 'Guardar',
      saved: 'Cambios guardados',
      search: 'Buscar…',
      error: 'Algo salió mal',
      previous: 'Anterior',
      next: 'Siguiente',
      page: 'Página',
      delete: 'Eliminar',
      restore: 'Restaurar',
      close: 'Cerrar',
      panel: 'Panel',
      help: 'Ayuda',
      signIn: 'Iniciar sesión',
      signUp: 'Crear cuenta',
      signOut: 'Salir',
      trash: 'Papelera',
      settings: 'Configuración',
    },
    en: {
      loading: 'Loading…',
      retry: 'Retry',
      cancel: 'Cancel',
      confirm: 'Confirm',
      save: 'Save',
      saved: 'Changes saved',
      search: 'Search…',
      error: 'Something went wrong',
      previous: 'Previous',
      next: 'Next',
      page: 'Page',
      delete: 'Delete',
      restore: 'Restore',
      close: 'Close',
      panel: 'Panel',
      help: 'Help',
      signIn: 'Sign in',
      signUp: 'Sign up',
      signOut: 'Sign out',
      trash: 'Trash',
      settings: 'Settings',
    },
  },
  projects: {
    es: {
      title: 'Proyectos',
      newProject: 'Nuevo proyecto',
      emptyTitle: 'Aún no tienes proyectos',
      emptyBody: 'Crea tu primer proyecto y sube un PDF para empezar a versionar.',
      createCta: 'Crear proyecto',
      name: 'Nombre',
      description: 'Descripción (opcional)',
      nameRequired: 'El nombre es obligatorio',
      creating: 'Creando…',
      documents: 'documentos',
      status: {
        active: 'Activo',
        archived: 'Archivado',
      },
      role: {
        admin: 'Admin',
        editor: 'Editor',
        reviewer: 'Revisor',
        viewer: 'Lector',
      },
    },
    en: {
      title: 'Projects',
      newProject: 'New project',
      emptyTitle: 'No projects yet',
      emptyBody: 'Create your first project and upload a PDF to start versioning.',
      createCta: 'Create project',
      name: 'Name',
      description: 'Description (optional)',
      nameRequired: 'The name is required',
      creating: 'Creating…',
      documents: 'documents',
      status: {
        active: 'Active',
        archived: 'Archived',
      },
      role: {
        admin: 'Admin',
        editor: 'Editor',
        reviewer: 'Reviewer',
        viewer: 'Viewer',
      },
    },
  },
  documents: {
    es: {
      title: 'Documentos',
      emptyTitle: 'Este proyecto no tiene documentos',
      emptyBody: 'Arrastra un PDF o haz clic para subir la primera versión.',
      dropHere: 'Arrastra tu PDF aquí o haz clic para elegirlo',
      onlyPdf: 'Solo se aceptan archivos PDF',
      tooBig: 'El archivo supera el límite de {mb} MB',
      previewTitle: 'Confirma la subida',
      documentTitle: 'Título del documento',
      versionMessage: 'Mensaje de la versión (como un commit)',
      upload: 'Subir versión',
      uploading: 'Subiendo…',
      analyzing: 'Analizando documento…',
      analysisFailed: 'El análisis falló',
      analysisDone: 'Versión lista',
      pages: 'páginas',
      sections: 'secciones',
      version: 'Versión',
      versions: 'Versiones',
      timelineEmpty: 'Sube la primera versión de este documento.',
      download: 'Descargar',
      compare: 'Comparar',
      viewer: 'Ver documento',
      editMessage: 'Editar mensaje',
      messageFrozen: 'El mensaje se congela al solicitar revisión o sellar',
      deletedVersion: 'versión eliminada',
      deleteVersionTitle: 'Eliminar borrador',
      deleteVersionBody:
        'La versión v{n} irá a la papelera 30 días antes de borrarse definitivamente. Las versiones selladas nunca pueden eliminarse.',
      approved: 'Aprobada',
      draft: 'Borrador',
      scenario: {
        text_native: 'Texto nativo',
        scanned_ocr: 'Escaneado',
        mixed: 'Mixto',
      },
    },
    en: {
      title: 'Documents',
      emptyTitle: 'This project has no documents',
      emptyBody: 'Drag a PDF or click to upload the first version.',
      dropHere: 'Drag your PDF here or click to choose it',
      onlyPdf: 'Only PDF files are accepted',
      tooBig: 'The file exceeds the {mb} MB limit',
      previewTitle: 'Confirm the upload',
      documentTitle: 'Document title',
      versionMessage: 'Version message (like a commit)',
      upload: 'Upload version',
      uploading: 'Uploading…',
      analyzing: 'Analyzing document…',
      analysisFailed: 'Analysis failed',
      analysisDone: 'Version ready',
      pages: 'pages',
      sections: 'sections',
      version: 'Version',
      versions: 'Versions',
      timelineEmpty: 'Upload the first version of this document.',
      download: 'Download',
      compare: 'Compare',
      viewer: 'View document',
      editMessage: 'Edit message',
      messageFrozen: 'The message freezes on review request or seal',
      deletedVersion: 'deleted version',
      deleteVersionTitle: 'Delete draft',
      deleteVersionBody:
        'Version v{n} will sit in the trash for 30 days before permanent deletion. Sealed versions can never be deleted.',
      approved: 'Approved',
      draft: 'Draft',
      scenario: {
        text_native: 'Native text',
        scanned_ocr: 'Scanned',
        mixed: 'Mixed',
      },
    },
  },
  trash: {
    es: {
      title: 'Papelera',
      emptyTitle: 'La papelera está vacía',
      emptyBody: 'Lo que elimines vivirá aquí 30 días antes de borrarse.',
      type: { project: 'Proyecto', document: 'Documento', version: 'Versión' },
      deletedBy: 'Eliminado por',
      purgeAfter: 'Se borra el',
      restored: 'Elemento restaurado',
    },
    en: {
      title: 'Trash',
      emptyTitle: 'The trash is empty',
      emptyBody: 'Deleted items live here for 30 days before purge.',
      type: { project: 'Project', document: 'Document', version: 'Version' },
      deletedBy: 'Deleted by',
      purgeAfter: 'Purges on',
      restored: 'Item restored',
    },
  },
  compare: {
    es: {
      title: 'Comparación',
      views: { side: 'Lado a lado', sections: 'Secciones', summary: 'Resumen' },
      change: {
        unchanged: 'Sin cambios',
        modified: 'Modificada',
        added: 'Agregada',
        removed: 'Eliminada',
        renamed_only: 'Renumerada',
      },
      hideUnchanged: 'Ocultar secciones sin cambios',
      noChanges: 'Sin cambios entre estas versiones',
      noChangesBody: 'Las dos versiones tienen exactamente el mismo contenido por sección.',
      comparing: 'Comparando versiones…',
      nextChange: 'Siguiente cambio',
      before: 'Antes',
      after: 'Después',
      sectionsChanged: 'secciones cambiadas',
      pickTwo: 'Elige dos versiones para comparar',
      compareCta: 'Comparar seleccionadas',
    },
    en: {
      title: 'Comparison',
      views: { side: 'Side by side', sections: 'Sections', summary: 'Summary' },
      change: {
        unchanged: 'Unchanged',
        modified: 'Modified',
        added: 'Added',
        removed: 'Removed',
        renamed_only: 'Renumbered',
      },
      hideUnchanged: 'Hide unchanged sections',
      noChanges: 'No changes between these versions',
      noChangesBody: 'Both versions have exactly the same content, section by section.',
      comparing: 'Comparing versions…',
      nextChange: 'Next change',
      before: 'Before',
      after: 'After',
      sectionsChanged: 'changed sections',
      pickTwo: 'Pick two versions to compare',
      compareCta: 'Compare selected',
    },
  },
  settings: {
    es: {
      title: 'Configuración',
      profile: 'Perfil',
      firstName: 'Nombre',
      lastName: 'Apellido',
      phone: 'Teléfono',
      language: 'Idioma',
      timezone: 'Zona horaria',
      languageEs: 'Español',
      languageEn: 'English',
    },
    en: {
      title: 'Settings',
      profile: 'Profile',
      firstName: 'First name',
      lastName: 'Last name',
      phone: 'Phone',
      language: 'Language',
      timezone: 'Timezone',
      languageEs: 'Español',
      languageEn: 'English',
    },
  },
} as const;

export type Namespace = keyof typeof DICTIONARIES;
export type Locale = 'es' | 'en';

export function getDict<N extends Namespace>(namespace: N, locale: Locale) {
  return DICTIONARIES[namespace][locale];
}

export function useDict<N extends Namespace>(namespace: N) {
  const locale = useLocaleStore((s) => s.locale) as Locale;
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => setIsHydrated(true), []);

  // Server and first client render must agree: the persisted locale is only
  // applied after hydration (otherwise React reports a text mismatch).
  const active: Locale = isHydrated ? locale : 'es';
  return DICTIONARIES[namespace][active] ?? DICTIONARIES[namespace].es;
}

export function interpolate(template: string, values: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, key) => String(values[key] ?? `{${key}}`));
}
