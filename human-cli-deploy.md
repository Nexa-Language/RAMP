# EvoBench 镜像与 CLI 部署说明（人类操作 / 宿主机 + 容器）

本文档汇总「多 backend 评测镜像」在宿主机与容器内的推荐操作、**版本固定**方式，以及已知的 **Claude 安装脚本地区拦截** 与 **Codex 信任目录 / CODEX_HOME** 问题的处理方式。

---

## 0. 宿主机：用旧镜像起临时改镜像容器

把 `YOUR_IMAGE` 换成当前评测镜像（例如 `evobench-openhands:latest`）。若要在容器里联调挂载的 EvoBench 代码，加上 `-v`（路径改成你宿主机上的仓库绝对路径）。

```bash
docker rm -f evobench-image-fix 2>/dev/null || true
docker run -dit \
  --name evobench-image-fix \
  -v "/path/to/EvoBench:/workspace/EvoBench:ro" \
  YOUR_IMAGE \
  bash
```

- **语法**：`docker rm -f` 删同名容器；`docker run -dit` 后台交互 tty；`-v 宿主机:容器:ro` 只读挂载；最后是镜像与入口 `bash`。
- **含义**：得到一个可 `docker exec` 进去改环境、最后用 `docker commit` 固化为新镜像的临时容器。

进入容器：

```bash
docker exec -it evobench-image-fix bash
```

- **语法**：在运行中容器里执行交互式 `bash`。
- **含义**：后续 `apt`/`npm`/`curl` 都在容器可写层执行。

---

## 1. 镜像盘点（容器内）

```bash
uname -m
cat /etc/os-release || true
command -v python3 python node npm curl ca-certificates git || true
python3 --version 2>/dev/null || true
node --version 2>/dev/null || true
npm --version 2>/dev/null || true
```

- **语法**：`uname -m` 看架构；`command -v` 查 PATH；`2>/dev/null || true` 避免缺命令时中断脚本。
- **含义**：确认是 `x86_64` 还是 `aarch64`，以及是否有 Python/Node 等依赖。

```bash
command -v claude cc-switch codex kimi || true
claude --version 2>/dev/null || true
cc-switch --version 2>/dev/null || true
codex --version 2>/dev/null || true
kimi --version 2>/dev/null || true
```

- **含义**：对照计划做 CLI 盘点；**当前 EvoBench 的 `claude` backend 会要求 PATH 上同时存在 `claude` 与 `cc-switch`**（见 `src/core/_agent_backends.py`）。

---

## 2. 系统依赖（Debian/Ubuntu 系示例）

```bash
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg git \
  build-essential \
  python3 python3-venv python3-pip
```

- **含义**：HTTPS、下载脚本、编译原生模块、Python 运行环境。

Node.js LTS（示例 20.x；团队可换版本）：

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
node --version && npm --version
```

- **语法**：`curl -fsSL` 拉安装脚本并交给 bash；然后 `apt-get install nodejs`。
- **含义**：为 `npm install -g @openai/codex` 等提供 Node；**企业环境若不允许 NodeSource，请改用内部 apt 源或自带 node 层**。

---

## 3. Codex CLI（推荐：npm 固定版本）

```bash
npm view @openai/codex version
CODEX_VER="$(npm view @openai/codex version)"
npm install -g "@openai/codex@${CODEX_VER}"
hash -r
codex --version
```

- **语法**：`npm view 包 version` 查 registry 上 latest 版本号；`npm install -g "包@版本"` 全局钉死版本。
- **含义**：避免每次构建拉到不同次版本。参考：[Codex quickstart](https://developers.openai.com/codex/quickstart)、[@openai/codex](https://www.npmjs.com/package/@openai/codex)。

### 3.1 `CODEX_HOME` 不要用 `/tmp`（你已遇到限制）

Codex 会拒绝把状态目录放在 `**/tmp` 树下**（安全/信任模型）。请改用例如：

- 用户家目录下：`export CODEX_HOME="${HOME}/.codex-evobench-smoke"`
- 或持久工作区下：`export CODEX_HOME="/workspace/codex-smoke-${RANDOM}"`（需保证父目录可写且**不在** `/tmp`）

```bash
mkdir -p "${CODEX_HOME}"
```

- **含义**：`CODEX_HOME` 下放 `config.toml`、`auth.json` 等；路径需符合 Codex 校验规则。

### 3.2 `Not inside a trusted directory and --skip-git-repo-check was not specified`

Codex 默认要求当前工作目录在某个 **受信任的 Git 仓库** 内。你在 `/workspace` 根目录直接跑时，若该目录**不是** git 根或未被标记为 trust，会报错。

**做法 A（推荐 smoke）**：在**已是 git 仓库根**的目录下执行（例如挂载的 EvoBench 仓库根，且存在 `.git`）。第三方网关下必须指定 **模型 id** 与 **OpenAI-compatible base_url**（否则 Codex 可能仍走默认官方端点或默认模型，与 EvoBench 运行时行为不一致）。

```bash
cd /workspace/EvoBench
export CODEX_HOME="${HOME}/.codex-evobench-smoke"
mkdir -p "${CODEX_HOME}"

# 改成网关上真实存在的 model id（与 api_keys.local.md 里该 key 对应的模型一致）
export CODEX_MODEL="kimi-k2.6"
# 改成该 key 对应的 base_url（须带网关要求的 path，常见为 .../v1）
export OPENAI_BASE_URL="https://aihub.arcsysu.cn/v1"
export OPENAI_API_KEY='sk-...'

cat > "${CODEX_HOME}/config.toml" <<EOF
model = "${CODEX_MODEL}"
openai_base_url = "${OPENAI_BASE_URL}"
EOF

codex exec --sandbox read-only --json "只回复一个字：好"
```

- **语法**：`cd` 到含 `.git` 的目录；`CODEX_HOME` 下放本段生成的 `config.toml`（顶层 `model` 与 `openai_base_url`，见 [Codex Advanced Configuration](https://developers.openai.com/codex/config-advanced)）；`OPENAI_API_KEY` 供内置 OpenAI provider 使用；最后 `codex exec` 非交互。
- **含义**：满足「在受信目录内」；**显式绑定网关与模型**，与仓库内 `src/core/_agent_backends.py` 为 Codex 写入的配置思路一致；`--sandbox read-only` 限制写盘，适合冒烟。

**等价一行式**（不写文件、仅单次覆盖；TOML 字符串需按 Codex 文档加引号）。仍需 **`cd` 到信任 git 根**（或另加 `--skip-git-repo-check`），并设置 **`CODEX_HOME`（非 `/tmp`）** 与 **`OPENAI_API_KEY`**：

```bash
cd /workspace/EvoBench
export CODEX_HOME="${HOME}/.codex-evobench-smoke"
mkdir -p "${CODEX_HOME}"
export CODEX_MODEL="kimi-k2.6"
export OPENAI_BASE_URL="https://aihub.arcsysu.cn/v1"
export OPENAI_API_KEY='sk-...'

codex --config "model=\"${CODEX_MODEL}\"" --config "openai_base_url=\"${OPENAI_BASE_URL}\"" \
  exec --sandbox read-only --json "只回复一个字：好"
```

- **语法**：`--config key=TOML值` 可多次；`exec` 子命令在最后。
- **含义**：与上面 `config.toml` 等价，适合快速验证；引号在 shell 里较易写错，不熟时优先用 `config.toml`。

**做法 B（明确跳过 git 根检查，慎用）**：官方/社区讨论里存在 `--skip-git-repo-check`，用于不在信任 git 根时强制执行。**注意**：在「非 git 根」目录使用该 flag 时，Codex 可能会扫描子树里的 `.git` 并产生意外行为（见 [openai/codex#15541](https://github.com/openai/codex/issues/15541)）。仅建议在隔离空目录或明确知晓目录结构时使用：

```bash
cd /workspace/some-empty-dir
mkdir -p /workspace/codex-home-smoke
export CODEX_HOME="/workspace/codex-home-smoke"
export CODEX_MODEL="kimi-k2.6"
export OPENAI_BASE_URL="https://aihub.arcsysu.cn/v1"
export OPENAI_API_KEY='sk-...'

cat > "${CODEX_HOME}/config.toml" <<EOF
model = "${CODEX_MODEL}"
openai_base_url = "${OPENAI_BASE_URL}"
EOF

codex exec --skip-git-repo-check --sandbox read-only --json "只回复一个字：好"
```

- **语法**：`--skip-git-repo-check` 跳过「必须在信任 git 目录」检查；模型与网关仍通过 `CODEX_HOME/config.toml` 指定。
- **含义**：解决你看到的报错；**不要在包含大量无关 git 子仓库的大目录里随便用**。

---

## 4. Claude Code CLI：地区拦截时不要用 `claude.ai/install.sh` 直装

### 4.1 现象（你已遇到）

执行：

```bash
curl -fsSL https://claude.ai/install.sh | bash -
```

若出口 IP 被判定为「不可用地区」，**HTTP 返回的是 HTML 页面**（例如标题含 `App unavailable in region`），不是 shell 脚本。此时若保存为 `install.sh` 再 `bash install.sh`，会出现：

```text
syntax error near unexpected token `<'
```

因为第一行是 `<!DOCTYPE html>`。

### 4.2 正确习惯：先校验再执行（避免把 HTML 当脚本）

```bash
curl -fsSL -o /tmp/claude-install.sh https://claude.ai/install.sh
head -n 5 /tmp/claude-install.sh
```

- **语法**：`-o` 写文件；`head` 看前几行。
- **含义**：若看到 `<!DOCTYPE` 或 `<html`，**立刻停止**，不要 `bash /tmp/claude-install.sh`。

更稳妥（失败非 200 则 curl 退出非零）：

```bash
curl -fSL -o /tmp/claude-install.sh https://claude.ai/install.sh
```

- **语法**：`-f` 让 4xx/5xx 时 curl 失败。
- **含义**：地区页若是 403/451 等，你会直接看到 curl 报错而不是 silent 的 HTML。

### 4.3 地区不可用时的替代安装（推荐容器内用 npm 钉版本）

在已有 Node/npm 的镜像里：

```bash
npm view @anthropic-ai/claude-code version
CLAUDE_PKG_VER="$(npm view @anthropic-ai/claude-code version)"
npm install -g "@anthropic-ai/claude-code@${CLAUDE_PKG_VER}"
hash -r
claude --version
```

- **语法**：与 Codex 相同的全局钉版本。
- **含义**：绕过 `claude.ai` 安装脚本；包见 [@anthropic-ai/claude-code](https://www.npmjs.com/package/@anthropic-ai/claude-code)。**注意**：Anthropic 文档可能标注 npm 为 deprecated，但在「地区无法下载 install.sh」时这是常见工程折中；以你方合规为准。

其他可选方案（择一）：

- 在**允许访问 Claude 下载域**的网络环境构建镜像，再 `docker save`/`docker load` 到评测区。
- 使用企业批准的**离线安装包**或内部制品库中的同版本 `claude` 二进制。

---

## 5. Kimi Code CLI（官方脚本或 uv 钉版本）

官方一键安装：

```bash
curl -LsSf https://code.kimi.com/install.sh | bash
hash -r
kimi --version
```

- **含义**：安装 `kimi`；文档见 [Getting Started](https://moonshotai.github.io/kimi-cli/en/guides/getting-started.html)。

用 PyPI 精确版本（示例思路）：

```bash
pip install "kimi-cli==$(python3 - <<'PY'
import json, urllib.request
print(json.load(urllib.request.urlopen("https://pypi.org/pypi/kimi-cli/json"))["info"]["version"])
PY
)"
kimi --version
```

- **含义**：把 Kimi CLI 锁到发布在 PyPI 的某一确切版本（需镜像内 Python/pip 可用）。

---

## 6. cc-switch（GitHub Release 固定版本）

**只从官方仓库下载**：[https://github.com/farion1231/cc-switch/releases](https://github.com/farion1231/cc-switch/releases)

以 `v3.15.0`、`Linux x86_64`、`.deb` 为例（文件名以 release 页为准）：

```bash
CCSWITCH_VER="v3.15.0"
DEB="CC-Switch-${CCSWITCH_VER}-Linux-x86_64.deb"
curl -fL "https://github.com/farion1231/cc-switch/releases/download/${CCSWITCH_VER}/${DEB}" -o "/tmp/${DEB}"
apt-get install -y "/tmp/${DEB}" || apt-get -f install -y
```

- **含义**：安装固定版本 cc-switch；ARM 机器请换 `Linux-arm64` 资产。

确认可执行文件名（EvoBench 当前检查的是 `**cc-switch`** 在 PATH 上）：

```bash
command -v cc-switch || true
dpkg -L cc-switch 2>/dev/null | head -n 50
```

若只有 `CC-Switch` 而无 `cc-switch`，可（路径以 `dpkg -L` 为准）：

```bash
ln -sf /usr/bin/CC-Switch /usr/local/bin/cc-switch   # 示例：请按实际路径改
command -v cc-switch
```

---

## 7. 网关连通性（OpenAI-compatible，两个 base_url）

**不要把 key 写进镜像层**；测试时用当前 shell 的 `export`，测完 `unset`。

```bash
export OPENAI_API_KEY='sk-...'
export TEST_BASE_URL='https://aihub.arcsysu.cn/v1'
curl -sS "${TEST_BASE_URL}/chat/completions" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.5","messages":[{"role":"user","content":"ping"}],"max_tokens":8}'
```

- **含义**：验证 OpenAI-compatible HTTP 是否通；第二个 base `https://www.duckcoding.ai` 请按网关文档补全路径（常见为带 `/v1`）。

---

## 8. 固化新镜像并在宿主机跑 EvoBench smoke

```bash
docker commit evobench-image-fix evobench-agent:20260517-multi
```

在宿主机仓库根：

```bash
python src/main.py launch --backend openhands --image evobench-agent:20260517-multi \
  --model kimi-k2.6 --tasks 0 --run-prefix smoke --parallel 1
```

再测 `codex` / `kimi` / `claude`（`--backend` 必填）：

```bash
python src/main.py launch --backend codex --image evobench-agent:20260517-multi \
  --model kimi-k2.6 --tasks 0 --run-prefix smoke-codex --parallel 1
```

失败时查看：`eval/container-runs/<run_id>/console.log`、`openhands_report.json`、`agent-events/`。

---

## 9. 版本审计清单（建议贴到 wiki）

```bash
{
  date -u
  uname -a
  python3 --version
  node --version
  npm --version
  claude --version 2>/dev/null
  cc-switch --version 2>/dev/null
  codex --version 2>/dev/null
  kimi --version 2>/dev/null
} | tee /tmp/evobench-image-versions.txt
```

- **含义**：镜像 tag 与 CLI 版本对应表，满足「镜像修改计划」文档记录要求。

---

## 附录：你遇到的两条报错的对应关系


| 现象                                | 原因                                                      | 处理                                                           |
| --------------------------------- | ------------------------------------------------------- | ------------------------------------------------------------ |
| `install.sh: line 1: '<!DOCTYPE`… | `https://claude.ai/install.sh` 返回地区拦截 **HTML**，不是 shell | 用 `curl -f` 先验；改 **npm 安装** 或换网络/离线包                         |
| `Not inside a trusted directory…` | 当前目录不是 Codex 认为的受信 git 根                                | `cd` 到信任仓库根，或 `**codex exec --skip-git-repo-check`**（慎用子树扫描） |
| `CODEX_HOME` 不能放 `/tmp`           | Codex 对状态目录路径的安全限制                                      | 使用 `$HOME/.codex-...` 或 `/workspace/...` 等非 `/tmp` 路径        |


