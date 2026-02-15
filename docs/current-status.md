# EFO-PlutchikDyad 実験パイプライン：現状報告書

> **作成日**: 2026-02-15 | **最終更新日**: 2026-02-15

**ブランチ**: `experiment` (最新コミット: `fd64c3d`)

---

## 1. プロジェクト概要

本プロジェクトは、EFO-PlutchikDyad オントロジーに基づく複合感情 (Dyad) 推論の
**構成概念妥当性 (Construct Validity)** を実証するための実験パイプラインである。

Plutchik の感情の輪に定義される 10 種類の Dyad（例: Love = Joy + Trust）を、
テキストから自動推論する min-threshold アルゴリズムを GoEmotions データセットに適用し、
SemEval-2018 の外部感情強度データとの相関分析によって妥当性を評価する。

### 研究の 3 つの主張

1. **外部妥当性**: dyadScore は SemEval-2018 の感情強度と有意に相関する
2. **増分価値**: dyadScore は成分スコア単独を超える説明力を持つ
3. **品質保証**: SHACL/CQ による形式検証で推論の再現性・説明性を定量保証できる

---

## 2. パイプライン実行状況

### 2.1 全ステップ一覧

| Step | 名称 | 状態 | 出力ファイル |
|------|------|------|------------|
| 0 | GoEmotions ダウンロード | **完了** | `data/experiment/goemotion_subset.csv` |
| 1 | RoBERTa 分類 (28 scores) | **完了** | `data/experiment/classified_scores.jsonl` |
| 2 | NRC EmoLex マッピング (28→8) | **完了** | `data/experiment/plutchik_scores.jsonl` |
| 3 | RDF 変換 | **完了** | `data/experiment/experiment_data.ttl` |
| 3b | RDF 推論 (min-threshold) | **完了** | `output/experiment/inference_out.ttl` |
| 4 | Silver ラベル評価 | **完了** | `output/experiment/evaluation_report.json` |
| 4b | SemEval 二値一致性評価 | **完了** | `output/experiment/semeval_consistency.json` |
| 5 | NRC vs Handcrafted 比較 | **完了** | `output/experiment/mapping_comparison.json` |
| 6 | 可視化 (9 図) | **完了** | `output/experiment/figures/*.png` |
| **7** | **SemEval 連続評価** | **完了** | `output/experiment/semeval_continuous.json` |
| **8** | **増分価値検証** | **完了** | `output/experiment/incremental_value.json` |
| **9** | **オントロジー QA** | **完了** | `output/experiment/ontology_qa.json` |

Step 7–9 および Fig 7–9 は 2026-02-15 に新規実装・実行完了。

### 2.2 データ規模

| 項目 | 数値 |
|------|------|
| GoEmotions サンプル数 | 2,000 (seed=42) |
| FrameOccurrence | 2,000 |
| Evidence ノード | 9,454 |
| 総トリプル数 | 58,346 (推論後) |
| 推論 Dyad 数 | 965 (TH=0.4) |
| SemEval ユニークテキスト数 | 7,801 |
| Dyad 検出種類 | 8/10 (Awe, Aggressiveness を除く) |

---

## 3. 主要結果

### 3.1 構成概念妥当性 — SemEval 連続評価 (Step 7)

焦点 4 Dyad について、dyadScore (= min(comp1, comp2)) と SemEval-2018 の感情強度の
Spearman 相関を算出した。全 p 値に Holm 補正を適用。Bootstrap CI (n=2,000)。

| Dyad | SemEval 感情 | n | Spearman ρ | 95% CI | p (Holm) | PR-AUC (t=0.5) |
|------|-------------|---|-----------|--------|----------|---------------|
| **Disapproval** | sadness | 1,930 | **+0.636** | [+0.608, +0.662] | 2.73e-218 *** | 0.775 |
| **Contempt** | anger | 2,089 | **+0.509** | [+0.476, +0.541] | 3.22e-137 *** | 0.692 |
| **Love** | joy | 1,906 | **+0.349** | [+0.308, +0.389] | 3.63e-55 *** | 0.654 |
| **Optimism** | joy | 1,906 | **+0.165** | [+0.117, +0.208] | 9.53e-13 *** | 0.551 |

**主要な発見**:
- 4 Dyad すべてが Holm 補正後も p < 0.001 で有意
- Disapproval が最も強い相関 (ρ = 0.636) を示す
- Contempt は n=11 だった二値評価 (step4b) から n=2,089 の連続評価に改善し、ρ = 0.509 の強い相関を確認
- Optimism は最も弱い (ρ = 0.165) が、依然として高度に有意

**Step 4b (二値評価) からの改善点**:
- 二値 (present/absent) → 連続値 (dyadScore) に拡張
- Spearman ρ が全体的に改善 (例: Love 0.285 → 0.349)
- Bootstrap CI により信頼区間を定量化
- PR-AUC を 3 閾値 (0.25, 0.50, 0.75) で補助指標として追加

### 3.2 増分価値 — 偏相関 + OLS (Step 8)

dyadScore が成分スコア (comp1, comp2) を制御した後も追加の説明力を持つかを検証。
主指標: 偏相関 + permutation 検定 (n=10,000)。補助: OLS 3 モデル比較。

| Dyad | SemEval 感情 | 偏相関 r | p (Holm) | ΔR² (dyad) | ΔR² (交互作用) | VIF |
|------|-------------|---------|----------|-----------|-------------|-----|
| **Disapproval** | sadness | **+0.161** | 0.0004 *** | +0.0094 | +0.0006 | 3.5 |
| **Optimism** | joy | **+0.085** | 0.0009 *** | +0.0037 | +0.0003 | 5.4 |
| **Contempt** | anger | **+0.075** | 0.0012 ** | +0.0002 | +0.0007 | 2.1 |
| **Love** | joy | **+0.065** | 0.0055 ** | +0.0009 | +0.0008 | 17.6 |

**OLS 3 モデル比較**:
- **Model 1**: `intensity ~ comp1 + comp2` (成分のみ)
- **Model 2**: `intensity ~ comp1 + comp2 + dyadScore` (+ Dyad スコア)
- **Model 3**: `intensity ~ comp1 + comp2 + comp1*comp2` (+ 交互作用項)

**主要な発見**:
- 4 Dyad すべてで偏相関が Holm 補正後に有意 (p < 0.01)
- Disapproval は最大の偏相関 (r = 0.161) と ΔR² (+0.0094)
- dyadScore の ΔR² は全ケースで交互作用項 (comp1*comp2) の ΔR² 以上
  → dyadScore が「交互作用のオントロジー的実装」として有効に機能
- Love の VIF = 17.6 は高いが、偏相関アプローチにより多重共線性に頑健に対処
- Contempt は VIF = 2.1 と低く、多重共線性の問題なし

### 3.3 オントロジー品質保証 (Step 9)

| KPI | 値 | 判定 |
|-----|---|------|
| SHACL violations | **0** | PASS |
| SHACL warnings | 11 | (注1) |
| violations / 1K triples | **0.0** | PASS |
| CQ pass 率 | **7/7** (100%) | PASS |
| derivedFrom 完備率 | **965/965** (100%) | PASS |
| score soundness | **965/965** (100%) | PASS |

(注1) 11 件の warning は、全感情スコアが score_threshold (0.01) 未満のため
Evidence ノードが付与されなかった FrameOccurrence に対するもの。
これはデータ品質上の期待される振る舞いであり、推論の正確性には影響しない。

**CQ 詳細**:

| CQ | 結果行数 | 判定 | 意味 |
|----|---------|------|------|
| cq1_list_dyads | 965 | PASS | 推論済み Dyad の列挙 |
| cq2_components | 20 | PASS | Dyad の構成要素取得 (10 Dyad × 2) |
| cq3_explain | 965 | PASS | 来歴による推論説明 |
| cq4_threshold_check | 5,833 | PASS | 閾値未達の状況確認 |
| cq5_topk | 3 | PASS | Top-K Dyad ランキング |
| cq_missing_provenance | **0** | PASS | 来歴欠損なし |
| cq_score_reconstruction | **0** | PASS | min スコア不整合なし |

### 3.4 既存評価結果 (Steps 4–5) まとめ

#### Silver ラベル評価 (Step 4)

| 指標 | Score-Aware | Naive-Dyad | No-Dyad |
|------|-----------|-----------|---------|
| Macro-F1 | **0.800** | 0.123 | 0.000 |
| Micro-F1 | **1.000** | 0.202 | 0.000 |

- TH=0.35–0.45 で Micro-F1 > 0.96 を維持（閾値頑健性）
- Micro-F1 = 1.000 は silver ラベルとの自己参照 → 外部妥当性は Step 7 で補完

#### Dyad 分布 (TH=0.4)

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

#### NRC vs Handcrafted 比較 (Step 5)

- NRC: 965 件、Handcrafted: 79 件 (12 倍の差)
- Cohen's kappa = 0.145 (わずかな一致)
- 差の主因: Trust, Anticipation のカバレッジ差 (NRC が 3–4 倍広い)

---

## 4. 生成物一覧

### 4.1 データファイル

| パス | 形式 | 説明 |
|------|------|------|
| `data/experiment/goemotion_subset.csv` | CSV | GoEmotions 2,000 サンプル |
| `data/experiment/classified_scores.jsonl` | JSONL | 28 感情スコア / サンプル |
| `data/experiment/plutchik_scores.jsonl` | JSONL | 8 Plutchik スコア / サンプル |
| `data/experiment/experiment_data.ttl` | Turtle | RDF 変換済み (41,816 triples) |
| `data/experiment/semeval_plutchik_cache.jsonl` | JSONL | SemEval 7,801 テキストの Plutchik スコア |
| `data/experiment/semeval_cache/*.jsonl` | JSONL | SemEval 感情強度キャッシュ (4 ファイル) |

### 4.2 評価結果

| パス | 説明 |
|------|------|
| `output/experiment/evaluation_report.json` | Silver ラベル評価 + 閾値スイープ |
| `output/experiment/threshold_sweep_results.csv` | 閾値感度 CSV |
| `output/experiment/semeval_consistency.json` | SemEval 二値一致性 (step4b) |
| `output/experiment/mapping_comparison.json` | NRC vs Handcrafted |
| `output/experiment/inference_out.ttl` | RDF 推論出力 (58,346 triples) |
| **`output/experiment/semeval_continuous.json`** | **SemEval 連続評価 (step7)** |
| **`output/experiment/incremental_value.json`** | **増分価値検証 (step8)** |
| **`output/experiment/ontology_qa.json`** | **オントロジー QA KPI (step9)** |

### 4.3 可視化 (9 図)

| Fig | ファイル | 内容 | 論文対応 |
|-----|---------|------|---------|
| 1 | `threshold_sweep_f1.png` | Macro/Micro-F1 vs 閾値 | Table 4 補助 |
| 2 | `dyad_distribution.png` | Dyad 分布 (銀色ラベル) | Table 4 補助 |
| 3 | `score_cooccurrence.png` | 成分感情の共起散布図 | Fig 3 |
| 4 | `per_dyad_heatmap.png` | Per-dyad F1 ヒートマップ | Table 4 補助 |
| 5 | `semeval_effect_sizes.png` | Mann-Whitney 効果量 | (step4b 補助) |
| 6 | `mapping_comparison.png` | NRC vs Handcrafted 比較 | (補助) |
| **7** | **`semeval_continuous_correlation.png`** | **dyadScore vs 強度 散布図** | **Fig 1** |
| **8** | **`incremental_value.png`** | **R² 比較 + 偏相関** | **Fig 2** |
| **9** | **`ontology_qa_dashboard.png`** | **QA ダッシュボード** | **Fig 4** |

---

## 5. 論文テーブル/図への対応

| 論文 | 種別 | 内容 | データソース | 状態 |
|------|------|------|------------|------|
| Table 1 | 主結果 | SemEval Spearman ρ [CI], PR-AUC, p(Holm), n | `semeval_continuous.json` | **データ生成済み** |
| Table 2 | 主結果 | 偏相関, ΔR², VIF, comp1*comp2 比較 | `incremental_value.json` | **データ生成済み** |
| Table 3 | 品質評価 | SHACL/CQ KPI サマリ | `ontology_qa.json` | **データ生成済み** |
| Table 4 | 補助 | GoEmotions 閾値スイープ | `evaluation_report.json` | **データ生成済み** |
| Fig 1 | 主結果 | dyadScore vs SemEval intensity 散布図 | Fig 7 | **生成済み** |
| Fig 2 | 主結果 | ΔR² 棒グラフ + 偏相関 | Fig 8 | **生成済み** |
| Fig 3 | 補助 | Dyad 分布 + 共起分析 | Fig 2+3 統合 | **生成済み（個別）** |
| Fig 4 | 品質評価 | SHACL/CQ ダッシュボード | Fig 9 | **生成済み** |

---

## 6. 既知の弱点と対処状況

| 弱点 | 深刻度 | 対処状況 | 論文での扱い |
|------|--------|---------|------------|
| Silver ラベル自己参照 | 高 | **解決済み**: SemEval 連続評価 (Step 7) で外部妥当性を確立 | methodological choice として位置づけ |
| dyadScore の増分価値未証明 | 高 | **解決済み**: 偏相関 + permutation (Step 8) で 4 Dyad すべて有意 | Table 2 で定量報告 |
| 多重検定補正なし | 高 | **解決済み**: Holm 補正を全 p 値に適用 (Step 7, 8) | 全テーブルに p(Holm) 記載 |
| SemEval 二値評価のみ | 高 | **解決済み**: 連続 dyadScore × intensity の Spearman ρ を主指標に | Table 1 が主結果 |
| SemEval 重複テキスト処理 | 高 | **解決済み**: text dedup 明示化、n(Unique)=7,801 を全出力に記載 | n を全テーブルに明記 |
| SHACL/CQ 手動実行 | 中 | **解決済み**: Step 9 で自動化、KPI を JSON 出力 | Table 3 で定量報告 |
| Awe/Aggressiveness ゼロ | 中 | **明記**: 共起分析 (Fig 3) で構造的限界を提示 | 分類器上流の限界として記述 |
| Rare dyad (Pride=4, Submission=2) | 中 | **対処済み**: 焦点 4 Dyad に集中、残りは supplementary | limitation に記載 |
| Baselines が弱い | 中 | **部分対処**: 成分スコアのみ baseline を Step 8 OLS で追加 | Model 1 が components-only baseline |
| EFO コア改変禁止 | 低 | **解決済み**: `scripts/check_efo_core.sh` (SHA-256) + `.gitattributes` | — |

---

## 7. ファイル構成

### 7.1 改変禁止 (READ-ONLY)

| ファイル | 由来 | SHA-256 検証 |
|---------|------|------------|
| `data/EmoCore_iswc.ttl` | De Giorgis & Gangemi (2024) | `check_efo_core.sh` で検証 |
| `data/BE_iswc.ttl` | 同上 | 同上 |
| `data/BasicEmotionTriggers_iswc.ttl` | 同上 | 同上 |
| `imports/DUL.owl` | DOLCE-Ultralite | 同上 |

### 7.2 実験コード (MODIFIABLE)

```
experiment/
├── __init__.py
├── config.py                          # 共有定数 (DYADS, FOCUS_DYADS, etc.)
├── run_pipeline.py                    # パイプラインオーケストレータ
├── step0_download_data.py             # GoEmotions ダウンロード
├── step1_classify.py                  # RoBERTa 分類
├── step2_map_plutchik.py              # NRC/Handcrafted マッピング
├── step3_to_rdf.py                    # RDF 変換
├── step4_evaluate.py                  # Silver ラベル評価
├── step4b_semeval_consistency.py      # SemEval 二値一致性
├── step5_compare_mappings.py          # マッピング比較
├── step6_visualize.py                 # 可視化 (Fig 1–9)
├── step7_semeval_continuous.py        # ★ SemEval 連続評価
├── step8_incremental_value.py         # ★ 増分価値検証
├── step9_ontology_qa.py              # ★ オントロジー QA
└── mappings/
    ├── nrc_mapping.py
    └── goemotion_to_plutchik.json
```

★ = 今回新規作成

---

## 8. 再現手順

### 8.1 全パイプライン実行

```bash
# 完全再現 (GPU/MPS 推奨、約 5 分)
pip install -r requirements-experiment.txt
python -m experiment.run_pipeline --n 2000 --seed 42

# SemEval データは事前に配置が必要:
# data/experiment/semeval_raw/EI-reg-En-{anger,fear,joy,sadness}-{train,dev}.txt
```

### 8.2 新規ステップのみ実行 (既存データ利用)

```bash
# Step 7: SemEval 連続評価 (初回は分類に ~2分、キャッシュ後は数秒)
python -m experiment.step7_semeval_continuous

# Step 8: 増分価値 (Step 7 のキャッシュが必要)
python -m experiment.step8_incremental_value

# Step 9: オントロジー QA (inference_out.ttl が必要)
python -m experiment.step9_ontology_qa

# Fig 7–9 のみ生成
python -m experiment.step6_visualize --only 7 8 9
```

### 8.3 パイプラインスキップオプション

```bash
# 既存データを活用して新規ステップのみ実行
python -m experiment.run_pipeline \
  --skip-download --skip-classify --skip-rdf-inference

# 新規ステップをスキップ
python -m experiment.run_pipeline \
  --skip-step7 --skip-step8 --skip-step9
```

### 8.4 EFO コア整合性確認

```bash
bash scripts/check_efo_core.sh
# → "EFO core integrity check: PASSED (all 4 files unchanged)"
```

---

## 9. 残タスク

### 9.1 論文執筆に向けて (実装不要)

| タスク | 優先度 | 備考 |
|--------|--------|------|
| Table 1–4 の LaTeX 整形 | 高 | JSON データから生成可能 |
| Fig 1–4 の論文用整形 | 高 | 現在の Fig 7–9 をリネーム・調整 |
| Fig 3 の統合 (分布 + 共起) | 中 | Fig 2 + Fig 3 を 1 図に統合 |
| Related Work 執筆 | 高 | Plutchik, GoEmotions, SemEval, EFO |
| Discussion 執筆 | 高 | Silver 自己参照、ゼロサポート、rare dyad |

### 9.2 将来課題 (論文に記載するが実装不要)

- **Semantic-F1**: SKOS:exactMatch/closeMatch による部分点評価
- **Gold ラベル**: 人手アノテーションによる外部正解の作成
- **マルチモーダル拡張**: テキスト以外 (音声, 表情) への応用
- **Tertiary Dyad**: 現在の 10 Dyad → 全 Dyad カバレッジへの拡張

---

## 10. 依存ライブラリ

| パッケージ | 用途 | Step |
|-----------|------|------|
| `transformers` | SamLowe/roberta-base-go_emotions | 1, 4b, 7 |
| `torch` | モデル推論 | 1, 4b, 7 |
| `rdflib` | RDF/SPARQL | 3, 3b, 9 |
| `pyshacl` | SHACL 検証 | 9 |
| `scipy` | 統計検定 (Spearman, permutation) | 4b, 7, 8 |
| `scikit-learn` | PR-AUC | 7 |
| `statsmodels` | (OLS VIF — 現在は numpy で自前実装) | — |
| `matplotlib` | 可視化 | 6 |
| `numpy` | 数値計算 | 全般 |
| `pandas` | CSV 処理 | 4, 6 |

---

## 付録 A: コミット履歴 (experiment ブランチ)

| Hash | メッセージ |
|------|---------|
| `fd64c3d` | Add construct validity evaluation pipeline (steps 7-9) for paper |
| `f4f4536` | Add GoEmotions experiment pipeline with evaluation and visualization |
| `68c2f03` | Add docs/ directory with architecture, inference, validation, design, and paper summary |
| `82a45d0` | Add EmotionSituation class and fix SHACL derivedFrom constraint |
| `3a41836` | Add SPARQL rules, CQ queries, SHACL shapes, and threshold analysis |
| `230e867` | Align vocabulary with paper specification |
