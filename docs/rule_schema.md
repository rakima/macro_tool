# Rule Schema

## 概要

Macro ToolのルールはJSONで管理する。

1つのルールは「探索範囲内に指定画像が現れたら、指定した動作を実行する」という単位で表現する。

v0.1では、単純で読みやすい構造を優先し、将来の拡張に備えてactionはオブジェクトとして定義する。

## ルール例

```json
{
  "enabled": true,
  "name": "Click start button",
  "image": "images/start_button.png",
  "region": {
    "x": 100,
    "y": 200,
    "width": 300,
    "height": 120
  },
  "confidence": 0.85,
  "action": {
    "type": "click",
    "button": "left",
    "offset": {
      "x": 0,
      "y": 0
    }
  },
  "cooldown": 1.5
}
```

## フィールド

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| enabled | boolean | yes | ルールを実行対象にするか |
| name | string | yes | ルール名 |
| image | string | yes | 検知に使う画像ファイルのパス |
| region | object | yes | 探索範囲 |
| confidence | number | yes | 検知に必要な信頼度 |
| action | object | yes | 検知時に実行する動作 |
| cooldown | number | yes | 同一ルールの再発火を抑制する秒数 |

## region

探索範囲を画面座標で表す。

```json
{
  "x": 100,
  "y": 200,
  "width": 300,
  "height": 120
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| x | integer | yes | 探索範囲の左上X座標 |
| y | integer | yes | 探索範囲の左上Y座標 |
| width | integer | yes | 探索範囲の幅 |
| height | integer | yes | 探索範囲の高さ |

### 制約

- x >= 0
- y >= 0
- width > 0
- height > 0

## confidence

画像検知のしきい値を0.0から1.0の数値で表す。

推奨初期値は`0.85`とする。

```json
{
  "confidence": 0.85
}
```

### 制約

- confidence >= 0.0
- confidence <= 1.0

## action

v0.1ではクリックのみ対応する。

```json
{
  "type": "click",
  "button": "left",
  "offset": {
    "x": 0,
    "y": 0
  }
}
```

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| type | string | yes | v0.1ではclickのみ |
| button | string | yes | left, right, middle |
| offset | object | no | 検出位置からクリック位置をずらす量 |

### offset

offsetは検出した画像の中心点からの相対座標とする。

```json
{
  "offset": {
    "x": 10,
    "y": -5
  }
}
```

offsetを省略した場合は`{"x": 0, "y": 0}`として扱う。

## cooldown

同一ルールが短時間で連続発火することを防ぐための秒数。

```json
{
  "cooldown": 1.5
}
```

### 制約

- cooldown >= 0

## 保存形式

複数ルールは、トップレベルにversionとrulesを持つJSONとして保存する。

```json
{
  "version": 1,
  "rules": [
    {
      "enabled": true,
      "name": "Click start button",
      "image": "images/start_button.png",
      "region": {
        "x": 100,
        "y": 200,
        "width": 300,
        "height": 120
      },
      "confidence": 0.85,
      "action": {
        "type": "click",
        "button": "left"
      },
      "cooldown": 1.5
    }
  ]
}
```

## v0.1では採用しない項目

以下は便利だが、v0.1では仕様に含めない。

- delay
- repeat count
- loop interval per rule
- keyboard action
- multiple actions
- conditional branching
- OCR condition

## 検討メモ

- imageはプロジェクト相対パスとして扱うか、設定ファイルからの相対パスとして扱うかを実装前に決める。
- regionはマルチモニター環境で負の座標を許可するか、v0.1では単一モニター前提にするかを決める。
- action.offsetの基準点は、検出矩形の中心で統一する。
