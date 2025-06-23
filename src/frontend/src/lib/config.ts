export const config = {
  backendUrl: import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000',
} as const;

export const buildApiUrl = (endpoint: string): string => {
  const baseUrl = config.backendUrl.replace(/\/$/, '');
  const cleanEndpoint = endpoint.replace(/^\//, '');
  return `${baseUrl}/${cleanEndpoint}`;
}; 