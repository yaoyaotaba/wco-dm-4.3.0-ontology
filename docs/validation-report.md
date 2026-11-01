# 校验报告：WCO Data Model 4.3.0 本体知识库

- 构建时间：2026-11-01T14:18:35Z（模型快照；后续标签/形状修订不改变三元组计数）
- 规范序列化：`ontology/wco-dm-4.3.0.ttl`
- 校验环境：Python 3.8.10、Node.js 22.22.2、N3.js 1.17.2、rdfxml-streaming-parser 2.4.0、jsonld.js 8.3.2、rdf-validate-shacl 0.5.4
- 结论：**语法解析通过；三种序列化均为 26,663 个三元组；引用完整性 0 缺失；SHACL 合规样例通过、违规样例按预期失败。**

---

## 1. 输入与下载

| 项目 | 结果 |
|---|---|
| 发布包文件树条目 | 135 个文件 |
| 实际下载 | 95 个文件（XLSX + 较小 XSD），18,234,800 字节 |
| 下载失败 | 0 |
| 未下载 | 2 个 50 MB 级合并模式（OIS、Declaration BIP）及 38 个 HTML/UML zip；原因记录在 `sources/package-tree.csv` |
| 清单 | `sources/download-manifest.csv`（URL、字节数、SHA-256、status） |

核心输入校验和：

| 文件 | SHA-256 |
|---|---|
| `sources/xlsx/wco_lib_430.xlsx` | `026a335f18426fffa4ad7032d37fb3c9881d85a383a70442d81486c1f04d7d54` |
| `sources/xlsx/wco_ois_430.xlsx` | `4f69b7d810f78191f036a8e7630a3d53bc0313e178b5df292a614f2ad940d63a` |
| `sources/package-tree.json` | `01a660d299ae24e02fb3ee3a329fde5d9bcd92e3d37f1fe07cab02db6510cbc7` |

---

## 2. 模型统计

| 指标 | 数值 |
|---|---:|
| OWL 类（含 OIS 根） | 274 |
| 对象属性 | 273 |
| 数据类型属性 | 836 |
| 类级包含关系（去重后） | 921 |
| (类, 数据元素) 使用对 | 1,188 |
| SKOS 概念方案 | 135 |
| SKOS 概念（有依据的代码值） | 69 |
| OIS 类出现位置 | 1,993 |
| OIS 属性出现位置 | 7,810 |
| LIB 类记录 / 唯一 Class ID | 273 / 272 |
| LIB 属性记录 / 唯一 Attr. ID | 1,156 / 836 |

### 模型一致性检查

- 对象属性的 `range` 缺失：**0**
- 对象属性的 `parent` 缺失：**0**
- 数据属性的 `usedByClass` 缺失：**0**
- 无路径的类：**0**（OIS 根路径为 `OIS`）
- 无父角色的非根类：**0**
- 重复类名：**0**
- 最大数据属性并集域：84 个类
- 最大对象属性并集域：87 个类

---

## 3. RDF 语法与序列化

| 序列化 | 解析器 | 结果 | 三元组/四元组 |
|---|---|---:|---:|
| Turtle | N3.js 1.17.2 | 通过 | **26,663** |
| RDF/XML | rdfxml-streaming-parser 2.4.0 | 通过 | **26,663** |
| JSON-LD 1.1 | jsonld.js 8.3.2 → N-Quads | 通过 | **26,663** |

三者谓词分布逐项一致（`rdf:type`、`rdfs:domain`、`rdfs:range`、`rdfs:label`、`skos:definition`、`wco:*` 等）；空白节点标识不同，未做形式化同构证明。

### 声明统计

| RDF 类型 | 数量 | 说明 |
|---|---:|---|
| `owl:Ontology` | 1 | 本体头 |
| `owl:Class` | 481 | 274 个命名类 + 207 个并集域匿名类 |
| `owl:ObjectProperty` | 276 | 273 个角色 + `hasComponent` + `isComponentOf` + `skos:inScheme` |
| `owl:DatatypeProperty` | 837 | 836 个数据元素 + `hasAttribute` |
| `owl:AnnotationProperty` | 50 | 29 个自定义 + 21 个外部词表术语 |
| `skos:ConceptScheme` | 135 | 代码表 |
| `skos:Concept` | 69 | 有依据的代码值 |

### 引用完整性

对全部 `wco:C_*`、`wco:dp_*`、`wco:has*` 引用做闭包检查：

- `rdfs:range` 指向未声明类：**0**
- `wco:usedByClass` 指向未声明类：**0**
- `wco:usedByDataElement` 指向未声明属性：**0**

---

## 4. OWL 2 DL 画像

本知识库按 OWL 2 DL 构造，未使用 OWL Full 特有构造：

- 类表达式仅使用 `owl:unionOf`（域并集）和命名类。
- 属性分为 `owl:ObjectProperty` 与 `owl:DatatypeProperty`，域/值域明确。
- 注解属性与对象属性不混用；自定义元数据均为 `owl:AnnotationProperty`。
- 所有具名类均声明为 `wco:DataModelComponent` 的子类。
- `wco:hasComponent` 与 `wco:isComponentOf` 通过 `owl:inverseOf` 关联。
- 未使用 `owl:sameAs`、`owl:disjointWith` 等可能引入不一致的公理。

**未执行**：HermiT/ELK 推理机一致性检查（环境中无 Java OWL API/推理机）。建议在 Protégé 中加载后运行 HermiT 做最终确认。

---

## 5. SHACL 校验

| 项目 | 数值 |
|---|---:|
| `sh:NodeShape` | 274 |
| `sh:PropertyShape` | 2,109 |
| 形状图三元组 | 18,459 |
| `sh:targetClass` 覆盖类 | 274 |
| `sh:maxCount 1`（数据元素 PropertyShape） | 1,188 |

### 合规样例 `wco-dm-4.3.0-sample.ttl`

```text
conforms = true
results  = 0
```

样例包含：

```turtle
wco:sampleGoodsShipment a wco:C_67A ;
  wco:dp_006 "1"^^xsd:decimal ;
  wco:dp_094 "10" ;
  wco:dp_030 "2026-10-31T10:00:00Z"^^xsd:dateTime ;
  wco:hasConsignee wco:sampleConsignee .

wco:sampleConsignee a wco:C_27A .
```

### 违规样例 `wco-dm-4.3.0-sample-invalid.ttl`

```text
conforms = false
results  = 1
message  = Value does not have datatype xsd:dateTime
focus    = wco:invalidGoodsShipment
```

说明形状确实在约束 `dp_030` 的 `xsd:dateTime` 值域，而不是空跑。

---

## 6. 已知限制与未覆盖项

1. **基数来源与范围**：OIS 不含消息级基数；数据元素 Min=0/Max=1 来自 4 个包级工作簿，对象角色的 Max 随包变化，未全局断言。SHACL 不强制可选属性出现。
2. **日期时间语义归一化**：XML 的 CCTS `DateTimeString + formatCode` 被统一映射为 `xsd:dateTime`，原始格式代码未保留。
3. **代码表成员不完整**：135 个表中仅 12 个在 LIB 中给出代码值；外部表的完整成员需从 UNECE/ISO/IMO 获取。
4. **两个超大模式未归档**：OIS 与 Declaration BIP 的合并 XSD 约 57 MB / 50 MB，未下载；不影响由工作簿构建的本体。
5. **空白节点同构未证明**：三种序列化计数与谓词分布一致，但未做 RDF Dataset Canonicalization（RDFC-1.0）比对。
6. **未执行推理机**：未验证所有并集域/子属性公理在 HermiT 下的可满足性；建议在 Protégé 中复核。
7. **包级 flag 未物化**：MDIP/AIP/BIP 工作簿中的 DIP 使用标记、Remark、IMO 映射与 Cell Address 未转为 OWL；已保留在 `data/package-cardinalities.csv`。
8. **变更日志未摄取**：Changes 工作簿的 3 个 sheet 是版本变更说明，仅归档，不作为当前模型公理。

---

## 7. Profile 层校验

| 项目 | 数值 |
|---|---:|
| 包剖面 | 4 |
| profile 类（OWL 子类） | 387 |
| 包内数据元素 | 1,541 |
| 包内关联 | 1,077 |
| 使用标记 | 37 |
| profile 图三元组 | 25,407 |
| profile NodeShape | 384 |
| profile PropertyShape | 2,618 |
| profile SHACL 三元组 | 14,248 |

样例：

```text
wco-dm-4.3.0-profiles-sample.ttl
  conforms = true, results = 0

wco-dm-4.3.0-profiles-sample-invalid.ttl
  conforms = false, results = 1
  message  = More than 1 values
```

Profile 类继承核心类，profile SHACL 只以 profile 类为 `sh:targetClass`，因此不会误伤核心实例。完整说明见 `docs/profile-layer.md`。

---

## 8. Excel 覆盖审计

7 个工作簿共 11 个 sheet：

- **4 个核心 sheet 已全量解析**：LIB 的 3 个 sheet（类/属性、核心数据类型、代码表）+ OIS 的 1 个 sheet（包含层次）。
- **4 个包级模型 sheet 已审计**：MDIP、AIP、BIP DEC、BIP LPCO，共 10,334 行；类/属性 ID 全部已在核心模型中，0 个新 ID、0 个定义冲突。
- **3 个变更日志 sheet 仅归档**：Introduction、LIB Changes、OIS Changes，不作为模型公理。

包级 Min/Max 统计：8,212 个数据元素行全部 `Min=0`、`Max=1`；对象属性 Max 在不同包中可为 `unbounded` 或 `1`，未全局断言。

逐 sheet 明细见 `docs/excel-coverage.md` 与 `data/package-sheets.csv`；10,334 行包级明细见 `data/package-cardinalities.csv`。

---

## 9. 复现命令

```bash
# 解析/构建
python3 scripts/build_all.py

# Turtle 解析与计数
node -e 'const fs=require("fs"),N3=require("n3");const q=new N3.Parser().parse(fs.readFileSync("ontology/wco-dm-4.3.0.ttl","utf8"));console.log(q.length)'

# RDF/XML / JSON-LD 解析与计数（需在含依赖的目录执行）
node scripts/validate-serializations.mjs
```

`scripts/validate-serializations.mjs` 需要以下 npm 包：`n3`、`rdfxml-streaming-parser`、`jsonld`、`rdf-validate-shacl`。
