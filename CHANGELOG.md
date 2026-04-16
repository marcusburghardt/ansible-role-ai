# Changelog

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
