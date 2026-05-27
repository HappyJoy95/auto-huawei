# 模块开发指南

请参阅 [shared/MODULE_DEVELOPMENT.md](../shared/MODULE_DEVELOPMENT.md)

Windows 平台特有说明：
- 敏感配置文件放在 `windows/modules/<module_name>/` 下（`config.json`、`config.yaml`）
- 共享模块代码在 `shared/modules/` 中，无需在本目录维护副本
- 平台特有模块（inspection、xiaohongshu）直接放在 `windows/modules/` 下
- ADB 相关模块需要在 `requirements.txt` 中包含 `pure-python-adb`
