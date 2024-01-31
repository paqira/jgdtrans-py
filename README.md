# JGDtrans

Unofficial Python impl. of coordinate transformer by _Gridded Correction Parameter_
which Geospatial Information Authority of Japan (GIAJ, formerly GSIJ) distributing.

国土地理院が公開しているパラメータファイル（par ファイル）による座標変換（順逆変換）の非公式な実装です。

Features:

- Supports offline transformation (no web API)
  - オフライン変換（web API 不使用）
- Supports both original forward and backward transformation
  - 順変換と逆変換の両方をサポート
- Supports verified backward transformation
  - 精度を保証した逆変換のサポート
- Supports all TKY2JGD, PatchJGD and PatchJGD(H), HyokoRev, SemiDynaEXE, geonetF3 and ITRF2014 (POS2JGD)
  e.g. Tokyo Datum to JGD2000 (EPSG:4301 to EPSG:4612) and JGD2000 to JGD2011 (EPSG:4612 to EPSG:6668)
  - 上記の全てをサポート
- Clean implementation
  - 保守が容易な実装

## Usage

You can install `JGDtrans` from PyPI:

```sh
pip install JGDtrans
```

`JGDtrans` depends on `typing-extensions` only, and requires `python>=3.9`.

This package does not contain parameter files, download it from GIAJ.

このパッケージはパラメータファイルを提供しません。公式サイトよりダウンロードしてください。

Sample code:

```python
import JGDtrans

with open('SemiDyna2023.par') as fp:
    tf = JGDtrans.load(fp, format="SemiDynaEXE")

# Geospatial Information Authority of Japan
origin = (36.10377479, 140.087855041)

# forward transformation
result = tf.forward(*origin)
# prints Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578102994)
print(result)

# backward transformation
point = tf.backward(*result)
# prints Point(latitude=36.10377479000002, longitude=140.087855041, altitude=-4.217551585750101e-10)
print(point)

# verified backward transformation
q = tf.backward_safe(*result)
# prints Point(latitude=36.10377479, longitude=140.087855041, altitude=2.3399999999970085)
print(q)
```

## Licence

MIT

## Reference

1. Geospatial Information Authority of Japan (GIAJ, 国土地理院):
   <https://www.gsi.go.jp/>,
   (English) <https://www.gsi.go.jp/ENGLISH/>.
2. _TKY2JGD for Windows Ver.1.3.79_ (reference implementation):
   <https://www.gsi.go.jp/sokuchikijun/tky2jgd_download.html> 
   released under [国土地理院コンテンツ利用規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)
   which compatible to CC BY 4.0.
3. Rust implementation: <https://github.com/paqira/jgdtrans-rs>.
