<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  getMessageTask, 
  updateMessageTask, 
  deleteMessageTask 
} from '@/api/messageTask'
import type { MessageTask, MessageTaskUpdate } from '@/types/messageTask'
import { Modal } from '@arco-design/web-vue'

const route = useRoute()
const router = useRouter()
const messageTask = ref<MessageTask | null>(null)
const loading = ref(false)
const error = ref('')
const isEdit = ref(false)
const formModel = reactive<MessageTaskUpdate>({
  message_template: '',
  web_hook_url: '',
  status: 0
})

// 获取消息任务详情
const fetchMessageTask = async () => {
  try {
    loading.value = true
    const data = await getMessageTask(route.params.id as string)
    messageTask.value = data
    Object.assign(formModel, {
      message_template: data.message_template,
      web_hook_url: data.web_hook_url,
      status: data.status
    })
  } catch (err) {
    error.value = err instanceof Error ? err.message : '获取消息任务失败'
  } finally {
    loading.value = false
  }
}

// 编辑操作
const handleEdit = () => {
  isEdit.value = true
}

// 删除操作
const handleDelete = () => {
  if (!messageTask.value) return
  
  Modal.confirm({
    title: '确认',
    content: '确定要删除此消息任务吗？',
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteMessageTask(messageTask.value!.id)
        router.push('/message-tasks')
      } catch (err) {
        error.value = err instanceof Error ? err.message : '删除消息任务失败'
      }
    }
  })
}

// 保存操作
const handleSave = async () => {
  try {
    if (messageTask.value) {
      await updateMessageTask(messageTask.value.id, formModel)
      await fetchMessageTask()
      isEdit.value = false
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '更新消息任务失败'
  }
}

// 取消操作
const handleCancel = () => {
  if (messageTask.value) {
    Object.assign(formModel, {
      message_template: messageTask.value.message_template,
      web_hook_url: messageTask.value.web_hook_url,
      status: messageTask.value.status
    })
  }
  isEdit.value = false
}

onMounted(() => {
  fetchMessageTask()
})
</script>

<template>
  <div class="message-task-detail">
    <a-page-header 
      :title="messageTask ? `消息任务 #${messageTask.id}` : '消息任务详情'"
      :subtitle="messageTask?.message_template"
      @back="router.push('/message-tasks')"
    >
      <template #extra>
        <a-space>
          <a-button v-if="!isEdit" type="primary" @click="handleEdit">
            <template #icon>
              <icon-edit />
            </template>
            编辑
          </a-button>
          <a-button v-if="!isEdit" status="danger" @click="handleDelete">
            <template #icon>
              <icon-delete />
            </template>
            删除
          </a-button>
          <a-button v-if="isEdit" type="primary" @click="handleSave">
            <template #icon>
              <icon-save />
            </template>
            保存
          </a-button>
          <a-button v-if="isEdit" @click="handleCancel">
            <template #icon>
              <icon-close />
            </template>
            取消
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-card>
      <a-space direction="vertical" fill>
        <a-alert v-if="error" type="error" show-icon>{{ error }}</a-alert>
        
        <div v-if="loading">
          <a-skeleton :animation="true">
            <a-skeleton-line :rows="5" />
          </a-skeleton>
        </div>
        <div v-else-if="messageTask">
          <a-descriptions v-if="!isEdit" :column="1" bordered>
            <a-descriptions-item label="ID">
              {{ messageTask.id }}
            </a-descriptions-item>
            <a-descriptions-item label="消息模板">
              {{ messageTask.message_template }}
            </a-descriptions-item>
            <a-descriptions-item label="Webhook地址">
              {{ messageTask.web_hook_url }}
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="messageTask.status === 1 ? 'green' : 'orange'">
                {{ messageTask.status === 1 ? '启用' : '禁用' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ messageTask.created_at }}
            </a-descriptions-item>
          </a-descriptions>

          <a-form v-else :model="formModel" layout="vertical">
            <a-form-item field="message_template" label="消息模板" required>
              <a-textarea
                v-model="formModel.message_template"
                placeholder="请输入消息模板"
                :auto-size="{ minRows: 3, maxRows: 6 }"
              />
            </a-form-item>
            <a-form-item field="web_hook_url" label="Webhook地址" required>
              <a-input
                v-model="formModel.web_hook_url"
                placeholder="请输入webhook地址"
              />
            </a-form-item>
            <a-form-item field="status" label="状态" required>
              <a-select v-model="formModel.status" placeholder="请选择状态">
                <a-option :value="0">禁用</a-option>
                <a-option :value="1">启用</a-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>
        <div v-else>
          <a-empty description="未找到消息任务" />
        </div>
      </a-space>
    </a-card>
  </div>
</template>

<style scoped>
.message-task-detail {
  padding: 20px;
}
</style>