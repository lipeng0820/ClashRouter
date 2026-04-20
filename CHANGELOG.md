# Changelog

## 2026-04-20: 修复 Google Gemini 流量分裂问题

### 问题描述
Google Gemini 的流量被分拆到两个不同的 IP 地址上，存在账户封号风险。

### 根因
`skip-proxy` (第4行) 包含 `*.google.com`、`*.googleapis.com`、`*.googleusercontent.com` 通配域名，
导致部分 Gemini 流量绕过代理走 DIRECT（真实 IP），而 `[Rule]` 中的 AI固定出口规则又将另一部分流量
路由到代理节点 IP。同一会话从两个不同 IP 发出请求，触发 Google 风控。

### 修复内容

#### 1. 从 `skip-proxy` 移除 Google 通配域名
- 移除: `*.googleapis.com, googleapis.com`
- 移除: `*.googleusercontent.com, googleusercontent.com`
- 移除: `*.google.com, google.com`

#### 2. 收窄 AI固定出口 规则为 Gemini 专用域名
- 移除过宽规则: `googleapis.com`, `googleusercontent.com`, `gstatic.com`, `apis.google.com`, `ogs.google.com`
- 新增精准规则: `alkalimakersuite-pa.googleapis.com`, `proactivebackend-pa.googleapis.com`
- 保留: `gemini.google.com`, `bard.google.com`, `aistudio.google.com`, `generativelanguage.googleapis.com`, `accounts.google.com`

#### 3. 清理死规则
- 删除: `DOMAIN-SUFFIX,bard.google.com,PROXY` (被 AI固定出口 同名规则覆盖)
- 删除: `DOMAIN-SUFFIX,generativelanguage.googleapis.com,PROXY` (被 AI固定出口 同名规则覆盖)

### 修复后效果
- Gemini 所有流量统一走 AI固定出口（单一代理 IP）
- YouTube/Gmail/Drive 等其他 Google 服务恢复走普通 PROXY
- `gstatic.com` 恢复走 PROXY（第3390行规则生效）
- `fonts.gstatic.com` 恢复走 DIRECT（第142行精确匹配生效）
