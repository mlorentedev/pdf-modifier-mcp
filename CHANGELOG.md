# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v1.0.3](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.3) (2026-01-15)



### Bug fixes


- remove .well-known folder (for HTTP servers only) ([`29cb390`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/29cb39054601cc9140dd4078c76a14244ff85726))





## [v1.0.2](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.2) (2026-01-15)



### Bug fixes


- only publish to PyPI when dist artifacts exist ([`81e14eb`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/81e14ebb1955c3413a2d105a0e17d5919b6976ea))





## [v1.0.1](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.1) (2026-01-15)



### Bug fixes


- use uvx to run package from PyPI ([`dffb565`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/dffb56587b903246d219eefac3926be6119e35df))





### Refactoring


- simplify release workflow and fix deprecation warning ([`4fe922c`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4fe922c74529186da9ac1a8b8fe2844dd512995c))





## [v1.0.0](https://github.com/mlorentedev/pdf-modifier-mcp/releases/tag/v1.0.0) (2026-01-15)



### Bug fixes


- use PAT token in checkout for git push ([`ce839c5`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ce839c542f91e2a8e15641a8a3737495c1a4192b))

- use RELEASE_TOKEN PAT to bypass branch protection ([`ce839c5`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ce839c542f91e2a8e15641a8a3737495c1a4192b))

- use RELEASE_TOKEN in checkout for git push auth ([`ce839c5`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ce839c542f91e2a8e15641a8a3737495c1a4192b))

- use RELEASE_TOKEN PAT to bypass branch protection ([`0af8e9e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0af8e9e0e745179f2258b70987bd7957a4ac8a97))

- avoid protected branch push issue ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- update semantic-release config for v9 compatibility ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- correct changelog template syntax for semantic-release v9 ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- use --no-push --no-commit to avoid protected branch issue ([`f42799e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f42799e782ebcef0a179b1aa93da269f7b024f05))

- correct changelog template for semantic-release v9 ([`7439740`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7439740ae12df8f2154798f638bc29c5d9561171))

- update semantic-release config for v9 compatibility ([`7439740`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7439740ae12df8f2154798f638bc29c5d9561171))

- correct changelog template syntax for semantic-release v9 ([`7439740`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/7439740ae12df8f2154798f638bc29c5d9561171))

- update semantic-release config for v9 compatibility ([`3100eae`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/3100eae3b6e30bf5fafa1440de642492ec621564))

- disable internal pypi upload in semantic-release config ([`4149d89`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4149d892437e1b0d4bb851a3ac577d63eb41802a))

- use trusted pypi publisher action ([`4652568`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/46525688c4161f4a4de3e2996f9f5eae1acfde6d))

- replace docker action with native python semantic-release workflow ([`c4dc483`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/c4dc48371f4c7a520dd2fd4bd50992922dc40c86))

- fetch full history to fix semantic-release detached head error ([`395106f`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/395106f5adbddf0ec4c458f2ebec55d7c591c442))

- repair yaml syntax error in ci workflow ([`0b03ce2`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0b03ce2e0b896a30a22dabddf7060c32a13060aa))

- remove remote config entirely to fix CI error ([`0985808`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/0985808ae667eb7fb0c97b46d8b21721ab990dad))

- trigger release on push to master for robustness ([`2604a10`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/2604a108c40ea50d9f14a0c02df4cc3836e0fb8b))

- remove problematic remote type config ([`f9a44f9`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/f9a44f94345e58bcba81f13cd49968cb9a24faf7))

- update semantic-release config to v9 standards ([`82f313e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/82f313e0be7ddc3545843f5c1cf9f92ab54f076c))

- enable ci on all branches and remove redundant release validation ([`ebb662e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/ebb662ed0192194f4eece80373c51a2405146aa4))

- remove unsupported description argument from FastMCP ([`cfe1225`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/cfe12255b55d7c19ad131e6ec4ff2784e6cc346e))





### Continuous integration


- reduce python matrix to min (3.10) and max (3.12) versions ([`6d23ad7`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/6d23ad7b9f9cc649e9189755752ce8914b8f88d4))

- switch to official python-semantic-release action for stability ([`fad8a7c`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/fad8a7c307714f03c0cc39d84faa7e1f32d38f03))

- remove release verification step to avoid detached head errors ([`fba23a8`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/fba23a818e5f01a84bed6d1183027fc630b13127))

- add semantic-release config verification to CI pipeline ([`4f2ea0d`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/4f2ea0dce42d286548539872b7d68b71fe8d32aa))

- test release workflow on feature branch ([`1f1dc85`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/1f1dc85f2924b83969c2736ed7c2c75ceb9ddc69))





### Documentation


- add smithery server card for discovery ([`dfa30d3`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/dfa30d39c153fedb30baaeb5a8785b9ff6672655))





### Features


- test semantic release workflow ([`aa7158e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/aa7158e46ba679195efaab5c43659cc4cb367567))





### Refactoring


- switch to tag-based release workflow (removes semantic-release) ([`edd0892`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/edd08926adfa754bb107dcfedbae8229e2928983))

- modernize project structure and update CI/CD ([`e024b0e`](https://github.com/mlorentedev/pdf-modifier-mcp/commit/e024b0e3af890f55457f15881c8fc9a2956221ea))
