# Windows WSL Bridge Skill

简体中文 | [English](README.md)

`windows-wsl-bridge` 是一个面向 Windows 端 agent 的可复用 skill，用来安全访问用户的 WSL Linux 发行版：包括检查、读取、写入文件，以及通过 `wsl.exe` 运行 Linux 命令。

核心场景是：Windows 桌面 agent 可以访问 Windows 文件系统并调用 `wsl.exe`，但真正需要使用的 Linux 工具、服务、用户目录或开发环境位于 WSL 中。

> 注意：示例使用 `Ubuntu-24.04`、Windows 用户 `LTY`、Linux 用户 `lty` 作为本机占位示例。迁移到其他机器前，必须先确认真实发行版名称、用户名、路径和沙盒行为。

## 覆盖内容

- 从 Windows 发现 WSL 发行版。
- 通过 `wsl.exe -d <DistroName> -- ...` 运行 Linux 命令。
- 通过 `\\wsl.localhost\<DistroName>\...` 从 Windows 读写 WSL 文件。
- 让 WSL 工具操作 `/mnt/<drive>/...` 下的 Windows workspace。
- 处理 Windows agent 沙盒身份与真实用户身份不一致的问题。
- 避免危险的文件系统、服务、网络和凭据处理操作。

## Skill 结构

```text
windows-wsl-bridge-skill/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── LICENSE
├── agents/
│   └── openai.yaml
└── tests/
    └── test_skill_integrity.py
```

## 安装方式

把包含 `SKILL.md` 的目录安装或复制到你的 agent 使用的 skills 目录中。对于 Codex 风格的本地 skill，最终目录根部应直接包含 `SKILL.md`。

如果你的 agent 支持 GitHub 托管 skill，可以指向该仓库，或把该文件夹复制到已配置的 skills 路径。

## 快速开始

列出 WSL 发行版：

```powershell
wsl.exe --list --all --verbose
```

在已发现的发行版中做只读检查：

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "whoami; pwd; uname -a"
```

从 Windows 读取 WSL 文件：

```powershell
Get-Content "\\wsl.localhost\Ubuntu-24.04\home\lty\README.md"
```

让 Linux 工具操作 Windows workspace：

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "cd /mnt/c/Users/LTY/Desktop/Software/codex_workspace && pwd"
```

## 安全模型

先做只读发现。项目文件操作默认使用普通 Linux 用户。只有在明确属于系统级任务、用户批准了具体目标和回滚方案后，才使用提升后的 Linux 权限。

不要展示凭据材料、完整环境变量、私钥材料、token 文件或认证存储内容。不要直接修改 WSL 的底层虚拟磁盘文件。

## 验证

在仓库根目录运行轻量完整性测试：

```bash
python3 tests/test_skill_integrity.py
```

如果要在 Hermes 中验证，也建议对位于 Linux 文件系统中的 skill 副本运行 Hermes skill security scanner。由于 Windows 挂载目录在 WSL 中可能显示为可执行权限，直接扫描 `/mnt/c` 下的文件可能产生本地权限误报。

## License

MIT。见 `LICENSE`。
