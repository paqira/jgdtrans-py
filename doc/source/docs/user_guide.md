# User Guide

In this section, we briefly explain usages of {py:mod}`jgdtrans`.
See [API Reference](../autodoc/package.rst) for detail.

## Install

You can install {py:mod}`jgdtrans` from PyPI:

```shell
pip install jgdtrans
```

This package depends on [`typing-extensions`][typing-extensions] only, and requires Python `>=3.9`.

[typing-extensions]: https://pypi.org/project/typing-extensions/

## Deserialize par File

{py:mod}`jgdtrans` supports deserialization of all kind of _Gridded Correction Parameter_ file
(we call it as _par file_ after its file extension)
which distributed by the [GIAJ] as of late 2023, such as
[TKY2JGD], [PatchJGD], [PatchJGD(H)], [HyokoRev], [SemiDynaEXE] and [POS2JGD] (geonetF3 and ITRF2014).
In this section, we show how to load par file,
and serialize and deserialize {py:class}`.Transformer` obj.

[GIAJ]: https://www.gsi.go.jp/ENGLISH/

[TKY2JGD]: https://www.gsi.go.jp/sokuchikijun/tky2jgd.html

[PatchJGD]: https://vldb.gsi.go.jp/sokuchi/surveycalc/patchjgd/index.html

[PatchJGD(H)]: https://vldb.gsi.go.jp/sokuchi/surveycalc/patchjgd_h/index.html

[HyokoRev]: https://vldb.gsi.go.jp/sokuchi/surveycalc/hyokorev/hyokorev.html

[SemiDynaEXE]: https://vldb.gsi.go.jp/sokuchi/surveycalc/semidyna/web/index.html

[POS2JGD]: https://positions.gsi.go.jp/cdcs

We note that none of par files are included in this package,
download them from GIAJ [^1].

[^1]: Download links;
TKY2JGD: <https://www.gsi.go.jp/sokuchikijun/tky2jgd_download.html>;
PatchJGD, PatchJGD(H) and HyokoRev: <https://www.gsi.go.jp/sokuchikijun/sokuchikijun41012.html>;
SemiDynaEXE: <https://www.gsi.go.jp/sokuchikijun/semidyna.html>;
geonetF3 and ITRF2014 (POS2JGD): <https://positions.gsi.go.jp/cdcs/>.

{py:mod}`jgdtrans` defines read/load API of par file
{py:func}`~jgdtrans.load` and {py:func}`~jgdtrans.loads`
which return a {py:class}`.Transformer` obj.
It uses `format` argument to specify the format of the par file;

```pycon
>>> import jgdtrans
>>> with open('SemiDyna2023.par') as fp:
...     tf = jgdtrans.load(fp, format='SemiDynaEXE')
>>> tf
Transformer(unit=5, parameter=<dict (21134 length) at 0x123456789>, description='for [...]')
```

It can access to header, format and parameter by
{py:attr}`.Transformer.description`,
{py:attr}`.Transformer.format` and
{py:attr}`.Transformer.parameter`
respectively.

```pycon
>>> tf.description
'for SemiDynaEXE    Ver.1.0.0\n[...]\nMeshCode dB(sec)  dL(sec) dH(m)'
>>> tf.format
'SemiDynaEXE'
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

The entry of {py:attr}`.Transformer.parameter`
represents one line of par file's parameter section,
its key is _meshcode_ and the key value is a {py:class}`.Parameter` obj.

We note that it fills by {py:obj}`0.0` for altitude of TKY2JGD and PathJGD,
and for latitude and longitude of PatchJGD(H) and HyokoRev;

```pycon
>>> with open('TKY2JGD.par') as fp:
...     tf = jgdtrans.load(fp, format='TKY2JGD')
>>> tf.parameter[46303582]
Parameter(latitude=12.79799, longitude=-8.13354, altitude=0.0)
```

This does not break coordinate transformation, because
it becomes the identity transformation
on the components whose parameter is zero.

{py:meth}`.Transformer.to_dict`
converts the {py:class}`.Transformer` (namely, contents of par file) to {py:obj}`dict` obj;

```pycon
>>> tf.to_dict()
{
    'description': 'for SemiDynaEXE    Ver.1.0.0\n[...]\nMeshCode dB(sec)  dL(sec) dH(m)',
    'format': 'SemiDynaEXE',
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

and {py:func}`.from_dict` is a constructor of {py:class}`.Transformer`
from the {py:obj}`dict` obj shown above;

```pycon
>>> data = {
...     'description': 'my SemiDynaEXE',
...     'format': 'SemiDynaEXE',
...     'parameter': {
...         36230600: {
...             'latitude': -0.05475,
...             'longitude': 0.04,
...             'altitude': 0.07721,
...         },
...     # and go on
...     },
... }
>>> jgdtrans.from_dict(data)
Transformer(unit=5, parameter=<dict (21134 length) at 0x987654321>, description='my [...]')
```

Hence, it can convert data of par file to/from python {py:obj}`dict` or other serialization format (e.g. JSON).

## Coordinate Transformation

In this section, we describe how perform coordinate transformation
with {py:class}`.Transformer` obj.

{py:meth}`.Transformer.forward` performs forward transformation,
and {py:meth}`.Transformer.backward` does backward transformation.
These return more precise results than the GIAJ web app/API.

```pycon
>>> tf.forward(36.10377479, 140.087855041, 2.34)
Point(latitude=36.103773017086695, longitude=140.08785924333452, altitude=2.4363138578103)
>>> tf.backward(36.103773017086695, 140.08785924333452, 2.4363138578103)
Point(latitude=36.10377479, longitude=140.087855041, altitude=2.34)
```

The return value is {py:class}`~jgdtrans.Point` obj.
It can access by the attribute to the resulting values, latitude, longitude and altitude;

```pycon
>>> point = tf.forward(36.10377479, 140.087855041, 2.34)
>>> point.latitude
36.103773017086695
>>> point.longitude
140.08785924333452
>>> point.altitude
2.4363138578103
```

It is unpackable because {py:class}`~jgdtrans.Point` is
{py:obj}`Sequence[flaot]` with length 3;

```pycon
>>> origin = Point(36.10377479, 140.087855041, 2.34)
>>> result = tf.forward(*origin)
>>> tf.backward(*result)
Point(latitude=36.10377479000002, longitude=140.087855041, altitude=2.34)
```

There is {py:meth}`.Transformer.transform`
which switches forward/backward transformation
depending on the {py:obj}`backward` argument.
That is, the following identities hold,
for all {py:obj}`point` which is {py:class}`~jgdtrans.Point` obj,
such that;

```pycon
>>> tf.transform(*point, backward=False) == tf.forward(*point)
True
>>> tf.transform(*point, backward=True) == tf.backward(*point)
True
```

We note that {py:meth}`.Transformer.backward` is _not_ exact,
but {py:meth}`.Transformer.backward` ensures that the error from exact solution is
suppressed by {py:attr}`.Transformer.ERROR_MAX`.
That is, the error from exact solution is less than $10^{-9}$ \[deg\],
which is error of GIAJ latitude and longitude parameter [^10].
This implies that altitude's error is less than $10^{-5}$ \[m\],
which is error of the GIAJ altitude parameter.

{py:meth}`.Transformer.backward` is not compatible to
GIAJ web service/APIs. We provide a compatible backward transformation by
{py:meth}`.Transformer.backward_compat`.

If the parameters are zero, e.g. altitude of TKY2JGD and PathJGD,
and latitude and longitude of PathJGD(H) and HyokoRev,
it becomes the identity transformation on such components.
We show an example of `TKY2JGD.par`.

```pycon
>>> tf.forward(36.10377479, 140.087855041, 2.34)
Point(latitude=36.106966279935016, longitude=140.08457686562787, altitude=2.34)
```

It supports DMS notation (sexadecimal degree) for {py:class}`.Transformer` I/O
in addition to DD notation (decimal degree) .

{py:class}`~jgdtrans.Point` has methods handling DMS notation,
{py:meth}`.Point.from_dms` is a constructor from DMS notation
and {py:meth}`.Point.to_dms` returns {py:obj}`self` in DMS notation;

```pycon
>>> Point.from_dms("360613.58925", "1400516.27815", 2.34)
Point(36.10377479166667, 140.08785504166664, 2.34)
>>> Point(36.10377479166667, 140.08785504166664, 2.34).to_dms()
("360613.58925", "1400516.27815", 2.34)
```

We note that {py:meth}`.Point.to_dms` returns
{py:obj}`tuple[str, str, float]`, not {py:class}`~jgdtrans.Point`.

By combining these, it can use DMS notation for I/O of {py:class}`.Transformer`,
for example,

```pycon
>>> point = Point.from_dms("360613.58925", "1400516.27815", 2.34)
>>> tf.forward(*point).to_dms()
("360613.58286751213", "1400516.293278404", 2.4363138577557226)
```

## Brief Introduction of Mesh-related Implementation

In this section, we briefly provide definitions of terms and corresponding to implementations
to help you understand the mesh-related implementations.
Please skip this section if you just want to use {py:mod}`jgdtrans`.

The following terms, except for meshcode, are specific to our implementation
and do not correspond to any other implementation, including official ones.

The {py:mod}`.mesh` module defines such API.

The transformation parameter is defined on the square lattice,
called as _mesh_, which defined on near Japan.
We call lattice coordinate as _mesh coordinate_
and lattice node as _mesh node_.
They are implemented as {py:class}`.MeshCoord`
and {py:class}`.MeshNode` respectively.
There is one-to-one correspondence, node to specific non-negative integer.
The corresponding integer is called _meshcode_.
The parameters of latitude, latitude, and altitude are linked to each node
by meshcode.
Such mappings can be found in par files.

It is known that there is two kind of mesh,
the approx. 1 \[km\] lattice constant and the approx. 5 \[km\] lattice constant.
We call lattice constant as _mesh unit_ or _unit_ shortly,
and use {py:obj}`1` and {py:obj}`5` literals as unit.

The mesh coordinate, {py:class}`.MeshCoord`,
is implemented for mesh with unit {py:obj}`1`,
and we implement the unit {py:obj}`5` coordinate system
by the unit {py:obj}`1` one with every fifth node for simplicity.
Therefore, it cannot handle a node which is not every fifth node
if the unit is {py:obj}`5`.
For example, user must specify the unit explicitly when resolving mesh cell
(we describe below) from mesh node,
because it cannot determine unit from node.

Calculating transformation correction requires a unit cell in the unit
called _mesh cell_ or _cell_ shortly.
We implement it as {py:class}`.MeshCell`.

{py:class}`~jgdtrans.Point` has several corresponding methods which helps
to handle mesh.
