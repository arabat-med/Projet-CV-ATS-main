const baseUrl = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')

export const apiUrl = (path) => `${baseUrl}${path}`

export const validateUpload = (file, extensions) => {
  if (!file) return 'Sélectionnez un fichier.'
  if (!extensions.some((extension) => file.name.toLowerCase().endsWith(extension))) {
    return `Formats acceptés : ${extensions.join(', ')}`
  }
  if (file.size > 10 * 1024 * 1024) return 'Le fichier dépasse la limite de 10 Mio.'
  return null
}
