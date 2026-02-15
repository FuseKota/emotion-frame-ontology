# 検証とコンピテンシー質問

> **作成日**: 2026-02-09 | **最終更新日**: 2026-02-09

本ドキュメントでは、SHACL シェイプによる構造検証、CQ (Competency Question) クエリによる意味的検証、および品質チェッククエリについて記述する。

---

## 1. SHACL シェイプ定義

`shacl/plutchik-dyad-shapes.ttl` に 6 つのシェイプが定義されている。論文 Appendix E に対応する。

### 1.1 シェイプ一覧

| # | シェイプ名 | ターゲット | 重大度 | 説明 |
|---|----------|----------|--------|------|
| 1 | `pl:EvidenceShape` | `pl:Evidence` | Violation | Evidence の基本構造を検証 |
| 2 | `pl:DyadEvidenceShape` | `pl:DyadEvidence` | Violation/Warning | DyadEvidence の構造と由来を検証 |
| 3 | `pl:FrameOccurrenceWithEvidenceShape` | `fschema:FrameOccurrence` | Warning | FrameOccurrence が Evidence を持つことを検証 |
| 4 | `pl:ScoreRangeShape` | `pl:score` の主語 | Violation | スコア値の範囲 [0,1] を検証 |
| 5 | `pl:SatisfiesShape` | `pl:satisfies` の主語 | Violation | satisfies リンクのターゲットが IRI であることを検証 |
| 6 | `pl:BasicEmotionEvidenceShape` | Evidence かつ非 DyadEvidence | Warning | 基本感情の Evidence が derivedFrom を持たないことを検証 |

### 1.2 各シェイプの詳細

#### Shape 1: EvidenceShape

`pl:Evidence` インスタンスに対して以下を検証:

- `pl:emotion` を正確に 1 つ持つこと (IRI)
- `pl:score` を正確に 1 つ持つこと (`xsd:decimal`, 範囲 [0, 1])

#### Shape 2: DyadEvidenceShape

`pl:DyadEvidence` インスタンスに対して以下を検証:

- `pl:emotion` を正確に 1 つ持つこと (IRI) — **Violation**
- `pl:score` を正確に 1 つ持つこと (`xsd:decimal`, 範囲 [0, 1]) — **Violation**
- `pl:derivedFrom` を正確に 2 つ持つこと (各リンク先が `pl:Evidence` クラス) — **Violation**
- `pl:method` を正確に 1 つ持つこと (`xsd:string`) — **Warning**

`pl:method` は Warning レベルである。これは、method 注釈が推論の正当性には必須ではないが、メタデータとして推奨されるためである。

#### Shape 3: FrameOccurrenceWithEvidenceShape

`fschema:FrameOccurrence` インスタンスに対して以下を検証:

- `pl:hasEvidence` を少なくとも 1 つ持つこと — **Warning**

Warning レベルである理由は、Evidence なしの FrameOccurrence も概念的には有効（まだ分析されていない状況）であるため。

#### Shape 4: ScoreRangeShape

`pl:score` プロパティを持つすべてのノードに対して以下を検証:

- `pl:score` の値が `xsd:decimal` 型であること
- 値が 0 以上 1 以下であること

#### Shape 5: SatisfiesShape

`pl:satisfies` プロパティを持つすべてのノードに対して以下を検証:

- `pl:satisfies` のターゲットが IRI であること

#### Shape 6: BasicEmotionEvidenceShape

SPARQL ターゲットを使用して「`pl:Evidence` であるが `pl:DyadEvidence` ではない」ノードを選択し、以下を検証:

- `pl:derivedFrom` を持たないこと (maxCount = 0) — **Warning**

基本感情の Evidence は他の Evidence から派生しないため、derivedFrom が存在すれば構造上の異常を示す。

---

## 2. SHACL 検証の実行

### 2.1 基本実行

```bash
# 推論出力を含めて検証 (推奨)
python scripts/validate_shacl.py

# カスタムデータファイルを指定
python scripts/validate_shacl.py --data output/out.ttl

# カスタムシェイプファイルを指定
python scripts/validate_shacl.py --shapes shacl/plutchik-dyad-shapes.ttl

# RDFS 推論を有効にして検証
python scripts/validate_shacl.py --inference

# 検証レポートをファイルに出力
python scripts/validate_shacl.py --output output/validation_report.ttl
```

### 2.2 コマンドラインオプション

| オプション | デフォルト | 説明 |
|-----------|----------|------|
| `--data` | `data/sample.ttl` | データファイルパス |
| `--shapes` | `shacl/plutchik-dyad-shapes.ttl` | SHACL シェイプファイルパス |
| `--inference` | (off) | RDFS 推論を有効化 |
| `--output` | (なし) | 検証レポートの出力先 |

### 2.3 データロード順序

検証スクリプトは以下の順序でデータをロードする:

1. `modules/EFO-PlutchikDyad.ttl` (オントロジー定義)
2. 指定データファイル (デフォルト: `data/sample.ttl`)
3. `output/out.ttl` (推論出力、存在する場合)

推論出力を含めることで、DyadEvidence の構造検証も実行される。

### 2.4 終了コード

| コード | 意味 |
|-------|------|
| 0 | 検証成功 (conforms) |
| 1 | 検証失敗 (violations あり) |
| 2 | ファイル未検出エラー |
| 3 | その他のエラー |

---

## 3. CQ クエリ一覧

`sparql/cq/` に 7 つのコンピテンシー質問クエリが格納されている。

### 3.1 クエリ一覧

| # | ファイル | 目的 | 期待結果 |
|---|---------|------|---------|
| CQ1 | `cq1_list_dyads.rq` | 推論された Dyad とスコアの一覧 | 5 行 (s1-s5 の各 Dyad と score) |
| CQ2 | `cq2_components.rq` | Dyad の構成要素を OWL restriction から取得 | 10 行 (10 Dyad × 各 2 成分) |
| CQ3 | `cq3_explain.rq` | 推論の説明: derivedFrom 経由で元 Evidence を追跡 | 5 行 (各 DyadEvidence の由来) |
| CQ4 | `cq4_threshold_check.rq` | Dyad 未推論の状況とその Evidence | s6 の Fear, Surprise が返る |
| CQ5 | `cq5_topk.rq` | Top-K Dyad (スコア降順、K=3) | 上位 3 件の Dyad |
| QC1 | `cq_missing_provenance.rq` | 由来リンクのない DyadEvidence を検出 | 空 (問題なし) |
| QC2 | `cq_score_reconstruction.rq` | dyadScore = min(score1, score2) を検証 | 空 (不一致なし) |

### 3.2 各クエリの詳細

#### CQ1: 推論された Dyad の一覧 (`cq1_list_dyads.rq`)

各状況について推論された Dyad とその dyadScore を返す。

```
結果列: ?situation, ?dyad, ?score
ソート: ?situation, ?dyad
```

`pl:satisfies` と `pl:hasEvidence` の両方を辿ることで、satisfies リンクと DyadEvidence が整合していることを暗黙的に検証する。

#### CQ2: Dyad の構成要素 (`cq2_components.rq`)

OWL の `equivalentClass` → `intersectionOf` → `someValuesFrom` パスを辿り、各 Dyad の構成基本感情を取得する。

```
結果列: ?dyad, ?dyadLabel, ?component1, ?component2
ソート: ?dyadLabel
フィルタ: component1 < component2 (重複排除)
```

#### CQ3: 推論の説明 (`cq3_explain.rq`)

DyadEvidence の `derivedFrom` リンクを追跡し、元の Evidence のスコアとともに推論の根拠を提示する。

```
結果列: ?situation, ?dyad, ?dyadScore, ?emotion1, ?score1, ?emotion2, ?score2
ソート: ?situation
フィルタ: ev1 != ev2 かつ emotion1 < emotion2 (重複排除)
```

#### CQ4: 閾値チェック (`cq4_threshold_check.rq`)

基本感情の Evidence を持つが Dyad が推論されなかった状況を返す。閾値の効果を確認するためのクエリ。

```
結果列: ?situation, ?label, ?emotion, ?score
ソート: ?situation, ?emotion
```

デフォルト閾値 (TH=0.4) では s6 が返る。

#### CQ5: Top-K Dyad (`cq5_topk.rq`)

スコア降順で上位 K 件の DyadEvidence を返す（例: K=3）。

```
結果列: ?situation, ?dyad, ?score
ソート: ?situation, DESC(?score)
制限: LIMIT 3
```

---

## 4. 品質チェッククエリ

### 4.1 由来リンクの欠損検出 (`cq_missing_provenance.rq`)

DyadEvidence で `pl:derivedFrom` リンクを持たないノードを検出する。正常な推論結果では空の結果セットが返る。

```sparql
SELECT ?dev WHERE {
    ?dev a pl:DyadEvidence .
    FILTER NOT EXISTS { ?dev pl:derivedFrom ?x . }
}
```

**期待結果**: 空 (0 行)。非空の場合、推論パイプラインに問題がある。

### 4.2 スコア再構成の検証 (`cq_score_reconstruction.rq`)

各 DyadEvidence の `pl:score` が、`derivedFrom` で参照される 2 つの Evidence の `min(score1, score2)` と一致するかを検証する。不一致のみを返す。

```sparql
SELECT ?dev ?dyad ?dyadScore ?score1 ?score2 ?computedMin WHERE {
    ?dev a pl:DyadEvidence ;
        pl:emotion ?dyad ;
        pl:score ?dyadScore ;
        pl:derivedFrom ?e1, ?e2 .
    ?e1 pl:score ?score1 .
    ?e2 pl:score ?score2 .
    FILTER (?e1 != ?e2)
    BIND (IF(?score1 <= ?score2, ?score1, ?score2) AS ?computedMin)
    FILTER (?dyadScore != ?computedMin)
}
```

**期待結果**: 空 (0 行)。非空の場合、スコア計算に不整合がある。
