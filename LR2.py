"""
 Licensed under the Unlicense License;
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://unlicense.org

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import math
import os
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import uic, QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem

"""
Rotates points by angle
"""


def rotate2d(pos, rad):
    x, y = pos
    s, c = math.sin(rad), math.cos(rad)
    return x * c - y * s, y * c + x * s


"""
Arduino map function
"""


def valmap(value, istart, istop, ostart, ostop):
    return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        # Load GUI file
        self.gui = uic.loadUi('LR2.ui')
        self.gui.show()

        self.points = []
        self.width = self.gui.graphWidget.width()
        self.height = self.gui.graphWidget.height()
        self.center = np.array([int(self.width / 2), int(self.height / 2)])

        # Mouse variables
        self.mouse = self.center
        self.mouse_move = np.array([0, 0])
        self.mouse_rot = np.array([0, 0])
        self.mouse_move_released = self.center
        self.mouse_rot_released = self.center
        self.mouse_pressed = self.center
        self.rot_flag = False
        self.move_flag = False

        # Connect GUI controls
        self.gui.btn_generate_data.clicked.connect(self.generate_data)
        self.gui.btn_show_3d.clicked.connect(self.draw_points)
        self.gui.btn_save_data.clicked.connect(self.save_data)
        self.gui.btn_load_data.clicked.connect(self.load_data)
        self.gui.brush_size.valueChanged.connect(self.draw_points)

        # Initialize charts and tables
        self.init_chart()
        self.init_table()

    """
    Initializes table of points
    """

    def init_table(self):
        self.gui.points_table.setColumnCount(3)
        self.gui.points_table.verticalHeader().setVisible(False)
        self.gui.points_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.gui.points_table.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem('X'))
        self.gui.points_table.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem('Y'))
        self.gui.points_table.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem('Z'))
        header = self.gui.points_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

    """
    Initializes main chart
    """

    def init_chart(self):
        self.gui.graphWidget.setBackground(QtGui.QColor('white'))
        # self.gui.graphWidget.getAxis('left').setPen(QtGui.QColor('black'))
        # self.gui.graphWidget.getAxis('left').setTextPen(QtGui.QColor('black'))
        # self.gui.graphWidget.getAxis('bottom').setPen(QtGui.QColor('black'))
        # self.gui.graphWidget.getAxis('bottom').setTextPen(QtGui.QColor('black'))

        self.gui.graphWidget.setRange(xRange=(0, 640), yRange=(0, 480), padding=0)
        self.gui.graphWidget.showGrid(x=True, y=True, alpha=1.0)

        self.gui.graphWidget.mouseMoveEvent = self.mouse_move_event
        self.gui.graphWidget.mouseReleaseEvent = self.mouse_release_event
        self.gui.graphWidget.mousePressEvent = self.mouse_press_event

    """
    Generates data
    """

    def generate_data(self):
        print('Generating data...')
        points_num = self.gui.points_num.value()
        deviation_val = self.gui.deviation_val.value()
        self.points = []
        for i in range(points_num):
            self.points.append([0.5 * math.cos(4 * math.pi * (i / points_num)) +  # 0.7, 6
                                random.normalvariate(0, deviation_val),

                                0.5 * math.sin(4 * math.pi * (i / points_num)) +  # 0.5, 4
                                random.normalvariate(0, deviation_val),

                                -1 + 2 * i / points_num + random.normalvariate(0, deviation_val)])
        self.points = np.array(self.points)

        self.show_on_table()
        self.gui.btn_save_data.setEnabled(True)
        print('Data generated.')

    """
    Shows points in table
    """

    def show_on_table(self):
        self.gui.points_table.setRowCount(0)
        for point in self.points:
            row_position = self.gui.points_table.rowCount()
            self.gui.points_table.insertRow(row_position)
            self.gui.points_table.setItem(row_position, 0, QTableWidgetItem(str(point[0])))
            self.gui.points_table.setItem(row_position, 1, QTableWidgetItem(str(point[1])))
            self.gui.points_table.setItem(row_position, 2, QTableWidgetItem(str(point[2])))
        self.gui.btn_save_data.setEnabled(True)

    """
    Draws 3D points over 2D chart
    """

    def draw_points(self):
        if self.points is not None and len(self.points) > 0:
            # Clear old points
            self.gui.graphWidget.clear()

            # Create color map
            z = np.array(np.array([item[2] for item in self.points]))
            cmap = plt.get_cmap('hsv')
            min_z = np.min(z)
            max_z = np.max(z)

            # Draw each point
            for point in self.points:
                x, y, z = point
                rgb_z = cmap(0.9 - ((z - min_z) / (max_z - min_z)))

                # Roll
                if self.gui.roll_enabled.isChecked():
                    x, y = rotate2d((x, y), math.radians((self.mouse_rot[0] + self.mouse_rot[1]) / 2))
                # Yaw
                x, z = rotate2d((x, z), math.radians(self.mouse_rot[0]))
                # Pitch
                y, z = rotate2d((y, z), math.radians(self.mouse_rot[1]))

                z += 5
                f = self.width / z
                x, y = x * f, y * f

                self.gui.graphWidget.plot([(self.center[0] + x) + self.mouse_move[0]],
                                          [(self.center[1] + y) + self.mouse_move[1]],
                                          pen=None,
                                          symbolBrush=(rgb_z[0] * 255, rgb_z[1] * 255, rgb_z[2] * 255),
                                          symbolSize=self.gui.brush_size.value(),
                                          symbolPen=None)

    """
    Moves or rotates points with mouse
    """

    def mouse_move_event(self, event):
        if event.buttons():
            self.mouse = np.array([event.pos().x(), (event.pos().y() - 480) * -1])
            if event.buttons() & QtCore.Qt.LeftButton:
                # Move
                self.move_flag = True
                self.rot_flag = False
                self.mouse -= self.mouse_pressed - self.mouse_move_released
                self.mouse_move = self.mouse - self.center
            else:
                # Rotate
                self.move_flag = False
                self.rot_flag = True
                self.mouse -= self.mouse_pressed - self.mouse_rot_released
                self.mouse_rot = self.mouse - self.center
                np.floor_divide(self.mouse_rot, 2)

            self.draw_points()

    """
    Remembers final position (when stop moving)
    """

    def mouse_release_event(self, event):
        if self.move_flag:
            self.mouse_move_released = self.mouse
        if self.rot_flag:
            self.mouse_rot_released = self.mouse

    """
    Remembers entry position (when start moving)
    """

    def mouse_press_event(self, event):
        self.mouse_pressed = np.array([event.pos().x(), (event.pos().y() - 480) * -1])

    """
    Saves points to CSV file
    """

    def save_data(self):
        print('Saving data...')
        np.savetxt(self.gui.data_file.text(), self.points, delimiter=' ')
        print('File', self.gui.data_file.text(), 'saved.')

    """
    Loads points to CSV file
    """

    def load_data(self):
        if os.path.exists(self.gui.data_file.text()):
            print('Loading data...')
            self.points = np.loadtxt(self.gui.data_file.text(), delimiter=' ')
            self.show_on_table()
            print('File', self.gui.data_file.text(), 'loaded.')
        else:
            print('File', self.gui.data_file.text(), 'doesn\'t exist!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    sys.exit(app.exec_())
