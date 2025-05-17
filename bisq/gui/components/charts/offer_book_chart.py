from .mpl_canvas import MplCanvas
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import typing

import matplotlib.ticker as ticker
import numpy as np

class OfferBookChart(QWidget):
    def __init__(self, parent: typing.Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.canvas = MplCanvas(self, dpi=100)
        self.hlayout = QVBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.addWidget(self.canvas)
        self.setLayout(self.hlayout)
        
    def updatePlot(self, sell_prices, sell_volumes, buy_prices, buy_volumes):
        ax = self.canvas.axes
        ax.clear()
        
        linewidth=0.5
        # Plot the sell orders (red, left side of the graph)
        ax.plot(sell_prices, sell_volumes, color='red', linestyle='-', marker='o',
                markerfacecolor='white', markeredgecolor='red', markersize=4, markeredgewidth=linewidth, linewidth=linewidth)
        ax.fill(np.append([sell_prices[0]], np.append(sell_prices, sell_prices[-1])),
                np.append([0], np.append(sell_volumes, 0)),
                color='#D62929', alpha=0.32)

        # Plot the buy orders (green, right side of the graph)
        ax.plot(buy_prices, buy_volumes, color='green', linestyle='-', marker='o',
                markerfacecolor='white', markeredgecolor='green', markersize=4, markeredgewidth=linewidth, linewidth=linewidth)
        ax.fill(np.append([buy_prices[0]],np.append(buy_prices, buy_prices[-1])),
                np.append([0], np.append(buy_volumes, 0)),
                color='#53AC5F', alpha=0.32)
        
        # Move y-axis to the right
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        
        # Remove top and left borders
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        # make spines (borders) thinner
        ax.spines['bottom'].set_linewidth(0.5)
        ax.spines['right'].set_linewidth(0.5)
        # make spines (borders) grey
        ax.spines['bottom'].set_color('grey')
        ax.spines['right'].set_color('grey')
        
        ax.set_xlabel('Price in USD for 1 BTC', labelpad=8, fontsize=9)
        ax.set_ylabel('BTC Order Volume', labelpad=8, fontsize=9)
        
        # make labels text size smaller
        ax.xaxis.label.set_fontsize(8)
        ax.yaxis.label.set_fontsize(8)
        
        # Make the tick labels and tick marks grey
        ax.tick_params(axis='both', colors='grey', labelsize=7)  # Apply grey color to ticks and labels

        # Add dotted grid lines with transparency
        ax.grid(True, which='both', linestyle='--', axis="y", linewidth=0.8, alpha=0.6)
        
        # Make the plot draw from 0 on y axis
        ax.set_ylim(bottom=0)
        
        # Format the x-axis tick labels with thousands separator
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

        self.canvas.draw()