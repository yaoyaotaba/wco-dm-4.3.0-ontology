# Excel 覆盖审计

**结论：不是“11 个 sheet 全部进入本体”。** 7 个工作簿共 11 个 sheet，按用途分为三类：

| 类别 | sheet 数 | 处理方式 |
|---|---:|---|
| 核心语义输入 | 4 | **全量解析**，直接生成本体类、属性、代码表 |
| 包级数据模型 | 4 | **已审计**；类/属性 ID 全部已在核心模型中，唯一新增语义 Min/Max 已吸收 |
| 变更日志 | 3 | **仅归档**；属于版本变更说明，不作为模型公理 |

因此，**8 个模型相关 sheet 已覆盖**（4 个解析 + 4 个审计），3 个变更日志 sheet 不作语义摄取。所有包级 sheet 中的类 ID、属性 ID 都能在核心模型中找到；0 个新 ID、0 个定义冲突。

---

## 1. 逐 sheet 清单

### 核心工作簿（2 个，4 个 sheet）

| 工作簿 | sheet | 非空行 | 内容 | 状态 |
|---|---|---:|---|---|
| `1.1 WCO DM LIB V4.3.0.xlsx` | `DataSet 1.2, 1.3, 1.4` | 1,431 | 270 个类、835 个数据元素、定义、格式、核心类型、UN/CEFACT 对齐 | **已解析** → 274 个 OWL 类 / 836 个数据属性 |
| `1.1 WCO DM LIB V4.3.0.xlsx` | `DataSet 1.5` | 39 | 37 条 WCO 核心数据类型与属性映射 | **已解析** → 用于 `wco:coreDataType` 与 XSD 类型映射 |
| `1.1 WCO DM LIB V4.3.0.xlsx` | `DataSet 1.6` | 137 | 135 个命名代码表、来源、部分代码值 | **已解析** → 135 个 SKOS ConceptScheme、69 个 Concept |
| `WCO DM OIS_V4.3.0.xlsx` | `OIS` | 9,806 | 1,993 个类出现位置、7,810 个属性出现位置、包含路径 | **已解析** → 921 条去重包含关系、1,188 个属性使用位置 |

### 包级数据模型工作簿（4 个，4 个 sheet）

| 工作簿 | sheet | 非空行 | 类 / 属性行 | 新类 ID | 新属性 ID | Min / Max | 状态 |
|---|---|---:|---:|---:|---:|---|---|
| `3.1. WCO DM MDIP_V4.3.0.xlsx` | `MDIP (MetaData)` | 67 | 8 C / 49 E | 0 | 0 | Min=0；Max=1 或 unbounded | **已审计；Min/Max 已吸收** |
| `3.2. WCO DM AIP_V4.3.0.xlsx` | `AIP (RES and InterGov)` | 440 | 39 C / 119 E | 0 | 0 | Min=0；Max=1 或 unbounded | **已审计；Min/Max 已吸收** |
| `3.3. WCO DM BIP DEC_V4.3.0.xlsx` | `BIP DEC` | 9,064 | 243 C / 741 E | 0 | 0 | Min=0；Max=1 或 unbounded | **已审计；Min/Max 已吸收** |
| `3.4. WCO DM BIP LPCO_V4.3.0.xlsx` | `BIP LPCO` | 763 | 97 C / 284 E | 0 | 0 | Min=0；Max=1 或 unbounded | **已审计；Min/Max 已吸收** |

合计：10,334 行；其中数据元素（E）行 8,212 行，**Min 全部为 0，Max 全部为 1**；类（C）行的 Max 大多为 `unbounded`，个别类在特定包中为 1（例如 `60C`），因此没有把对象角色的 max 写成全局公理。

这些 sheet 还包含包级配置/映射信息。它们已经被物化到 **Profile 层**（`ontology/wco-dm-4.3.0-profiles.ttl`）：

- 包成员、Min/Max、Seq. No.、Path；
- 37 个使用标记（eTIR、SSTL、AEO Master Data、Maritime API/BRI、UPU CUSRSP/CUSITM/REFRSP、FAL 1–7 等）；
- `Remark`、IMO ID/Term/Compendium 映射；
- `Unique Pos. ID`、`Cell Address`（有值的行）。

尚未物化的是 `MyDataSet` 扩展字段、原始批注/颜色等非结构化内容；这些保留在 `data/package-cardinalities.csv` 与源工作簿中。Profile 层说明见 `docs/profile-layer.md`。

### 变更日志工作簿（1 个，3 个 sheet）

| 工作簿 | sheet | 非空行 | 内容 | 状态 |
|---|---|---:|---|---|
| `Section 4. WCO DM Overview of Changes_V4.3.0-final 260622.xlsx` | `Introduction` | 7 | 工作簿说明 | **仅归档** |
| 同上 | `1. LIB Changes` | 4,452 | LIB 变更条目（Change、DMR、版本） | **仅归档** |
| 同上 | `2. OIS Changes` | 26,016 | OIS 变更条目 | **仅归档** |

变更日志是“为什么变成现在这样”的审计线索，不是当前模型的类/属性定义；未将其作为本体公理，但保留原文件与校验和。

---

## 2. 已吸收的基数信息

包级 sheet 的 `Min` / `Max` 列是核心 LIB/OIS 没有的语义。处理方式：

- 8,212 个数据元素行：`Min=0`、`Max=1`。
- 本体：每个 `owl:DatatypeProperty` 增加
  ```turtle
  wco:minOccurs 0 ;
  wco:maxOccurs 1 .
  ```
- SHACL：每个数据元素 PropertyShape 增加
  ```turtle
  sh:maxCount 1 .
  ```
- 对象属性：仅增加 `wco:minOccurs 0`；不写全局 `wco:maxOccurs`，因为类（C）行的最大值在不同包中可能是 `unbounded` 或 `1`。

因此，原先“完全不写基数”的说法已不再准确；现在是：

> **Min 全部为 0；数据元素 Max 为 1；对象角色的 Max 是包级可变，未全局断言。**

---

## 3. 复现审计

```bash
python3 scripts/package_audit.py
```

输出：

- `data/package-sheets.csv`：逐 sheet 的行数、类/属性数、新 ID 数、Min/Max 分布、定义冲突数、状态。
- `data/package-cardinalities.csv`：10,334 行包级明细（package、sheet、path、type、WCO ID、name、Min、Max、format、code list、definition）。

审计脚本会验证：

- 包级类/属性 ID 是否都在核心模型中；
- 定义是否与核心 LIB 冲突；
- 数据元素 Min/Max 是否一致。

本次结果：**0 个新类 ID、0 个新属性 ID、0 个定义冲突；8,212 个数据元素行全部 Min=0 / Max=1。**
