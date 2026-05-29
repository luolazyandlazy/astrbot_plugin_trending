# astrbot_plugin_trending

AstrBot 插件，用于获取热榜内容，目前支持 GitHub 热榜。

## 功能特性

- 聊天命令：`/trending github`
- AI可调用工具：`get_trending`
- 每个项目包含字段：
  - 项目名称
  - 项目链接
  - 今日Star数
  - 编程语言
  - 项目描述
  - 中文摘要
- 摘要模式：
  - `astrbot_default` - 使用AstrBot当前模型
  - `custom_openai_compatible` - 使用自定义OpenAI兼容API
- 智能缓存机制：
  - 默认缓存5分钟，减少GitHub请求
  - 可配置缓存时长或完全禁用

## 安装方法

1. 将此插件放置在 `AstrBot/data/plugins/astrbot_plugin_trending/` 目录下。
2. 确保在 AstrBot 运行环境中安装了 `requirements.txt` 中的依赖。
3. 重启 AstrBot，如需要请启用插件。

## 命令使用

使用以下命令：

```text
/trending github
```

该命令会从 `https://github.com/trending` 获取当前所有热门项目。

## 插件配置

在 AstrBot WebUI 中配置以下字段：

- `summary_mode` - 摘要模式（astrbot_default / custom_openai_compatible）
- `custom_base_url` - 自定义OpenAI兼容端点URL
- `custom_api_key` - API密钥
- `custom_model` - 模型名称
- `custom_timeout_seconds` - 自定义摘要请求超时时间（默认30秒）
- `request_timeout_seconds` - 热榜页面请求超时时间（默认20秒）
- `cache_ttl_seconds` - 缓存有效期（默认300秒，设置为0禁用缓存）
- `user_agent` - 请求时使用的User-Agent

### 摘要模式说明

**astrbot_default**

- 使用当前对话中 AstrBot 选择的聊天提供商。

**custom_openai_compatible**

- 使用自定义的 OpenAI 兼容 `base_url`、`api_key` 和 `model`。
- 如果缺少必需字段，摘要生成将返回配置错误。

## 本地开发

1. 克隆此仓库到本地
2. 将插件目录同步到 `AstrBot/data/plugins/astrbot_plugin_trending/`
3. 修改代码后重启 AstrBot
4. 测试 `/trending github` 命令
5. 通过 AstrBot 的 LLM 工具流程测试 AI 工具调用

## 许可证

MIT License
