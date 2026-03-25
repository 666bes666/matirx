import { apiClient } from './client'

export const exportApi = {
  downloadMatrixXlsx: (params?: { department_id?: string; team_id?: string }) => {
    const query = new URLSearchParams()
    if (params?.department_id) query.set('department_id', params.department_id)
    if (params?.team_id) query.set('team_id', params.team_id)
    const url = `/export/matrix.xlsx${query.toString() ? '?' + query.toString() : ''}`
    return apiClient
      .get(url, { responseType: 'blob' })
      .then((r) => {
        const href = URL.createObjectURL(r.data)
        const link = document.createElement('a')
        link.href = href
        link.download = 'matrix.xlsx'
        link.click()
        URL.revokeObjectURL(href)
      })
  },

  downloadUserReportXlsx: (userId: string) =>
    apiClient
      .get(`/export/users/${userId}/report.xlsx`, { responseType: 'blob' })
      .then((r) => {
        const href = URL.createObjectURL(r.data)
        const link = document.createElement('a')
        link.href = href
        link.download = `report_${userId}.xlsx`
        link.click()
        URL.revokeObjectURL(href)
      }),
}
