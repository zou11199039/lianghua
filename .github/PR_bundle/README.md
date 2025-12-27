PR Bundle: ci/qmt-client-tests

说明：
这个目录包含将变更应用到仓库的补丁文件和一个 PowerShell 脚本，适用于无法直接在仓库中使用 git 的情况。

文件：
- files/src_data_qmt_client.py -> 会被复制到 src/data/qmt_client.py
- files/ci_workflow.yml -> 会被复制到 .github/workflows/ci.yml
- files/test_qmt_client.py -> 会被复制到 tests/test_qmt_client.py
- files/test_receipt_parser_xtquant.py -> 会被复制到 tests/test_receipt_parser_xtquant.py
- files/ci-qmt-client-draft.md -> 会被复制到 .github/PRs/ci-qmt-client-draft.md
- apply_patch.ps1 -> PowerShell 脚本，执行后会备份原文件并替换为补丁版本

使用方法（PowerShell）：
1. 进入仓库根目录（D:\lianghua）
2. 运行： .\.github\PR_bundle\apply_patch.ps1
3. 检查变更，运行测试： .venv\Scripts\Activate.ps1; python -m pytest -q
4. 创建分支并提交：
   git init  # 如果尚未初始化
   git checkout -b ci/qmt-client-tests
   git add -A
   git commit -m "ci: add qmt_client tests; make xtquant import optional; add py3.13 to CI matrix"
   git remote add origin <your-repo-url>  # 如果需要
   git push -u origin ci/qmt-client-tests
5. 在 GitHub 创建 Draft PR（使用 gh 或 Web UI）。

注意：脚本会先备份被替换文件到相同路径下的 .bak 文件（例如 src/data/qmt_client.py.bak）。
如果遇到问题，可手动还原备份文件。
