# EFO オントロジー再現作業ログ

**作業日**: 2026-01-09
**目的**: 論文「EFO: The Emotion Frame Ontology (De Giorgis & Gangemi, 2024)」のOWLオントロジー構造を再現可能な状態にする

---

## 1. 背景と目標

### 1.1 論文情報

- **タイトル**: EFO: the Emotion Frame Ontology
- **著者**: Stefano De Giorgis, Aldo Gangemi
- **arXiv**: https://arxiv.org/abs/2401.10751
- **公開日**: 2024年1月19日

### 1.2 成功条件（Acceptance Criteria）

| ID | 条件 | 達成状況 |
|----|------|----------|
| A | EmoCore（EmoCore_iswc.ttl）を取得し、Protégéでエラーなく開ける | **達成** |
| B | EFO-BE（Basic Emotionsモジュール）を特定・取得し、Protégéでエラーなく開ける | **達成** |
| C | ローカルRDFストアにEmoCore + EFO-BEをロードできる | **達成** |
| D-1 | SPARQLでBE_Emotion配下の感情クラス一覧を取得できる | **達成** |
| D-2 | SPARQLでmoreIntenseThan/lessIntenseThanの強度関係を取得できる | **達成** |
| D-3 | SPARQLでhasAntidote/hasImpediment/hasPreCondition等の関係を取得できる | **達成** |

---

## 2. 実施手順

### 2.1 配布元の特定

**問題**: 論文で指定されていたURL `https://anonymous.4open.science/r/EFO-C124/` はJavaScriptレンダリングが必要で、直接ダウンロードできなかった。

**解決**: Web検索により、正式なGitHubリポジトリを発見。

| 元URL | 実際の配布元 |
|-------|-------------|
| anonymous.4open.science/r/EFO-C124 | https://github.com/StenDoipanni/EFO |

### 2.2 リポジトリ構造の調査

GitHub APIを使用してリポジトリ内のファイルを列挙：

```
BE_Stats.png
BE_emotions_diagram.png
BE_iswc.ttl              ← EFO-BE（Basic Emotionsモジュール）
BasicEmotionTriggers_iswc.ttl
CREMA-kg.ttl
EmoCore_iswc.ttl         ← EmoCore
FER-kg.ttl
OCC_conceptual_map.png
README.md
WASSA2017.zip
occ_2023.owl
quokka_basic_emotions.png
```

**発見**:
- `EmoCore_iswc.ttl` がEmoCoreモジュール
- `BE_iswc.ttl` がEFO-BE（Basic Emotions）モジュール（論文では明示されていなかった）

### 2.3 オントロジーファイルのダウンロード

```bash
# 実行したコマンド
curl -sL "https://raw.githubusercontent.com/StenDoipanni/EFO/main/EmoCore_iswc.ttl" -o data/EmoCore_iswc.ttl
curl -sL "https://raw.githubusercontent.com/StenDoipanni/EFO/main/BE_iswc.ttl" -o data/BE_iswc.ttl
curl -sL "https://raw.githubusercontent.com/StenDoipanni/EFO/main/BasicEmotionTriggers_iswc.ttl" -o data/BasicEmotionTriggers_iswc.ttl
```

| ファイル | サイズ | 説明 |
|----------|--------|------|
| EmoCore_iswc.ttl | 7 KB | 感情のコア語彙（Frame Semanticsベース） |
| BE_iswc.ttl | 105 KB | Basic Emotions（Ekman理論） |
| BasicEmotionTriggers_iswc.ttl | 738 KB | 感情トリガーパターン |

### 2.4 owl:imports の解析

**EmoCore_iswc.ttl**:
- 明示的な `owl:imports` 宣言なし
- 参照のみ: DUL, Framester, DBpedia

**BE_iswc.ttl**:
```turtle
owl:imports <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl>
```

### 2.5 外部依存の取得

```bash
curl -sL "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl" -o imports/DUL.owl
```

**注意**: DUL.owlはTurtle形式で配信されていた（拡張子は.owlだがRDF/XMLではない）

| 依存 | IRI | 取得元 | 形式 |
|------|-----|--------|------|
| DUL (DOLCE-Ultralite) | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl | OntologyDesignPatterns.org | Turtle |

### 2.6 Protégé用catalog.xml作成

`imports/catalog-v001.xml` を作成し、IRIからローカルファイルへのマッピングを定義：

```xml
<uri name="http://www.ontologydesignpatterns.org/ont/dul/DUL.owl" uri="DUL.owl"/>
<uri name="http://www.ontologydesignpatterns.org/ont/emotions/EmoCore.owl" uri="../data/EmoCore_iswc.ttl"/>
<uri name="http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl" uri="../data/BE_iswc.ttl"/>
```

---

## 3. 検証結果

### 3.1 オントロジーロードテスト

Python (rdflib) を使用して検証：

```python
from rdflib import Graph
g = Graph()
g.parse('imports/DUL.owl', format='turtle')
g.parse('data/EmoCore_iswc.ttl', format='turtle')
g.parse('data/BE_iswc.ttl', format='turtle')
# 結果: 2955トリプル
```

### 3.2 SPARQL検証結果

#### Query 1: BE_Emotion配下の感情クラス一覧

```
結果: 55クラス
例: BE_Emotion, Anger, Annoyance, Fear, Anxiety, Sadness, Disgust, Enjoyment, Surprise...
```

#### Query 2: 強度関係 (moreIntenseThan)

```
結果: 41関係
例:
  Abhorrence > Revulsion
  Fury > Rage
  Anguish > Sorrow
  Anxiety > Nervousness
  Terror > Panic
  Ecstasy > Excitement
```

#### Query 3: hasAntidote関係

```
結果: 30関係
例:
  Annoyance -> AnnoyanceAntidote
  Anxiety -> AnxietyAntidote
  Despair -> DespairAntidote
```

#### Query 4: hasImpediment関係

```
結果: 10関係
例:
  Amusement -> AmusementImpediment
  Compassion -> CompassionImpediment
  Ecstasy -> EcstasyImpediment
```

#### Query 5: hasPreCondition関係

```
結果: 0関係
（このオントロジーではPreConditionは制約として定義されていない）
```

---

## 4. オントロジー構造の概要

### 4.1 名前空間

| Prefix | IRI |
|--------|-----|
| emo: | http://www.ontologydesignpatterns.org/ont/emotions/EmoCore.owl# |
| be: / basicemotions: | http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl# |
| dul: | http://www.ontologydesignpatterns.org/ont/dul/DUL.owl# |

### 4.2 主要クラス階層

```
dul:Description
  └── framester:ConceptualFrame
        └── emo:Emotion
              └── emo:BE_Emotion (EmoCore)
                    ├── be:Anger (BE)
                    │     ├── be:Annoyance
                    │     ├── be:Frustration
                    │     ├── be:Fury
                    │     └── ...
                    ├── be:Fear (BE)
                    ├── be:Sadness (BE)
                    ├── be:Disgust (BE)
                    ├── be:Enjoyment (BE)
                    └── be:Surprise (BE)
```

### 4.3 主要オブジェクトプロパティ

| プロパティ | ドメイン | レンジ | 説明 |
|-----------|---------|--------|------|
| emo:triggers | EmotionTrigger | Emotion | トリガー関係 |
| be:moreIntenseThan | Emotion | Emotion | 強度が高い（推移的） |
| be:lessIntenseThan | Emotion | Emotion | 強度が低い（inverse） |
| be:hasAntidote | Emotion | EmotionAntidote | 対処法 |
| be:hasImpediment | Emotion | EmotionImpediment | 阻害要因 |
| be:hasPreCondition | Emotion | PreCondition | 前提条件 |

---

## 5. 成果物一覧

```
./efo_repro/
├── README.md                      # 利用ガイド
├── WORK_LOG.md                    # 本ドキュメント
├── data/
│   ├── EmoCore_iswc.ttl           # コアモジュール (7KB)
│   ├── BE_iswc.ttl                # Basic Emotions (105KB)
│   └── BasicEmotionTriggers_iswc.ttl  # トリガー (738KB)
├── imports/
│   ├── DUL.owl                    # DOLCE-Ultralite (187KB)
│   └── catalog-v001.xml           # Protégé用IRI解決
├── sparql/
│   ├── 01_list_be_emotions.rq     # 感情クラス一覧
│   ├── 02_intensity_relations.rq  # 強度関係
│   ├── 03_optional_relations.rq   # hasAntidote
│   ├── 04_impediments.rq          # hasImpediment
│   └── 05_ontology_stats.rq       # 統計
└── scripts/
    ├── download.sh                # 一括ダウンロード
    ├── extract_imports.py         # imports解析
    └── run_fuseki.sh              # Fuseki管理
```

---

## 6. 既知の問題と注意点

### 6.1 DUL.owlのファイル形式

- 拡張子は `.owl` だが、実際はTurtle形式
- rdflibで読み込む際は `format='turtle'` を指定する必要がある

### 6.2 参照のみの外部IRI（stub不要）

以下のIRIは参照されているが、ロード時にエラーにならないためstub化は不要：

- `https://w3id.org/framester/schema/ConceptualFrame`
- `https://w3id.org/framester/schema/FrameOccurrence`
- `http://dbpedia.org/resource/Emotion`

### 6.3 hasPreConditionの利用状況

`be:hasPreCondition` プロパティは定義されているが、BE_iswc.ttl内の感情クラスに対する制約としては使用されていない。

---

## 7. 参考文献

1. De Giorgis, S., & Gangemi, A. (2024). EFO: the Emotion Frame Ontology. arXiv:2401.10751
2. Ekman, P. Atlas of Emotions. http://atlasofemotions.org
3. DOLCE-Ultralite. http://www.ontologydesignpatterns.org/ont/dul/DUL.owl
4. EFO GitHub Repository. https://github.com/StenDoipanni/EFO
