# 設計判断の記録

本ドキュメントでは、EFO-PlutchikDyad 再現プロジェクトにおける主要な設計判断とその根拠を記録する。

---

## 1. 論文との対応関係

### 1.1 再現範囲

本プロジェクトは De Giorgis & Gangemi (2024) "EFO: the Emotion Frame Ontology" の以下の範囲を再現する:

| 論文セクション | 再現内容 | 対応ファイル |
|--------------|---------|-------------|
| Plutchik の感情の輪 | 8 基本感情 + 10 Dyad の OWL 定義 | `modules/EFO-PlutchikDyad.ttl` |
| Dyad 推論 | min-threshold 集約による複合感情推論 | `scripts/run_inference.py` |
| Section VII (E2) | 閾値感度分析 (Table III 形式) | `scripts/threshold_sweep.py` |
| Appendix E | SHACL シェイプによる構造検証 | `shacl/plutchik-dyad-shapes.ttl` |

### 1.2 非再現範囲

以下は本プロジェクトの範囲外とする:

- **OCC モジュール** (`occ_2023.owl`): 認知的評価理論に基づく感情モデル
- **CREMA-KG / WASSA データセット**: 大規模感情コーパスの RDF 変換
- **Framester との完全統合**: FrameNet フレームと感情の自動マッピング
- **DL 推論器 (HermiT/Pellet) による完全推論**: OWL DL レベルのクラス分類

---

## 2. EmotionSituation の equivalentClass 設計

### 判断

`pl:EmotionSituation` を独立したクラスとして定義し、`fschema:FrameOccurrence` と `owl:equivalentClass` で結ぶ。

### 根拠

- EFO 論文では `fschema:FrameOccurrence` を感情状況のクラスとして使用している
- しかし PlutchikDyad モジュールとして独自の概念名を提供する必要がある
- `equivalentClass` により、既存の FrameOccurrence インスタンスが自動的に EmotionSituation としても扱われる
- `rdfs:subClassOf` ではなく `owl:equivalentClass` を選択したのは、双方向の推論互換性を確保するため

### 影響

実データでは `fschema:FrameOccurrence` のみを型宣言すれば十分であり、`pl:EmotionSituation` の明示的なインスタンス化は不要。

---

## 3. min-threshold 選択の根拠

### 判断

複合感情のスコア集約関数として `min` を採用し、閾値フィルタリングと組み合わせる。

### 代替案の検討

| 集約関数 | 特性 | 不採用理由 |
|---------|------|-----------|
| `mean` | 平均値を取る | 片方のスコアが極端に低くても平均化されてしまう |
| `max` | 最大値を取る | 弱い成分を無視してしまい、複合感情の定義に反する |
| `product` | 積を取る | スコアが 0 に近いと結果が過度に小さくなる |
| **`min`** | **最小値を取る** | **両成分が十分なスコアを持つことを保証** |

### 根拠

- Plutchik の理論では、Dyad は 2 つの基本感情が**同時に十分な強度で**存在する場合に成立する
- `min` 関数はこの「両方が十分」という意味論を自然に表現する
- 閾値は「十分な強度」の下限を定義する
- 論文の Table III との対応を可能にするため、TH=0.4 をデフォルトとした

---

## 4. Evidence / DyadEvidence の分離設計

### 判断

`pl:Evidence` を基底クラス、`pl:DyadEvidence` をそのサブクラスとして分離する。

### 根拠

- **基本感情の Evidence** (入力データ由来) と **複合感情の Evidence** (推論結果) は本質的に異なる
  - 基本感情 Evidence: 外部分析システムからのスコア、`derivedFrom` を持たない
  - DyadEvidence: 推論により生成、`derivedFrom` で元の Evidence を参照、`method` を持つ
- サブクラス関係により、SPARQL クエリで `?ev a pl:Evidence` と書けば両方を取得でき、`?ev a pl:DyadEvidence` と書けば推論結果のみをフィルタリングできる
- SHACL シェイプでも、各クラスに適切な制約を個別に定義できる (Shape 1 vs Shape 2)

### 代替案

単一の Evidence クラスに `isInferred` フラグを追加する設計も検討したが、OWL のクラス階層による自然な分類を優先した。

---

## 5. SHACL の Violation / Warning 使い分け方針

### 判断

SHACL シェイプの `sh:severity` を以下の方針で使い分ける。

### 方針

| 重大度 | 基準 | 例 |
|--------|------|-----|
| **Violation** (デフォルト) | データの論理的正当性に影響する制約 | Evidence に emotion がない、score が範囲外 |
| **Warning** | メタデータの欠損やベストプラクティス違反 | method 注釈がない、Evidence のない FrameOccurrence |

### 具体的な Warning 設定

| シェイプ | 制約 | Warning の理由 |
|---------|------|---------------|
| DyadEvidenceShape | `pl:method` minCount 1 | 推論結果の正当性は method なしでも検証可能 |
| FrameOccurrenceWithEvidenceShape | `pl:hasEvidence` minCount 1 | 未分析の状況も概念的に有効 |
| BasicEmotionEvidenceShape | `pl:derivedFrom` maxCount 0 | 構造上の異常だが、データ破損ではなくモデリングミスの可能性 |

### 根拠

- Violation は検証スクリプトの終了コードに影響する (exit 1)
- Warning はレポートに表示されるが、検証自体は通過する (exit 0)
- この使い分けにより、CI パイプラインでの段階的な品質管理が可能になる

---

## 6. Python 推論 vs SPARQL CONSTRUCT の両立理由

### 判断

推論ロジックを Python スクリプト (`run_inference.py`) と SPARQL CONSTRUCT ルール (`sparql/dyad_rules/`) の両方で実装する。

### Python スクリプトの利点

- **閾値パラメータ化**: コマンドライン引数で閾値を変更可能
- **セルフテスト内蔵**: 期待結果との自動照合
- **出力制御**: ファイル出力、名前空間バインディング、オントロジー IRI 宣言
- **感度分析**: `threshold_sweep.py` との統合

### SPARQL CONSTRUCT ルールの利点

- **宣言的記述**: 推論ロジックが人間に読みやすい形で表現される
- **トリプルストア統合**: Fuseki 等の SPARQL エンジンで直接実行可能
- **再現性**: Python 環境なしでも推論を再現可能
- **形式検証**: 推論ルールの正当性を形式的に議論しやすい

### 両立の根拠

- 研究再現プロジェクトとして、複数の実行環境に対応することが重要
- Python 版は日常的な開発・実験に使用し、SPARQL 版は形式的な記述・検証に使用する
- 両者の出力が一致することは CQ クエリで検証可能

### 注意点

SPARQL CONSTRUCT ルール内の閾値は `0.4` にハードコードされている。異なる閾値で実験する場合は Python スクリプトを使用すること。

---

## 7. 既知の制限事項

### 7.1 サンプルデータの規模

`sample.ttl` は 6 状況のみを含む小規模なテストデータである。実際の感情分析パイプラインからの大規模データでの検証は未実施。

### 7.2 Dyad のカバレッジ

Plutchik の理論では Secondary Dyad (1 つ隣を飛ばした組み合わせ) と Tertiary Dyad (2 つ隣を飛ばした組み合わせ) が定義されるが、本モジュールでは Primary Dyad 8 つと Secondary Dyad 2 つ (Hope, Pride) の計 10 Dyad のみを実装している。

### 7.3 OWL DL 推論との非統合

`owl:equivalentClass` による Dyad 定義 (OWL restriction パターン) は、DL 推論器 (HermiT, Pellet) での自動分類を意図して記述されている。しかし、本プロジェクトの推論パイプラインは Python/SPARQL ベースであり、DL 推論器との統合テストは未実施。

### 7.4 名前空間の暫定性

`http://example.org/efo/plutchik#` は暫定的な名前空間である。正式な公開時には永続的な IRI (例: W3ID) に移行する必要がある。

### 7.5 EmoCore の owl:imports 修正

`data/EmoCore_iswc.ttl` は Protege での作業により `owl:imports` に `sample.ttl` や推論出力のローカルパスが含まれている。これは本プロジェクトのローカル環境固有の問題であり、配布時には除去が必要。

### 7.6 スコアの数値精度

`xsd:decimal` 型を使用しているが、Python の `Decimal` 型との変換時に浮動小数点の精度問題が生じる可能性がある。閾値感度分析の `mean_dyad_score` 列で微小な丸め誤差が観測されている (例: 0.6499999... ≈ 0.65)。
