# Implementation Note

ここでは、オリジナルの実装の基づく、
変換方法の解説と精度保証逆変換の解説および実装記録です。

## Formal Definition of Transformation

ここでは変換方法を導入します。

オリジナル実装の座標変換は、線形変換になっています。
（補正量が十分に小さいと仮定しているのだと思います）
つまり、順変換前の点を $p$、変換後の点を $p'$ とした時、順変換と逆変換はそれぞれ次の式で表現されます。

$$\begin{align}
p' &= p + C(p) \,,&
p &= p' + C'(p') \,.
\end{align}$$

順変換の補正量 $C(p)$ や逆変換の補正量 $C'(p')$ は経緯度にのみ依存し、
高度には依存しません。すなわち、補正関数 $C$ と $C'$ はどちらも
$\mathbf{R}^2 \rightarrow \mathbf{R}^3$ なる関数です。

前述の逆変換は exact ですが、オリジナル実装の逆変換は exact ではなく、近似になっています。
すなわち、オリジナルの逆変換の補正量 $\tilde C '(p')$ は、 
$q = p' - (12 / 3600, -12 / 3600, 0)$ そして $q' = p' - C(q)$ とした時に、

$$\begin{align}
\tilde C '(p') &:= - C(q') \,,
\end{align}$$

となっています（念の為 $q'$ は $p'$ に依存しています）。
値 $12 / 3600$ は、XXXの コメントから推測するに、おそらく TKY2JGD のパラメータの経緯度毎の平均値です。
（正確には、経度で約 $10.8 / 3600$ 、緯度で約 $-11.2 / 3600$ です）。

## Correction Function

逆変換は順変換の補正関数 $C$ で定義されており、
順変換の補正関数 $C$ が定義できてば、逆変換も可能です。
そして、この補正関数 $C$ 双線形補完になっています。 

$$\begin{align}
C(p) &:= a_{\text{sw}} (1 - x_p) (1 - y_p)
+ a_{\text{se}} x_p (1 - y_p)
+ a_{\text{nw}} (1 - x_p) y_p
+ a_{\text{ne}} x_p y_p \,,
\end{align}$$

$a_i$ where $i=\text{sw},\text{se},\text{nw}$ and $\text{ne}$
は各ノードの変換パラメータ、
$x_p$, $y_p$ は、 点 $p$ の mesh cell における座標 $(x_p, y_p)$ です。

この章では、それぞれの導出を説明します。

### Introduction of Mesh

ここでは mesh cell を導入します。

座標変換対象地域に、経緯度にそって正方格子を導入します。
この時、格子間隔を、経度方向には XXX 度、緯度方向には経度方向の 1.5 倍の YYY 度とします。
また、原点は 経緯度 0 度の点とします。
この様な格子を選ぶことで、格子間隔が、日本周辺でおよそ 1 [km] となります。
パラメータによっては 5 倍の格子間隔を持つ格子上に定義されます、つまり単位格子が 5 [km] 四方となるものです。
その時は、前述の格子から ５つとびの格子点からなる格子として定義します。

本実装では、以下のような呼び名を与え、実装しています。

| Formal Name          | Our Name         | Implementation              | 
|----------------------|------------------|-----------------------------|
| Lattice              | Mesh             | --                          |
| Lattice constant     | Mesh Unit (unit) | {py:obj}`1` and {py:obj}`5` |
| (Lattice) Coordinate | Mesh Coordinate  | {py:class}`MeshCoord`       |
| (Lattice) Node       | Mesh Node (node) | {py:class}`MeshNode`        |
| Unit Cell            | Mesh Cell (cell) | {py:class}`MeshCell`        |

Mesh node には、対応する非負整数が存在します。
これを meshcode と呼びます。
パラメータは、対象地域の格子点毎に緯度高度の 3 成分存在しますが、
meshcode を用いて mesh node と紐づけられています。

```text
 North/latitude
   ^
   |           |
   |           |
---+-----------+----
   |           |
   |           |
  ^| mesh cell |
yp||           |
  ||           |
---+-----------+----> East/longitude
   |------>    |
      xp
```

補正関数の計算に必要は値は、mesh cell を定める必要が有ります。

変換地点を含む mesh cell を解決します。

本実装では、変換前の地点の最近の南西のメッシュノードを解決し、
そのメッシュノードを南西の node とするような（最小の）メッシュセルを解決する方法で実装しています。

### パラメータの解決

mesh cell を構成する各 node に紐づくパラメータが、補正関数で用いるパラメータになります。

具体的には、経緯度高度それぞれについて、以下のように対応します。

|     Symbol      | Node of Cell    |
|:---------------:|-----------------|
| $a_{\text{sw}}$ | south-west node |
| $a_{\text{se}}$ | south-east node |
| $a_{\text{nw}}$ | north-west node |
| $a_{\text{ne}}$ | north-east node |

$a_i$ where $i=\text{sw},\text{se},\text{nw}$ and $\text{ne}$ は
補正関数に現れるパラメータです。

### mesh cell 内座標の計算

mesh cell の 1辺の長さが 1 となるような、
mesh cell の南東を原点として、南東の node が $(1,0)$、北西の node が $(0, 1)$
となるような単位格子で正規化された座標系 $x, y$ を定義します。

この座標系の上の $p$ の position が $(x_p, y_p)$ です。


## Verified Transformation

ここでは、精度保証逆変換の説明をします。

前述のように逆変換は厳密ではありません。
また、厳密解との誤差を保証できません。

そこで、本実装の XXX では、ニュートン法を用いて、
厳密解との誤差をパラメータの誤差以下である 2.5e-9 以下に抑えています。

User Guid にある例では、経度緯度の誤差は IEEE binary64 で
0 となっています（およそ 15 桁程度の精度）。

本方法でも一般には精度を保証できません。
しかし、以下３ファイルで数値的に検証した限りでは、 精度が保証されていることを確認しました。
 
- `TKY2JGD.par`.
- `touhokutaiheiyouoki2011.par`
- `pos2jgd_202307_ITRF2014.par`

実用的なケースではおそらく問題なく精度保証ができていると思います。
