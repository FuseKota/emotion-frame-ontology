# 論文化計画: EFO-PlutchikDyad による複合感情検出の構成概念妥当性

> **作成日**: 2026-02-15 | **最終更新日**: 2026-02-15

---

## A. 改変禁止 / 改変OK 境界リスト

### READ-ONLY（EFO コア・先行研究由来 — 改変禁止）

| ファイル | 由来 |
|---------|------|
| `data/EmoCore_iswc.ttl` | De Giorgis & Gangemi (2024) 公開モジュール |
| `data/BE_iswc.ttl` | 同上 (Ekman Basic Emotions) |
| `data/BasicEmotionTriggers_iswc.ttl` | 同上 (トリガーパターン) |
| `imports/DUL.owl` | DOLCE-Ultralite 基盤オントロジー |
| `imports/catalog-v001.xml` | Protege IRI 解決用 |

### MODIFIABLE（自作拡張・実験系 — 改変OK）

| ファイル / ディレクトリ | 内容 |
|----------------------|------|
| `modules/EFO-PlutchikDyad.ttl` | 自作 Plutchik Dyad OWL モジュール |
| `scripts/*.py` | 推論・検証スクリプト |
| `shacl/plutchik-dyad-shapes.ttl` | 自作 SHACL シェイプ |
| `sparql/cq/*.rq`, `sparql/dyad_rules/*.rq` | 自作クエリ・ルール |
| `experiment/*.py` | 実験パイプライン全体 |
| `data/sample.ttl` | テストデータ |
| `data/experiment/` | 実験生成データ (CSV, JSONL, TTL) |
| `output/` | 全出力 |
| `docs/` | ドキュメント |

---

## B. 現状把握メモ

### 完了済み (Steps 0–6)

- **データ**: GoEmotions N=2,000 (seed=42), SemEval-2018 EI-reg 7,431 ユニークテキスト
- **分類**: SamLowe/roberta-base-go_emotions → 28 scores/sample
- **マッピング**: NRC EmoLex (28→8, max 集約) → 8 Plutchik scores/sample
- **RDF 変換**: 2,000 FrameOccurrence, 9,454 Evidence, 41,816 triples
- **推論**: min-threshold (TH=0.4) → 965 Dyad (8/10 種類検出)
- **評価**: Silver-F1 (Macro=0.800, Micro=1.000), 3 baselines
- **SemEval 検証**: 二値 (present/absent) Spearman + Mann-Whitney → 4/10 Dyad 有意
  - Love ρ=0.285, Disapproval ρ=0.237, Optimism ρ=0.110, Contempt ρ=0.068
- **マッピング比較**: NRC vs Handcrafted (kappa=0.145, NRC が 12x 多い)
- **可視化**: 6 PNG (threshold, distribution, cooccurrence, heatmap, semeval, mapping)

### 主要な弱点

| 弱点 | 深刻度 | 対策の方向 |
|------|--------|-----------|
| Silver ラベル自己参照 (TH=0.4 で Micro-F1=1.0 は定義上) | **高** | SemEval 連続評価を主軸にする |
| SemEval は二値評価のみ (dyadScore 連続値を使っていない) | **高** | Spearman(dyadScore vs intensity) を主指標 + PR-AUC は補助 |
| dyadScore の増分価値が未証明 | **高** | 偏相関 + permutation 検定 を主に、OLS は補助 |
| 多重検定補正なし | **高** | Holm 補正 (or BH) を全 p 値に適用 |
| SemEval の重複テキスト処理が曖昧 | **高** | text dedup を明示、n(Unique) を Table に記載 |
| Awe/Aggressiveness ゼロサポート | 中 | 構造的限界として明記 + 共起分析で根拠提示 |
| Rare dyad (Pride=4, Submission=2) | 中 | 検証対象から除外、頻出 4 Dyad に集中 |
| SHACL/CQ が手動実行のみ | 中 | KPI 自動集計で「再現性」を定量化 |
| Baselines が弱い (No-Dyad, Naive のみ) | 中 | 成分スコアのみ baseline を追加 |
| EFO コア改変禁止が口頭ルールのみ | 低 | CI / pre-commit で機械的に保護 |

### データ所在確認

| データ | パス | 形式 | 再利用方法 |
|--------|------|------|-----------|
| Plutchik scores (GoEmotions) | `data/experiment/plutchik_scores.jsonl` | `{"plutchik_scores": {"Joy": 0.55, ...}}` | dyadScore 計算可能 |
| SemEval raw | `data/experiment/semeval_raw/EI-reg-En-{emo}-{split}.txt` | TSV (id, text, emotion, intensity) | 8 ファイル全存在 |
| SemEval cache | `data/experiment/semeval_cache/semeval_ei_reg_{emo}.jsonl` | `{"text":..., "intensity":...}` | 4 ファイル全存在 |
| SemEval 分類済み | **未生成** | — | step4b._classify_and_map() で生成、キャッシュ必要 |
| RDF 推論出力 | `output/experiment/inference_out.ttl` | Turtle | SHACL/CQ の入力 |

### dyadScore（連続値）の状態

- **RDF 出力**: `inference_out.ttl` に `pl:score` として格納済み (decimal)
- **Python 出力**: `evaluation_report.json` には binary カウントのみ。連続 dyadScore は JSON 未保存
- **step4b (SemEval)**: `_infer_dyads_binary()` — binary のみ。連続値関数なし
- **計算自体は簡単**: `dyadScore = min(score_comp1, comp2)` で閾値なしに算出可能

### SemEval 重複テキストの現状

- 4 感情ファイル (anger, fear, joy, sadness) × 2 split (train, dev) = 8 TSV
- 同一ツイートが複数感情ファイルに出現する（例: anger-train と joy-train に同一 text）
- 現行 step4b は `text_to_intensities[text][emo] = intensity` で text キーでユニーク化
- **7,431 unique texts**（8,566 レコードから text dedup 後）
- 相関分析では「ある感情の intensity を持つサンプル」に絞るため、n は感情ごとに異なる
  - joy: ~1,906、sadness: ~1,930、anger: ~2,000、fear: ~2,000

### 多重共線性リスク

- `dyadScore = min(comp1, comp2)` は comp1/comp2 の決定的関数
- OLS に dyadScore + comp1 + comp2 を入れると多重共線性が生じ ΔR² が不安定になるリスク
- **対策**: 偏相関 + permutation 検定を主指標にし、OLS は交互作用項 (comp1*comp2) との比較で補助

---

## C. 研究ストーリー（方針案）

### 主張

> EFO-PlutchikDyad のオントロジーに基づく複合感情推論 (min-threshold) は:
> 1. **外部妥当性**: SemEval-2018 の感情強度と連続的に有意に相関する (construct validity)
> 2. **増分価値**: コンポーネントスコア単独よりも、dyadScore が追加の説明力を持つ (incremental value)
> 3. **評価の質**: SHACL/CQ による形式検証で、推論の再現性・説明性を定量保証できる

### 評価フレームワーク

```
┌─────────────────────────────────────────────────────────┐
│  主評価: SemEval-2018 連続評価 (外部妥当性)               │
│  ├─ 主指標: Spearman ρ [Bootstrap 95% CI]                │
│  │   dyadScore vs SemEval intensity (per Dyad-Emotion)   │
│  ├─ 補助: PR-AUC (t ∈ {0.25, 0.5, 0.75} の複数閾値)      │
│  ├─ 多重検定: Holm 補正 (Dyad×Emotion ペア数)             │
│  └─ n(Unique): text dedup 後の実サンプル数を明記          │
├─────────────────────────────────────────────────────────┤
│  補助評価 A: 増分価値 (incremental value)                 │
│  ├─ 主指標: 偏相関 (comp1, comp2 制御) + permutation 検定 │
│  ├─ 補助: OLS → ΔR² + F検定                              │
│  │   Model 1: intensity ~ comp1 + comp2                   │
│  │   Model 2: intensity ~ comp1 + comp2 + dyadScore       │
│  │   Model 3: intensity ~ comp1 + comp2 + comp1*comp2     │
│  │   → dyadScore が「交互作用のオントロジー的実装」        │
│  └─ 多重共線性対策: VIF チェック、偏相関を主に置く        │
├─────────────────────────────────────────────────────────┤
│  補助評価 B: GoEmotions E2E (内部整合性)                  │
│  ├─ Silver-F1 threshold sweep (既存: Table/Fig)           │
│  ├─ NRC vs Handcrafted 比較 (既存: Table/Fig)             │
│  └─ 共起分析 (既存: Fig)                                  │
├─────────────────────────────────────────────────────────┤
│  品質評価: SHACL/CQ KPI (再現性・説明性)                  │
│  ├─ SHACL violation 率 (/1000 samples)                    │
│  ├─ derivedFrom 完備率                                    │
│  ├─ score soundness (dyadScore ≤ min(comp1, comp2))       │
│  └─ CQ explanation coverage                               │
└─────────────────────────────────────────────────────────┘
```

### 論文の主テーブル/主図

| # | 種別 | 内容 | 新規/既存 | 位置 |
|---|------|------|----------|------|
| Table 1 | Table | SemEval 連続評価: Dyad × Emotion の Spearman ρ [95% CI], PR-AUC(t=0.25/0.5/0.75), p(Holm), n(Unique) | **新規** | 主結果 |
| Table 2 | Table | 増分価値: 偏相関 (permutation p), ΔR², comp1*comp2 との比較 | **新規** | 主結果 |
| Table 3 | Table | SHACL/CQ KPI サマリ (violation率, 完備率, CQ pass率) | **新規** | 品質評価 |
| Table 4 | Table | GoEmotions threshold sweep (既存データ整形) | 既存 | 補助 |
| Fig 1 | Figure | dyadScore vs SemEval intensity 散布図 (2×2: Love, Disapproval, Optimism, Contempt) | **新規** | 主結果 |
| Fig 2 | Figure | 増分価値: ΔR² 棒グラフ | **新規** | 主結果 |
| Fig 3 | Figure | Dyad 分布 + 共起分析 (既存 Fig 2+3 統合) | 既存 | 補助 |
| Fig 4 | Figure | SHACL/CQ ダッシュボード | **新規** | 品質評価 |

### 弱点の書き方

| 弱点 | 論文での扱い |
|------|------------|
| Silver 自己参照 | 「Silver-F1 は内部整合性の確認であり、外部妥当性は SemEval 連続評価で示す」→ limitation ではなく methodological choice として位置づけ |
| Awe/Aggressiveness ゼロ | 「分類器出力の構造的制約であり、共起分析 (Fig 3) で根拠を明示。本手法の限界ではなくパイプライン上流の限界」 |
| Rare dyads | 「頻出 4 Dyad (Love, Disapproval, Optimism, Contempt) に焦点。6 dyads は SemEval カバレッジ外 or n<10 のため supplementary に回す」 |
| 人手アノテーションなし | 「SemEval intensity は第三者が付与した連続スコアであり、外部基準として十分。Gold dyad ラベルは future work」 |

---

## D. 実装タスク（優先度順）

### Task 1: `experiment/step7_semeval_continuous.py` — SemEval dyadScore 連続評価

**目的**: 現行の二値評価 (step4b) を連続評価に拡張。論文の **Table 1, Fig 1** を生成。

**入出力**:
- 入力: SemEval データ (`semeval_cache/*.jsonl`) + 分類済みキャッシュ (新規生成)
- 出力: `output/experiment/semeval_continuous.json`

**処理フロー**:
1. `step4b._load_semeval_data()` で SemEval データ読み込み (再利用)
2. `step4b._classify_and_map()` で Plutchik スコア取得 (再利用) → `semeval_plutchik_cache.jsonl` にキャッシュ保存
3. **Dedup 明示化**: text キーでユニーク化。同一テキストが複数感情に出る場合、各感情の intensity を保持。n(Unique) を全出力に記載
4. 各サンプルの dyadScore 計算: `min(comp1, comp2)` — 閾値なし、全サンプルで連続値
5. 各 Dyad-SemEval emotion ペアについて:
   - **主指標: Spearman ρ** (dyadScore vs intensity) + **Bootstrap 95% CI** (n_boot=2000)
   - **補助: PR-AUC** (t ∈ {0.25, 0.5, 0.75} の 3 閾値) — intensity > t を正例、dyadScore で識別
6. **多重検定補正**: 全 p 値に **Holm 補正** を適用 (テストされる Dyad-Emotion ペア数に対して)
7. `DYAD_CONSISTENCY_MAP` (step4b:50–61) をそのまま使用

**再利用コード**:
- `step4b._load_semeval_data()` (L64–121)
- `step4b._classify_and_map()` (L124–168)
- `step4b.DYAD_CONSISTENCY_MAP` (L50–61)

**新規関数**:
```python
def _compute_dyad_scores(plutchik: Dict[str, float]) -> Dict[str, float]:
    """Return continuous dyadScore = min(comp1, comp2) for all dyads."""
    return {dyad: min(plutchik.get(e1, 0), plutchik.get(e2, 0))
            for dyad, (e1, e2) in DYADS.items()}
```

**依存**: `scipy.stats`, `sklearn.metrics.average_precision_score`, `numpy`

**推定所要時間**: 分類キャッシュがあれば数秒。初回は分類に ~2分 (7,431 テキスト)。

---

### Task 2: `experiment/step8_incremental_value.py` — 増分価値検証

**目的**: dyadScore が成分スコア単独を超える説明力を持つことを示す。論文の **Table 2, Fig 2**。

**処理フロー**:
1. Task 1 のキャッシュ (`semeval_plutchik_cache.jsonl`) + SemEval intensity を読み込み
2. 頻出 4 Dyad (Love/joy, Disapproval/sadness, Optimism/joy, Contempt/anger) に対して:

**主指標: 偏相関 + Permutation 検定**
   - dyadScore と intensity の偏相関（comp1, comp2 を制御変数）
   - Permutation 検定 (n_perm=10000) で p 値算出 — OLS より解釈しやすく多重共線性に頑健

**補助: OLS 回帰 (3 モデル比較)**
   - **Model 1** (components only): `intensity ~ comp1 + comp2`
   - **Model 2** (+ dyadScore): `intensity ~ comp1 + comp2 + dyadScore`
   - **Model 3** (+ interaction): `intensity ~ comp1 + comp2 + comp1*comp2`
   - **ΔR²**: Model 2 vs Model 1, Model 3 vs Model 1
   - **F 検定**: nested model comparison
   - **VIF チェック**: dyadScore の VIF を報告（多重共線性の程度を明示）
   - **論点**: dyadScore (= min) と comp1*comp2 (交互作用) の比較
     → dyadScore が「交互作用のオントロジー的実装」であることを示す

3. **Holm 補正**: 全 p 値に適用

**依存**: `statsmodels>=0.14.0` (OLS, VIF), `scipy.stats`, `numpy`

**出力**: `output/experiment/incremental_value.json`

---

### Task 3: `experiment/step9_ontology_qa.py` — SHACL/CQ KPI 自動化

**目的**: 推論の再現性・説明性を定量 KPI として報告。論文の **Table 3, Fig 4**。

**処理フロー**:
1. **SHACL 検証**:
   - `scripts/validate_shacl.py:load_data_graph()`, `load_shapes_graph()`, `run_validation()` を import
   - 入力: `data/experiment/experiment_data.ttl` + `output/experiment/inference_out.ttl` + `modules/EFO-PlutchikDyad.ttl`
   - KPI: conforms (bool), violation 数, warning 数
2. **CQ 実行**: `sparql/cq/*.rq` の 7 クエリを rdflib で実行
   - 各クエリの結果行数・pass/fail を判定
   - 特に重要:
     - `cq_missing_provenance.rq`: 来歴欠損数 → 0 が期待値
     - `cq_score_reconstruction.rq`: min 不整合数 → 0 が期待値
     - `cq3_explain.rq`: 説明可能な DyadEvidence 数 (= explanation coverage)
3. **追加 KPI**:
   - `derivedFrom 完備率`: DyadEvidence のうち derivedFrom が 2 本揃う割合
   - `score soundness`: dyadScore ≤ min(comp1, comp2) の満足率
   - `violations per 1K triples`

**再利用コード**:
- `scripts/validate_shacl.py:load_data_graph()` (L29–62), `load_shapes_graph()` (L65–83), `run_validation()` (L86–104)

**注意**: `inference_out.ttl` の存在が前提。不在時はスキップ + warning。

**出力**: `output/experiment/ontology_qa.json`

---

### Task 4: 可視化拡張 — `experiment/step6_visualize.py` に Fig 7–9 追加

#### Fig 7: `semeval_continuous_correlation.png` (論文 Fig 1)
- 2×2 scatter: dyadScore (X) vs SemEval intensity (Y)
- 4 パネル: Love/joy, Disapproval/sadness, Optimism/joy, Contempt/anger
- 回帰線 + 95% CI 帯
- Spearman ρ [CI] と PR-AUC をアノテーション
- データ: `semeval_plutchik_cache.jsonl` + `semeval_cache/*.jsonl`

#### Fig 8: `incremental_value.png` (論文 Fig 2)
- Grouped bar: 4 Dyad × 2 Models の R²
- ΔR² をオーバーレイ (有意なら *)
- 偏相関値をテキスト注釈
- データ: `incremental_value.json`

#### Fig 9: `ontology_qa_dashboard.png` (論文 Fig 4)
- 2-panel:
  - Left: SHACL pass/violation/warning (stacked bar or pie)
  - Right: CQ 7 クエリの pass/fail グリッド
- データ: `ontology_qa.json`

---

### Task 5: パイプライン統合 — `experiment/run_pipeline.py`

- Step 7, 8, 9 を追加 (step4b の後に配置)
- `--skip-step7`, `--skip-step8`, `--skip-step9` フラグ
- Step 7 → 8 は依存関係あり (Plutchik キャッシュ共有)
- Step 9 は Step 3b (inference_out.ttl) に依存
- step6 拡張で Fig 7–9 も生成 (既存 `--only` で制御可能)

---

### Task 6: `experiment/config.py` 更新

```python
# step4b から昇格 (共有定数化)
DYAD_CONSISTENCY_MAP: Dict[str, List[str]] = {
    "Love": ["joy"], "Submission": ["fear"], "Awe": ["fear"],
    "Disapproval": ["sadness"], "Remorse": ["sadness"],
    "Contempt": ["anger"], "Aggressiveness": ["anger"],
    "Optimism": ["joy"], "Hope": [], "Pride": ["anger", "joy"],
}

# 焦点 Dyad (SemEval で十分なサンプル数がある 4 Dyad)
FOCUS_DYADS: List[str] = ["Love", "Disapproval", "Optimism", "Contempt"]

# Bootstrap
N_BOOTSTRAP = 2000
```

---

### Task 7: docs 更新

- `docs/goemotion-experiment-report.md`: Section 11–13 追加 (連続評価, 増分価値, QA KPI)
- `docs/inference-pipeline.md`: step7–9 の実行方法追記
- 実行コマンド例とファイル名を docs に明記

---

### Task 8: EFO コア改変禁止の機械的保護

**目的**: 境界リストを口頭ルールではなく CI / pre-commit で担保する。

**実装 (2 ファイル)**:

1. **`.github/workflows/protect-efo-core.yml`** (or pre-commit hook):
   ```yaml
   # data/EmoCore_iswc.ttl, data/BE_iswc.ttl,
   # data/BasicEmotionTriggers_iswc.ttl, imports/DUL.owl
   # に差分があったら fail
   ```
   実装: `git diff --name-only HEAD~1` で対象ファイルを検出、存在すれば exit 1

2. **`.gitattributes`** にロック表記追加:
   ```
   data/EmoCore_iswc.ttl -diff merge=ours
   data/BE_iswc.ttl -diff merge=ours
   data/BasicEmotionTriggers_iswc.ttl -diff merge=ours
   imports/DUL.owl -diff merge=ours
   ```

**軽量代替**: pre-commit hook として `scripts/check_efo_core.sh` を用意し、sha256 チェック。

---

## E. 実装順序

```
0. scripts/check_efo_core.sh + .gitattributes — EFO コア保護 (Task 8)
1. experiment/config.py          — 共有定数追加 (DYAD_CONSISTENCY_MAP 昇格, FOCUS_DYADS)
2. experiment/step7_semeval_continuous.py — 新規作成・実行 → semeval_continuous.json
3. experiment/step8_incremental_value.py — 新規作成・実行 → incremental_value.json
4. experiment/step9_ontology_qa.py      — 新規作成・実行 → ontology_qa.json
5. experiment/step6_visualize.py        — Fig 7–9 追加・生成 → 3 PNG
6. experiment/run_pipeline.py           — Step 7–9 統合
7. docs/ 更新                           — 実行手順・結果・解釈
```

各ステップで「実行→結果確認→次へ」を行い、中間結果を報告する。

---

## F. 検証

1. `python -m experiment.step7_semeval_continuous` → `semeval_continuous.json` 生成、Love の ρ > 0.2 かつ p < 0.001 を確認
2. `python -m experiment.step8_incremental_value` → `incremental_value.json` 生成、ΔR² > 0 の Dyad が存在することを確認
3. `python -m experiment.step9_ontology_qa` → `ontology_qa.json` 生成、SHACL conforms=true、CQ 7/7 pass
4. `python -m experiment.step6_visualize --only 7 8 9` → 3 PNG 生成
5. 全パイプライン通し: `python -m experiment.run_pipeline --skip-download --skip-classify --skip-semeval`

---

## G. 論文構成案（参考）

| Section | 内容 | 主要な Table/Fig |
|---------|------|-----------------|
| 1. Introduction | 複合感情検出の重要性、flat classifier の限界 | — |
| 2. Related Work | Plutchik, GoEmotions, SemEval-2018, EFO, ontology-based emotion | — |
| 3. EFO-PlutchikDyad | OWL 定義、min-threshold、SPARQL rules | — |
| 4. Experimental Setup | GoEmotions pipeline, NRC mapping, SemEval validation | — |
| 5. Results | | |
| 5.1 Construct Validity | dyadScore vs SemEval intensity | **Table 1, Fig 1** |
| 5.2 Incremental Value | dyadScore vs components alone | **Table 2, Fig 2** |
| 5.3 Ontology QA | SHACL/CQ KPI | **Table 3, Fig 4** |
| 5.4 Threshold Analysis | Sweep, distribution, mapping comparison | Table 4, Fig 3 |
| 6. Discussion | Silver 自己参照の位置づけ、ゼロサポート、rare dyad、将来課題 (Semantic-F1, Gold ラベル) | — |
| 7. Conclusion | | — |

### 将来課題として記載 (実装不要)
- **Semantic-F1**: SKOS:exactMatch/closeMatch による部分点評価のプロトタイプ案
- **Gold ラベル**: 人手アノテーションによる外部正解の作成
- **マルチモーダル拡張**: テキスト以外 (音声, 表情) への応用
- **Tertiary Dyad**: 現在の 10 Dyad → 全 Dyad カバレッジへの拡張
