# 集約関数・閾値の最適化実験計画

## Context

### 問題提起

現在の Dyad 推論は `dyadScore = min(comp1, comp2)` + 固定閾値 TH=0.4 を使用しているが、以下の問題がある：

1. **min() の情報損失**: min(0.8, 0.4) = min(0.4, 0.4) = 0.4 → 強い方の成分を完全に無視
2. **ΔR² が小さい** (最大 0.0094): min() が成分の決定的関数のため、独立した説明力が乏しい
3. **VIF が高い** (Love で 17.6): 多重共線性が深刻
4. **固定閾値の非最適性**: Love の平均 dyadScore=0.27 vs Contempt=0.016 — 1 つの閾値で全 Dyad を扱えない
5. **Silver-F1 の自己参照**: TH=0.4 で Micro-F1=1.0 は定義上の帰結であり、閾値の妥当性を示さない

### 目的

- 複数の集約関数と閾値戦略を**体系的に比較**
- **SemEval Spearman ρ（外部妥当性）** を主指標として最適手法を特定
- 論文の Discussion / Ablation Study として報告可能なデータを生成

---

## 実装計画

### 新規ファイル: `experiment/step10_aggregation_study.py`

SemEval データ（`semeval_plutchik_cache.jsonl` + `semeval_cache/*.jsonl`）を使い、
各集約関数 × 閾値の組み合わせで Spearman ρ を算出する。

#### 比較する集約関数 (7 種)

| # | 名称 | 数式 | 理論的根拠 |
|---|------|------|----------|
| 1 | **Min** (現行) | `min(a, b)` | Gödel t-norm。弱い方の感情が Dyad の強さを決定 |
| 2 | **Product** | `a * b` | 独立事象の同時確率。Bayesian 分類器結合で使用実績 |
| 3 | **Geometric Mean** | `sqrt(a * b)` | 両成分をバランスよく考慮。分類器アンサンブルで使用実績 |
| 4 | **Harmonic Mean** | `2ab / (a + b)` | F1 スコアと同じ構造。不均衡を強くペナルティ |
| 5 | **Łukasiewicz** | `max(0, a + b - 1)` | 閾値が暗黙的に内蔵。合計が 1 を超えないと 0 |
| 6 | **Power Mean (p=-2)** | `((a^p + b^p) / 2)^(1/p)` | min と harmonic mean の中間。パラメトリックに調整可能 |
| 7 | **OWA (w=0.3/0.7)** | `0.3*max(a,b) + 0.7*min(a,b)` | 感情分析で使用実績あり (Cogn. Comput., 2021) |

#### 閾値戦略 (3 種)

| # | 名称 | 方法 |
|---|------|------|
| A | **固定閾値** | TH ∈ {0.0, 0.2, 0.3, 0.4, 0.5} でスイープ |
| B | **閾値なし** | 全サンプルで連続スコアを算出 (TH=0.0 と同等) |
| C | **Łukasiewicz 暗黙閾値** | 集約関数 #5 のみ。TH 不要 |

**注**: Spearman ρ は連続値同士の相関なので、主評価は**閾値なし (B)** で行う。
閾値スイープ (A) は PR-AUC の補助評価に使用。

#### 評価指標

焦点 4 Dyad (Love, Disapproval, Optimism, Contempt) × 各手法で：

- **主指標**: Spearman ρ (dyadScore vs SemEval intensity) — 閾値なし
- **補助**: PR-AUC (t=0.5) — 閾値なし時の dyadScore をスコアとして使用
- **補助**: 偏相関 (comp1, comp2 制御) — 増分価値
- **参考**: dyadScore の平均・標準偏差・ゼロ率

#### 処理フロー

1. `semeval_plutchik_cache.jsonl` から Plutchik スコアを読み込み（既存キャッシュ再利用）
2. `semeval_cache/*.jsonl` から SemEval intensity を読み込み
3. 7 つの集約関数それぞれで全サンプルの dyadScore を算出
4. 焦点 4 Dyad × 7 関数 = 28 ペアで Spearman ρ + Bootstrap CI を算出
5. Holm 補正を全 p 値に適用
6. 偏相関を 7 関数それぞれで算出（comp1, comp2 制御）
7. 結果を JSON + サマリテーブルとして出力

#### 再利用コード

- `step7_semeval_continuous.py`: `_bootstrap_spearman_ci()`, `_holm_correction()`
- `step8_incremental_value.py`: `_partial_corr()`
- `experiment/config.py`: `DYADS`, `FOCUS_DYADS`, `DYAD_CONSISTENCY_MAP`

#### 出力

- `output/experiment/aggregation_study.json`

### 可視化追加: `experiment/step6_visualize.py` に Fig 10 追加

#### Fig 10: `aggregation_comparison.png`

- 左パネル: 7 集約関数 × 4 Dyad の Spearman ρ ヒートマップ
- 右パネル: 最良手法 vs min() の散布図比較 (2 パネル)

### パイプライン統合: `experiment/run_pipeline.py`

- `--skip-step10` フラグ追加
- Step 7 のキャッシュに依存

---

## 実装手順

1. **ドキュメント保存**: この計画を `docs/aggregation-study-plan.md` として保存
2. **Step 10 実装**: `experiment/step10_aggregation_study.py` を新規作成
3. **可視化追加**: `experiment/step6_visualize.py` に Fig 10 追加
4. **パイプライン統合**: `experiment/run_pipeline.py` に Step 10 統合
5. **実行・検証**: Step 10 を実行し結果を確認
6. **ドキュメント更新**: `docs/current-status.md` に結果を反映

---

## 修正ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `docs/aggregation-study-plan.md` | **新規作成** — 本計画のドキュメント化 |
| `experiment/step10_aggregation_study.py` | **新規作成** |
| `experiment/step6_visualize.py` | Fig 10 追加 |
| `experiment/run_pipeline.py` | Step 10 統合 + `--skip-step10` |
| `docs/current-status.md` | 結果反映 |

---

## 検証手順

```bash
# 1. Step 10 実行（既存キャッシュ使用、数秒で完了）
python -m experiment.step10_aggregation_study

# 2. 結果確認: 各集約関数の Spearman ρ 比較テーブルが出力されること
#    → min() より高い ρ を示す関数があるか確認

# 3. Fig 10 生成
python -m experiment.step6_visualize --only 10

# 4. パイプライン統合テスト
python -m experiment.run_pipeline --skip-download --skip-classify --skip-rdf-inference --skip-semeval --skip-step8 --skip-step9
```

## 事前仮説

- **Geometric Mean** と **Harmonic Mean** は min() より高い ρ を示す可能性が高い（両成分を考慮するため）
- **Product** は min() より低い ρ になる可能性がある（スコアが圧縮されすぎる）
- **Łukasiewicz** はゼロが多すぎて ρ が低下する可能性がある
- **いずれの関数でも ΔR²（増分価値）は小さいまま**の可能性が高い（成分の決定的関数である限り本質的制約）
- 結果に関わらず、「複数の集約関数を比較し、min() の選択を実験的に検証した」こと自体が論文の Ablation Study として価値がある

---

## 実験結果

> **実行日**: 2026-02-16 | **データ**: SemEval-2018 EI-reg (n=7,801 unique texts)
> **統計**: Holm 補正 (28 検定)、Bootstrap 95% CI (n=2,000)

### 主指標: Spearman ρ 比較行列

| 集約関数 | Love | Disapproval | Optimism | Contempt | **Mean** |
|---------|------|------------|---------|---------|----------|
| **Min (baseline)** | +0.349 | **+0.636** | +0.165 | +0.509 | +0.415 |
| Product | +0.475 | +0.613 | +0.394 | +0.573 | +0.514 |
| Geometric Mean | +0.475 | +0.613 | +0.394 | +0.573 | +0.514 |
| Harmonic Mean | +0.402 | +0.638 | +0.226 | +0.539 | +0.451 |
| Łukasiewicz | +0.322 | +0.279 | +0.152 | +0.065 | +0.204 |
| Power Mean (p=-2) | +0.378 | **+0.639** | +0.188 | +0.520 | +0.431 |
| **OWA (0.3/0.7)** | **+0.504** | +0.584 | **+0.519** | +0.566 | **+0.544** |

全 28 検定で Holm 補正後 p < 0.01（Łukasiewicz/Contempt の p=0.003 を含む）。

### Dyad 別最良手法

| Dyad | 最良手法 | ρ (最良) | 95% CI | ρ (min) | Δρ |
|------|---------|---------|--------|---------|-----|
| Love | OWA (0.3/0.7) | +0.504 | [+0.470, +0.537] | +0.349 | **+0.155** |
| Disapproval | Power Mean (p=-2) | +0.639 | [+0.611, +0.664] | +0.636 | +0.003 |
| Optimism | OWA (0.3/0.7) | +0.519 | [+0.484, +0.553] | +0.165 | **+0.355** |
| Contempt | Product | +0.573 | [+0.543, +0.604] | +0.509 | **+0.064** |

### 補助指標: PR-AUC (t=0.5)

| 集約関数 | Love | Disapproval | Optimism | Contempt |
|---------|------|------------|---------|---------|
| Min | 0.654 | 0.775 | 0.551 | 0.692 |
| Product | 0.686 | **0.782** | 0.614 | **0.728** |
| Geometric Mean | 0.686 | **0.782** | 0.614 | **0.728** |
| Harmonic Mean | 0.667 | **0.783** | 0.568 | 0.709 |
| Łukasiewicz | 0.593 | 0.534 | 0.501 | 0.457 |
| Power Mean (p=-2) | 0.661 | 0.780 | 0.559 | 0.700 |
| **OWA (0.3/0.7)** | **0.696** | 0.773 | **0.667** | 0.725 |

### 補助指標: 偏相関 (comp1, comp2 制御)

| 集約関数 | Love | Disapproval | Optimism | Contempt |
|---------|------|------------|---------|---------|
| Min | +0.065 | **+0.161** | +0.085 | +0.075 |
| Product | +0.121 | +0.017 | **+0.125** | −0.099 |
| Geometric Mean | +0.121 | +0.017 | **+0.125** | −0.099 |
| Harmonic Mean | +0.101 | +0.147 | +0.104 | **+0.100** |
| Łukasiewicz | −0.087 | +0.003 | −0.030 | −0.003 |
| Power Mean (p=-2) | +0.088 | +0.156 | +0.095 | +0.099 |
| OWA (0.3/0.7) | +0.026 | −0.111 | +0.109 | −0.119 |

偏相関は全関数で |r| < 0.17 — 成分の決定的関数である限り増分価値は本質的に小さい。

### 記述統計: ゼロ率

| 集約関数 | Love | Disapproval | Optimism | Contempt |
|---------|------|------------|---------|---------|
| Min | 0.0% | 0.0% | 0.0% | 0.0% |
| Product | 0.0% | 0.0% | 0.0% | 0.0% |
| Geometric Mean | 0.0% | 0.0% | 0.0% | 0.0% |
| Harmonic Mean | 0.0% | 0.0% | 0.0% | 0.0% |
| **Łukasiewicz** | **74.9%** | **91.2%** | **90.3%** | **99.6%** |
| Power Mean (p=-2) | 0.0% | 0.0% | 0.0% | 0.0% |
| OWA (0.3/0.7) | 0.0% | 0.0% | 0.0% | 0.0% |

---

## 仮説の検証

| # | 仮説 | 結果 | 判定 |
|---|------|------|------|
| 1 | Geometric Mean と Harmonic Mean は min() より高い ρ | Geometric Mean: +0.514 > +0.415、Harmonic Mean: +0.451 > +0.415 | **支持** |
| 2 | Product は min() より低い ρ | Product: +0.514 > +0.415（min() より高い） | **棄却** |
| 3 | Łukasiewicz はゼロが多すぎて ρ が低下 | ゼロ率 75–99%、Mean ρ = +0.204（最低） | **支持** |
| 4 | いずれの関数でも ΔR² は小さいまま | 全関数で偏相関 |r| < 0.17 | **支持** |

**想定外の発見**:
- OWA (0.3/0.7) が全体最良 (Mean ρ = +0.544) — 事前仮説では言及せず
- Product と Geometric Mean の Spearman ρ が完全一致 — 単調変換 (sqrt) は順位を保存するため
- Optimism での改善幅が突出 (Δρ = +0.355) — Joy が SemEval の正解と直接対応し、min() では弱い Anticipation に引きずられる

---

## 考察

### OWA が最良だった理由

OWA (0.3/0.7) は `0.3 × max(comp1, comp2) + 0.7 × min(comp1, comp2)` であり、
弱い方の成分を重視しつつ（70%）、強い方の情報も一部保持する（30%）。

min() が完全に強い方を捨てるのに対し、OWA は「弱い環がチェーンの強さを決める」
という直感を維持しながら情報損失を緩和する。これは特に、2 成分の SemEval 対応感情が
非対称な Dyad（Love: Joy ↔ joy、Optimism: Joy ↔ joy）で効果的だった。

### Disapproval で min() が堅調な理由

Disapproval = Surprise + Sadness で、SemEval の対応感情は sadness。
Sadness は 2 成分のうちの片方であり、min() は「Sadness が弱ければ低く、
Sadness が強くても Surprise が弱ければ低く」なるため、sadness 強度との相関が
他の関数と同程度に保たれる。成分間の非対称性が小さいことが min() の堅調さの要因。

### Product = Geometric Mean の理由

`geometric_mean(a, b) = sqrt(a × b) = sqrt(product(a, b))`

Spearman ρ は順位相関であり、sqrt() は単調増加変換なので順位を変えない。
したがって Spearman ρ は数学的に一致する。PR-AUC も同様に閾値の順序のみに依存するため一致。
ただし偏相関も一致したのは、rank-based 実装のため。

### 論文での活用方針

1. **Ablation Study** (Discussion セクション): min() を含む 7 関数の比較行列を Table 5 として提示
2. **理論 vs 実験のトレードオフ**: min() は Gödel t-norm（ファジィ論理の標準的結合子）としての
   理論的根拠を持つが、OWA はデータ駆動では +0.13 の改善を示す。
   「理論的一貫性を維持しつつ、代替関数の検討余地がある」と balanced に議論
3. **Łukasiewicz の教訓**: 暗黙的閾値が過度に保守的であることを定量的に示し、
   明示的閾値 + 連続集約が望ましいことを根拠づける
4. **将来課題**: OWA の重みパラメータ (0.3/0.7) の最適化、Dyad ごとの適応的集約関数選択

---

## 生成物

| パス | 説明 |
|------|------|
| `output/experiment/aggregation_study.json` | 全結果 (7 関数 × 4 Dyad の詳細指標) |
| `output/experiment/figures/aggregation_comparison.png` | Fig 10: ヒートマップ + 散布図 |
| `docs/current-status.md` セクション 3.4 | 結果サマリ（現状報告書に統合） |
