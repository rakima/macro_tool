# Architecture

## 目的

この文書は、Macro Tool v0.1の実装前にアプリケーション構成と責務分割を整理するための設計メモである。

v0.1では、PySide6によるGUI、PyAutoGUIによる画面操作、OpenCVによる画像検知、JSONによるルール保存を前提とする。

## 設計方針

- UIとマクロ実行処理を分離する。
- ルール定義はPython上でも明確なモデルとして扱う。
- JSON読み書き、画像検知、クリック実行をそれぞれ別の責務に分ける。
- PySide6固有の処理をアプリケーション全体に広げすぎない。
- v0.1では拡張しやすさを意識しつつ、過剰な抽象化は避ける。

## 想定ディレクトリ構成

```text
macro_tool/
  app/
    __init__.py
    main.py
    models.py
    storage.py
    screenshot.py
    detector.py
    actions.py
    runner.py
    ui/
      __init__.py
      main_window.py
      rule_editor.py
      region_selector.py
  tests/
    test_models.py
    test_storage.py
  docs/
    design.md
    rule_schema.md
    architecture.md
```

## モジュール責務

### app.main

アプリケーションのエントリーポイント。

主な責務:

- QApplicationの作成
- MainWindowの作成
- アプリケーション起動

### app.models

ルール定義を表すデータモデルを持つ。

主な責務:

- Rule
- Region
- Action
- RuleSet
- バリデーション
- JSON向けdictとの変換

v0.1ではdataclassを使う想定とする。

### app.storage

ルール定義JSONの読み書きを担当する。

主な責務:

- JSONファイルの読み込み
- JSONファイルへの保存
- versionチェック
- JSON構造の最低限の検証
- モデルへの変換
- 画像パスをルールJSONからの相対パスとして保存

### app.detector

画像検知を担当する。

主な責務:

- スクリーンショットの受け取り
- regionによる切り出し
- テンプレート画像の読み込み
- OpenCVによるテンプレートマッチング
- 検知結果の返却

検知結果は、座標・検出スコア・検出矩形を持つ値として扱う。

### app.screenshot

スクリーンショット取得を担当する。

主な責務:

- PyAutoGUIによるスクリーンショット取得
- 必要に応じたregion指定
- Pillow/RGB画像からOpenCV/BGR配列への変換
- マルチディスプレイ向けの仮想スクリーン原点の保持
- スクリーンショット取得エラーの隠蔽

### app.actions

検知時の操作を実行する。

主な責務:

- clickアクションの実行
- action.offsetの適用
- PyAutoGUI呼び出しの隠蔽

v0.1ではclickのみ対応する。

### app.runner

実行中のマクロループを管理する。

主な責務:

- 有効なルールの実行
- スクリーンショット取得
- cooldown判定
- detectorの呼び出し
- actionsの呼び出し
- 実行ログの通知
- 開始・停止状態の管理

v0.1の初期実装ではPySide6のQTimerで短い周期の実行サイクルを回す。
検知処理が重くなる場合は、PySide6のQThreadまたはQObject workerへ移す。

### app.ui.main_window

メイン画面を担当する。

主な責務:

- 実行開始・停止
- テスト検知
- ルール一覧表示
- 選択ルールの概要表示
- ログ表示
- ルール編集画面の起動

### app.ui.rule_editor

ルール編集画面を担当する。

主な責務:

- ルール名の編集
- 検知画像の選択
- 探索範囲の表示
- confidenceの編集
- actionの編集
- cooldownの編集
- 保存前バリデーション

### app.ui.region_selector

探索範囲の選択画面を担当する。

主な責務:

- スクリーンショットの表示
- ドラッグによる矩形選択
- 選択範囲の座標表示
- 確定・キャンセル

## データフロー

### 起動時

```text
app.main
  -> MainWindow
  -> storage.load_rules()
  -> models.RuleSet
  -> MainWindow displays rules
```

### 実行時

```text
MainWindow
  -> runner.start(rules)
  -> screenshot captures screen
  -> runner receives screenshot
  -> detector.match(rule, screenshot)
  -> actions.execute(rule.action, match)
  -> runner emits log/status
  -> MainWindow updates UI
```

### ルール保存時

```text
RuleEditor
  -> models.Rule validation
  -> MainWindow updates RuleSet
  -> storage.save_rules(rule_set)
```

## 依存方向

依存方向は以下を基本とする。

```text
ui -> runner -> detector
runner -> screenshot
ui -> storage -> models
runner -> actions
runner -> models
detector -> models
actions -> models
```

避けたい依存:

- modelsがuiに依存する
- detectorがuiに依存する
- actionsがuiに依存する
- storageがuiに依存する

## スレッド方針

PySide6のメインスレッドではUI更新のみ行う。

マクロ実行ループはバックグラウンドで動かす。

```text
Main Thread:
  - PySide6 UI
  - button events
  - list updates
  - log view updates
  - v0.1初期のQTimer実行サイクル

Worker Thread:
  - 将来的なscreenshot capture
  - 将来的なimage matching
  - 将来的なcooldown checks
  - 将来的なaction execution
```

WorkerからUIへは、PySide6のsignalを使って状態やログを通知する。

## エラー処理方針

v0.1で扱う主なエラー:

- JSONファイルが存在しない
- JSON形式が不正
- 画像ファイルが存在しない
- regionが不正
- confidenceが範囲外
- screenshot取得に失敗
- 画像検知に失敗
- click実行に失敗

ユーザーに見せるべきエラーはログに表示する。

保存できない不正入力は、ルール編集画面で保存前に分かるようにする。

## テスト方針

v0.1では、UIよりもモデルと保存処理を優先してテストする。

優先してテストする対象:

- modelsのバリデーション
- JSONからRuleSetへの変換
- RuleSetからJSONへの変換
- cooldown判定

UIテストはv0.1では必須にしない。

## v0.1の実装順序案

1. modelsを作る。
2. storageでJSON読み書きを作る。
3. detectorの最小実装を作る。
4. actionsでclick実行を作る。
5. runnerで実行ループを作る。
6. PySide6でメイン画面を作る。
7. ルール編集画面を作る。
8. 範囲選択画面を作る。
9. PyInstallerでexe化を検討する。

## v0.1ではやらないこと

- 複雑なプラグイン構造
- 複数アクションの連続実行
- アクションの条件分岐
- マクロ記録機能
- 高度なテーマ切り替え
- 設定同期
- マルチプロファイル

## 検討メモ

- imageのパスは、ルールJSONファイルからの相対パスとして扱うのが分かりやすい。
- regionはマルチディスプレイ環境を考慮し、xとyに負の座標を許可する。
- スクリーンショット取得とクリック実行はPyAutoGUIに集約する。
- OpenCVのテンプレートマッチングはdetector内に閉じ込め、UIから直接呼ばない。
- 将来的にキーボード入力や複数アクションを追加する場合も、action.typeで分岐できる構造にする。
