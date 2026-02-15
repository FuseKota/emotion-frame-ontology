# 先行研究: EFO: the Emotion Frame Ontology

> **作成日**: 2026-02-09 | **最終更新日**: 2026-02-09

> De Giorgis, S., & Gangemi, A. (2024). **EFO: the Emotion Frame Ontology**. arXiv:2401.10751
> https://arxiv.org/abs/2401.10751
> ライセンス: Creative Commons BY 4.0
> 分野: cs.AI, cs.CY, cs.SC

---

## 1. 概要

EFO (Emotion Frame Ontology) は、感情を**意味フレーム (semantic frame)** として扱う OWL ベースのオントロジーである。感情体験の異なる側面を捉える意味役割 (semantic role) を持つフレーム構造により、複数の感情理論を統一的にモデリングする。

### 論文の形式的な感情の定義

> "cognitive entities resulting from reifying a relation including physiological states that are experienced, recognised, appraised, or provoked by agents in their interaction as an internal cognitive state, or as an environmental or social situation, in some spatio-temporal context."

（感情とは、生理的状態の経験・認識・評価・誘発を含む関係を具象化した認知的実体であり、エージェントの相互作用における内的認知状態または環境的・社会的状況として、ある時空間コンテキストにおいて生じるものである。）

### 主要貢献 (5 点)

1. **フレームベース感情オントロジー**: DOLCE 基盤オントロジーに準拠し、eXtreme Design 方法論とオントロジー設計パターン (ODP) に基づくパターンベース設計
2. **モジュラーアーキテクチャ**: 複数の感情理論をモジュールとして接続可能な Emotion Ontology Network の構築
3. **EFO-BE モジュール**: Ekman の基本感情理論の完全な形式化 — 6 基本感情、55 サブクラス、強度階層、対処法・阻害要因・精神病理との関連
4. **自動推論の実証**: FRED 知識抽出器と Framester を組み合わせたグラフベース感情検出器を構築し、WASSA 2017 コーパスで評価 (Precision 100%, F1 42-52%)
5. **マルチモーダル拡張**: CREMA-D (音声 7,442 件) と FER+ (顔表情 35,887 件) の RDF 統合によるクロスモーダル感情意味論の実現

---

## 2. 背景と動機

### 2.1 問題意識

> "Despite the proliferation of theories and definitions, there is still no consensus on what emotions are, and how to model the different concepts involved when we talk about –– or categorize –– them."

感情研究には統一的なコンセンサスが存在せず、「感情とは何か、どのように関連概念をモデリングすべきか」について合意がない。感情は以下のように多様な側面を持ち、これらを統一的に扱うフレームワークが必要とされている:

- **生理的状態**: 皮膚電位活動 (EDA)、バイオフィードバック
- **社会的概念・行動**: 社会的相互作用における感情の役割
- **態度・認知的評価**: アプレイザル理論に基づく認知的評価プロセス
- **感情的現象の重複**: 感情 (emotion)、感覚 (feeling)、気分 (mood) の境界の曖昧さ

### 2.2 感情理論の分類

論文はカテゴリ的モデル (categorical model) に焦点を当てる。カテゴリ的アプローチは感情を離散的カテゴリ (「基本感情」「一次感情」) として組織化する。

各理論における基本感情の数:
| 理論家 | 基本感情の数 |
|-------|------------|
| Ekman | 5-6 |
| Mehrabian | 6 |
| Izard | 7 |

Ekman の基本感情理論 (Atlas of Emotions, 2021 年版) を最初の実装対象とした理由: **FACS (Facial Action Coding System)** との統合により、感情検出・顔表情認識における運用面の価値が高いため。

### 2.3 既存の感情オントロジーとの比較

| オントロジー | 正式名称 | 基盤 | 特徴 | EFO との差異 |
|------------|---------|------|------|-------------|
| **EmOCA** | Emotion Ontology for Context Awareness | RDF/RDFS (not OWL) | 生理的顕在化に基づく感情検出、`:Stimulus`, `:PersonalityTrait` クラス、Ekman 理論採用 | EFO は OWL で複数理論対応 |
| **EmotionsOnto** | — | DOLCE + D&S ODP | OWL 記述、マルチモーダル表現/感覚認識を組み込み。**EFO に最も近い先行研究** | EFO は 4 点で改良 (下記) |
| **SOCAM Affective** | Ontology-based Affective Context Representation | OWL | ファジー論理による複雑感情状態の表現 | EFO はフレーム意味論を採用 |
| **MFOEM** | Multi-Foundational Ontology for Emotions Module | BFO (OBO Foundry) | Sanders-Scherer 理論、`mfoem:emotion process` ← `mfoem:affective process`、`mfoem:physiological process involved in an emotion` | EFO は DOLCE を採用 (社会構成概念に適合)、複数理論同時表現 |
| **framECO** | — | フレームベース | 文学における非自明な感情状況 (Dictionary of Obscure Sorrows に着想)、感情カテゴリ化の困難性に関する実験認知結果 | EFO はより包括的な理論統合 |
| **WordNet Affect** | — | WordNet 拡張 | シンセットに肯定/否定/曖昧/中立ラベル付け、stative/causative 次元、SenticNet・DepecheMood の基盤 | 形式的オントロジーではない |

#### EFO が EmotionsOnto から改良した 4 点

1. 感情フレームの**語彙化** (lexicalization) — Framester を通じた多言語語彙との接続
2. **Semantic Web 資源**の再利用 — FrameNet, WordNet, VerbNet, BabelNet, DBpedia 等
3. **複数感情理論**の同時モデリング — モジュラー設計により理論ごとにモジュールを追加可能
4. 既存マルチモーダルデータセットの **RDF 変換・再利用** — CREMA-D, FER+ の統合

#### EFO と MFOEM の差異の根拠

- MFOEM は BFO を基盤とするが、BFO は主に生物医学的実体に適した存在論
- EFO は DOLCE を採用。DOLCE は「社会的に構成された実体」(socially-constructed entities) のモデリングに適しており、感情の認知的・社会的側面をより自然に表現できる
- EFO は意味フレーム表現を用いることで、語彙資源との統合が容易

---

## 3. EFO アーキテクチャ

### 3.1 設計方法論

| 項目 | 採用手法 | 説明 |
|------|---------|------|
| 設計方法論 | **eXtreme Design (XD)** | テスト駆動型のオントロジー設計方法論 |
| 設計パターン | **オントロジー設計パターン (ODP)** | 再利用可能な設計パターンの適用 |
| 基盤オントロジー | **DOLCE-Zero** | DOLCE の軽量実装。認知的側面に適合 |
| 核心パターン | **Description & Situation (D&S) ODP** | 感情の具象化関係のモデリング |

### 3.2 Description & Situation ODP の役割

EFO の核心的設計パターン。D&S ODP は DOLCE-Zero に含まれ、以下の二重表現を可能にする:

```
[内包的レベル: 概念としての感情]
dul:Description ← fs:ConceptualFrame ← efo:Emotion
    (感情は「意味フレーム」として記述される抽象概念)

[外延的レベル: 状況としての感情]
dul:Situation ← fs:FrameOccurrence ← efo:EmotionSituation
    (感情の具体的な発生・経験のインスタンス)
```

**具象化 (reification)** により、感情を:
- 抽象的な概念フレーム (`efo:Emotion` = `fs:ConceptualFrame`) として定義しつつ
- その具体的な発生 (`efo:EmotionSituation` = `fs:FrameOccurrence`) をインスタンスとして表現

OWL2 の **punning** (同一 IRI をクラスと個体の両方として使用) を活用し、内包的 (intensional) と外延的 (extensional) の両面での表現を可能にしている。

`efo:EmotionSituation` は複数のエンティティ型を巻き込むことができる: 精神状態、評価表現、トリガーとなる瞬間、`PhysicalManifestation` のサブパート等。

### 3.3 Framester 統合

EFO は **Framester** 知識グラフと深く統合されている。Framester は「意味フレームに対する形式的意味論を、複数の言語的・事実的データ資源を統合したキュレーション済みリンクトデータとして提供する」。

統合される資源:

| カテゴリ | 資源 | 役割 |
|---------|------|------|
| 意味フレーム | **FrameNet** | フレーム定義とフレーム要素 |
| 語彙 | **WordNet** | 語義・シンセット |
| 動詞 | **VerbNet** | 動詞の意味クラス |
| 認知 | **MetaNet / ImageSchemaNet** | メタファー・イメージスキーマ |
| 多言語 | **BabelNet** | 多言語語彙資源 |
| 事実知識 | **DBpedia, YAGO** | 百科事典的知識 |
| オントロジー | **DOLCE** | 基盤オントロジースキーマ |

Framester SPARQL エンドポイント: `http://etna.istc.cnr.it/framester2/sparql`

### 3.4 オントロジーネットワーク構成

```
EFO オントロジーネットワーク
  ├── EmoCore モジュール   (感情の最小限語彙 — 全モジュールの共通基盤)
  ├── BE モジュール        (Ekman 基本感情理論の形式化)
  └── BET モジュール       (基本感情トリガー — Framester 経由の語彙・事実的トリガー)
```

将来計画として **OCC モジュール** (Ortony-Clore-Collins 認知的評価理論) や**次元的感情モデル** (Plutchik, Valence-Arousal 等) のモジュール追加が言及されている。

---

## 4. EmoCore モジュール

感情に関する最小限の語彙を定義するコアモジュール。すべての理論固有モジュールの共通基盤となる。

### 4.1 クラス階層

```
dul:Description
  └── fs:ConceptualFrame
        ├── efo:Emotion                         ← 最も広範な感情概念
        │     └── efo:BE_Emotion                ← 理論固有サブクラス (BE モジュールで定義)
        ├── fs:SynsetFrame
        ├── wn:synset-emotion-noun-1
        └── wn:synset-emotional_state-noun-1

dul:Situation
  └── fs:FrameOccurrence                        ← 感情状況の基底クラス
        ├── efo:EmotionSituation                ← EFO 固有の感情状況
        ├── fs:EmotionActive                    ← Undergoer への肯定/否定的作用
        ├── fs:EmotionDirected                  ← Experiencer の Stimulus/Topic への反応
        ├── fs:Feeling                          ← 評価を伴う感情状態
        └── fs:MentalProperty                   ← 行動から推測される一般的精神状態

dbpedia:Emotion
  └── (rdfs:subClassOf fs:ConceptualFrame)      ← DBpedia 感情概念との接続
```

### 4.2 クラスの詳細

| クラス | 上位クラス | 説明 |
|-------|----------|------|
| `efo:Emotion` | `fs:ConceptualFrame` | 最も広範な感情の概念。すべての理論固有定義を包含する。Primitive クラス (形式的定義なし) |
| `efo:BE_Emotion` | `efo:Emotion` | 基本感情理論における感情クラス (BE モジュールで詳細化) |
| `fs:EmotionActive` | `fs:FrameOccurrence` | Undergoer (感情の対象) への肯定/否定的作用に焦点を当てるフレーム |
| `fs:EmotionDirected` | `fs:FrameOccurrence` | Experiencer (感情の主体) が Stimulus/Topic に対して感情反応を示すフレーム |
| `fs:Feeling` | `fs:FrameOccurrence` | アプレイザル (評価) を伴う可能性のある感情状態 |
| `fs:MentalProperty` | `fs:FrameOccurrence` | 行動から推測される一般的精神状態 |
| `dbpedia:Emotion` | `fs:ConceptualFrame` | DBpedia の感情概念。外部資源との接続点 |

### 4.3 プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `efo:triggers` | ObjectProperty | EmotionTrigger が Emotion を誘発する関係。全感情理論で共通の二項関係 |

---

## 5. BE モジュール (Ekman 基本感情理論)

Ekman の基本感情理論 (Atlas of Emotions, 2021 年版: http://atlasofemotions.org) を形式化したモジュール。

### 5.1 基本感情 (6 感情)

| 基本感情 | 極性 | サブクラス数 | 強度階層 (低→高) |
|---------|------|------------|-----------------|
| **Enjoyment** | Positive | 複数 | (論文に完全リスト未記載) |
| **Fear** | Negative | 8 | Trepidation < Nervousness < Anxiety < Dread < Desperation < Panic < Horror < Terror |
| **Sadness** | Negative | 複数 | (論文に完全リスト未記載) |
| **Anger** | Negative | 複数 | (論文に完全リスト未記載、Annoyance, Frustration, Fury 等を含む) |
| **Disgust** | Negative | 7 | Dislike < Aversion < Distaste < Repugnance < Revulsion < Abhorrence < Loathing |
| **Surprise** | — | 複数 | (論文に完全リスト未記載) |

**注**: 論文では Fear と Disgust の強度階層のみが完全に列挙されている。BE_iswc.ttl 全体で 55 クラスが定義されている (WORK_LOG.md セクション 3.2 で確認済み)。rdflib での検証結果として、moreIntenseThan 関係は 41 件存在する。

### 5.2 Fear の詳細構造 (論文の主要例)

論文は Fear を代表例として、BE モジュールの構造を詳細に記述している:

```
be:Fear (Negative Polarity)
  ├── be:Trepidation     — Antidote: TrepidationAntidote
  ├── be:Nervousness     — Antidote: NervousnessAntidote
  ├── be:Anxiety         — Antidote: AnxietyAntidote
  ├── be:Dread           — Antidote: DreadAntidote
  ├── be:Desperation     — Antidote: DesperationAntidote
  ├── be:Panic           — Antidote: PanicAntidote
  ├── be:Horror          — Antidote: HorrorAntidote
  └── be:Terror          — Antidote: TerrorAntidote

  関連精神病理 (be:emotionalTendencyTowards):
    - AvoidantPersonalityDisorder (回避性パーソナリティ障害)
    - GeneralizedAnxietyDisorder (全般性不安障害)
    - ObsessiveCompulsiveDisorder (強迫性障害)
    - PostTraumaticStressDisorder (心的外傷後ストレス障害)
    - SocialAnxietyDisorder (社会不安障害)

  パーソナリティ特性 (be:hasPersonalityTrait):
    "A shy or timid person... timid people may perceive the world
     as full of difficult situations"
    (内気/臆病な人は世界を困難な状況に満ちていると知覚しうる)
```

### 5.3 BE モジュールのクラス体系

| クラス | 説明 | 役割 |
|-------|------|------|
| `be:BE_Emotion` | 基本感情理論における感情クラス (Primitive) | 6 基本感情の親クラス |
| `be:PreCondition` | 感情の前提条件/コンテキスト — 感情的参入に影響する状況 | 感情の発生条件 |
| `be:Mood` | 長期的な感情状態 — 明示的トリガーなしに反復を促進 | 状態の持続性 |
| `be:PerceptionDatabase` | 普遍的 (hardwired) 反応と個人的に獲得された記憶 | 感情トリガーの知識基盤 |
| `be:Trigger` | 評価 (appraisal) と PerceptionDatabase のスクリプトの相互作用 | 感情の発火メカニズム |
| `be:PersonalityTrait` | 特定の感情状態への傾向 | 個人差の表現 |
| `be:Psychopathology` | 感情に紐づく病理 — `be:emotionalTendencyTowards` で特定感情と関連 | 臨床的関連性 |
| `be:PhysicalChange` | 感情中の身体的変化 | 生理的顕在化 |
| `be:PhysiologicalChange` | 質的経験の顕在化 | 内的経験 |
| `be:Signal` | 外部的な普遍的プロトタイプ的顕在化 (顔の表情、声) | 外的シグナル |
| `be:SelectiveFilterPeriod` | 感情に一致した知覚の狭窄/歪曲の期間 | 認知的影響 |
| `be:PostCondition` | 感情的行動の結果 (外的/内的) | 感情の帰結 |
| `be:EmotionCounter` | 感情に対する対抗力の親クラス | 感情の調整 |
| `be:EmotionAntidote` | 否定的感情に対する対処行動 (EmotionCounter のサブクラス) | 例: "Making a special effort of letting go of ruminations about the past and anticipations of the future" |
| `be:EmotionImpediment` | 肯定的感情との葛藤 (EmotionCounter のサブクラス) | 肯定的感情の阻害要因 |

### 5.4 BE モジュールのプロパティ

| プロパティ | ドメイン | レンジ | 説明 |
|-----------|---------|--------|------|
| `be:moreIntenseThan` | 感情サブクラス | 感情サブクラス | 強度が高い (推移的) |
| `be:lessIntenseThan` | 感情サブクラス | 感情サブクラス | 強度が低い (`moreIntenseThan` の inverse) |
| `be:hasAntidote` | 否定的感情 | `be:EmotionAntidote` | 対処法 |
| `be:hasImpediment` | 肯定的感情 | `be:EmotionImpediment` | 阻害要因 |
| `be:hasPreCondition` | 感情状態 | `be:PreCondition` | 前提条件 |
| `be:hasAction` | 感情 | アクション型 | 感情に関連する行動 |
| `be:hasPolarity` | 感情 | 極性型 | 感情の極性 (Positive/Negative) |
| `be:hasPersonalityTrait` | 感情 | `be:PersonalityTrait` | 関連するパーソナリティ特性 |
| `be:emotionalTendencyTowards` | `be:Psychopathology` | `be:BE_Emotion` | 精神病理から特定感情への傾向 |

### 5.5 コンピテンシー質問 (CQ)

| CQ | 質問 | 回答例 |
|----|------|--------|
| CQ1 | Ekman 理論にはどのような感情がいくつあるか? | 6 基本感情、55 クラス (サブクラス含む) |
| CQ2 | 各基本感情の極性 (polarity) は何か? | Fear → NegativePolarity, Enjoyment → PositivePolarity |
| CQ3 | どの精神病理が特定の感情への傾向を持つか? | PTSD → Fear, GeneralizedAnxietyDisorder → Fear |
| CQ4 | 特定の感情に対する「対処法」(antidote) / 「阻害要因」(impediment) は何か? | AnxietyAntidote → Anxiety |
| CQ5 | ある感情は別の感情より強度が高いか? | Terror > Horror > Panic > ... > Trepidation |

### 5.6 SPARQL クエリ例 (Listing 1: Fear の包括的探索)

論文で提示された主要 SPARQL クエリ:

```sparql
SELECT DISTINCT ?emotion ?polarity ?psychopathology
                ?subEmotion ?antidote ?action
WHERE {
    ?emotion rdfs:subClassOf be:BE_Emotion .
    ?emotion be:hasPolarity ?polarity .
    ?psychopathology be:emotionalTendencyTowards ?emotion .
    ?emotion be:hasPersonalityTrait ?personalityTrait .
    ?subEmotion rdfs:subClassOf ?emotion ;
        be:hasAntidote|be:hasImpediment ?antidote ;
        be:moreIntenseThan ?siblingEmotion .
    ?emotion be:hasAction ?action .
    FILTER(regex(str(?emotion), 'Fear'))
}
```

このクエリにより、Fear に関する以下の情報を一括取得:
- 極性 (`be:NegativePolarity`)
- 関連精神病理 (5 件)
- パーソナリティ特性
- 全サブクラスとその強度順序
- 各サブクラスの Antidote
- 関連アクション

---

## 6. BET モジュール (基本感情トリガー)

Framester 知識グラフを活用し、各基本感情のトリガー (誘発語彙・概念) を体系的に抽出するモジュール。

### 6.1 Starting Lexical Material (SLM)

各基本感情の強度サブクラスのラベル (語彙単位) が初期トリガー語彙を構成する。例えば Disgust の場合:
**Dislike, Aversion, Distaste, Repugnance, Revulsion, Abhorrence, Loathing** の 7 語彙が SLM となる。

### 6.2 トリガー抽出の多段階ワークフロー (Disgust を例に)

論文では Disgust フレームを用いて、5 層の段階的トリガー抽出を実演している (Figure 1):

#### Layer 1: フレームトリガー (Frame Triggering)

SLM を起点に FrameNet フレームを検索。Disgust から誘発される関連フレーム:

| 取得フレーム | 説明 |
|------------|------|
| `fscore:Excreting` | 排泄行為 |
| `fscore:BeingRotted` | 腐敗状態 |
| `fscore:CauseToRot` | 腐敗の原因 |
| `fscore:Rotting` | 腐敗過程 |

#### Layer 2: フレーム要素トリガー (Frame-Element-Driven Triggering)

フレーム要素 (FE) をトリガーとして継承:

| フレーム要素 | 説明 |
|------------|------|
| `fe:Manner.CauseToRot` | 腐敗の様態 |
| `fe:Undergoer.CauseToRot` | 腐敗の対象 |
| `fe:Place.CauseToRot` | 腐敗の場所 |

#### Layer 3: 語彙トリガー (Lexical Triggering)

WordNet シンセットと VerbNet 動詞クラスを取得:

| 資源 | 取得エントリ | 説明 |
|------|------------|------|
| WordNet | `wn:synset-putrefactive-adjectivesatellite-1` | 腐敗性の形容詞 |
| WordNet | `wn:synset-putrefy-verb-1` | 腐敗する動詞 |
| VerbNet | `vn:Putrefy_45040000` | 腐敗動詞クラス |

#### Layer 4: SKOS CloseMatch トリガー (Cross-Resource Bridging)

`skos:closeMatch` による資源横断ブリッジ:

| 資源 | エントリ | 説明 |
|------|---------|------|
| YAGO | `yago:rancidity_114561839` | 腐臭の概念 |
| Premon | `premon:fn17-excreting` | FrameNet 排泄フレーム |
| PropBank | `pb:puke.01` | 嘔吐の述語 |
| BabelNet | `babel:s00028852n` ("muck") | 汚物の多言語概念 |

#### Layer 5: ConceptNet トリガー (Concept Expansion)

ConceptNet による概念拡張:

| エントリ | 説明 |
|---------|------|
| `cn:dislike` | 嫌悪 |
| `cn:disdain` | 軽蔑 |

これにより、8 つの Semantic Web 資源 (FrameNet, WordNet, VerbNet, DBpedia, Wikidata, ConceptNet, BabelNet, PropBank) を横断するトリガーネットワークが構築される。

### 6.3 トリガー統計

GitHub リポジトリに `BE_Stats.png` としてトリガー数の統計が公開されている。各感情×各資源のトリガー数の分布を示す。

---

## 7. 評価: テキストからの感情検出

### 7.1 FRED 知識抽出器

**FRED** (http://wit.istc.cnr.it/stlab-tools/fred/demo/) はハイブリッド知識抽出システムで、以下の機能を提供:

- 統計的手法 + ルールベースの**ハイブリッド知識抽出**
- 自然言語から **RDF/OWL 知識グラフ**を自動生成
- **エンティティリンキング**と**語義曖昧性解消**
- **フレーム検出** (FrameNet) と**意味役割検出**

FRED の出力に含まれる情報:
- WordNet 語義曖昧性解消 (WSD)
- VerbNet 動詞義曖昧性解消 + 意味役割
- FrameNet フレーム検出
- PropBank フレーム認識
- DBpedia エンティティリンキング

### 7.2 感情検出パイプライン (3 段階)

```
Step 1: 自然言語文を FRED に入力
        ↓
        FRED が文を解析し、意味依存関係の知識グラフを構築
        (フレーム抽出、WordNet 曖昧性解消、エンティティ認識を実行)
        ↓
Step 2: グラフ中の各 Framester ノードについて、
        BET (Basic Emotion Triggers) グラフに対して SPARQL クエリを実行し、
        感情トリガーを抽出
        ↓
Step 3: 各感情トリガーについて、元のグラフに
        「どの感情がトリガーされたか」を宣言するトリプルを追加
```

### 7.3 評価データセット: WASSA 2017

| 項目 | 値 |
|------|-----|
| コーパス種別 | ツイート |
| 感情カテゴリ | Ekman の 4 感情 (Fear, Anger, Enjoyment, Sadness) |
| 規模 | 各感情約 1000 ツイート |
| アノテーション | 1 ツイート = 1 感情ラベル |

### 7.4 評価結果 (Table 1)

| 感情 | Total tweets | FRED 生成グラフ数 | 検出数 | Precision | Recall | F1 | Pearson r |
|------|-------------|-------------------|--------|-----------|--------|----|-----------|
| **Anger** | 857 | 816 | 282 | 100% | 34.60% | 51.41 | 0.60 |
| **Fear** | 1,157 | 1,076 | 374 | 100% | 34.76% | 51.59 | 0.59 |
| **Sadness** | 786 | 752 | 200 | 100% | 26.23% | 42.06 | 0.64 |
| **Enjoyment** | 824 | 711 | 204 | 100% | 28.41% | 44.25 | 0.60 |

### 7.5 結果の詳細分析

#### Precision 100% の理由

知識グラフ内で明示的にマッチするトリガーのみを検出する**保守的手法**のため。誤検出は原理的に発生しない (false positive = 0)。

#### 低い Recall の要因

1. **ツイートの短さ・不規則な構文**: FRED の解析が困難
2. **皮肉・アイロニー**: フレーム意味論では捕捉不可
3. **1 感情ラベル制約**: データセットが 1 ツイート 1 感情を想定しているが、実際のツイートは複数感情を含みうる
4. **ハッシュタグの影響**: ハッシュタグが意見やアイロニーを反映する場合がある

#### 感情別の詳細知見

**Enjoyment** (824 tweets → 711 graphs → 204 detections):
- 204 件で `be:Enjoyment` を検出
- 67 件で `be:Surprise` も共起
- その他の組み合わせは各 10 件未満

**Sadness** (786 tweets → 752 graphs → 200 detections):
- 単一感情ラベルの限界が顕著
- 例: サッカーに関するツイートが明らかに Fear も含むが、Sadness のみラベル付け

**Anger** (857 tweets → 816 graphs → 282 detections):
- FrameNet の `fs:EmotionHeat` フレームとの強い相関
- 特に `wn:blood-noun-1`, `vn:Fume_31030800`, `vn:Boil_45030000` (怒りの「熱」メタファー) との関連

**Fear** (1,157 tweets → 1,076 graphs → 374 detections):
- `be:Sadness` との共起が「despair (絶望)」概念周辺で頻繁に観察
- Fear と Sadness の概念的重複を示唆

#### 具体例: ツイートの分析 (Figure 2)

入力ツイート:
> "Cosplaying properly for the first time on Saturday! Pretty nervous…"

FRED による分析:
1. 知識グラフが生成される
2. `wn:nervous-adjectivesatellite-1` (WordNet シンセット) がノードとして抽出
3. BET グラフへの SPARQL クエリにより `be:Fear` がトリガーとして検出
4. 元のグラフに `be:Fear` 感情フレーム活性化のトリプルが追加

#### 統計的検証

Pearson 相関は中程度の一致 (r = 0.59-0.64) を示す。これは:
- 方法論的バイアス (ハッシュタグの意見/アイロニー反映)
- フレームの対比 (contrast) 的使用
- カテゴリ的感情モデルの限界

を示唆している。論文は次のように述べている:
> "real life affective situations can be much richer than what a simple categorisation could express"

### 7.6 推論器による一貫性検証

> "The ontology has proven consistent via testing it with HermiT 1.4.3.456 reasoner in Protégé, version 5.5.0"

オントロジー全体 (EmoCore + BE + BET) が HermiT 推論器で一貫性を確認済み。

---

## 8. マルチモーダル拡張

2 つの感情認識データセットを RDF に変換し、EFO オントロジーネットワークと統合。クロスモーダル感情意味論の探索を可能にする。

### 8.1 CREMA-D (Crowd-sourced Emotional Multimodal Actors Dataset)

| 項目 | 値 |
|------|-----|
| 正式名称 | Crowd-sourced Emotional Multimodal Actors Dataset |
| データ | 91 人の俳優による **7,442 音声録音** |
| 内容 | 単一の文をさまざまなイントネーションで発話 |
| 感情ラベル | Anger, Disgust, Fear, Happy, Neutral, Sad (6 感情) |
| アノテーション | **2,443 参加者**による **219,687 アノテーション** |
| RDF 名称 | CREMA-kg |
| 公開場所 | EFO GitHub リポジトリ (TTL 形式) |

#### RDF 表現パターン

各音声クリップを `efo:EmotionSituation` (`owl:NamedIndividual`) として表現。アノテーション値 > 0 の各感情について 2 種類のトリプルを生成:

```turtle
# (1) 感情の数値スコア
cr:1001_DFA_ANG_XX fer:hasAngerValue "5.0"^^xsd:float .

# (2) 感情クラスへのリンク
cr:1001_DFA_ANG_XX be:includesSignalOf be:Anger, be:Disgust .
```

**クエリ能力**: 複数感情の数値プロファイルに基づいて、特定の感情プロファイルを持つ音声クリップを検索可能。

### 8.2 FER+ (Facial Emotion Recognition Plus)

| 項目 | 値 |
|------|-----|
| 正式名称 | Facial Emotion Recognition Plus |
| データ | **35,887 枚**の顔表情画像 |
| アノテータ | 画像あたり **10 人** |
| 感情ラベル | neutral, happiness, surprise, sadness, anger, disgust, fear, contempt, unknown (9 ラベル) |
| RDF 名称 | FER-kg |
| 公開場所 | EFO GitHub リポジトリ (TTL 形式) |

#### 除外ラベル

| ラベル | 除外理由 |
|-------|---------|
| **"unknown"** | 単一理論へのコミットメントの限界を示す。EFO のモチベーション (複数理論の必要性) を裏付ける |
| **"contempt"** | Basic Emotions と Contempt-Anger-Disgust モデルのハイブリッドであり、現行 EFO に未実装 |

#### RDF 表現パターン

```turtle
# 各画像を EmotionSituation として表現
fer:0014735 a efo:EmotionSituation, owl:NamedIndividual .

# (1) 感情の数値スコア
fer:0014735 fer:hasAngerValue "3.0"^^xsd:float .

# (2) 感情クラスへのリンク (値 > 0 の感情)
fer:0014735 be:includesSignalOf be:Fear .
```

#### 複合感情クエリの例 (Figure 3)

複数感情の値フィルタを組み合わせ、特定の感情プロファイルを持つ画像を検索:

| 画像 ID | 検出感情 | 条件 |
|---------|---------|------|
| `fer:0035509` | `be:Anger` + `be:Fear` | 両方の値 > 3.0 |
| `fer:0014735` | `be:Enjoyment` + `be:Anger` | 両方の値 > 3.0 |
| `fer:0030527` | `be:Sadness` + `be:Disgust` | 両方の値 > 3.0 |

### 8.3 クロスモーダル感情意味論の意義

> 統合により、「感情フレームの役割と型、およびそれらの役割を果たすエンティティのクラス (生理的状態、エージェント、空間、時間、社会的シナリオ、情報オブジェクト等) について、多様なモダリティを横断して統一的に語る」ことが可能になる。

テキスト (WASSA 2017)、音声 (CREMA-D)、画像 (FER+) の 3 モダリティにわたる感情データを統一的な RDF/OWL グラフで表現し、クロスモーダルな SPARQL クエリを可能にする。

---

## 9. 論文の図表一覧

| 番号 | 種類 | 内容 |
|------|------|------|
| **Figure 1** | ワークフロー図 | Disgust トリガー抽出ワークフロー — 8 つの Semantic Web 資源 (FrameNet, WordNet, VerbNet, DBpedia, Wikidata, ConceptNet, BabelNet, PropBank) を横断 |
| **Figure 2** | 知識グラフ例 | "Cosplaying properly..." ツイートの FRED 知識グラフ — `wn:nervous-adjectivesatellite-1` 経由で `be:Fear` が活性化される過程 |
| **Figure 3** | クエリ結果例 | FER-kg の複合感情クエリ結果 — 複数感情を同時に持つ顔表情画像 |
| **Table 1** | 評価結果 | WASSA 2017 感情検出の Precision/Recall/F1/Pearson 指標 |
| **BE_Stats** | 統計図 (GitHub) | 各基本感情の資源別トリガー数分布 |

---

## 10. 結論と今後の方向性

### 10.1 達成事項

1. **DOLCE 準拠のフレームベース感情オントロジー**の構築 — D&S ODP による二重表現 (概念/状況)
2. **Ekman 基本感情理論の完全な形式化** (BE モジュール) — 6 感情, 55 クラス, 41 強度関係, 30 Antidote, 10 Impediment
3. **Framester 経由の自動トリガー抽出** (BET モジュール) — 5 層の多段階ワークフロー
4. **テキスト感情検出の実証** — FRED + Framester で Precision 100%, F1 42-52%
5. **マルチモーダル RDF 統合** — CREMA-D (音声 7,442 件) + FER+ (画像 35,887 件)

### 10.2 今後の方向性

- **次元的感情モデル** (Valence-Arousal, Plutchik 等) のモジュール追加
- **OCC モジュール** (Ortony-Clore-Collins 認知的評価理論) の開発
- カテゴリ的アプローチの限界の克服 — "unknown" ラベル問題への対処
- framECO が示す非自明な感情状況への対応

### 10.3 公開資源

| 資源 | URL |
|------|-----|
| EFO GitHub | https://github.com/StenDoipanni/EFO |
| 論文 (arXiv) | https://arxiv.org/abs/2401.10751 |
| Framester SPARQL | http://etna.istc.cnr.it/framester2/sparql |
| FRED デモ | http://wit.istc.cnr.it/stlab-tools/fred/demo/ |
| Atlas of Emotions | http://atlasofemotions.org |

---

## 11. 本再現プロジェクトとの関係

本再現プロジェクト (efo_repro) では、EFO の EmoCore モジュールを基盤とし、論文の将来方向性で言及された **Plutchik の感情の輪** に基づく Dyad (複合感情) 推論モジュールを拡張として実装している。

| 論文の範囲 | 本プロジェクトの対応 |
|-----------|-------------------|
| EmoCore モジュール | `data/EmoCore_iswc.ttl` として利用 |
| BE モジュール | `data/BE_iswc.ttl` として利用 (オプション) |
| BET モジュール | `data/BasicEmotionTriggers_iswc.ttl` として利用 (オプション) |
| Plutchik への言及 (将来方向性) | `modules/EFO-PlutchikDyad.ttl` として実装 |
| SPARQL による推論 | `sparql/dyad_rules/` + `scripts/run_inference.py` |
| 評価・検証 | SHACL 検証 + CQ クエリ + 閾値感度分析 |

詳細は [design-decisions.md](design-decisions.md) のセクション 1「論文との対応関係」を参照。
