"""Custom tab widget with horizontal text in west-oriented tabs.

thanks to:
https://stackoverflow.com/questions/51230544/pyqt5-how-to-set-tabwidget-west-but-keep-the-text-horizontal/51230694#51230694
"""


from PyQt5 import QtCore, QtGui, QtWidgets


class WestTabBar(QtWidgets.QTabBar):
    """Tab bar which paints wester panels horizontally."""

    # def tabSizeHint(self, index):
    #     s = QtWidgets.QTabBar.tabSizeHint(self, index)
    #     s.transpose()
    #     return s

    # def paintEvent(self, event):
    #     painter = QtWidgets.QStylePainter(self)
    #     opt = QtWidgets.QStyleOptionTab()

    #     for i in range(self.count()):
    #         self.initStyleOption(opt, i)
    #         painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
    #         painter.save()

    #         s = opt.rect.size()
    #         s.transpose()
    #         r = QtCore.QRect(QtCore.QPoint(), s)
    #         r.moveCenter(opt.rect.center())
    #         opt.rect = r

    #         c = self.tabRect(i).center()
    #         painter.translate(c)
    #         painter.rotate(90)
    #         painter.translate(-c)
    #         painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt);
    #         painter.restore()


class WestTabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
        self.setTabBar(WestTabBar(self))
        self.setTabPosition(QtWidgets.QTabWidget.West)
        self.setTabShape(QtWidgets.QTabWidget.TabShape.Rounded)
        self.setIconSize(QtCore.QSize(40, 40))

    def addTab(self, tab, icon, name):
        pixmap = icon.pixmap(50, 50)
        tr = QtGui.QTransform()
        tr.rotate(90)
        pixmap = pixmap.transformed(tr)
        icon = QtGui.QIcon(pixmap)
        return super(WestTabWidget, self).addTab(tab, icon, name)
