# システムアーキテクチャ

> **作成日**: 2026-02-09 | **最終更新日**: 2026-02-09

本ドキュメントでは、EFO-PlutchikDyad 再現プロジェクトのオントロジー構成、名前空間、クラス階層、プロパティ構造、およびデータフローを記述する。

---

## 1. オントロジーモジュール構成と依存関係

本プロジェクトは、DOLCE 基盤オントロジーの上に EmoCore を配置し、さらに PlutchikDyad モジュールを拡張として構築する階層的なモジュール構成を取る。

```
DUL (DOLCE-Ultralite)
  └── EmoCore (感情コア語彙)
        ├── EFO-BE (Basic Emotions: Ekman 6 感情)
        └── EFO-PlutchikDyad (本プロジェクトの拡張モジュール)
```

| モジュール | ファイル | 役割 |
|-----------|---------|------|
| DUL | `imports/DUL.owl` | 基盤オントロジー (Description, Situation 等) |
| EmoCore | `data/EmoCore_iswc.ttl` | 感情のコア語彙 (Emotion, BE_Emotion, triggers 等) |
| EFO-BE | `data/BE_iswc.ttl` | Ekman 理論に基づく基本感情と強度階層 |
| PlutchikDyad | `modules/EFO-PlutchikDyad.ttl` | Plutchik の感情の輪に基づく複合感情推論 |

**依存方向**: PlutchikDyad → EmoCore → DUL。PlutchikDyad は EmoCore の `emo:Emotion` クラスを継承し、Framester の `fschema:FrameOccurrence` をデータインスタンスのクラスとして利用する。

---

## 2. 名前空間一覧

| Prefix | IRI | 用途 |
|--------|-----|------|
| `pl:` | `http://example.org/efo/plutchik#` | PlutchikDyad モジュールのクラス・プロパティ |
| `emo:` | `http://www.ontologydesignpatterns.org/ont/emotions/EmoCore.owl#` | EmoCore のクラス・プロパティ |
| `be:` | `http://www.ontologydesignpatterns.org/ont/emotions/BasicEmotions.owl#` | Basic Emotions モジュール |
| `fschema:` | `https://w3id.org/framester/schema/` | Framester スキーマ (FrameOccurrence 等) |
| `dul:` | `http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#` | DOLCE-Ultralite 基盤オントロジー |
| `ex:` | `http://example.org/data#` | テストデータ (sample.ttl) のインスタンス |

---

## 3. クラス階層

### 3.1 感情クラス

```
dul:Description
  └── fschema:ConceptualFrame
        └── emo:Emotion
              ├── emo:BE_Emotion                    (EmoCore)
              ├── pl:PlutchikBasicEmotion            (PlutchikDyad)
              │     ├── pl:Joy
              │     ├── pl:Trust
              │     ├── pl:Fear
              │     ├── pl:Surprise
              │     ├── pl:Sadness
              │     ├── pl:Disgust
              │     ├── pl:Anger
              │     └── pl:Anticipation
              └── pl:PlutchikDyad                    (PlutchikDyad)
                    ├── pl:Love           (Joy + Trust)
                    ├── pl:Submission     (Trust + Fear)
                    ├── pl:Awe            (Fear + Surprise)
                    ├── pl:Disapproval    (Surprise + Sadness)
                    ├── pl:Remorse        (Sadness + Disgust)
                    ├── pl:Contempt       (Disgust + Anger)
                    ├── pl:Aggressiveness (Anger + Anticipation)
                    ├── pl:Optimism       (Anticipation + Joy)
                    ├── pl:Hope           (Anticipation + Trust)   [Secondary]
                    └── pl:Pride          (Anger + Joy)            [Secondary]
```

### 3.2 状況・証拠クラス

```
dul:Situation
  └── fschema:FrameOccurrence
        ≡ pl:EmotionSituation        (equivalentClass)

pl:Evidence
  └── pl:DyadEvidence               (推論により生成)
```

- `pl:EmotionSituation` は `fschema:FrameOccurrence` の `owl:equivalentClass` として定義されている。これにより EFO との互換性を保ちつつ、Plutchik モジュール固有の概念名を提供する。
- `pl:DyadEvidence` は `pl:Evidence` のサブクラスで、推論結果（複合感情の証拠）を表現する。

---

## 4. プロパティ構造

### 4.1 オブジェクトプロパティ

| プロパティ | ドメイン | レンジ | 説明 |
|-----------|---------|--------|------|
| `pl:hasEvidence` | `fschema:FrameOccurrence` | `pl:Evidence` | 状況から証拠ノードへのリンク |
| `pl:emotion` | `pl:Evidence` | `emo:Emotion` | 証拠ノードが示す感情 |
| `pl:derivedFrom` | `pl:DyadEvidence` | `pl:Evidence` | DyadEvidence から元の 2 つの Evidence への由来リンク |
| `pl:satisfies` | `fschema:FrameOccurrence` | `emo:Emotion` | 推論結果として状況が満たす感情 |
| `pl:hasComponentEmotion` | `pl:PlutchikDyad` | `pl:PlutchikBasicEmotion` | Dyad の構成要素となる基本感情 |

### 4.2 データタイププロパティ

| プロパティ | ドメイン | レンジ | 説明 |
|-----------|---------|--------|------|
| `pl:score` | `pl:Evidence` | `xsd:decimal` | 感情の確信度/強度 [0, 1] |
| `pl:method` | `pl:DyadEvidence` | `xsd:string` | 推論手法の名称 (例: `"min-threshold"`) |

---

## 5. データフロー

### 5.1 コア推論パイプライン

```
[入力データ]                [推論]                    [出力・検証]

data/sample.ttl  ─────┐
data/EmoCore_iswc.ttl ─┼──→ run_inference.py ──→ output/out.ttl
modules/EFO-          ─┘    (min-threshold          │
  PlutchikDyad.ttl           アルゴリズム)            │
                                                      ├──→ validate_shacl.py
                                                      │    (SHACL 検証)
                                                      │
                                                      ├──→ sparql/cq/*.rq
                                                      │    (CQ クエリ)
                                                      │
                                                      └──→ threshold_sweep.py
                                                           (閾値感度分析)
```

### 5.2 GoEmotions 実験パイプライン

```
[データ取得]          [NLP 分類]         [マッピング]         [RDF 変換]
GoEmotions ──→  roberta-base  ──→  NRC EmoLex  ──→  RDF (Turtle)
(N=2000)        (28 スコア)        (8 Plutchik)      (FrameOccurrence
step0                step1              step2           + Evidence)
                                                          step3
                                                            │
                     [評価]               [推論]             │
               ┌─ step4_evaluate  ←── run_inference.py ←────┘
               │   (Silver + Baselines    (--data 引数)
               │    + Metrics)
               │
               ├─ step4b (SemEval-2018 整合性)
               ├─ step5 (NRC vs Handcrafted 比較)
               └─ step6 (図表生成)
```

### 5.3 処理の流れ

**コアパイプライン:**

1. **入力**: `sample.ttl` (6 つの FrameOccurrence + 各 2 つの Evidence) と オントロジーモジュールをロード
2. **推論**: `run_inference.py` が min-threshold アルゴリズムで DyadEvidence を生成し、`pl:satisfies` トリプルを追加
3. **出力**: 推論結果を含む全トリプルを `output/out.ttl` に書き出し
4. **検証**:
   - `validate_shacl.py`: SHACL シェイプによる構造検証
   - `sparql/cq/`: コンピテンシー質問による意味的検証
   - `threshold_sweep.py`: 閾値パラメータの感度分析

**実験パイプライン:**

1. **データ取得** (step0): GoEmotions から 2,000 件の Reddit コメントをサンプリング
2. **NLP 分類** (step1): `SamLowe/roberta-base-go_emotions` で 28 感情スコアを取得
3. **マッピング** (step2): NRC EmoLex を用いて 28 → 8 Plutchik 感情に変換 (max 集約)
4. **RDF 変換** (step3): 8 スコアを FrameOccurrence + Evidence の Turtle 形式に変換 (41,816 トリプル)
5. **推論** (step3b): `run_inference.py --data` で Dyad を推論
6. **評価** (step4): Silver ラベル + 3 Baselines で Macro-F1/Micro-F1 を算出
7. **クロスドメイン検証** (step4b): SemEval-2018 EI-reg との整合性を Spearman 相関で確認
8. **比較分析** (step5): NRC vs Handcrafted マッピングの検出差を分析
9. **可視化** (step6): 6 枚の図表を生成

### ディレクトリ構成（プロジェクト全体）

```
emotion-frame-ontology/
├── data/
│   ├── EmoCore_iswc.ttl              # EmoCore モジュール
│   ├── BE_iswc.ttl                   # Basic Emotions モジュール
│   ├── BasicEmotionTriggers_iswc.ttl # トリガーパターン
│   ├── sample.ttl                    # テストデータ (6 状況)
│   └── experiment/                   # GoEmotions 実験データ (生成物)
│       ├── goemotion_subset.csv      # サブセット (N=2000)
│       ├── classified_scores.jsonl   # 28 感情スコア
│       ├── plutchik_scores.jsonl     # 8 Plutchik スコア
│       └── experiment_data.ttl       # RDF 形式 (41,816 トリプル)
├── experiment/                       # GoEmotions 評価パイプライン
│   ├── config.py                     # 共通定数 (DYADS, ラベル)
│   ├── step0_download_data.py        # データ取得
│   ├── step1_classify.py             # HuggingFace 分類
│   ├── step2_map_plutchik.py         # 28→8 マッピング
│   ├── step3_to_rdf.py               # RDF 変換
│   ├── step4_evaluate.py             # 評価
│   ├── step4b_semeval_consistency.py  # SemEval 整合性
│   ├── step5_compare_mappings.py     # マッピング比較
│   ├── step6_visualize.py            # 図表生成
│   ├── run_pipeline.py               # オーケストレータ
│   └── mappings/                     # マッピング定義
│       ├── goemotion_to_plutchik.json
│       └── nrc_mapping.py
├── imports/
│   ├── DUL.owl                       # DOLCE-Ultralite
│   └── catalog-v001.xml              # Protege IRI 解決
├── modules/
│   └── EFO-PlutchikDyad.ttl          # Plutchik Dyad 拡張モジュール
├── output/
│   ├── out.ttl                       # 推論出力 (生成物)
│   ├── threshold_sensitivity.csv     # 閾値分析結果 (生成物)
│   └── experiment/                   # 実験結果 (生成物)
│       ├── evaluation_report.json
│       ├── threshold_sweep_results.csv
│       ├── semeval_consistency.json
│       ├── mapping_comparison.json
│       └── figures/                  # 6 PNG 図表
├── scripts/
│   ├── run_inference.py              # Dyad 推論スクリプト
│   ├── threshold_sweep.py            # 閾値感度分析
│   ├── validate_shacl.py             # SHACL 検証
│   ├── download.sh                   # オントロジー一括ダウンロード
│   ├── extract_imports.py            # imports 解析
│   └── run_fuseki.sh                 # Fuseki 管理
├── shacl/
│   └── plutchik-dyad-shapes.ttl      # SHACL シェイプ定義
├── sparql/
│   ├── cq/                           # コンピテンシー質問 (7 クエリ)
│   └── dyad_rules/                   # SPARQL CONSTRUCT ルール (10 本)
└── docs/                             # 本ドキュメント群
```
