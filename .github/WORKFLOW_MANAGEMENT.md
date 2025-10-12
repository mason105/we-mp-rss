# Workflow 管理说明

## 当前策略

这个仓库是上游的 fork，我们只保留以下两个 workflow：
- `docker-build.yaml` - Docker 镜像构建和推送
- `deploy.yaml` - 部署到服务器

**我们使用 Git Sparse-Checkout 技术自动过滤其他 workflow 文件。**

## Sparse-Checkout 配置

### 什么是 Sparse-Checkout？

Sparse-Checkout 是 Git 的原生功能，允许你只检出仓库的一部分文件到工作目录中。类似 `.gitignore`，但作用于已追踪的文件。

### 当前配置

配置位置：`.git/info/sparse-checkout`

```
/*
.github/*
\!.github/workflows/*
/.github/workflows/deploy.yaml
/.github/workflows/docker-build.yaml
```

这个配置的含义：
- `/*` - 包含所有根目录文件和目录
- `.github/*` - 包含 .github 目录下的所有内容
- `\!.github/workflows/*` - **排除** workflows 目录下的所有文件
- `/.github/workflows/deploy.yaml` - 但**保留** deploy.yaml
- `/.github/workflows/docker-build.yaml` - 但**保留** docker-build.yaml

### 从上游同步代码

**完全自动化，无需任何手动操作：**

```bash
# 获取上游更新
git fetch upstream

# 合并上游代码
git merge upstream/main

# 就这样！上游的其他 workflow 文件会自动被忽略，不会出现在你的工作目录中
```

### 查看当前配置

```bash
# 查看 sparse-checkout 规则
git sparse-checkout list

# 验证配置是否启用
git config core.sparseCheckout  # 应该返回 true
```

### 添加新的 workflow 文件

如果将来需要添加其他 workflow：

```bash
git sparse-checkout add /.github/workflows/new-workflow.yaml
```

### 完全禁用 Sparse-Checkout

如果需要看到所有文件：

```bash
git sparse-checkout disable
```

## .gitattributes 策略

我们同时设置了 `.gitattributes` 使用 `merge=ours` 策略作为额外保护：
- 当合并上游代码时，workflows 目录会优先使用我们的版本
- 这是双重保护机制

## 注意事项

如果上游更新了 `docker-build.yaml` 或 `deploy.yaml`，需要手动检查并合并有用的更改：

```bash
# 查看上游的更改
git show upstream/main:.github/workflows/docker-build.yaml
git show upstream/main:.github/workflows/deploy.yaml

# 如果需要，手动应用更改
```
