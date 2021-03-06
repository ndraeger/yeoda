========
Examples
========

The following examples shall help to understand what the package is able to accomplish
and how you can use the interface *yeoda* offers to access and play around with your data.


Contents
========

.. contents:: Table of contents
   :depth: 2

.. _dc_setup:

Setting up a data cube
======================
In simple words, *yeoda* is a filename based data cube tool, which means that it tries to interpret the data structure via the filename.
In the future it will be also possible to create a data cube based on metadata or dataset attributes. To define a filenaming convention,
*geopathfinder* can be used. Each (existing) filenaming convention has a ``create_[naming_convention]_filename(...)`` function to create a Python object,
which can be handled like a dictionary to access parts of the filename.

First, to setup a data cube, you need to prepare some input attributes:

   - A list of filepaths with the same extension (``filepaths``). Currently GeoTIFF and NetCDF files are supported as default by *veranda*.

   - A list of dimensions you want you work with. The dimension names relate to the keys defined by filenaming convention, e.g.: ``dimensions = ['time', 'var_name', 'pol']``

   - A function to create a Python object/class instance representing a filenaming convention, e.g.: ``smart_filename_creator = create_sgrt_filename``

   - A grid/tiled projection system, which is a class instance of ``pytileproj.base.TiledProjection`` being inherited to a grid package, e.g. *Equi7Grid*: ``grid = Equi7Grid(10).EU``

You can then initiate a data cube object with the ``EODataCube`` class:

.. code-block:: python

   dc = EODataCube(filepaths=filepaths, smart_filename_creator=smart_filename_creator,
                   dimensions=dimensions, grid=grid)

We have also prepared some higher-level data cubes, especially designed to work with (backscatter) products generated by the research group Remote Sensing of the GEO Department at TU Wien (TUWGEO).
To work with preprocessed data you can use the classes ``SIG0DataCube`` for sigma nought and ``GMRDataCube`` for radiometric terrain flattened gamma nought data.
On the value-added data side, ``SSMDataCube`` allows you to access the TUWGEO SSM data.

.. _dc_ops:

Data cube operations
====================
Now we can use our initialised data cubes to work with our data.
*yeoda* uses a *GeoPandas* dataframe to store the filename and geometry information internally.
On top of that, data cube functions where defined to filter, split, sort, align, etc. the data.
It has to be noted that most functions have a keyword argument ``in_place``.
If it is set to true, the original object will be overwritten.
If not, a new data cube object will be returned.
In the next sections some of these functions will be shortly described.

Renaming a dimension
--------------------
If you have to work with a pre-defined naming convention in *geopathfinder* (e.g. the SGRT naming convention)
and if you do not agree with the naming of the filename parts/dimensions, you can still rename dimensions afterwards:

.. code-block:: python

   dimensions_map = {'tile_name': 'tile'}
   dc.rename_dimension(dimensions_map, in_place=True)

In the example above, the dimension "tile_name" was renamed to "tile".

Adding a dimension
------------------
You can simply add new filepath-dependent values (e.g. file size, cloud coverage, ...) along a new dimension (e.g. named "new_dimension")
with a few lines of code:

.. code-block:: python

   values = ... # list containing values equal to len(dc)
   dc.add_dimension("new_dimension", values, in_place=True)

Sorting along a dimension
-------------------------
Sorting along a dimension can be accomplished with:

.. code-block:: python

   dc.sort_by_dimension('time', ascending=True, in_place=True)

All rows with respect to the values along "time" are now sorted in ascending order.

Filter by metadata
------------------
If you have stored metadata attributes in you NetCDF or GeoTIFF files, you can also filter the data cube by certain attributes.

.. code-block:: python

   metadata = {'creator': 'me'}
   dc.filter_by_metadata(metadata, in_place=True)

After executing the code above, ``dc`` only stores file where a metadata attribute "creator" is equal to "me".

Filter by dimension
-------------------
A very important function is ``filter_by_dimension``, which accepts a list of values and expressions to filter the data along a dimension.
``expressions`` is a list having the same length as ``values`` and includes mathematical comparison operators, i.e. "==", "<=", ">=", "<", ">" ("==" is default).
Some examples are:

.. code-block:: python

   values = ['VV']
   dc.filter_by_dimension(self, values, name="pol", in_place=True)

The command above would limit the data cube to only store entries where the dimension 'pol' contains 'VV' values.
Next, we could also filter by time ranges, i.e. to only allow values between 01-01-2016 and 01-02-2016:

.. code-block:: python

   from datetime import datetime
   start_time = datetime.strptime('01-01-2016', '%Y-%m-%d')
   end_time = datetime.strptime('01-02-2016', '%Y-%m-%d')
   values = [(start_time, end_time)]
   expressions = [('>=', '<=')]
   dc.filter_by_dimension(self, values, expressions=expressions, name="pol", in_place=True)

Spatial filtering with tile names
---------------------------------
This function is just a wrapper around ``filter_by_dimension`` to steer spatial filtering by tile names, ideally defined by a grid.
If ``use_grid`` is True, the requested tile names are cross-checked versus available tiles defined by the grid.
The statement below filters for two Equi7 grid tiles at 10m covering Austria.

.. code-block:: python

   tilenames = ["E048N015T1", "E052N016T1"]
   dc.filter_spatially_by_tilename(tilenames, dimension_name="tile", in_place=True, use_grid=True)

.. _sfilterGeom:

Spatial filtering with a geometry
---------------------------------
Works very similar as ``filter_spatially_by_tilename``, but this time you can filter by an arbitrary geometry, e.g.
a Shapely geometry, and OGR geometry or a list of bounding box coordinates.

.. code-block:: python

   import osr
   bbox = [(4.36, 43.44), (6.48, 45.80)]  # [(x_min, y_min), (x_max, y_max)]
   sref = osr.SpatialReference()
   sref.ImportFromEPSG(4326)  # LonLat spatial reference system
   dc.filter_spatially_by_geom(geom, sref=sref, dimension_name="tile", in_place=True)

Split by dimension
------------------
``split_by_dimension`` works very similar to ``filter_by_dimension``, but now all filtered values are also split up into new data cubes:

.. code-block:: python

       values = ['VV', 'VH']
       dc_vv, dc_vh = dc.split_by_dimension(self, values, name="pol")

where ``dc_vv`` is now a data cube only containing VV data and ``dc_vh`` a data cube only containing VH.

Yearly split
------------
If you want to analyse your data under certain temporal aspects, in this case in a yearly manner, you can split up the original data cube into
smaller yearly data cubes (if the data covers more than a year):

.. code-block:: python

   yearly_dcs = dc.split_yearly(name='time')

where ``name`` is the name of the temporal dimension. If need be, you can also use the keyword argument ``years`` to
select specific years of interest.

Monthly split
-------------
``split_monthly`` works the same as ``split_yearly``, but this time monthly data cubes are returned:

.. code-block:: python

   monthly_dcs = dc.split_monthly(name='time')

Union
-----
If you have two data cubes and you want to unite their information, you can simply do:

.. code-block:: python

   dc_1 = ...  # initialise first data cube
   dc_2 = ...  # initialise second data cube
   dc_united = dc_1.unite(dc_2)

``dc_united`` has all columns/dimensions from ``dc_1`` and ``dc_2`` and gaps are filled with NaN.

Intersection
------------
You can also intersect two data cubes to get their common set of dimensions:

.. code-block:: python

   dc_1 = ...  # initialise first data cube
   dc_2 = ...  # initialise second data cube
   dc_intersected = dc_1.intersect(dc_2)

If you want to intersect them along a dimension, i.e. to only keep common dimension values, you can use the keyword argument ``on_dimension``:

.. code-block:: python

   dc_1 = ...  # initialise first data cube
   dc_2 = ...  # initialise second data cube
   dc_intersected = dc_1.intersect(dc_2, on_dimension='time')

Alignment
---------
Another very import set operation is the ``align_dimension`` method. It allows to align a data cube with respect to a second data cube along a dimension (``name``).
In other words, the order and the length of the dimension will then be the same.
This also means that data cube entries are duplicated if they appear more often in the second data cube.

.. code-block:: python

   dc_1 = ...  # initialise first data cube
   dc_2 = ...  # initialise second data cube
   name = "time"
   dc_aligned = dc_1.align_dimension(dc_2, name)

.. _dc_load:

Loading data
============
This section is dedicated on loading the data, where currently three functions can be used to do so. All functions have a common set of keyword arguments, where the most important ones are discussed here:

   - ``band``: This argument specifies the band name as a string.

   - ``dtype``: There are many different types of Python data structure to store array-like data and their selection mainly depends on what you want to do with the loaded data later on. *yeoda* offers to use three of them:

      - xarray.DataSet ("xarray")
      - numpy.ndarray ("numpy")
      - pandas.DataFrame ("dataframe")

   - ``origin``: Depending on the chosen return data type, ``origin`` defines the origin of the pixel coordinates in the world system. The origin can be one of the following:

      - upper left ("ul")
      - upper right ("ur", default)
      - lower right ("lr")
      - lower left ("ll")
      - center ("c")

Loading data by coordinates
---------------------------
The first function is ``load_by_coords``, which accepts a list of x and a list of y (world system) coordinates as input.
If the spatial reference of the coordinates is not equal to the data, you need to specify the spatial reference keyword argument ``sref``.

.. code-block:: python

   xs = ... # list of world system x coordinates (in this case the same system as dc)
   ys = ... # list of world system y coordinates (in this case the same system as dc)
   data = dc.load_by_coords(xs, ys, band='1', dtype="xarray", origin="ur")

``data`` is an xarray with a data variable "1" and three dimensions time, x, y, where all spatial coordinates refer to the upper right pixel origin.

Loading data by pixels
----------------------
``load_by_pixels`` expects pixel coordinates given by a list of row and column indexes. The keyword arguments
``row_size`` and ``col_size`` allow you to define a window, where the specified ranges count from left to right (columns) and
from top to bottom (rows) starting at the given row and column coordinates.

.. code-block:: python

   rows = ... # list of row indexes
   cols = ... # list of column indexes
   row_size = 10
   col_size = 10
   data = dc.load_by_pixels(self, rows, cols, row_size=row_size, col_size=col_size, dtype="numpy")

``data`` is now a 3D NumPy array.

Loading data by geometries
--------------------------
Relying on the same geometry types as described in `Spatial filtering with a geometry`_, you can also load data for a region defined by an arbitrary geometry.
Geometries do not need to be axis-parallel, so additional data has to be loaded to follow an array-like structure.
If one is not interested in values outside the region of interest, it is possible to set the keyword parameter ``apply_mask`` to true.

.. code-block:: python

   geom = ... # geometry residing in the same reference system as the data cube
   data = dc.load_by_geom(geom, band='1', apply_mask=True, dtype="xarray", origin='c')

``data`` is an xarray with a data variable "1" and three dimensions time, x, y, where all spatial coordinates refer to the center pixel origin.
``data['1'].data``, the array or actual data stored, is a masked numpy array (``numpy.ma``).
It still contains all information, but has a mask allowing to mask pixels outside the geometry.