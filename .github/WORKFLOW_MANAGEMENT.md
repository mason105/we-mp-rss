# Workflow 管理说明

## 当前策略

这个仓库是上游的 fork，我们只保留以下两个 workflow：
- `test-docker-build.yaml` - Docker 镜像构建和测试
- `deploy.yaml` - 部署到服务器

其他 workflow 文件已被删除，因为它们不适用于我们的部署环境。

## 从上游同步代码

### 方法 1：使用自动清理脚本（推荐）

运行同步脚本会自动合并上游代码并清理不需要的 workflow：

```bash
./.github/sync-upstream.sh
```

### 方法 2：手动同步

如果你更喜欢手动控制：

```bash
# 1. 获取上游更新
git fetch upstream

# 2. 合并上游代码（.gitattributes 会自动使用我们的 workflow 版本）
git merge upstream/main

# 3. 如果有新的不需要的 workflow 文件被引入，手动删除它们
cd .github/workflows
ls -la  # 检查是否有新文件
rm unwanted-workflow.yaml  # 删除不需要的文件

# 4. 提交更改（如果有）
git add .
git commit -m "chore: cleanup workflows after upstream sync"
```

## .gitattributes 策略

我们设置了 `.gitattributes` 使用 `merge=ours` 策略：
- 当合并上游代码时，workflows 目录会优先使用我们的版本
- 这可以减少合并冲突，但也意味着需要手动检查上游对保留的 workflow 的更新

## 注意事项

如果上游更新了 `test-docker-build.yaml` 或 `deploy.yaml`，需要手动检查并合并有用的更改：

```bash
# 查看上游的更改
git show upstream/main:.github/workflows/test-docker-build.yaml
git show upstream/main:.github/workflows/deploy.yaml

# 如果需要，手动应用更改
```
