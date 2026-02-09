# 推論パイプライン

本ドキュメントでは、Plutchik Dyad 推論の min-threshold アルゴリズム、SPARQL CONSTRUCT ルール、テストデータの設計意図、および閾値感度分析について記述する。

---

## 1. min-threshold アルゴリズム

### 1.1 概要

各 `fschema:FrameOccurrence`（感情状況）に付与された基本感情の Evidence スコアから、Plutchik の感情の輪に基づく複合感情 (Dyad) を推論する。集約関数として **min** を採用し、閾値 (threshold) によるフィルタリングを行う。

### 1.2 アルゴリズムの手順

```
入力:
  - FrameOccurrence のリスト
  - 各 FrameOccurrence に紐づく Evidence (emotion, score)
  - 閾値 TH (デフォルト: 0.4)

処理:
  FOR EACH FrameOccurrence fo:
    evidence_map ← {emotion_name: max_score} を fo の Evidence から構築
    FOR EACH Dyad d = (e1, e2):
      IF e1 ∈ evidence_map AND e2 ∈ evidence_map:
        score1 ← evidence_map[e1]
        score2 ← evidence_map[e2]
        IF score1 >= TH AND score2 >= TH:
          dyadScore ← min(score1, score2)
          → DyadEvidence ノードを生成

出力:
  - pl:satisfies トリプル (FrameOccurrence → Dyad)
  - DyadEvidence ノード (score, derivedFrom, method)
```

### 1.3 DyadEvidence の出力構造

推論によって生成される DyadEvidence ノードは以下の構造を持つ:

```turtle
_:dyadEv a pl:DyadEvidence ;
    pl:emotion pl:Love ;                 # 推論された Dyad
    pl:score "0.70"^^xsd:decimal ;       # min(score1, score2)
    pl:derivedFrom ex:s1_ev_joy ;        # 元の Evidence 1
    pl:derivedFrom ex:s1_ev_trust ;      # 元の Evidence 2
    pl:method "min-threshold" .          # 推論手法
```

加えて、FrameOccurrence に以下のトリプルが追加される:

```turtle
ex:s1 pl:satisfies pl:Love .            # 推論結果
ex:s1 pl:hasEvidence _:dyadEv .         # DyadEvidence へのリンク
```

---

## 2. 実行方法

### 2.1 基本実行

```bash
# デフォルト閾値 (0.4) で推論
python scripts/run_inference.py --out output/out.ttl

# カスタム閾値で推論
python scripts/run_inference.py --th 0.5 --out output/out.ttl
```

### 2.2 コマンドラインオプション

| オプション | デフォルト | 説明 |
|-----------|----------|------|
| `--th` | `0.4` | 推論閾値 (両成分スコアがこの値以上で推論実行) |
| `--out` | `output/out.ttl` | 出力ファイルパス |

### 2.3 ロードされるファイル

スクリプトは以下のファイルを自動ロードする:

| ファイル | 必須 | 説明 |
|---------|------|------|
| `data/EmoCore_iswc.ttl` | Yes | EmoCore モジュール |
| `modules/EFO-PlutchikDyad.ttl` | Yes | PlutchikDyad モジュール |
| `data/sample.ttl` | Yes | テストデータ |
| `data/BE_iswc.ttl` | No | Basic Emotions (あれば読み込み) |
| `data/BasicEmotionTriggers_iswc.ttl` | No | トリガーパターン (あれば読み込み) |

### 2.4 セルフテスト

推論実行後、期待結果との自動照合が行われる。6 つの状況すべてで期待結果と一致すれば `All tests PASSED!` と表示される。

---

## 3. SPARQL CONSTRUCT ルール

`sparql/dyad_rules/` に、Python 推論と等価な SPARQL CONSTRUCT ルールが 10 本格納されている。各ルールは 1 つの Dyad に対応する。

### 3.1 ルール一覧

| ファイル | Dyad | 構成要素 | タイプ |
|---------|------|---------|--------|
| `01_love.rq` | Love | Joy + Trust | Primary |
| `02_submission.rq` | Submission | Trust + Fear | Primary |
| `03_awe.rq` | Awe | Fear + Surprise | Primary |
| `04_disapproval.rq` | Disapproval | Surprise + Sadness | Primary |
| `05_remorse.rq` | Remorse | Sadness + Disgust | Primary |
| `06_contempt.rq` | Contempt | Disgust + Anger | Primary |
| `07_aggressiveness.rq` | Aggressiveness | Anger + Anticipation | Primary |
| `08_optimism.rq` | Optimism | Anticipation + Joy | Primary |
| `09_hope.rq` | Hope | Anticipation + Trust | Secondary |
| `10_pride.rq` | Pride | Anger + Joy | Secondary |

### 3.2 ルールの共通構造

各ルールは以下の共通パターンを持つ:

```sparql
CONSTRUCT {
    ?s pl:satisfies pl:<Dyad> .
    ?s pl:hasEvidence ?evDy .
    ?evDy a pl:DyadEvidence ;
        pl:emotion pl:<Dyad> ;
        pl:score ?minScore ;
        pl:method "min-threshold" ;
        pl:derivedFrom ?ev1, ?ev2 .
}
WHERE {
    ?s a fschema:FrameOccurrence ;
        pl:hasEvidence ?ev1, ?ev2 .
    ?ev1 pl:emotion pl:<Component1> ; pl:score ?a .
    ?ev2 pl:emotion pl:<Component2> ; pl:score ?b .
    FILTER (?a >= 0.4 && ?b >= 0.4)
    BIND (IF(?a <= ?b, ?a, ?b) AS ?minScore)
    BIND (BNODE() AS ?evDy)
}
```

ルール内の閾値は `0.4` にハードコードされている。異なる閾値で実験する場合は Python スクリプト (`run_inference.py --th`) を使用する。

---

## 4. テストデータの設計意図

`data/sample.ttl` には 6 つの FrameOccurrence が定義されている。各状況は推論パイプラインの異なる側面をテストする。

| 状況 | Evidence | 期待 Dyad | Score | テスト観点 |
|------|----------|----------|-------|-----------|
| `ex:s1` | Joy=0.80, Trust=0.70 | Love | 0.70 | 標準ケース: 両スコアが閾値を十分上回る |
| `ex:s2` | Disgust=0.60, Anger=0.60 | Contempt | 0.60 | 等スコアケース: min で同値 |
| `ex:s3` | Anger=0.90, Anticipation=0.50 | Aggressiveness | 0.50 | 非対称ケース: スコア差が大きい |
| `ex:s4` | Surprise=0.60, Sadness=0.45 | Disapproval | 0.45 | 閾値近傍: 片方が閾値にわずかに上回る |
| `ex:s5` | Anticipation=0.42, Trust=0.41 | Hope | 0.41 | 境界ケース: 両方が閾値ぎりぎり (Secondary Dyad) |
| `ex:s6` | Fear=0.39, Surprise=0.80 | (なし) | - | 閾値不達: Fear が TH=0.4 未満で Awe 不成立 |

### 設計方針

- **Primary Dyad と Secondary Dyad の両方**をカバー (s1-s4: Primary, s5: Secondary)
- **境界条件**のテスト (s5: ぎりぎり成立、s6: ぎりぎり不成立)
- 各状況は 1 つの Dyad のみを検証し、テストの独立性を確保

---

## 5. 閾値感度分析

### 5.1 実行方法

```bash
# 基本実行 (TH=0.3, 0.4, 0.5, 0.6)
python scripts/threshold_sweep.py

# 詳細表示
python scripts/threshold_sweep.py --detailed

# CSV 出力
python scripts/threshold_sweep.py --csv output/threshold_sensitivity.csv

# カスタム閾値
python scripts/threshold_sweep.py --thresholds 0.2,0.3,0.4,0.5,0.6,0.7
```

### 5.2 コマンドラインオプション

| オプション | デフォルト | 説明 |
|-----------|----------|------|
| `--data` | `data/sample.ttl` | データファイルパス |
| `--thresholds` | `0.3,0.4,0.5,0.6` | カンマ区切りの閾値リスト |
| `--detailed` | (off) | 状況ごとの詳細ブレークダウンを表示 |
| `--csv` | (なし) | CSV ファイルへのエクスポートパス |

### 5.3 結果テーブル (Table III 形式)

論文 Section VII (E2) に対応する閾値感度分析の結果:

| TH | Sit. w/ >=1 dyad | Mean dyads/sit. | Mean dyadScore |
|----|-------------------|-----------------|----------------|
| 0.3 | 6/6 (100.0%) | 1.000 | 0.508 |
| 0.4 | 5/6 (83.3%) | 0.833 | 0.532 |
| 0.5 | 3/6 (50.0%) | 0.500 | 0.600 |
| 0.6 | 2/6 (33.3%) | 0.333 | 0.650 |

### 5.4 結果の解釈

- **TH=0.3**: 全状況で Dyad が推論される。s6 の Fear=0.39 も閾値を超えるため Awe が成立する。
- **TH=0.4** (デフォルト): s6 のみ不成立。5/6 状況で推論成功。
- **TH=0.5**: s4 (Sadness=0.45) と s5 (Trust=0.41, Anticipation=0.42) も不成立となる。
- **TH=0.6**: s3 (Anticipation=0.50) も不成立。高スコアの s1, s2 のみ残る。

閾値を上げるほど推論数は減少するが、平均 dyadScore は上昇する（低スコアの推論がフィルタリングされるため）。TH=0.4 は精度と網羅性のバランスが取れた選択である。
