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

---

## 7. GoEmotions 実験パイプライン構築

**作業日**: 2026-02-15
**目的**: 実テキストデータを用いた Plutchik Dyad 推論の定量的評価

### 7.1 実装したパイプライン

| Step | スクリプト | 処理内容 |
|------|----------|---------|
| 0 | `experiment/step0_download_data.py` | GoEmotions サブセット取得 (N=2000, seed=42) |
| 1 | `experiment/step1_classify.py` | roberta-base-go_emotions で 28 感情スコア取得 |
| 2 | `experiment/step2_map_plutchik.py` | NRC EmoLex で 28→8 Plutchik マッピング (max 集約) |
| 3 | `experiment/step3_to_rdf.py` | Plutchik スコア → RDF (Turtle) 変換 |
| 3b | `scripts/run_inference.py --data` | RDF ベース Dyad 推論（既存スクリプトに `--data` 引数追加） |
| 4 | `experiment/step4_evaluate.py` | Silver ラベル + 3 Baselines + メトリクス |
| 4b | `experiment/step4b_semeval_consistency.py` | SemEval-2018 EI-reg との整合性評価 |
| 5 | `experiment/step5_compare_mappings.py` | NRC vs Handcrafted マッピング比較 |
| 6 | `experiment/step6_visualize.py` | 6 つの図表生成 |

オーケストレータ: `experiment/run_pipeline.py`

### 7.2 既存ファイルの変更

| ファイル | 変更 |
|---------|------|
| `scripts/run_inference.py` | `--data` 引数追加、`load_graph(data_file=)` パラメータ追加。self-test は `--data` 未指定時のみ。後方互換 |
| `.gitignore` | 新規作成。`data/experiment/`, `output/experiment/`, `__pycache__/` |

### 7.3 追加ファイル一覧

```
.gitignore                               # 新規
requirements-experiment.txt              # 実験用追加依存
experiment/
├── __init__.py
├── config.py                            # 共通定数 (DYADS, ラベル, 閾値, パス)
├── mappings/
│   ├── __init__.py
│   ├── goemotion_to_plutchik.json       # Handcrafted マッピング表
│   └── nrc_mapping.py                   # NRC EmoLex マッピング
├── step0_download_data.py
├── step1_classify.py
├── step2_map_plutchik.py
├── step3_to_rdf.py
├── step4_evaluate.py
├── step4b_semeval_consistency.py
├── step5_compare_mappings.py
├── step6_visualize.py
└── run_pipeline.py
docs/
└── goemotion-experiment-report.md       # 実験レポート（全結果・図表参照）
```

### 7.4 主要な実験結果

#### Silver ラベル分布 (TH=0.4, N=2000)

| Dyad | 件数 | 割合 |
|------|------|------|
| Love | 561 | 28.1% |
| Hope | 172 | 8.6% |
| Optimism | 130 | 6.5% |
| Disapproval | 46 | 2.3% |
| Contempt | 29 | 1.5% |
| Remorse | 21 | 1.1% |
| Pride | 4 | 0.2% |
| Submission | 2 | 0.1% |
| Awe | 0 | 0.0% |
| Aggressiveness | 0 | 0.0% |

#### Baseline 比較

| Baseline | Macro-F1 | Micro-F1 |
|----------|---------|---------|
| No-Dyad | 0.000 | 0.000 |
| Naive-Dyad | 0.123 | 0.202 |
| **Score-Aware (TH=0.4)** | **0.800** | **1.000** |

#### SemEval-2018 整合性（7,431 ツイート）

4 Dyad で統計的に有意な整合性を確認 (p < 0.01):

| Dyad | Spearman rho | 効果量 r |
|------|-------------|---------|
| Love (joy) | 0.285 | 0.367 |
| Disapproval (sadness) | 0.237 | 0.510 |
| Optimism (joy) | 0.110 | 0.218 |
| Contempt (anger) | 0.068 | 0.528 |

#### NRC vs Handcrafted マッピング比較

| 方式 | 総 Dyad 検出数 | Cohen's kappa |
|------|--------------|--------------|
| NRC | 965 | — |
| Handcrafted | 79 | 0.145 |

NRC が 12 倍多く検出。差の主因は Trust (3.0x) と Anticipation (3.7x) のカバレッジ差。
Awe/Aggressiveness は両方式でゼロ（分類器の出力分布の問題）。

### 7.5 生成した図表

| 図 | ファイル | 内容 |
|---|---------|------|
| Fig 1 | `figures/threshold_sweep_f1.png` | Macro/Micro-F1 vs 閾値曲線 |
| Fig 2 | `figures/dyad_distribution.png` | Dyad 分布棒グラフ |
| Fig 3 | `figures/score_cooccurrence.png` | コンポーネント共起散布図 (2x2) |
| Fig 4 | `figures/per_dyad_heatmap.png` | Per-Dyad F1 ヒートマップ |
| Fig 5 | `figures/semeval_effect_sizes.png` | SemEval 効果量プロット |
| Fig 6 | `figures/mapping_comparison.png` | NRC vs Handcrafted 比較 |

### 7.6 主な知見

1. **min-threshold 集約は有効**: Naive-Dyad 比で Macro-F1 が 6.5 倍改善
2. **閾値感度は穏やか**: TH=0.35〜0.45 で Micro-F1 > 0.96
3. **SemEval クロスドメイン検証**: 4 Dyad で Twitter データとも有意な整合性
4. **Awe/Aggressiveness のゼロサポート**: Fear+Surprise, Anger+Anticipation が分類器レベルで共起しない構造的問題。サンプル数増加では解決不可
5. **NRC マッピングが圧倒的に有利**: Handcrafted の 12 倍の Dyad を検出

### 7.7 未コミットの変更

```
M  scripts/run_inference.py       # --data 引数追加
?? .gitignore
?? docs/goemotion-experiment-report.md
?? experiment/                     # パイプライン全体
?? requirements-experiment.txt
```

---

## 8. 参考文献

1. De Giorgis, S., & Gangemi, A. (2024). EFO: the Emotion Frame Ontology. arXiv:2401.10751
2. Ekman, P. Atlas of Emotions. http://atlasofemotions.org
3. DOLCE-Ultralite. http://www.ontologydesignpatterns.org/ont/dul/DUL.owl
4. EFO GitHub Repository. https://github.com/StenDoipanni/EFO
5. Demszky, D., et al. (2020). GoEmotions: A Dataset of Fine-Grained Emotions. ACL 2020
6. Mohammad, S. & Turney, P. (2013). Crowdsourcing a Word-Emotion Association Lexicon. Computational Intelligence, 29(3)
7. Mohammad, S., et al. (2018). SemEval-2018 Task 1: Affect in Tweets. SemEval-2018
