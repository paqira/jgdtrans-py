# ユーザーガイド

ここでは {py:mod}`JGDtrans` の使い方を紹介します。各 API の詳細は [API Reference](../autodoc/JGDtrans.rst) をみてください。

## インストール

PyPI よりインストールできます。

```shell
pip install JGDtrans
```

依存は [`typing-extensions`][typing-extensions] のみです。また `Python>=3.9` であることが必要です。

[typing-extensions]: https://pypi.org/project/typing-extensions/

ドキュメントは [`Sphinx`][Sphinx] によってビルドできます。

```shell
sphinx-apidoc -f -e --no-toc -d 1 -o ./doc/source/autodoc ./JGDtrans/ 
sphinx-build -b html ./doc/source ./doc/build/html
```

[Sphinx]: https://pypi.org/project/Sphinx/

## par ファイルの読み込み

{py:mod}`JGDtrans` は、以下の[国土地理院][GIAJ]が2023年時点で公開している全ての
_Gridded Correction Parameter_ ファイル（拡張子にちなんで
par ファイルと呼びます）の読み込みに対応しています。

- [TKY2JGD]
- [PatchJGD]
- [PatchJGD(H)]
- [HyokoRev]
- [SemiDynaEXE]
- [POS2JGD] (geonetF3 and ITRF2014)

[GIAJ]: https://www.gsi.go.jp
[TKY2JGD]: https://www.gsi.go.jp/sokuchikijun/tky2jgd.html
[PatchJGD]: https://vldb.gsi.go.jp/sokuchi/surveycalc/patchjgd/index.html
[PatchJGD(H)]: https://vldb.gsi.go.jp/sokuchi/surveycalc/patchjgd_h/index.html
[HyokoRev]: https://vldb.gsi.go.jp/sokuchi/surveycalc/hyokorev/hyokorev.html
[SemiDynaEXE]: https://vldb.gsi.go.jp/sokuchi/surveycalc/semidyna/web/index.html
[POS2JGD]: https://positions.gsi.go.jp/cdcs

ここでは、 par ファイルの読み込み方法と紹介します。

{py:mod}`JGDtrans` は par ファイルを提供しません。
par ファイルを利用する場合は、国土地理院よりダウンロードしてください [^1]。

[^1]: Download links;
      TKY2JGD: <https://www.gsi.go.jp/sokuchikijun/tky2jgd_download.html>;
      PatchJGD, PatchJGD(H) and HyokoRev: <https://www.gsi.go.jp/sokuchikijun/sokuchikijun41012.html>;
      SemiDynaEXE: <https://www.gsi.go.jp/sokuchikijun/semidyna.html>;
      geonetF3 and ITRF2014 (POS2JGD): <https://positions.gsi.go.jp/cdcs/>.

{py:func}`.load` と {py:func}`.loads` 
によって par ファイルを読み込みます。この
API は {py:class}`.Transformer` を返します。
`format` 引数を用いて、par ファイルのフォーマットを指定してください。

```pycon
>>> import JGDtrans
>>> with open('SemiDyna2023.par') as fp:
...     tf = JGDtrans.load(fp, format="SemiDynaEXE")
>>> tf
Transformer(unit=5, parameter=<object (21134 length) at 0x123456789>, description='for [...]')
```
ヘッダ、 unit （{py:obj}`1` もしくは {py:obj}`5`、 [](#メッシュに関連する実装の導入) にて説明します)、パラメータには、それぞれ、
{py:attr}`.Transformer.description` 、
{py:attr}`.Transformer.unit` 、
{py:attr}`.Transformer.parameter` にてアクセスできます。

```pycon
>>> tf.description
'for SemiDynaEXE    Ver.1.0.0\n[...]\nMeshCode dB(sec)  dL(sec) dH(m)'
>>> tf.unit
5
>>> tf.parameter
{
    36230600: Parameter(
        latitude=-0.05475,
        longitude=0.04,
        altitude=0.07721,
    ),
    # and go on
}
```

{py:attr}`.Transformer.parameter` のエントリは、
par ファイルのパラメータ部の一行に対応します。キーはメッシュコード（_meshcode_）、値は {py:class}`.Parameter` オブジェクトです。

TKY2JGD の高度、 PatchJGD(H) の経緯度は {py:obj}`0.0` になります。 

```pycon
>>> with open('TKY2JGD.par') as fp:
...     tf = JGDtrans.load(fp, format="TKY2JGD")
>>> tf.parameter[46303582]
Parameter(latitude=12.79799, longitude=-8.13354, altitude=0.0)
```

{py:meth}`.Transformer.to_dict` は、
{py:class}`.Transformer` オブジェクトを {py:obj}`dict` に変換して返します。

```pycon
>>> tf.to_dict()
{
    'description': 'for SemiDynaEXE    Ver.1.0.0\n[...]\nMeshCode dB(sec)  dL(sec) dH(m)',
    'unit': 5,
    'parameter': {
        36230600: {
            'latitude': -0.05475,
            'longitude': 0.04,
            'altitude': 0.07721,
        },
        # and go on
    },
}
```

{py:func}`.from_dict` は、前述の {py:obj}`dict` オブジェクトを受け取る
{py:class}`.Transformer` のコンストラクタです。

```pycon
>>> data = {
...     'description': 'my SemiDynaEXE',
...     'unit': 5,
...     'parameter': {
...         36230600: {
...             'latitude': -0.05475,
...             'longitude': 0.04,
...             'altitude': 0.07721,
...         },
...     # and go on
...     },
... }
>>> tf = JGDtrans.from_dict(data)
>>> tf
Transformer(unit=5, parameter=<object (21134 length) at 0x987654321>, description='my [...]')
```

これらを用いることで、 par 形式データを、 python {py:obj}`dict` や他シリアライズ形式（例えば JSON）に相互に変換できます。

## 座標変換

ここでは、 {py:class}`.Transformer` オブジェクトを使った座標変換方法を紹介します。

順方向の変換は {py:meth}`.Transformer.forward` によって、
逆方向の変換は {py:meth}`.Transformer.backward` によって行います。いずれも _TKY2JGD for Windows Ver.1.3.79_ や国土地理院の web API よりも高い精度の結果を返します。

```pycon
>>> tf.forward(36.10377479, 140.087855041, 2.34)
Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)
>>> tf.backward(36.103773017086695, 140.08785924333452, 2.4363138578103)
Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.3399999995782443)
```

戻り値は {py:class}`~JGDtrans.Point` オブジェクトです。経緯度、高度には各属性でアクセスできます。

```pycon
>>> point = tf.forward(36.10377479, 140.087855041, 2.34)
>>> point.latitude
36.103773017086695
>>> point.longitude
140.08785924333452
>>> point.altitude
2.4363138578103
```

{py:class}`~JGDtrans.Point` オブジェクトはアンパックをサポートしています（{py:class}`~JGDtrans.Point`
は長さ 3 の {py:obj}`Sequence[flaot]` です）。

```pycon
>>> origin = Point(36.10377479, 140.087855041, 2.34)
>>> result = tf.forward(*origin)
>>> tf.backward(*result)
Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)
```

引数（{py:obj}`backward`）によって順逆変換を切り替える {py:meth}`.Transformer.transform`
も提供しています。動作は前述の {py:meth}`.Transformer.forward` や {py:meth}`.Transformer.backward`
と同じです。つまり、任意の {py:class}`~JGDtrans.Point` オブジェクト {py:obj}`point` に対して、以下の恒等式が成り立ちます。

```pycon
>>> tf.transform(*point, backward=False) == tf.forward(*point)
True
>>> tf.transform(*point, backward=True) == tf.backward(*point)
True
```

{py:meth}`.Transformer.backward` は _TKY2JGD for Windows Ver.1.3.79_ や国土地理院の web API
がそうである様に、正確ではありません [^2]。逆変換の結果は、厳密解からわずかですがズレています（２つ前のコードを見てください）。

[^2]: 私が調べたかぎりでは。

{py:meth}`.Transformer.backward_safe`
を用いることで、結果の精度（厳密解からのずれ）を保証した逆変換が行えます。経緯度の誤差は、国土地理院が公開しているパラメータの誤差
$2.7\times10^{-9}$ \[deg\] 以下となることを保証し、高度の誤差は、経緯度の精度保証によって
$10^{-5}$ \[m\] 以下となります（と思います）。

```pycon
>>> point = Point(36.10377479, 140.087855041, 2.34)
>>> tf.backward_safe(*tf.forward(*point))
Point(latitude=36.10377479, longitude=140.087855041, altitude=2.3399999999970085)
```

上記の例（ `SemiDyna2023.par`）では、経緯度の誤差がありません。

もし、その様な解を見つけられなかった場合、
{py:meth}`.Transformer.backward_safe` は
{py:class}`~JGDtrans.NotConvergeError` を送出します。私が `TKY2JGD.par` 、
`touhokutaiheiyouoki2011.par` 、 `pos2jgd_202307_ITRF2014.par`
を用いて数値的に検証した限りでは、必ずその様な解が見つかっていますので、多くの場合で問題なく動作すると思います。

TKY2JGD や PathJGD の高度や PatchJGD(H) や HyokoRev
の経緯度のように、パタメータが 0.0 の場合、その成分上の変換は（順逆ともに）恒等変換になります。つぎは
TKY2JGD の例です。

```pycon
>>> tf.forward(36.10377479, 140.087855041, 2.34)
Point(latitude=36.106966279935016, longitude=140.08457686562787, altitude=2.34)
```

{py:class}`.Transformer` は、DMS 形式（60 進度）による I/O もサポートしています。

{py:class}`~JGDtrans.Point` には DMS 形式をあつかうためのメソッドがあります。
{py:meth}`.Point.from_dms` は DMS 形式によるコンストラクタで、
{py:meth}`.Point.to_dms` は {py:class}`~JGDtrans.Point` オブジェクトを DMS 形式に変換します。

```pycon
>>> Point.from_dms("360613.58925", "1400516.27815", 2.34)
Point(36.10377479166667, 140.08785504166664, 2.34)
>>> Point(36.10377479166667, 140.08785504166664, 2.34).to_dms()
("360613.58925", "1400516.27815", 2.34)
```

{py:meth}`.Point.to_dms` の戻り値は
{py:obj}`tuple[str, str float]` であり {py:class}`~JGDtrans.Point` ではないことに注意してください。

これらを組み合わせることで、DMS 形式による {py:class}`.Transformer` の I/O が可能です。

```pycon
>>> point = Point.from_dms("360613.58925", "1400516.27815", 2.34)
>>> tf.forward(*point).to_dms()
("360613.58286751213", "1400516.293278404", 2.4363138577557226)
```

## メッシュに関連する実装の導入

{py:mod}`JGDtrans` を利用するにあたり、この章を読む必要はありません。

この章では、メッシュに関連する実装の理解を助けるために、各用語の定義とその実装との関連を説明します。
各実装は {py:mod}`.mesh` モジュールに公開されています。
ここでの用語は本実装に固有であり、オリジナルを含む他実装と関連はありません（meshcode を除く）。

パラメータは、日本周辺で定義された正方格子の上に定義されています。この正方格子のことをメッシュ（_mesh_）と呼びます。格子の座標系のことを
_mech coordinate_ 、格子点のことを _mesh node_ （もしくは _node_）と呼びます。それぞれ {py:class}`.MeshCoord` と
{py:class}`.MeshNode` として実装しています。
mesh node には、対応するある非負整数が存在し、それをメッシュコード（_meshcode_）と呼びます。経緯度高度の各パラメータは、メッシュコードによって、
mesh node に紐づけられます。特に par ファイルでは、そのように紐づけられています。  

メッシュは、格子間隔がおよそ 1 \[km\] のメッシュと、 5 \[km\]
のメッシュの 2 種類が存在します。格子間隔のことを _mesh unit_ （もしくは _unit_）と呼び、 
{py:obj}`1` ならびに {py:obj}`5` リテラルで表現しています。

Mesh coordinate （{py:class}`.MeshCoord`）は unit {py:obj}`1` の座標系として実装しています。
unit {py:obj}`5` の座標系は、簡単のために、５つ飛びの unit {py:obj}`1` の座標系として実装しています。したがって、５つ飛びでない node は、
unit {py:obj}`5` の時に扱うことができません。例えば、
node だけでは unit を決定できないので、 node から cell （すぐあとで説明します）の解決では、ユーザーが明示的に unit を指定しなければなりません。

変換の補正を計算するには、その unit における単位胞が必要です。単位胞 のことを _mesh cell_（もしくは _cell_ ）と呼び、
{py:class}`.MeshCell` として実装しています。

{py:class}`~JGDtrans.Point` にも関連するメソッドが存在します。
