"""
A module for generating circle plots.
"""

# Author: Jonathan Collier


import pandas as pd
import numpy as np
from matplotlib.patheffects import withStroke
from matplotlib.patches import Circle
from matplotlib.colors import is_color_like
from typing import Set
from dataclasses import dataclass, field


class PlotAttributes:
    """The PlotAttributes object defines the structure of plot_attributes.
    
    Parameters
    ----------
    color
        The color of the circle.
    alpha : float
        The opacity of the circle.
    label
        The label of the circle.
        
    Attributes
    ----------
    color
        Stores the validated color of the circle.
    alpha : float
        Stores the validated opacity of the circle.
    label
        Stores the label of the circle.
        
    """
    def __init__(self, color, alpha: float, label):
        self.color = color
        self.alpha = alpha
        self.label = label
        
    @property
    def color(self):
        return self._color
        
    @color.setter
    def color(self, value):
        if not is_color_like(value):
            raise ValueError('Must specify a valid color.')
        self._color = value
        
    @property
    def alpha(self):
        return self._alpha
    
    @alpha.setter 
    def alpha(self, value):
        if not isinstance(value, (float, int)):
            raise TypeError('alpha must be of type float')
        if 0 > value <= 1:
            raise ValueError('Must specify an alpha value between 0 and 1')
        self._alpha = value


class CirclePlotter:
    """The CirclePlotter object is used for generating circle plots.
    
    Parameters
    ----------
    radius : float, default=.2
        The radius circles to be plotted.
    x_init : float, default=0
        The initial position of x.
    y_init : float, default=1
        The initial position of y.
    circles_per_column : int, default=10
        The number of circles per column.
    plot_attributes : dict
        A dict that contains attributes for plotting
        for selecting the color, alpha, and label of circles.
    
    Attributes:
    -----------
    radius : float, default=.2
        Stores the validated radius of each circle.
    pad : float, default=.4
        Stores the amount of space between each group of circles
        in addition to 2*`radius`.
    x_init : float, default=0
        Stores the initial position of x.
    y_init : float, default=1
        Stores the initial position of y.
    circles_per_column : int, default=10
        Stores the number of circles per column.
    plot_attributes : dict
        A dictionary that contains attributes for plotting
        
    """
    def __init__(self, plot_attributes: dict, radius=.2, x_init=0, y_init=1, 
                 circles_per_column=10):
        """The init method of the CirclePlotter class."""
        self.radius = radius
        self.x_init = x_init
        self.y_init = y_init
        self.circles_per_column = circles_per_column
        self.plot_attributes = plot_attributes
    
    @property
    def radius(self):
        return self._radius
    
    @radius.setter
    def radius(self, value):
        if value <= 0:
            raise ValueError('Radius must be greater than 0.')
        self._pad = None
        self._radius = value
            
    @property 
    def pad(self):
        if self._pad is None:
            self._pad = 2 * self._radius
        return self._pad
        
    @property
    def x_init(self):
        return self._x_init
        
    @x_init.setter
    def x_init(self, value):
        if value < 0:
            raise ValueError('x_init must be greater than or equal to 0.')
        self._x_init = value
    
    @property
    def y_init(self):
        return self._y_init
        
    @y_init.setter
    def y_init(self, value):
        if value < 0:
            raise ValueError('y_init must be greater than or equal to 0.')
        self._y_init = value
        
    @property
    def plot_attributes(self):
        return self._plot_attributes
    
    @plot_attributes.setter
    def plot_attributes(self, value):
        
        if not isinstance(value, dict):
            raise TypeError('plot_attributes must of type dictionary.')
        
        for group, attributes in value.items():
            if not isinstance(attributes, (list, tuple)):
                raise TypeError("""plot_attributes must be of type tuple or
                    list."""
                )
                
            if len(attributes) != 3:
                raise ValueError('plot_attributes must include color,' 
                    'alpha, and label.'
                )
            
            value[group] = PlotAttributes(*attributes)
            
        self._plot_attributes = value


    def _validate_input_data(self, input_data, group, order):
        """Validates input_data."""
        if not isinstance(input_data, pd.DataFrame):
            raise TypeError('input_data must be of type pandas.DataFrame.')
        
        if group not in input_data.columns:
            raise ValueError(
                f'DataFrame must contain the following column: {group}'
            )
        
        for value in order:
            if value not in input_data.columns:
                raise ValueError(
                    f'DataFrame must contain the following columns: {order}'
                )

    def create_circle(self, x, y, edgecolor, 
                      facecolor, alpha: float):
        """Creates a circle at center (x, y) position with given radius.
        
        Parameters:
        -----------
        x : float
            The center x-position of the circle.
        y : float
            The center y-position of the circle.
        edgecolor : color
            The color of the outer edge of the circle.
        facecolor : color
            The inner color of the circle.
        alpha : scaler
            The opacity of the circle.
           
        Returns:
        --------
        : matplotlib.patches.Circle
            A circle patch.
            
        """
        return Circle(
            (x, y), radius=self.radius, clip_on=False, zorder=10, 
            linewidth=2, edgecolor=edgecolor, facecolor=facecolor, 
            alpha=alpha, 
            path_effects=[withStroke(linewidth=2, foreground='white')])

    def circle_generator(self, input_data: pd.DataFrame, group: str, 
                         order: list):
        """Yields attributes for plotting group circles using `input_data`.

        Parameters
        ----------
        input_data : pandas.DataFrame
            Input DataFrame used to generate attributes for plotting.
        group : str
            Column to group `input_data` by.
        order: list
            Column to order `input_data` by.

        Returns
        -------
        None
        
        Yields
        ------
        : CircleAttributes or GroupLabel   
            Yields a CircleAttributes or GroupLabel class instance 
            for plotting circles, labeling groups, and 
            drawing gridlines using `input_data`.
        """
        self._validate_input_data(input_data, group, order)

        x = self.x_init
        circle_pad = 3 * self.radius
        group_pad = 2 * self.radius + self.pad
        
        for group, data in input_data.groupby(group, sort=False):
            
            # Shifts x by group_pad for each group after x_init.
            if x > self.x_init:
                x += group_pad

            # Initializes an empty list for storing values of x 
            # within the current group.
            point_history = CirclePointHistory()
            
            ordered_data = data.sort_values(by=order, ascending=False)
            
            for i, row in enumerate(ordered_data.itertuples()):

                # Checks whether the column has been filled.
                if i % self.circles_per_column == 0:
                    if i == 0:
                        x += group_pad
                    else:
                        x += circle_pad
                    # Resets y to y_init after all circles in a column 
                    # have been plotted.
                    y = self.y_init 

                else:
                    y += circle_pad

                # Adds x, y 
                point_history.add_point(x, y)
                
                yield CircleAttributes (
                    group=group,
                    count=data.shape[0],
                    row=row,
                    x=x,
                    y=y
                )

                if i + 1 == data.shape[0]:
                    yield GroupLabel (
                        group_label=group,
                        group_sublabel=self.plot_attributes[group].label,
                        group_count=data.shape[0],
                        label_x=sum(point_history.x)/len(point_history.x), 
                        label_y= self.y_init + (circle_pad * self.circles_per_column),
                        gridline_x=max(point_history.x) + group_pad
                    )
                

@dataclass 
class CirclePointHistory:
    """
    A dataclass that stores x and y values 
    of each circle in a group.
    """
    x: Set[float] = field(default_factory=set)
    y: Set[float] = field(default_factory=set)
    
    def add_point(self, x, y):
        self.x.add(x)
        self.y.add(y)

@dataclass
class CircleAttributes:
    """
    A dataclass for returning attributes related to
    each circle.
    """
    group: str
    count: int
    row: tuple
    x: float
    y: float
    
@dataclass
class GroupLabel:
    """
    A dataclass that stores group-level attributes 
    related to labeling each group of circles.
    """
    group_label: str
    group_sublabel: str
    group_count: int
    label_x: float
    label_y: float 
    gridline_x: float
    

        
        


