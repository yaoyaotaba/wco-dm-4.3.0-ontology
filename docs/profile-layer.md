# 包配置剖面（Profile Layer）

## 1. 为什么单独建一层

核心本体 `wco-dm-4.3.0.ttl` 回答的是：

> WCO DM 的类、数据元素、包含关系**是什么**。

但 WCO 的发布包还包含 4 个 **Information Package**：MDIP、AIP、BIP DEC、BIP LPCO。它们回答的是：

> 某个具体包**如何使用**核心模型：包含哪些类/元素、Min/Max、顺序、使用标记、备注、外部映射。

把这些“包内配置”直接写进核心本体会污染全局语义，所以另建 profile 层：

```text
wco-dm-4.3.0.ttl                 核心语义
        ▲
        │ owl:imports
wco-dm-4.3.0-profiles.ttl        包配置知识图谱
        │
        ├── wco-dm-4.3.0-profiles-shapes.ttl   按包校验
        ├── ...-profiles-sample.ttl            合规样例
        └── ...-profiles-sample-invalid.ttl    违规样例
```

---

## 2. 规模

| 指标 | 数值 |
|---|---:|
| 包剖面 | 4（MDIP、AIP、BIP DEC、BIP LPCO） |
| profile 类（OWL 子类） | 387 |
| 包内数据元素（`prof:ProfileProperty`） | 1,541 |
| 包内关联（`prof:ProfileAssociation`） | 1,077 |
| 使用标记（`prof:Flag`） | 37 |
| Min/Max 断言 | 各 2,618 |
| `prof:hasFlag` 链接 | 1,988 |
| profile 图三元组 | 25,407 |
| profile NodeShape | 384 |
| profile PropertyShape | 2,618 |
| profile SHACL 三元组 | 14,248 |

---

## 3. 建模方式

### 3.1 包 → `prof:PackageProfile`

```turtle
prof:PKG_BIP_DEC a prof:PackageProfile ;
  skos:prefLabel "BIP DEC" ;
  prof:packageCode "DEC" ;
  prof:sourceWorkbook "3.3. WCO DM BIP DEC_V4.3.0.xlsx" ;
  prof:sourceSheet "BIP DEC" .
```

### 3.2 包内类 → 核心类的 OWL 子类

```turtle
prof:P_BIP_DEC_C_42A a owl:Class ;
  rdfs:subClassOf wco:C_42A ;
  rdfs:label "BIP DEC · Declaration" ;
  prof:inPackage prof:PKG_BIP_DEC ;
  prof:sourceClass wco:C_42A .
```

这样实例可以声明为 `prof:P_BIP_DEC_C_42A`，推理机可推出它同时是 `wco:C_42A`。

### 3.3 包内数据元素 → `prof:ProfileProperty`

```turtle
prof:P_BIP_DEC_42A_D014 a prof:ProfileProperty ;
  prof:profile prof:PKG_BIP_DEC ;
  prof:ofClass prof:P_BIP_DEC_C_42A ;
  prof:ofProperty wco:dp_D014 ;
  prof:minOccurs 0 ;
  prof:maxOccurs 1 ;
  prof:sequence 12 ;
  prof:path "Declaration/identification" .
```

`prof:ofClass` / `prof:ofProperty` 是**注解属性**，用 IRI 指向 profile 类/核心属性，避免把“类”当作个体使用（punning）。

### 3.4 包内关联 → `prof:ProfileAssociation`

```turtle
prof:P_BIP_DEC_A_42A_GoodsShipment a prof:ProfileAssociation ;
  prof:profile prof:PKG_BIP_DEC ;
  prof:parentClass prof:P_BIP_DEC_C_42A ;
  prof:childClass prof:P_BIP_DEC_C_67A ;
  prof:roleName "GoodsShipment" ;
  prof:ofProperty wco:hasGoodsShipment ;
  prof:maxOccurs "unbounded" .
```

### 3.5 使用标记 → `prof:Flag`

```turtle
prof:F_Mar_API a prof:Flag ;
  skos:prefLabel "Mar. API" ;
  prof:flagName "Mar. API" ;
  prof:sourceColumn "Mar. API" .

prof:P_BIP_DEC_C_42A prof:hasFlag prof:F_Mar_API .
```

---

## 4. 可查询示例

### 4.1 BIP DEC 中 `Declaration` 的数据元素及 Max

```sparql
PREFIX prof: <https://w3id.org/wco-dm/4.3.0/profile#>
PREFIX wco:  <https://w3id.org/wco-dm/4.3.0#>

SELECT ?prop ?min ?max WHERE {
  ?e a prof:ProfileProperty ;
     prof:profile prof:PKG_BIP_DEC ;
     prof:ofClass prof:P_BIP_DEC_C_42A ;
     prof:ofProperty ?prop ;
     prof:minOccurs ?min ;
     prof:maxOccurs ?max .
}
```

### 4.2 只在 BIP DEC 出现、不在 BIP LPCO 出现的类

```sparql
SELECT ?class WHERE {
  ?a prof:inPackage prof:PKG_BIP_DEC ;
     prof:sourceClass ?class .
  FILTER NOT EXISTS {
    ?b prof:inPackage prof:PKG_BIP_LPCO ;
       prof:sourceClass ?class .
  }
}
```

### 4.3 每个包使用的标记

```sparql
SELECT ?pkg (COUNT(DISTINCT ?flag) AS ?n) WHERE {
  ?pkg a prof:PackageProfile .
  ?x prof:profile ?pkg ;
     prof:hasFlag ?flag .
}
GROUP BY ?pkg
```

### 4.4 BIP DEC 中声明了 IMO 映射的数据元素

```sparql
SELECT ?prop ?imoTerm WHERE {
  ?e a prof:ProfileProperty ;
     prof:profile prof:PKG_BIP_DEC ;
     prof:ofProperty ?prop ;
     prof:imoTerm ?imoTerm .
}
```

---

## 5. 可校验

profile SHACL 只针对 profile 类，不会误伤核心实例：

```turtle
prof:Shape_P_BIP_DEC_C_42A a sh:NodeShape ;
  sh:targetClass prof:P_BIP_DEC_C_42A ;
  sh:property [
    sh:path wco:dp_D014 ;
    sh:datatype xsd:string ;
    sh:maxCount 1 ;
  ] .
```

### 合规样例

```turtle
ex:declaration a prof:P_BIP_DEC_C_42A ;
  wco:dp_D014 "DOC-001" .
```

```text
conforms = true
results  = 0
```

### 违规样例

```turtle
ex:declaration a prof:P_BIP_DEC_C_42A ;
  wco:dp_D014 "DOC-001" ;
  wco:dp_D014 "DOC-002" .
```

```text
conforms = false
results  = 1
message  = More than 1 values
```

---

## 6. 当前覆盖范围

**已物化：**

- 包、包内类、包内数据元素、包内关联；
- Min/Max、Seq. No.、Path；
- 37 个使用标记（`prof:Flag` + `prof:hasFlag`）；
- Remark；
- IMO ID / Term / Compendium name / definition（有值的行）；
- Cell Address、Unique Position ID（有值的行）。

**未物化：**

- 包的 `MyDataSet` 扩展字段（源表大多为空或非结构化）；
- 所有行的原始文本、颜色、批注；
- 包之间的差异报告（可用 SPARQL 实时计算）。

这些保留在 `data/package-cardinalities.csv` 与源工作簿中。

---

## 7. 重新生成

```bash
python3 scripts/build_profiles.py
```

该脚本读取 4 个包级工作簿，生成：

```text
ontology/wco-dm-4.3.0-profiles.ttl
ontology/wco-dm-4.3.0-profiles-shapes.ttl
ontology/wco-dm-4.3.0-profiles-sample.ttl
ontology/wco-dm-4.3.0-profiles-sample-invalid.ttl
data/profiles.json
```
