/**
 * Environment configuration with type safety and defaults
 */

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = import.meta.env[key] || defaultValue;
  if (value === undefined) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
};

const getBooleanEnv = (key: string, defaultValue: boolean = false): boolean => {
  const value = import.meta.env[key];
  if (value === undefined) return defaultValue;
  return value === 'true' || value === '1';
};

const getNumberEnv = (key: string, defaultValue: number): number => {
  const value = import.meta.env[key];
  if (value === undefined) return defaultValue;
  const num = parseInt(value, 10);
  return isNaN(num) ? defaultValue : num;
};

export const config = {
  // API Configuration
  api: {
    baseUrl: getEnvVar('VITE_API_URL', 'http://localhost:8000'),
    wsUrl: getEnvVar('VITE_WS_URL', 'ws://localhost:8000'),
  },
  
  // Feature Flags
  features: {
    auth: getBooleanEnv('VITE_ENABLE_AUTH', true),
    fileUpload: getBooleanEnv('VITE_ENABLE_FILE_UPLOAD', true),
    pipelines: getBooleanEnv('VITE_ENABLE_PIPELINES', true),
    websockets: getBooleanEnv('VITE_ENABLE_WEBSOCKETS', true),
  },
  
  // Upload Configuration
  upload: {
    maxFileSize: getNumberEnv('VITE_MAX_FILE_SIZE', 52428800), // 50MB
    maxFiles: getNumberEnv('VITE_MAX_FILES', 5),
  },
  
  // App Information
  app: {
    name: getEnvVar('VITE_APP_NAME', 'Web+'),
    description: getEnvVar('VITE_APP_DESCRIPTION', 'AI Model Management Platform'),
  },
  
  // Analytics
  analytics: {
    vercelId: import.meta.env.VITE_VERCEL_ANALYTICS_ID,
  },
  
  // Development
  dev: {
    debug: getBooleanEnv('VITE_DEBUG', false),
  },
  
  // Computed values
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const;

export type Config = typeof config;