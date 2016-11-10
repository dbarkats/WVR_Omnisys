#!/usr/bin/env python
#
"""
This set of libraries, plotUtils.py, is a collection of often useful
python functions for plotting.  It is an open package for anyone
on the science team to add to and generalize (and commit).  
Please use the same practices as in analysisUtils:

1) Write the routines as generally as you can.

2) Before fundamentally changing the default behavior of a function
or class, consider your coworkers.  Do not modify the default behavior
without extreme need and warning.  If you need to modify it quickly,
consider a separate version until the versions can be blended (but please
do try to do the blending!).

3) There is a comment structure within the routines.  Please keep this
for additions because the documentation is automatically generated from
these comments.
 
All examples assume you have imported the library to pu, as import
plotUtils as pu. You can of course do whatever you like, but the
examples will thus have to be modified.

Thanks and good luck!  If you have any questions, bother Denis or Nicole 
Nicole Larsen, 20161013
"""

import os
import sys
from pylab import *

        
#from matplotlib.externals import six
import six
#from matplotlib.externals.six.moves import reduce, xrange, zip, zip_longest
from six.moves import reduce, xrange, zip, zip_longest

import math
import warnings

import numpy as np
from numpy import ma

import matplotlib
#from matplotlib import unpack_labeled_data

#import maptlotlib.pyplot as plt
import matplotlib.cbook as cbook
from matplotlib.cbook import (mplDeprecation, iterable, is_string_like)
import matplotlib.collections as mcoll
import matplotlib.colors as mcolors
import matplotlib.contour as mcontour
import matplotlib.dates as _  # <-registers a date unit converter
from matplotlib import docstring
import matplotlib.image as mimage
import matplotlib.legend as mlegend
import matplotlib.lines as mlines
import matplotlib.markers as mmarkers
import matplotlib.mlab as mlab
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.quiver as mquiver
import matplotlib.stackplot as mstack
import matplotlib.streamplot as mstream
import matplotlib.table as mtable
import matplotlib.text as mtext
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
import matplotlib.tri as mtri
import matplotlib.transforms as mtrans
from matplotlib.container import BarContainer, ErrorbarContainer, StemContainer
#from matplotlib.axes._base import _AxesBase
#from matplotlib.axes._base import _process_plot_format


rcParams = matplotlib.rcParams

_alias_map = {'color': ['c'],
              'linewidth': ['lw'],
              'linestyle': ['ls'],
              'facecolor': ['fc'],
              'edgecolor': ['ec'],
               'markerfacecolor': ['mfc'],
              'markeredgecolor': ['mec'],
              'markeredgewidth': ['mew'],
              'markersize': ['ms'],
             }



#@unpack_labeled_data(replace_names=["x", "y"], label_namer="y")
@docstring.dedent_interpd
def rectbin(x, y, C=None, gridsize=100, bins=None,
               xscale='linear', yscale='linear', extent=None,
               cmap=None, norm=None, vmin=None, vmax=None,
               alpha=None, linewidths=None, edgecolors='none',
               reduce_C_function=np.mean, mincnt=None, marginals=False,
               **kwargs):
    """
    Make a rectangular binning plot.  Created by NL 20161012, 
    copied exactly then slightly adapted from matplotlib's hexbin method.

    Call signature::

       rectbin(x, y, C = None, gridsize = 100, bins = None,
                  xscale = 'linear', yscale = 'linear',
                  cmap=None, norm=None, vmin=None, vmax=None,
                  alpha=None, linewidths=None, edgecolors='none'
                  reduce_C_function = np.mean, mincnt=None, marginals=True
                  **kwargs)

    Make a rectangular binning plot of *x* versus *y*, where *x*,
    *y* are 1-D sequences of the same length, *N*. If *C* is *None*
    (the default), this is a histogram of the number of occurences
    of the observations at (x[i],y[i]).

    If *C* is specified, it specifies values at the coordinate
    (x[i],y[i]). These values are accumulated for each rectangular
    bin and then reduced according to *reduce_C_function*, which
    defaults to numpy's mean function (np.mean). (If *C* is
    specified, it must also be a 1-D sequence of the same length
    as *x* and *y*.)

    *x*, *y* and/or *C* may be masked arrays, in which case only
    unmasked points will be plotted.

        Optional keyword arguments:

        *gridsize*: [ 100 | integer ]
           The number of hexagons in the *x*-direction, default is
           100. The corresponding number of hexagons in the
           *y*-direction is chosen such that the hexagons are
           approximately regular. Alternatively, gridsize can be a
           tuple with two elements specifying the number of hexagons
           in the *x*-direction and the *y*-direction.

        *bins*: [ *None* | 'log' | integer | sequence ]
           If *None*, no binning is applied; the color of each hexagon
           directly corresponds to its count value.

           If 'log', use a logarithmic scale for the color
           map. Internally, :math:`log_{10}(i+1)` is used to
           determine the hexagon color.

           If an integer, divide the counts in the specified number
           of bins, and color the hexagons accordingly.

           If a sequence of values, the values of the lower bound of
           the bins to be used.

        *xscale*: [ 'linear' | 'log' ]
           Use a linear or log10 scale on the horizontal axis.

        *scale*: [ 'linear' | 'log' ]
           Use a linear or log10 scale on the vertical axis.

        *mincnt*: [ *None* | a positive integer ]
           If not *None*, only display cells with more than *mincnt*
           number of points in the cell

        *marginals*: [ *True* | *False* ]
           if marginals is *True*, plot the marginal density as
           colormapped rectagles along the bottom of the x-axis and
           left of the y-axis

        *extent*: [ *None* | scalars (left, right, bottom, top) ]
           The limits of the bins. The default assigns the limits
           based on gridsize, x, y, xscale and yscale.

        """

    ax = plt.gca()
    if not ax._hold:
        ax.cla()
    
    #if not self._hold:
    #    self.cla()

    ax._process_unit_info(xdata=x, ydata=y, kwargs=kwargs)

    x, y, C = cbook.delete_masked_points(x, y, C)

    # Set the size of the hexagon grid
    if iterable(gridsize):
        nx, ny = gridsize
    else:
        nx = gridsize
        ny = int(nx / math.sqrt(3))
    # Count the number of data in each hexagon
    x = np.array(x, float)
    y = np.array(y, float)
    if xscale == 'log':
        if np.any(x <= 0.0):
            raise ValueError("x contains non-positive values, so can not"
                                 " be log-scaled")
        x = np.log10(x)
    if yscale == 'log':
        if np.any(y <= 0.0):
            raise ValueError("y contains non-positive values, so can not"
                                 " be log-scaled")
        y = np.log10(y)
    if extent is not None:
        xmin, xmax, ymin, ymax = extent
    else:
        xmin, xmax = (np.amin(x), np.amax(x)) if len(x) else (0, 1)
        ymin, ymax = (np.amin(y), np.amax(y)) if len(y) else (0, 1)

        # to avoid issues with singular data, expand the min/max pairs
        xmin, xmax = mtrans.nonsingular(xmin, xmax, expander=0.1)
        ymin, ymax = mtrans.nonsingular(ymin, ymax, expander=0.1)
            

    # In the x-direction, the hexagons exactly cover the region from
    # xmin to xmax. Need some padding to avoid roundoff errors.
    xpadding = 1.e-9 * (xmax - xmin)
    xmin -= xpadding
    xmax += xpadding
    ypadding = 1.e-9 * (ymax - ymin)
    ymin -= ypadding
    ymax += ypadding
    sx = (xmax - xmin) / nx
    sy = (ymax - ymin) / ny

    if marginals:
        xorig = x.copy()
        yorig = y.copy()

    x = (x - xmin) / sx
    y = (y - ymin) / sy

    ix1 = np.round(x).astype(int)
    iy1 = np.round(y).astype(int)

    nx1 = nx + 1
    ny1 = ny + 1
    nx2 = nx
    ny2 = ny
    nsq = nx1 * ny1 # total number of rectangular bins if we are doing rectangles. Do 1+ the desired number of bins just to make sure we cover all the edges 

    if C is None:
        # Create appropriate views into "accum" array.
        accumsq = np.zeros(nsq)
        lattice.shape = (nx1, ny1)

        for i in xrange(len(x)):

            if ((ix1[i] >= 0) and (ix1[i] < nx1) and
                (iy1[i] >= 0) and (iy1[i] < ny1)):
            
                lattice[ix1[i], iy1[i]] += 1

        # threshold
        if mincnt is not None:
            for i in xrange(nx1):
                for j in xrange(ny1):
                    if lattice[i,j] < mincnt:
                        lattice[i,j] = np.nan

        accum = lattice.astype(float).ravel()
        good_idxs_sq = ~np.isnan(accum)
        

    else:
        if mincnt is None:
            mincnt = 0

        # create accumulation arrays
        lattice = np.empty((nx1, ny1), dtype=object)
        for i in xrange(nx1):
            for j in xrange(ny1):
                lattice[i, j] = []

        for i in xrange(len(x)):
            if ((ix1[i] >= 0) and (ix1[i] < nx1) and
                (iy1[i] >= 0) and (iy1[i] < ny1)):
                lattice[ix1[i], iy1[i]].append(C[i])

        for i in xrange(nx1):
            for j in xrange(ny1):
                vals = lattice[i, j]
                if len(vals) > mincnt:
                    lattice[i, j] = reduce_C_function(vals)
                else:
                    lattice[i, j] = np.nan

        accum = lattice.astype(float).ravel()
        good_idxs_sq = ~np.isnan(accum)

    offset = np.zeros((nsq, 2), float)
    offset[:, 0] = np.repeat(np.arange(nx1), ny1)
    offset[:, 1] = np.tile(np.arange(ny1), nx1)
    offset[:, 0] *= sx
    offset[:, 1] *= sy
    offset[:, 0] += xmin
    offset[:, 1] += ymin

    # remove accumulation bins with no data

    offset = offset[good_idxs_sq,:]
    accum = accum[good_idxs_sq]

    polygon = np.zeros((4,2), float)
    polygon[:,0] = sx * np.array([0.5, 0.5, -0.5, -0.5])
    polygon[:,1] = sy * np.array([-0.5, 0.5, 0.5, -0.5])

    if edgecolors == 'none':
            edgecolors = 'face'

    if xscale == 'log' or yscale == 'log':
            polygons = np.expand_dims(polygon, 0) + np.expand_dims(offsets_sq, 1)
            
            if xscale == 'log':
                polygons[:, :, 0] = 10.0 ** polygons[:, :, 0]
                xmin = 10.0 ** xmin
                xmax = 10.0 ** xmax
                self.set_xscale(xscale)               
            if yscale == 'log':
                polygons[:, :, 1] = 10.0 ** polygons[:, :, 1]
                ymin = 10.0 ** ymin
                ymax = 10.0 ** ymax
                self.set_yscale(yscale)

            collection = mcoll.PolyCollection(
                polygons,
                edgecolors=edgecolors,
                linewidths=linewidths,
                )
            
    else:

        collection = mcoll.PolyCollection(
                [polygon],
                edgecolors=edgecolors,
                linewidths=linewidths,
                offsets=offset,
                transOffset=mtransforms.IdentityTransform(),
                offset_position="data"
                )

    if isinstance(norm, mcolors.LogNorm):
        if (accum == 0).any():
            # make sure we have not zeros
            accum += 1

    # autoscale the norm with curren accum values if it hasn't
    # been set
    if norm is not None:
        if norm.vmin is None and norm.vmax is None:
            norm.autoscale(accum)

    # Transform accum if needed
    if bins == 'log':
            accum = np.log10(accum+1)
    elif bins is not None:
            if not iterable(bins):
                minimum, maximum = min(accum), max(accum)
                bins -= 1  # one less edge than bins
                bins = minimum + (maximum - minimum) * np.arange(bins) / bins
                
            bins = np.sort(bins)
            accum = bins.searchsorted(accum)

    if norm is not None and not isinstance(norm, mcolors.Normalize):
            msg = "'norm' must be an instance of 'mcolors.Normalize'"
            raise ValueError(msg)
    collection.set_array(accum)
    collection.set_cmap(cmap)
    collection.set_norm(norm)
    collection.set_alpha(alpha)
    collection.update(kwargs)

    if vmin is not None or vmax is not None:
            collection.set_clim(vmin, vmax)
    else:
            collection.autoscale_None()

    corners = ((xmin, ymin), (xmax, ymax))
    ax.update_datalim(corners)
    ax.autoscale_view(tight=True)

    
    # add the collection last
    ax.add_collection(collection, autolim=False)
    if not marginals:
        return collection

    if C is None:
        C = np.ones(len(x))

    def coarse_bin(x, y, coarse):
        ind = coarse.searchsorted(x).clip(0, len(coarse) - 1)
        mus = np.zeros(len(coarse))
        for i in range(len(coarse)):
            yi = y[ind == i]
            if len(yi) > 0:
                mu = reduce_C_function(yi)
            else:
                mu = np.nan
            mus[i] = mu
        return mus

    coarse = np.linspace(xmin, xmax, gridsize)

    xcoarse = coarse_bin(xorig, C, coarse)
    valid = ~np.isnan(xcoarse)
    verts, values = [], []
    for i, val in enumerate(xcoarse):
        thismin = coarse[i]
        if i < len(coarse) - 1:
            thismax = coarse[i + 1]
        else:
            thismax = thismin + np.diff(coarse)[-1]

        if not valid[i]:
            continue

        verts.append([(thismin, 0),
                      (thismin, 0.05),
                      (thismax, 0.05),
                      (thismax, 0)])
        values.append(val)

    values = np.array(values)
    trans = ax.get_xaxis_transform(which='grid')

    hbar = mcoll.PolyCollection(verts, transform=trans, edgecolors='face')

    hbar.set_array(values)
    hbar.set_cmap(cmap)
    hbar.set_norm(norm)
    hbar.set_alpha(alpha)
    hbar.update(kwargs)
    ax.add_collection(hbar, autolim=False)

    coarse = np.linspace(ymin, ymax, gridsize)
    ycoarse = coarse_bin(yorig, C, coarse)
    valid = ~np.isnan(ycoarse)
    verts, values = [], []
    for i, val in enumerate(ycoarse):
        thismin = coarse[i]
        if i < len(coarse) - 1:
            thismax = coarse[i + 1]
        else:
            thismax = thismin + np.diff(coarse)[-1]
        if not valid[i]:
            continue
        verts.append([(0, thismin), (0.0, thismax),
                      (0.05, thismax), (0.05, thismin)])
        values.append(val)

    values = np.array(values)

    trans = ax.get_yaxis_transform(which='grid')

    vbar = mcoll.PolyCollection(verts, transform=trans, edgecolors='face')
    vbar.set_array(values)
    vbar.set_cmap(cmap)
    vbar.set_norm(norm)
    vbar.set_alpha(alpha)
    vbar.update(kwargs)
    ax.add_collection(vbar, autolim=False)

    collection.hbar = hbar
    collection.vbar = vbar

    def on_changed(collection):
        hbar.set_cmap(collection.get_cmap())
        hbar.set_clim(collection.get_clim())
        vbar.set_cmap(collection.get_cmap())
        vbar.set_clim(collection.get_clim())

    collection.callbacksSM.connect('changed', on_changed)

    return collection
