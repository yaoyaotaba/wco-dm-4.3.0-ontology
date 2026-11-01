# NOTICE / 来源与使用声明

## 1. WCO 源数据

本仓库包含并派生自 **World Customs Organization (WCO) Data Model 4.3.0** 的公开出版包：

- 发布包页面：<https://datamodel.wcoomd.org/#/package>
- 包文件树接口：<https://datamodel.wcoomd.org/datamodel/infopage/4.3.0>
- 文件根路径：`https://datamodel.wcoomd.org/webpage/4.3.0/`

WCO 数据模型、LIB/OIS 工作簿、XML Schema、UML 图及其中的定义、代码表与文档，其版权归世界海关组织（WCO）所有。使用、复制、再分发或创作衍生作品，应遵守 WCO 的适用条款与条件。请以 WCO 官方发布为准：

- <https://www.wcoomd.org/>
- <https://datamodel.wcoomd.org/>

本仓库的派生本体、CSV 表、SHACL 形状与可视化页面是**独立的技术产物**，**不是 WCO 官方出版物**，未经 WCO 审核、认证或背书。仓库作者不对源数据的准确性、完整性或时效性作出保证。

## 2. 外部代码表

知识库中引用了以下外部标准/代码表来源，其版权与使用条件归各自发布方所有：

- UN/EDIFACT / UNTDID（UNECE）
- UN/CEFACT Core Component Library、Recommendation 19/20/21/28
- ISO 3166、ISO 4217、ISO 6346 等
- IMO Compendium / SOLAS
- IANA Character Set / MIME Media Type
- 世界海关组织 WCO 自有代码表

本仓库仅在 `skos:ConceptScheme` 中保留 LIB 给出的来源字符串；未列出具名代码值的表，不表示其不存在或为空，而是源工作簿未列出。

## 3. 本仓库代码与页面的使用

`scripts/` 与 `site/` 中的构建脚本和前端代码用于解析、转换和展示上述源数据。它们按“原样”提供，不附任何明示或暗示担保。使用这些代码不构成对 WCO 源数据的再许可。

生成的知识库建议在再分发时保留：

1. 本 NOTICE；
2. WCO 发布包链接与版本号（4.3.0）；
3. `ontology/provenance.ttl` 中的来源与校验和；
4. 对“非官方派生作品”的明确说明。

## 4. 引用

```text
WCO Data Model 4.3.0 Ontology (derived knowledge base).
Generated from the WCO DM 4.3.0 LIB and OIS workbooks, 2026-10-31.
https://w3id.org/wco-dm/4.3.0
```

如引用原始数据模型，请优先引用 WCO 官方版本：

```text
World Customs Organization. WCO Data Model, version 4.3.0.
https://datamodel.wcoomd.org/
```

## 5. 联系与更正

如发现源文件、IRI 或建模错误，请在项目内记录问题并附上对应的 WCO Class ID / Attr. ID / OIS 路径，以便追溯。
