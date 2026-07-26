# データ来歴・更新手順

最終取得・検証日時: **2026-07-26T12:00:00+09:00**

## 入力データ

|用途|公式配布元・版|取得物のSHA-256|加工・利用範囲|
|---|---|---|---|
|書き順|KanjiVG [`r20260714`](https://github.com/KanjiVG/kanjivg/releases/tag/r20260714)、commit `d95a97627fd9fe5b2c8d06ca81e38149609c0c1e`|Gitコミットで固定|現行の小学校配当漢字1,026字のSVGから`path`要素の`d`属性を画順順に抽出し、アプリ内`DATA`へ埋込み。|
|音訓|[EDRDG KANJIDIC2](http://ftp.edrdg.org/pub/Nihongo/kanjidic2.xml.gz)|`12cbd54ca51967cf2ead06b97e816a2d6e0a25757c4eb0a07df4272d2f2e1428`|児童向けに選定した音・訓のみを表示。中黒は複数読みの区切り、ハイフン位置は表示用に整形。|
|語例|[EDRDG JMdict_e](http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz)|`b835226b13a6c661001df83dddee281198b2a2871e44fdc2200dd547d7dccdb9`|児童向けに選定した語例と読みの組を表示。語例は当該取得物に同じ表記・読みの組があることを検証。|

KanjiVG は Ulrich Apel の著作物で [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/legalcode) です。KANJIDIC2・JMdict は James William Breen および EDRDG の著作物で、[EDRDG General Dictionary Licence](https://www.edrdg.org/edrdg/licence.html) および [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) に従います。

## 児童向け表示の選定

辞書にある全音訓・全語を機械表示しません。学年別の出題範囲はアプリ内の固定リストを正本とし、音訓・語例は児童向けに選定したものだけを表示します。これは出題、書き順、正誤判定を変更しないためです。選定済みの表示値は、上記の公式取得物から確認できる場合だけ維持します。

今回の再照合では、現行JMdictにない語例を `刀: 横刀（だいとう）→刀剣（とうけん）`、`里: 旧里（ふるさと）→里山（さとやま）`、`旧: 旧里（ふるさと）→旧友（きゅうゆう）` に置換し、`統` の訓読みを `ほびる→すべる` に訂正しました。その他の出題範囲・書き順・判定ロジックは変更していません。

## 再現可能な検証

取得物はリポジトリに含めません。次のコマンドで、公式取得物とアプリ内データが整合することを検証します。

```sh
python3 scripts/verify_source_data.py \
  --kanjivg-dir /path/to/kanjivg/kanji \
  --kanjidic2 /path/to/kanjidic2.xml.gz \
  --jmdict /path/to/JMdict_e.gz
```

この検証は、現行の小学校配当漢字1,026字のKanjiVG書き順パスの完全一致、選定音訓のKANJIDIC2照合、選定語例のJMdict照合、入力ファイルのSHA-256を確認します。

## 更新手順

少なくとも月1回、および公開更新時に、以下を実施して記録します。EDRDG配布物に更新があった場合は、取得日時・URL・ハッシュ、検証結果およびアプリへの反映可否を記録し、差分をレビューしてから反映します。

1. KanjiVGの公式リリースとEDRDGの公式配布物を再取得する。
2. 取得日時、URL、版／コミット、SHA-256をこのファイルへ追記する。
3. 上記検証を実行する。差分があれば、児童向け表示を人手レビューし、修正理由をここへ記録する。
4. 構文確認、スマートフォン・Chromebook相当のブラウザQA、ライセンス確認を行う。
5. Gitの変更内容を確認し、承認後に公開する。
