<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { 
  listMessageTasks, 
  createMessageTask, 
  updateMessageTask, 
  deleteMessageTask 
} from '@/api/messageTask'
import type { MessageTask, MessageTaskCreate, MessageTaskUpdate } from '@/types/messageTask'
import { Modal } from '@arco-design/web-vue'

const messageTasks = ref<MessageTask[]>([])
const loading = ref(false)
const error = ref('')
const pagination = reactive({
  current: 0,
  pageSize: 10,
  total: 0,
  showTotal: true,
  showPageSize: true
})
const searchForm = reactive({
  template: '',
  status: undefined as number | undefined
})
const visible = ref(false)
const isEdit = ref(false)
const currentTask = ref<MessageTask | null>(null)
const formModel = reactive<MessageTaskCreate & MessageTaskUpdate>({
  message_template: '',
  web_hook_url: '',
  status: 0
})

// 获取消息任务列表
const fetchMessageTasks = async () => {
  try {
    loading.value = true
    const res = await listMessageTasks({
      page: pagination.current,
      pageSize: pagination.pageSize,
      template: searchForm.template,
      status: searchForm.status
    })
    messageTasks.value = res.list
    pagination.total = res.total
  } catch (err) {
    error.value = err instanceof Error ? err.message : '获取消息任务列表失败'
  } finally {
    loading.value = false
  }
}

// 添加消息任务
const handleAdd = () => {
  isEdit.value = false
  currentTask.value = null
  Object.assign(formModel, {
    message_template: '',
    web_hook_url: '',
    status: 0
  })
  visible.value = true
}

// 编辑消息任务
const handleEdit = (task: MessageTask) => {
  isEdit.value = true
  currentTask.value = task
  Object.assign(formModel, {
    message_template: task.message_template,
    web_hook_url: task.web_hook_url,
    status: task.status
  })
  visible.value = true
}

// 删除消息任务
const handleDelete = (id: number) => {
  Modal.confirm({
    title: '确认',
    content: '确定要删除此消息任务吗？',
    okText: '删除',
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteMessageTask(id)
        fetchMessageTasks()
      } catch (err) {
        error.value = err instanceof Error ? err.message : '删除消息任务失败'
      }
    }
  })
}

// 提交表单
const handleSubmit = async () => {
  try {
    if (isEdit.value && currentTask.value) {
      await updateMessageTask(currentTask.value.id, formModel)
    } else {
      await createMessageTask(formModel)
    }
    visible.value = false
    fetchMessageTasks()
  } catch (err) {
    error.value = err instanceof Error ? err.message : '保存消息任务失败'
  }
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.current = page
  fetchMessageTasks()
}

onMounted(() => {
  fetchMessageTasks()
})
</script>

<template>
  <div class="message-task-list">
    <a-page-header title="消息任务管理" subtitle="管理您的消息任务">
      <template #extra>
        <a-button type="primary" @click="handleAdd">
          <template #icon>
            <icon-plus />
          </template>
          添加消息任务
        </a-button>
      </template>
    </a-page-header>

    <a-card>
      <a-space direction="vertical" fill>
        <a-alert v-if="error" type="error" show-icon>{{ error }}</a-alert>
        
        <a-form layout="inline" :model="searchForm">
          <a-form-item field="template" label="模板">
            <a-input v-model="searchForm.template" placeholder="按模板搜索" />
          </a-form-item>
          <a-form-item field="status" label="状态">
            <a-select v-model="searchForm.status" placeholder="选择状态" allow-clear>
              <a-option :value="0">禁用</a-option>
              <a-option :value="1">启用</a-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="fetchMessageTasks">搜索</a-button>
          </a-form-item>
        </a-form>

        <a-table
          :data="messageTasks"
          :loading="loading"
          :pagination="pagination"
          @page-change="handlePageChange"
          row-key="id"
        >
          <template #columns>
            <a-table-column title="ID" data-index="id" :width="80" />
            <a-table-column title="消息模板" data-index="message_template" />
            <a-table-column title="Webhook地址" data-index="web_hook_url" />
            <a-table-column title="状态" :width="120">
              <template #cell="{ record }">
                <a-tag :color="record.status === 1 ? 'green' : 'orange'">
                  {{ record.status === 1 ? '启用' : '禁用' }}
                </a-tag>
              </template>
            </a-table-column>
            <a-table-column title="创建时间" data-index="created_at" :width="180" />
            <a-table-column title="操作" :width="180">
              <template #cell="{ record }">
                <a-space>
                  <a-button size="mini" @click="handleEdit(record)">
                    <template #icon>
                      <icon-edit />
                    </template>
                  </a-button>
                  <a-button size="mini" status="danger" @click="handleDelete(record.id)">
                    <template #icon>
                      <icon-delete />
                    </template>
                  </a-button>
                  <router-link :to="`/message-tasks/${record.id}`">
                    <a-button size="mini">
                      <template #icon>
                        <icon-eye />
                      </template>
                    </a-button>
                  </router-link>
                </a-space>
              </template>
            </a-table-column>
          </template>
        </a-table>
      </a-space>
    </a-card>

    <a-modal
      v-model:visible="visible"
      :title="isEdit ? '编辑消息任务' : '添加消息任务'"
      @ok="handleSubmit"
      @cancel="visible = false"
    >
      <a-form :model="formModel" layout="vertical">
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
            placeholder="请输入Webhook地址"
          />
        </a-form-item>
        <a-form-item field="status" label="状态" required>
          <a-select v-model="formModel.status" placeholder="请选择状态">
            <a-option :value="0">禁用</a-option>
            <a-option :value="1">启用</a-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<style scoped>
.message-task-list {
  padding: 20px;
}
</style>