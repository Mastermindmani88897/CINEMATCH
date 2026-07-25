export function parseApiError(err: any, defaultMessage = 'An unexpected error occurred'): string {
  if (!err) return defaultMessage;
  
  const detail = err.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  
  if (Array.isArray(detail) && detail.length > 0) {
    const firstErr = detail[0];
    if (typeof firstErr === 'string') return firstErr;
    if (firstErr?.msg) return firstErr.msg;
  }

  if (err.response?.data?.message) {
    return err.response.data.message;
  }

  if (err.message) {
    return err.message;
  }

  return defaultMessage;
}
