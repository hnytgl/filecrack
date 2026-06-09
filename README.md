# FileCrack

FileCrack 是一个面向授权场景的常见加密文件密码恢复工具，支持单个密码尝试、内置弱密码检查、字典档和多线程批量尝试，自动识别多种文件格式。

请只对你拥有所有权或明确授权的文件使用本工具。

## 安装

基础安装（支持标准 ZipCrypto）：

```bash
pip install filecrack
```

完整格式支持（ZIP AES-256 / RAR / 7z / PDF / Office / WPS）：

```bash
pip install "filecrack[full]"
```

从源码安装：

```bash
pip install -e ".[full]"
```

## 快速使用

```bash
# 单个密码尝试
filecrack ./locked.zip -p "my-secret"

# 内置弱密码检查（20+ 常见弱密码）
filecrack ./locked.pdf --weak-check

# 字典档爆破
filecrack ./locked.zip -w ./dict.txt -t 8

# 组合：单密码 + 弱密码 + 字典档
filecrack ./locked.docx -p "2026@Company" --weak-check -w ./dict.txt -t 8

# 脚本中只输出密码本身
filecrack ./locked.pdf -w ./dict.txt --quiet
```

## 支持格式

| 格式 | 加密类型 | 依赖 | 说明 |
| --- | --- | --- | --- |
| ZIP | ZipCrypto（传统） | 内置 | Python 标准库原生支援 |
| ZIP | AES-256 | `pyzipper` | 由 7-Zip / WinZip 等工具产生时需完整安装 |
| RAR | RAR3/RAR5 | `rarfile` | 部分系统还需 `unrar` / `bsdtar` |
| 7z | AES-256 | `py7zr` | |
| Office | ECMA-376 / AES | `msoffcrypto-tool` | `.doc` / `.docx` / `.xls` / `.xlsx` / `.ppt` / `.pptx` |
| WPS | Office 相容 | `msoffcrypto-tool` | `.wps` / `.et` / `.el` / `.dps` / `.wpt` |
| PDF | RC4 / AES | `pikepdf` | |

> **提示**：若出现 `ZIP uses AES-256 encryption; install pyzipper` 错误，表示该 ZIP 使用 AES 加密而非传统 ZipCrypto，执行 `pip install "filecrack[full]"` 即可支援。

## 参数说明

| 参数 | 说明 |
| --- | --- |
| `target` | 需要恢复密码的文件路径 |
| `-p, --password` | 单个密码尝试 |
| `--weak-check` | 启用内置弱密码检查（20+ 常见弱密码） |
| `-w, --wordlist` | 字典档路径，每行一个候选密码 |
| `-t, --threads` | 线程数，默认使用 CPU 核心数 |
| `--encoding` | 字典档编码，默认 `utf-8` |
| `--format` | 强制指定格式：`zip`、`rar`、`7z`、`pdf`、`office`、`docx` 等 |
| `--chunk-size` | 每个线程任务批量尝试的密码数，默认 `512` |
| `--quiet` | 只输出找到的密码，便于脚本调用 |
| `--version` | 显示版本号 |

至少需要提供 `--password`、`--weak-check` 或 `--wordlist` 中的一种密码来源。

## 格式识别规则

FileCrack 默认依据文件头魔数识别格式（Magic Signature），而非扩展名：

| 魔数 | 识别为 |
| --- | --- |
| `PK\x03\x04` | ZIP（.docx / .xlsx / .pptx 则判断 Office） |
| `Rar!\x1a\x07` | RAR |
| `7z\xbc\xaf\x27\x1c` | 7z |
| `%PDF` | PDF |
| `\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1`（OLE2） | Office / WPS |

仅当无法读取文件头时回退到扩展名判断。因此，文件被改名或扩展名错误时仍能正确识别。

```bash
# 文件头损坏或非标准扩展名时强制指定格式
filecrack ./unknown.bin -w ./dict.txt --format zip
```

## 故障排除

| 问题 | 原因 | 解决 |
| --- | --- | --- |
| `ZIP uses AES-256 encryption; install pyzipper` | ZIP 使用 AES 加密，需 `pyzipper` | `pip install "filecrack[full]"` |
| `xxx 支持需要安装 xxx` | 对应格式的后端未安装 | `pip install "filecrack[full]"` |
| 未加密文件返回未找到 | 文件其实没有加密，正确密码是空字串 | 尝试 `-p ""` |
| 速度慢 | 单线程或字典太大 | 加 `-t` 参数提高线程数 |

## 退出码

- `0`：找到密码
- `1`：未找到密码  
- `2`：依赖缺失或后端错误

## 开发测试

```bash
pip install -e ".[test]"
python -m pytest
```

## 许可证

MIT
