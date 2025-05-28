import http from './http'

export interface Subscription {
  id: string
  mp_id: string
  name: string
  mp_name: string
  mp_cover: string
  mp_intro: string
  status: number
  sync_time: string
  rss_url: string
  article_count: number
}

export interface SubscriptionListResult {
  code: number
  data: {
    list: Subscription[]
    total: number
  }
}

export interface AddSubscriptionParams {
  mp_name: string
  mp_id: string
  avatar: string
  mp_intro?: string
}

export const getSubscriptions = (params?: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<SubscriptionListResult>('/wx/mps', { params: apiParams })
}

export const getSubscriptionDetail = (mp_id: string) => {
  return http.get<{code: number, data: Subscription}>(`/wx/mps/${mp_id}`)
}

// 添加订阅公众号信息
export const addSubscription = (data: AddSubscriptionParams) => {
  return http.post<{code: number, message: string}>('/wx/mps', data)
}
export const deleteMpApi = (mp_id: string) => {
  return http.delete<{code: number, message: string}>(`/wx/mps/${mp_id}`)
}

export const deleteSubscription = (mp_id: string) => {
  return http.delete<{code: number, message: string}>(`/wx/mps/${mp_id}`)
}

// 更新订阅公众号文章列表 
export const UpdateMps = (mp_id: string) => {
  return http.get<{code: number, message: string}>(`/wx/mps/update/${mp_id||'all'}`)
}

// 更新订阅公众号信息
export const updateSubscription = (mp_id: string, data: Partial<Subscription>) => {
  return http.put<{code: number, message: string}>(`/wx/mps/${mp_id}`, data)
}
export const searchBiz = (kw: string, params: { page?: number; pageSize?: number }) => {
  const apiParams = {
    offset: (params?.page || 0) * (params?.pageSize || 10),
    limit: params?.pageSize || 10
  }
  return http.get<SubscriptionListResult>(`/wx/mps/search/${kw}`,{ params: apiParams })
}