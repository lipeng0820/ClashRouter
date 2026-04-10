# ClashRouter - 多协议高精度分流规则生成引擎

本项目旨在解决多平台（Clash, Sing-box, Shadowrocket, Surge, Surfboard）分流规则的标准化同步问题，并特别强化了“硬骨头”内网/金融域名的直连免劫持逻辑。

---

## 🛠️ 核心功能

- **一键全端同步**：读取 Markdown 格式的高精度规则源，自动转化为各客户端适配的 JSON/YAML/INI 格式。
- **“硬骨头”穿透逻辑**：
  - **DNS 免疫**：强制注入 `nameserver-policy`。使用 `dhcp://system` (Meta 内核) 或 `local` (Sing-box) 绕过系统 DNS 环回劫持，解决开启 TUN 模式下的 DNS 死锁。
  - **路由优先级**：规则始终插入至配置文件最顶部，拥有最高处理权。
  - **内核豁免**：自动配置 `fake-ip-filter` 和 `skip-proxy`，确保敏感域名不触发代理内核。
- **内网/金融优先**：预设了主流远控、内地银行、香港虚拟银行及底层风控测绘域名的直连名单。

## 📂 项目结构

- `migrate_rules.py`: **核心处理器**。包含解析 MD 规则、格式转化、以及各平台（Clash, Sing-box 等）的注入逻辑。
- `manage.py`: **管理工具**。提供简单的 CLI 界面，用于新增域名、执行同步、提交 GitHub。
- `分流规则参考.md`: **解析源**。包含上万条高精度国内外分流规则原始定义。
- `v2b/`: **输出目录**。存放所有适配后的 `.json` 配置文件。

---

## 🤖 LMP 助手指南 (For AI Coding Assistants)

如果你是接手此项目的大模型，请遵循以下逻辑进行维护与扩充：

### 1. 扩充分流规则
- 所有的“硬骨头”域名都在 `migrate_rules.py` 的 `HARDBONES` 数组中维护。
- **场景判断**：
  - 如果用户反馈某个 App（如银行）提示“网络不安全”，通常是 RASP 侦测到了代理。应检查其底层的风控域名（如 `*.alipay.com`, `*.antgroup.com` 等）是否已全部加入 `HARDBONES`。
  - 如果用户反馈开启 TUN 后无法连接内网域名（如 `corp.xxxx.com`），说明发生了 DNS 死锁循环。需确保该域名指向了 `dhcp://system` 或 `direct` 策略。

### 2. 跨平台适配逻辑
- **Clash (YAML)**: 处理 `fake-ip-filter` 和 `nameserver-policy`。
- **Sing-box (JSON)**: 维护 `dns.servers` 中的 `local` 节点，并在 `route.rules` 中设置 `dns` 协议过滤。
- **Shadowrocket (INI)**: 修改 `skip-proxy` 全局参数并将规则注入 `[Rule]` 区间。

### 3. 操作流建议
当需要增加新地址时，请通过修改 `HARDBONES` -> 运行 `migrate_rules.py` -> `git push` 的顺序完成闭环。

---

## 🚀 快速开始

### 增加域名
运行管理工具：
```bash
python3 manage.py
```
选择 `1. Add new Hardbone domain` 即可。

### 手动刷新所有模版
```bash
python3 migrate_rules.py
```

## ⚠️ 隐私声明
本项目代码公开。请勿在 `README.md` 或提交记录中提及任何具体的公司内部隐私域名。所有公司级域名应以 `corp.xxxx.com` 等占位符表述。
