# Changelog

## [0.3.1](https://github.com/marcusburghardt/ansible-role-ai/compare/v0.3.0...v0.3.1) (2026-09-22)


### Bug Fixes

* enable release-please auto-tagging and inline Galaxy publish ([9581570](https://github.com/marcusburghardt/ansible-role-ai/commit/95815702651865620fd8a5296c49c4188ed2d08e))
* filter 'unknown' project names from dashboard panels ([1c2dbd8](https://github.com/marcusburghardt/ansible-role-ai/commit/1c2dbd889076ef8eee88da26c627a58f33c2af3f))
* metrics plugin loader missing named export ([66b5bd8](https://github.com/marcusburghardt/ansible-role-ai/commit/66b5bd8c7bf08649f64b1c8d71f218d53fb54ede))


### Miscellaneous

* **main:** release 0.3.0 ([c801a32](https://github.com/marcusburghardt/ansible-role-ai/commit/c801a32f132676871e3db9de9ccdfe19f586ae9b))

## [0.3.0](https://github.com/marcusburghardt/ansible-role-ai/compare/v0.2.0...v0.3.0) (2026-09-18)


### ⚠ BREAKING CHANGES

* ai_grafana_metrics_data_dir renamed to ai_opencode_metrics_data_dir. Playbooks referencing the old variable name must be updated.

### Features

* add local install mode for opencode-metrics plugin ([5ad71a6](https://github.com/marcusburghardt/ansible-role-ai/commit/5ad71a6df261f3ecd50c156a0608698049585fb7))
* add openspec change for default metrics plugin ([9ab606f](https://github.com/marcusburghardt/ansible-role-ai/commit/9ab606fa0ba1b27d694474984cbfcfe44ac67893))
* restructure dashboard with sub-agent analytics and question-based rows ([6f3f4c2](https://github.com/marcusburghardt/ansible-role-ai/commit/6f3f4c239ba7980881ab453b7a4c77a27a72985a))
* restructure dashboard with sub-agent analytics and question-based rows ([3144b28](https://github.com/marcusburghardt/ansible-role-ai/commit/3144b281613d3d24cc7273fdb844041873011137))
* ship opencode-metrics plugin as default with optional config ([366f353](https://github.com/marcusburghardt/ansible-role-ai/commit/366f353c9bf9fab73df14b9fe23eddf40112b34f))


### Miscellaneous

* archive default-metrics-plugin change and sync specs ([fd3b272](https://github.com/marcusburghardt/ansible-role-ai/commit/fd3b27209a4402f1e7d06bd9cf89f9b3d6a8052f))
* bump opencode-metrics default version to 0.3.0 ([e91f6f7](https://github.com/marcusburghardt/ansible-role-ai/commit/e91f6f74bb9b0921f5207777738d9c3540af2e7a))
* **main:** release 0.2.0 ([dc98b4d](https://github.com/marcusburghardt/ansible-role-ai/commit/dc98b4d8747c41ceb691cabd4280fbe881b8d7e8))


### Documentation

* add openspec proposal for metrics local install mode ([03d69a6](https://github.com/marcusburghardt/ansible-role-ai/commit/03d69a611f1db5cf891ea0f02b49158d91f4b462))
* archive metrics-local-install-mode and sync specs ([76abc0b](https://github.com/marcusburghardt/ansible-role-ai/commit/76abc0bc25f58854bb5d9850dc2ee4af2fb68c33))

## [0.2.0](https://github.com/marcusburghardt/ansible-role-ai/compare/v0.1.1...v0.2.0) (2026-09-16)


### Features

* add agent model routing, plugin support, and data-driven compaction ([4e34a33](https://github.com/marcusburghardt/ansible-role-ai/commit/4e34a33db078c72082b7a494d329b85d585c1d88))
* add configure_grafana_metrics task for metrics visualization ([808dd79](https://github.com/marcusburghardt/ansible-role-ai/commit/808dd79b8e9d46a91797f82011314ef83ce4730e))
* add PR & Issue Analytics row to Grafana dashboard ([c849f19](https://github.com/marcusburghardt/ansible-role-ai/commit/c849f19147ba6feff17274663325f1a149cbea0d))
* add PR template instruction file for OpenCode ([f07271b](https://github.com/marcusburghardt/ansible-role-ai/commit/f07271b84a9922a337dd9dc1a2b23a48bbf5e714))
* introduce options section for opencode.json template ([9a817fe](https://github.com/marcusburghardt/ansible-role-ai/commit/9a817fe328ebc605ba479cd62dbf619cbd4f0e23))
* overhaul Grafana metrics dashboard with ~30 panels and budget thresholds ([7731e2c](https://github.com/marcusburghardt/ansible-role-ai/commit/7731e2cbb462086c30647a61fa18d76884a60a9e))


### Miscellaneous

* allow minor version bumps for feat commits pre-1.0 ([75ab0e5](https://github.com/marcusburghardt/ansible-role-ai/commit/75ab0e5c09f28cd7770ce24ce8031a9353231057))
* archive 7 completed changes and sync delta specs ([e3f7ac6](https://github.com/marcusburghardt/ansible-role-ai/commit/e3f7ac66508502b27b6873ea6a6a0bbcc49509fc))
* archive dashboard-pr-analytics (16/16 tasks complete) ([899154f](https://github.com/marcusburghardt/ansible-role-ai/commit/899154f83b10a84499a53a82c155733a7cfddaec))
* **deps:** Bump actions/checkout from 6.0.2 to 6.0.3 ([33f1836](https://github.com/marcusburghardt/ansible-role-ai/commit/33f1836e42f66b8d086a8b7077c6ac294e849e67))
* **deps:** Bump actions/checkout from 6.0.2 to 6.0.3 ([b21cdd0](https://github.com/marcusburghardt/ansible-role-ai/commit/b21cdd0184d70274852735025ba1d2fb34c3785c))
* **deps:** Bump actions/checkout from 6.0.3 to 7.0.1 ([6077f0d](https://github.com/marcusburghardt/ansible-role-ai/commit/6077f0d6f49d25abd87061ef4e6a5879141b567a))
* **deps:** Bump actions/checkout from 6.0.3 to 7.0.1 ([9594a77](https://github.com/marcusburghardt/ansible-role-ai/commit/9594a77fca4c9a6d3bc67e54c3ae609f809398e0))
* **deps:** Bump actions/setup-python from 6.2.0 to 7.0.0 ([72be8f3](https://github.com/marcusburghardt/ansible-role-ai/commit/72be8f3f2776dfb966b6635b29a2cbcecca7f06c))
* **deps:** Bump actions/setup-python from 6.2.0 to 7.0.0 ([74d8da8](https://github.com/marcusburghardt/ansible-role-ai/commit/74d8da8f68d0deb81cec6287c32c3079f9ee8118))
* **deps:** Bump googleapis/release-please-action from 4.4.1 to 5.0.0 ([17e8993](https://github.com/marcusburghardt/ansible-role-ai/commit/17e89937f5336db0b4a49bfe9ba50ba8505635ca))
* **deps:** Bump googleapis/release-please-action from 4.4.1 to 5.0.0 ([8a52393](https://github.com/marcusburghardt/ansible-role-ai/commit/8a523935d043603095942222c846bb203c560d96))
* unbound-force as trusted org in github ([6ce2f64](https://github.com/marcusburghardt/ansible-role-ai/commit/6ce2f64d9d05bafad73ab6473219282a8bfdfc68))


### Documentation

* add openspec change artifacts for dashboard-pr-analytics ([87688bf](https://github.com/marcusburghardt/ansible-role-ai/commit/87688bfe51e5636a130d0f86b71beb91595044bb))
* add openspec change artifacts for dashboard-visual-overhaul ([ff500a5](https://github.com/marcusburghardt/ansible-role-ai/commit/ff500a54fee39766613dbf85e439b8017a0ccbfe))
* spec for grafana dashboard used for metrics ([e820c92](https://github.com/marcusburghardt/ansible-role-ai/commit/e820c92f4d3d2ca012bc77eda12930127f8c8979))

## [0.1.1](https://github.com/marcusburghardt/ansible-role-ai/compare/v0.1.0...v0.1.1) (2026-04-17)


### Features

* add declarative model removal via 'removed' flag in ai_ollama_models ([db772d3](https://github.com/marcusburghardt/ansible-role-ai/commit/db772d3624efba575e008d6f095b16bab3938e45))


### Bug Fixes

* allow ollama_t to exec its own binary for model runners ([b7dcc2c](https://github.com/marcusburghardt/ansible-role-ai/commit/b7dcc2c7d362c6e4c203ce8bd8bb46ab8a631519))


### Documentation

* add release process documentation to README ([06d11b7](https://github.com/marcusburghardt/ansible-role-ai/commit/06d11b7615bd92a7d8d681d39785d3c71e51cf26))

## [0.2.0](https://github.com/marcusburghardt/ansible-role-ai/compare/v0.1.0...v0.2.0) (2026-04-16)


### ⚠ BREAKING CHANGES

* ai_model and ai_small_model now default to ollama/qwen3:8b. The provider block in opencode.json is now rendered from ai_opencode_providers instead of being hardcoded. See README migration section for details.

### Features

* add Ollama support with data-driven provider configuration ([455f1f6](https://github.com/marcusburghardt/ansible-role-ai/commit/455f1f66bb9a9d736390276f55b4e4e42fcb552d))
* add optional Cursor IDE installation task with multi-format support ([cdb1b31](https://github.com/marcusburghardt/ansible-role-ai/commit/cdb1b3103e75e4310763d7bd47b91f13af5e6889))
* add optional SELinux confined policy for Ollama ([91edb29](https://github.com/marcusburghardt/ansible-role-ai/commit/91edb29ac5c90f20e2f2e05e20f0200c2f0e4465))
* add release-please workflow and gate Galaxy on releases ([3690167](https://github.com/marcusburghardt/ansible-role-ai/commit/36901670042ecafc31b54cc88b23b5f4475e5d7c))
* add security remediation command for GitHub alert triage and fix ([501a20a](https://github.com/marcusburghardt/ansible-role-ai/commit/501a20a9ce97e53e3bd9d2704a5e8758f6fd02c3))
* add workflow_next command and Next Steps to existing commands ([8d0c1f2](https://github.com/marcusburghardt/ansible-role-ai/commit/8d0c1f2f5386819a0e7289f00ff90a2cdc953758))
* auto-discover commands/skills with blocklist and custom source support ([28d0d45](https://github.com/marcusburghardt/ansible-role-ai/commit/28d0d45d8c5e091e4fc17e53b5aeba1529503993))
* deploy global coding standards as baseline OpenCode instruction file ([7e8994e](https://github.com/marcusburghardt/ansible-role-ai/commit/7e8994e5f7ccfe6a9bcbccb01afd9e86a6bfc07f))
* implement ansible-role-ai for AI developer tools management ([5be65a2](https://github.com/marcusburghardt/ansible-role-ai/commit/5be65a24f4ca24e65a53aefb093d8b5b8bd9061c))
* prefer native package manager for Ollama installation ([f1681e9](https://github.com/marcusburghardt/ansible-role-ai/commit/f1681e9d4894b608e3ab637212843a8a6b8121ae))


### Bug Fixes

* deploy systemd unit and ensure server responds for package installs ([b29729c](https://github.com/marcusburghardt/ansible-role-ai/commit/b29729c419f5ca900854a521a5f72142b82fd2e3))
* keep version in 0.x by enabling pre-major bump guards ([c8a227d](https://github.com/marcusburghardt/ansible-role-ai/commit/c8a227db77d6e8e11de8c37973850f4a8d6f846c))
* reset manifest to 0.1.0 for correct initial release ([c63c245](https://github.com/marcusburghardt/ansible-role-ai/commit/c63c245f80c78fc15ccea03b1ac167cdf9ef2b30))
* use declared service state instead of runtime check for model pulls ([bdf9d51](https://github.com/marcusburghardt/ansible-role-ai/commit/bdf9d5188416018e49eecd2644d17ac38c1ab450))


### Miscellaneous

* allow yamllint in OpenCode permissions ([6e93170](https://github.com/marcusburghardt/ansible-role-ai/commit/6e9317000e2808550fdcd442d1e5f19d3e3efb72))
* archive completed changes and sync specs to main ([37b6614](https://github.com/marcusburghardt/ansible-role-ai/commit/37b6614bec9db532c8a0ccef381efa51b3fb89ab))
* archive global-coding-constitution and sync specs ([31f6e7f](https://github.com/marcusburghardt/ansible-role-ai/commit/31f6e7f9a3983ad4f490f9b8015524602aea99c8))
* **deps:** Bump actions/checkout from 4.2.2 to 6.0.2 ([9ee9dc3](https://github.com/marcusburghardt/ansible-role-ai/commit/9ee9dc3212bc2b4f2c3dccaec57fa6c78cd825a5))
* **deps:** Bump actions/checkout from 4.2.2 to 6.0.2 ([d2ad1a7](https://github.com/marcusburghardt/ansible-role-ai/commit/d2ad1a770fd9c94bf99cfe1de8c3b89329989660))
* **deps:** Bump actions/setup-python from 5.6.0 to 6.2.0 ([7aadde4](https://github.com/marcusburghardt/ansible-role-ai/commit/7aadde4da8df37008a4ebb1597831cfd3b6c508e))
* **deps:** Bump actions/setup-python from 5.6.0 to 6.2.0 ([7af6476](https://github.com/marcusburghardt/ansible-role-ai/commit/7af64763e3f5d602446a0d2ffc47f76a7fed8c9c))
* disable release-please PR labeling ([ef08e88](https://github.com/marcusburghardt/ansible-role-ai/commit/ef08e88d080e7e6e0341e4c90d4282d7b09eb666))
* include more common bash commands ([2df0e63](https://github.com/marcusburghardt/ansible-role-ai/commit/2df0e637750ef0886c9907b85034c0fe46a5cce5))
* include new common commands ([82eaa27](https://github.com/marcusburghardt/ansible-role-ai/commit/82eaa272117b66f823765eca391bed20af6c3ca8))
* **main:** release 0.1.0 ([2d5a28f](https://github.com/marcusburghardt/ansible-role-ai/commit/2d5a28f47145f34a3c9eec86dbef62cfa6b931f0))
* **main:** release 0.2.0 ([8af4317](https://github.com/marcusburghardt/ansible-role-ai/commit/8af4317d96a57194b3fd2368bf4aad328d08794a))

## [0.2.0](https://github.com/marcusburghardt/ansible-role-ai/compare/v0.1.0...v0.2.0) (2026-04-16)


### ⚠ BREAKING CHANGES

* ai_model and ai_small_model now default to ollama/qwen3:8b. The provider block in opencode.json is now rendered from ai_opencode_providers instead of being hardcoded. See README migration section for details.

### Features

* add Ollama support with data-driven provider configuration ([455f1f6](https://github.com/marcusburghardt/ansible-role-ai/commit/455f1f66bb9a9d736390276f55b4e4e42fcb552d))
* add optional Cursor IDE installation task with multi-format support ([cdb1b31](https://github.com/marcusburghardt/ansible-role-ai/commit/cdb1b3103e75e4310763d7bd47b91f13af5e6889))
* add optional SELinux confined policy for Ollama ([91edb29](https://github.com/marcusburghardt/ansible-role-ai/commit/91edb29ac5c90f20e2f2e05e20f0200c2f0e4465))
* add release-please workflow and gate Galaxy on releases ([3690167](https://github.com/marcusburghardt/ansible-role-ai/commit/36901670042ecafc31b54cc88b23b5f4475e5d7c))
* add security remediation command for GitHub alert triage and fix ([501a20a](https://github.com/marcusburghardt/ansible-role-ai/commit/501a20a9ce97e53e3bd9d2704a5e8758f6fd02c3))
* add workflow_next command and Next Steps to existing commands ([8d0c1f2](https://github.com/marcusburghardt/ansible-role-ai/commit/8d0c1f2f5386819a0e7289f00ff90a2cdc953758))
* auto-discover commands/skills with blocklist and custom source support ([28d0d45](https://github.com/marcusburghardt/ansible-role-ai/commit/28d0d45d8c5e091e4fc17e53b5aeba1529503993))
* deploy global coding standards as baseline OpenCode instruction file ([7e8994e](https://github.com/marcusburghardt/ansible-role-ai/commit/7e8994e5f7ccfe6a9bcbccb01afd9e86a6bfc07f))
* implement ansible-role-ai for AI developer tools management ([5be65a2](https://github.com/marcusburghardt/ansible-role-ai/commit/5be65a24f4ca24e65a53aefb093d8b5b8bd9061c))
* prefer native package manager for Ollama installation ([f1681e9](https://github.com/marcusburghardt/ansible-role-ai/commit/f1681e9d4894b608e3ab637212843a8a6b8121ae))


### Bug Fixes

* deploy systemd unit and ensure server responds for package installs ([b29729c](https://github.com/marcusburghardt/ansible-role-ai/commit/b29729c419f5ca900854a521a5f72142b82fd2e3))
* keep version in 0.x by enabling pre-major bump guards ([c8a227d](https://github.com/marcusburghardt/ansible-role-ai/commit/c8a227db77d6e8e11de8c37973850f4a8d6f846c))
* use declared service state instead of runtime check for model pulls ([bdf9d51](https://github.com/marcusburghardt/ansible-role-ai/commit/bdf9d5188416018e49eecd2644d17ac38c1ab450))


### Miscellaneous

* allow yamllint in OpenCode permissions ([6e93170](https://github.com/marcusburghardt/ansible-role-ai/commit/6e9317000e2808550fdcd442d1e5f19d3e3efb72))
* archive completed changes and sync specs to main ([37b6614](https://github.com/marcusburghardt/ansible-role-ai/commit/37b6614bec9db532c8a0ccef381efa51b3fb89ab))
* archive global-coding-constitution and sync specs ([31f6e7f](https://github.com/marcusburghardt/ansible-role-ai/commit/31f6e7f9a3983ad4f490f9b8015524602aea99c8))
* **deps:** Bump actions/checkout from 4.2.2 to 6.0.2 ([9ee9dc3](https://github.com/marcusburghardt/ansible-role-ai/commit/9ee9dc3212bc2b4f2c3dccaec57fa6c78cd825a5))
* **deps:** Bump actions/checkout from 4.2.2 to 6.0.2 ([d2ad1a7](https://github.com/marcusburghardt/ansible-role-ai/commit/d2ad1a770fd9c94bf99cfe1de8c3b89329989660))
* **deps:** Bump actions/setup-python from 5.6.0 to 6.2.0 ([7aadde4](https://github.com/marcusburghardt/ansible-role-ai/commit/7aadde4da8df37008a4ebb1597831cfd3b6c508e))
* **deps:** Bump actions/setup-python from 5.6.0 to 6.2.0 ([7af6476](https://github.com/marcusburghardt/ansible-role-ai/commit/7af64763e3f5d602446a0d2ffc47f76a7fed8c9c))
* disable release-please PR labeling ([ef08e88](https://github.com/marcusburghardt/ansible-role-ai/commit/ef08e88d080e7e6e0341e4c90d4282d7b09eb666))
* include more common bash commands ([2df0e63](https://github.com/marcusburghardt/ansible-role-ai/commit/2df0e637750ef0886c9907b85034c0fe46a5cce5))
* include new common commands ([82eaa27](https://github.com/marcusburghardt/ansible-role-ai/commit/82eaa272117b66f823765eca391bed20af6c3ca8))
