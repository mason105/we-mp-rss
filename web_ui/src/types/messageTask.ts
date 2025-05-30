export interface MessageTask {
  id: number
  message_template: string
  web_hook_url: string
  mps_id: any // JSON类型
  status: number
  created_at: string
  updated_at: string
}

export interface MessageTaskCreate {
  message_template: string
  web_hook_url: string
  mps_id: any
  status?: number
}

export interface MessageTaskUpdate {
  message_template?: string
  web_hook_url?: string
  mps_id?: any
  status?: number
}