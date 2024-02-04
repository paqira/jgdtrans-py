```{eval-rst}
.. toctree::
    :hidden:
    :maxdepth: 2
    :glob:
    :caption: Documents:
    
    docs/user_guide
    docs/user_guide.ja
    docs/sample.ipynb
```

```{eval-rst}
.. toctree::
    :hidden:
    :maxdepth: 2
    :glob:
    :caption: API Reference:
    
    autodoc/JGDtrans
```

# JGDtrans

Coordinate Transformer by _Gridded Correction Parameter_
which Geospatial Information Authority of Japan (GIAJ, formerly GSIJ) distributing [^1].

国土地理院が公開しているパラメータファイル（par ファイル）による座標変換（順逆変換）を提供します。

Features:

- Supports offline transformation (no web API)
- Supports both original forward and backward transformation
- Supports verified backward transformation
- Supports all TKY2JGD [^2], PatchJGD and PatchJGD(H) [^3],
  HyokoRev [^4], SemiDynaEXE [^5], geonetF3 and ITRF2014 (POS2JGD) [^6]
  - For example, Tokyo Datum to JGD2000 (EPSG:4301 to EPSG:4612)
  - and JGD2000 to JGD2011 (EPSG:4612 to EPSG:6668)
- Clean implementation

Example:

```python
import JGDtrans

with open('SemiDyna2023.par') as fp:
    tf = JGDtrans.load(fp, format="SemiDynaEXE")

# Geospatial Information Authority of Japan
origin = (36.10377479, 140.087855041, 2.34)

# forward transformation
result = tf.forward(*origin)
# prints Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)
print(result)

# backward transformation
p = tf.backward(*result)
# prints Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.339999999578243)
print(p)

# verified backward transformation
q = tf.backward_safe(*result)
# prints Point(latitude=36.10377479, longitude=140.087855041, altitude=2.3399999999970085)
print(q)
```

This package does not contain parameter files, the GIAJ distributes such files [^7].

このパッケージはパラメータファイルを提供しません。公式サイトよりダウンロードしてください [^7]。

We use _TKY2JGD for Windows Ver.1.3.79_ [^8] as a reference.

[^1]: Geospatial Information Authority of Japan (GIAJ, 国土地理院): <https://www.gsi.go.jp/>,
      (English) <https://www.gsi.go.jp/ENGLISH/>.
[^2]: TKY2JGD: <https://www.gsi.go.jp/sokuchikijun/tky2jgd.html>.
[^3]: PatchJGD and PatchJGD(H): <https://vldb.gsi.go.jp/sokuchi/surveycalc/patchjgd/index.html>.
[^4]: HyokoRev: <https://vldb.gsi.go.jp/sokuchi/surveycalc/hyokorev/hyokorev.html>
[^5]: SemiDynaEXE: <https://vldb.gsi.go.jp/sokuchi/surveycalc/semidyna/web/index.html>.
[^6]: geonetF3 and ITRF2014: <https://positions.gsi.go.jp/cdcs/>.
[^7]: TKY2JGD: <https://www.gsi.go.jp/sokuchikijun/tky2jgd_download.html>;
      PatchJGD, PatchJGD(H) and HyokoRev: <https://www.gsi.go.jp/sokuchikijun/sokuchikijun41012.html>;
      SemiDynaEXE: <https://www.gsi.go.jp/sokuchikijun/semidyna.html>;
      geonetF3 and ITRF2014 (POS2JGD): <https://positions.gsi.go.jp/cdcs/>.
[^8]: TKY2JGD for Windows Ver.1.3.79 (reference implementation):
      <https://www.gsi.go.jp/sokuchikijun/tky2jgd_download.html> 
      released under [国土地理院コンテンツ利用規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)
      which compatible to CC BY 4.0.
[^9]: Rust implementation: <https://github.com/paqira/jgdtrans-rs>.

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
