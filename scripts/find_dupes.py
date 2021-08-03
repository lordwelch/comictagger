#!/usr/bin/python3
"""Find all duplicate comics"""

import argparse
import hashlib
import shutil
import signal
from pathlib import Path
from operator import itemgetter
from typing import Dict, List

import filetype
import typing
from PyQt5 import QtCore, QtGui, QtWidgets, uic

from comictaggerlib.ui.qtutils import centerWindowOnParent

from comictaggerlib.comicarchive import *
from comictaggerlib.settings import *
from comictaggerlib.imagehasher import ImageHasher
from comictaggerlib.filerenamer import FileRenamer

root = 1 << 31 - 1
something = 1 << 31 - 1


class ImageMeta:
    def __init__(self, name, file_hash, image_hash, image_type, score=-1, score_file_hash=""):
        self.name = name
        self.file_hash = file_hash
        self.image_hash = image_hash
        self.type = image_type
        self.score = score
        self.score_file_hash = score_file_hash


class Duplicate:
    """docstring for Duplicate"""
    imageHashes: Dict[str, ImageMeta]

    def __init__(self, path, metadata: GenericMetadata, ca: ComicArchive, cover):
        self.path = path
        self.digest = ""
        self.ca = ca
        self.metadata = metadata
        self.imageHashes = dict()
        self.duplicateImages = set()
        self.extras = set()
        self.extractedPath = ""
        self.deletable = False
        self.keeping = False
        self.fileCount = 0  # Excluding comicinfo.xml
        self.imageCount = 0
        self.cover = cover
        blake2b = hashlib.blake2b(digest_size=16)
        for f in open(self.path, "rb"):
            blake2b.update(f)

        self.digest = blake2b.hexdigest()

    def extract(self, directory):
        if self.ca.seemsToBeAComicArchive():
            self.extractedPath = directory
            for filepath in self.ca.archiver.getArchiveFilenameList():
                filename = os.path.basename(filepath)
                if filename.lower() in ["comicinfo.xml"]:
                    continue

                self.fileCount += 1
                archived_file = self.ca.archiver.readArchiveFile(filepath)

                image_type = filetype.image_match(archived_file)
                if image_type is not None:
                    self.imageCount += 1
                    file_hash = hashlib.blake2b(archived_file, digest_size=16).hexdigest().upper()
                    if file_hash in self.imageHashes.keys():
                        self.duplicateImages.add(filename)
                    else:
                        image_hash = ImageHasher(data=archived_file, width=12, height=12).average_hash()
                        self.imageHashes[file_hash] = ImageMeta(os.path.join(self.extractedPath, filename), file_hash,
                                                                image_hash, image_type.extension)
                else:
                    self.extras.add(filename)

                os.makedirs(self.extractedPath, 0o777, True)

                unarchived_file = Path(os.path.join(self.extractedPath, filename))
                unarchived_file.write_bytes(archived_file)

    def clean(self):
        shutil.rmtree(self.extractedPath, ignore_errors=True)

    def delete(self):
        if not self.keeping:
            self.clean()
            try:
                os.remove(self.path)
            except Exception:
                pass
        return not (os.path.exists(self.path) or os.path.exists(self.extractedPath))


class Tree(QtCore.QAbstractListModel):
    def __init__(self, item: List[List[Duplicate]]):
        super(Tree, self).__init__()
        self.rootItem = item

    def rowCount(self, index: QtCore.QModelIndex = ...) -> int:
        if not index.isValid():
            return len(self.rootItem)

        return 0

    def columnCount(self, index: QtCore.QModelIndex = ...) -> int:
        if index.isValid():
            return 1

        return 0

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QtCore.QVariant()

        f = FileRenamer(self.rootItem[index.row()][0].metadata)
        f.setTemplate("{series} #{issue} - {title} ({year})")
        if role == QtCore.Qt.DisplayRole:
            return f.determineName('')
        elif role == QtCore.Qt.UserRole:
            return f.determineName('')
        return QtCore.QVariant()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, file_list, style, work_path, parent=None):
        super().__init__(parent)
        uic.loadUi(ComicTaggerSettings.getUIFile("../../scripts/mainwindow.ui"), self)
        self.dupes = []
        self.firstRun = 0
        self.dupe_set_list: List[List[Duplicate]] = list()
        self.style = style
        if work_path == "":
            work_path = tempfile.mkdtemp()
        self.work_path = work_path
        self.initFiles = file_list
        self.dupe_set_qlist.clicked.connect(self.dupe_set_clicked)
        self.dupe_set_qlist.doubleClicked.connect(self.dupe_set_double_clicked)
        self.actionCompare_Comic.triggered.connect(self.compare_action)

    def comic_deleted(self, archive_path):
        self.update_dupes()

    def update_dupes(self):
        # print("updating duplicates")
        new_set_list = list()
        for dupe in self.dupe_set_list:
            dupe_list = list()
            for d in dupe:
                QtCore.QCoreApplication.processEvents()
                if os.path.exists(d.path):
                    dupe_list.append(d)
                else:
                    d.clean()

            if len(dupe_list) > 1:
                new_set_list.append(dupe_list)
            else:
                dupe_list[0].clean()
        self.dupe_set_list: List[List[Duplicate]] = new_set_list
        self.dupe_set_qlist.setModel(Tree(self.dupe_set_list))

        self.dupe_set_qlist.setSelection(QtCore.QRect(0, 0, 0, 1), QtCore.QItemSelectionModel.ClearAndSelect)
        self.dupe_set_clicked(self.dupe_set_qlist.model().index(0, 0))

    def compare(self, i):
        if len(self.dupe_set_list) > i:
            dw = DupeWindow(self.dupe_set_list[i], self.work_path, self)
            dw.closed.connect(self.update_dupes)
            dw.show()

    def compare_action(self, b):
        selection = self.dupe_set_qlist.selectedIndexes()
        if len(selection) > 0:
            self.compare(selection[0].row())

    def dupe_set_double_clicked(self, index: QtCore.QModelIndex):
        self.compare(index.row())

    def dupe_set_clicked(self, index: QtCore.QModelIndex):
        for f in self.dupe_list.children():
            f.deleteLater()
        self.dupe_set_list[index.row()].sort(key=lambda k: k.digest)
        for i, f in enumerate(self.dupe_set_list[index.row()]):
            color = "black"
            if i > 0:
                if self.dupe_set_list[index.row()][i - 1].digest == f.digest:
                    color = "green"
            elif i == 0:
                if len(self.dupe_set_list[index.row()]) > 1:
                    if self.dupe_set_list[index.row()][i + 1].digest == f.digest:
                        color = "green"
            ql = DupeImage(duplicate=f, style=f".path {{color: black;}}.hash {{color: {color};}}",
                           parent=self.dupe_list)
            ql.deleted.connect(self.update_dupes)
            ql.setMinimumWidth(300)
            ql.setMinimumHeight(500)
            self.dupe_list.layout().addWidget(ql)

    def showEvent(self, event: QtGui.QShowEvent):
        if self.firstRun == 0:
            self.firstRun = 1

            self.load_files(self.initFiles)
        if len(self.dupe_set_list) < 1:
            dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.NoIcon, "ComicTagger Duplicate finder",
                                           "No duplicate comics found", QtWidgets.QMessageBox.Ok, parent=self)
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            qw = QtWidgets.QWidget()
            qw.setFixedWidth(90)
            dialog.layout().addWidget(qw, 3, 2, 1, 3)
            dialog.exec()
            QtWidgets.QApplication.quit()
            sys.exit(0)
        self.dupe_set_qlist.setSelection(QtCore.QRect(0, 0, 0, 1), QtCore.QItemSelectionModel.ClearAndSelect)
        self.dupe_set_clicked(self.dupe_set_qlist.model().index(0, 0))

    def load_files(self, file_list):
        # Progress dialog on Linux flakes out for small range, so scale up
        dialog = QtWidgets.QProgressDialog("", "Cancel", 0, len(file_list), parent=self)
        dialog.setWindowTitle("Reading Comics")
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.setMinimumDuration(300)
        dialog.setMinimumWidth(400)
        centerWindowOnParent(dialog)

        comic_list = []
        max_name_len = 2
        for filename in file_list:
            QtCore.QCoreApplication.processEvents()
            if dialog.wasCanceled():
                break
            dialog.setValue(dialog.value() + 1)
            dialog.setLabelText(filename)
            ca = ComicArchive(path=filename, rar_exe_path=settings.rar_exe_path,
                              default_image_path=ComicTaggerSettings.getGraphic('nocover.png'))
            if ca.seemsToBeAComicArchive() and ca.hasMetadata(self.style):
                # fmt_str = "{{0:{0}}}".format(max_name_len)
                # print(fmt_str.format(filename) + "\r", end='', file=sys.stderr)
                # sys.stderr.flush()
                md = ca.readMetadata(self.style)
                cover = ca.getPage(0)
                comic_list.append((make_key(md), filename, ca, md, cover))
                # max_name_len = len(filename)

        comic_list.sort(key=itemgetter(0), reverse=False)

        # look for duplicate blocks
        dupe_set = list()
        prev_key = ""

        dialog.setWindowTitle("Finding Duplicates")
        dialog.setMaximum(len(comic_list))
        dialog.setValue(dialog.minimum())

        set_list = list()
        for new_key, filename, ca, md, cover in comic_list:
            dialog.setValue(dialog.value() + 1)
            QtCore.QCoreApplication.processEvents()
            if dialog.wasCanceled():
                break
            dialog.setLabelText(filename)

            # if the new key same as the last, add to to dupe set
            if new_key == prev_key:
                dupe_set.append((filename, ca, md, cover))
            # else we're on a new potential block
            else:
                # only add if the dupe list has 2 or more
                if len(dupe_set) > 1:
                    set_list.append(dupe_set)
                dupe_set = list()
                dupe_set.append((filename, ca, md, cover))

            prev_key = new_key

        # Final dupe_set
        if len(dupe_set) > 1:
            set_list.append(dupe_set)

        for d_set in set_list:
            new_set = list()
            for filename, ca, md, cover in d_set:
                new_set.append(Duplicate(filename, md, ca, cover))
            self.dupe_set_list.append(new_set)

        self.dupe_set_qlist.setModel(Tree(self.dupe_set_list))
        # print()
        dialog.close()

    # def delete_hashes(self):
    #     working_dir = os.path.join(self.tmp, "working")
    #     s = False
    #     # while working and len(dupe_set) > 1:
    #     remaining = list()
    #     for dupe_set in self.dupe_set_list:
    #         not_deleted = True
    #         if os.path.exists(working_dir):
    #             shutil.rmtree(working_dir, ignore_errors=True)
    #
    #         os.mkdir(working_dir)
    #         extract(dupe_set, working_dir)
    #         if mark_hashes(dupe_set):
    #             if s:  # Auto delete if s flag or if there are not any non image extras
    #                 dupe_set.sort(key=attrgetter("fileCount"))
    #                 dupe_set.sort(key=lambda x: len(x.duplicateImages))
    #                 dupe_set[0].keeping = True
    #             else:
    #                 dupe_set[select_archive("Select archive to keep: ", dupe_set)].keeping = True
    #         else:
    #             # app.exec_()
    #             compare_dupe(dupe_set[0], dupe_set[1])
    #         for i, dupe in enumerate(dupe_set):
    #             print("{0}. {1}: {2.series} #{2.issue:0>3} {2.year}; extras: {3}; deletable: {4}".format(
    #                 i,
    #                 dupe.path,
    #                 dupe.metadata,
    #                 ", ".join(sorted(dupe.extras)), dupe.deletable))
    #         dupe_set = delete(dupe_set)
    #         if not_deleted:
    #             remaining.append(dupe_set)
    #     self.dupe_set_list = remaining


class DupeWindow(QtWidgets.QWidget):
    closed = QtCore.pyqtSignal()

    def __init__(self, duplicates: List[Duplicate], tmp, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        uic.loadUi(ComicTaggerSettings.getUIFile("../../scripts/dupe.ui"), self)

        for f in self.comic1Image.children():
            f.deleteLater()
        for f in self.comic2Image.children():
            f.deleteLater()
        self.deleting = -1
        self.duplicates = duplicates
        self.dupe1 = -1
        self.dupe2 = -1

        self.tmp = tmp

        self.setWindowTitle("ComicTagger Duplicate compare")

        self.pageList.currentItemChanged.connect(self.current_item_changed)
        self.comic1Delete.clicked.connect(self.delete_1)
        self.comic2Delete.clicked.connect(self.delete_2)
        self.dupeList.itemSelectionChanged.connect(self.show_dupe_list)
        # self.dupeList = QtWidgets.QListWidget()
        self.dupeList.setIconSize(QtCore.QSize(100, 50))

        while self.pageList.rowCount() > 0:
            self.pageList.removeRow(0)

        self.pageList.setSortingEnabled(False)

        if len(duplicates) < 2:
            return
        extract(duplicates, tmp)

        tmp1 = DupeImage(self.duplicates[0])
        tmp2 = DupeImage(self.duplicates[1])
        self.comic1Data.layout().replaceWidget(self.comic1Image, tmp1)
        self.comic2Data.layout().replaceWidget(self.comic2Image, tmp2)
        self.comic1Image = tmp1
        self.comic2Image = tmp2
        self.comic1Image.deleted.connect(self.update_dupes)
        self.comic2Image.deleted.connect(self.update_dupes)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self.update_dupes()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.closed.emit()
        event.accept()

    def show_dupe_list(self):
        dupes = self.dupeList.selectedItems()
        if len(dupes) != 2:
            return
        self.dupe1 = int(dupes[0].data(QtCore.Qt.UserRole))
        self.dupe2 = int(dupes[1].data(QtCore.Qt.UserRole))
        if len(self.duplicates[self.dupe2].imageHashes) > len(self.duplicates[self.dupe1].imageHashes):
            self.dupe1, self.dupe2 = self.dupe2, self.dupe1
        compare_dupe(self.duplicates[self.dupe1].imageHashes, self.duplicates[self.dupe2].imageHashes)
        self.display_dupe()

    def update_dupes(self):
        dupes: List[Duplicate] = list()
        for f in self.duplicates:
            if os.path.exists(f.path):
                dupes.append(f)
            else:
                f.clean()
        self.duplicates = dupes
        if len(self.duplicates) < 2:
            self.close()

        for i, dupe in enumerate(self.duplicates):
            item = QtWidgets.QListWidgetItem()
            item.setText(dupe.path)
            item.setToolTip(dupe.path)
            pm = QtGui.QPixmap()
            pm.loadFromData(dupe.cover)
            item.setIcon(QtGui.QIcon(pm))
            item.setData(QtCore.Qt.UserRole, i)
            self.dupeList.addItem(item)
        self.dupeList.setCurrentRow(0)
        self.dupeList.setCurrentRow(1, QtCore.QItemSelectionModel.Select)

    def delete_1(self):
        self.duplicates[self.dupe1].delete()
        self.update_dupes()

    def delete_2(self):
        self.duplicates[self.dupe2].delete()
        self.update_dupes()

    def display_dupe(self):
        for f in range(self.pageList.rowCount()):
            self.pageList.removeRow(0)
        for h in self.duplicates[self.dupe1].imageHashes.values():
            row = self.pageList.rowCount()
            self.pageList.insertRow(row)
            name = QtWidgets.QTableWidgetItem()
            score = QtWidgets.QTableWidgetItem()
            dupe_name = QtWidgets.QTableWidgetItem()

            item_text = os.path.basename(h.name)
            name.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            name.setText(item_text)
            name.setData(QtCore.Qt.UserRole, h.file_hash)
            name.setData(QtCore.Qt.ToolTipRole, item_text)
            self.pageList.setItem(row, 0, name)

            item_text = str(h.score)
            score.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            score.setText(item_text)
            score.setData(QtCore.Qt.UserRole, h.file_hash)
            score.setData(QtCore.Qt.ToolTipRole, item_text)
            self.pageList.setItem(row, 1, score)

            item_text = os.path.basename(self.duplicates[self.dupe2].imageHashes[h.score_file_hash].name)
            dupe_name.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            dupe_name.setText(item_text)
            dupe_name.setData(QtCore.Qt.UserRole, h.file_hash)
            dupe_name.setData(QtCore.Qt.ToolTipRole, item_text)
            self.pageList.setItem(row, 2, dupe_name)

        self.pageList.resizeColumnsToContents()
        self.pageList.selectRow(0)

    def current_item_changed(self, curr, prev):

        if curr is None:
            return
        if prev is not None and prev.row() == curr.row():
            return

        file_hash = str(self.pageList.item(curr.row(), 0).data(QtCore.Qt.UserRole))
        image_hash = self.duplicates[self.dupe1].imageHashes[file_hash]
        score_hash = self.duplicates[self.dupe2].imageHashes[image_hash.score_file_hash]

        image1 = QtGui.QPixmap(image_hash.name)
        image2 = QtGui.QPixmap(score_hash.name)

        page_color = "red"
        size_color = "red"
        type_color = "red"
        file_color = "black"
        image_color = "black"
        if image1.width() == image2.width() and image2.height() == image1.height():
            size_color = "green"
        if len(self.duplicates[self.dupe1].imageHashes) == len(self.duplicates[self.dupe2].imageHashes):
            page_color = "green"
        if image_hash.type == score_hash.type:
            type_color = "green"
        if image_hash.image_hash == score_hash.image_hash:
            image_color = "green"
        if image_hash.file_hash == score_hash.file_hash:
            file_color = "green"
        style = f"""
.page {{
color: {page_color};
}}
.size {{
color: {size_color};
}}
.type {{
color: {type_color};
}}
.file {{
color: {file_color};
}}
.image {{
color: {image_color};
}}
"""
        text = "name: {{duplicate.path}}<br/>" \
               "page count: <span class='page'>{len}</span><br/>" \
               "size/type: <span class='size'>{{width}}x{{height}}</span>/<span class='type'>{meta.type}</span><br/>" \
               "file_hash: <span class='file'>{meta.file_hash}</span><br/>" \
               "image_hash: <span class='image'>{meta.image_hash}</span>" \
            .format(meta=image_hash, style=style, len=len(self.duplicates[self.dupe1].imageHashes))
        self.comic1Image.setDuplicate(self.duplicates[self.dupe1])
        self.comic1Image.setImage(image_hash.name)
        self.comic1Image.setText(text)
        self.comic1Image.setLabelStyle(style)

        text = "name: {{duplicate.path}}<br/>" \
               "page count: <span class='page'>{len}</span><br/>" \
               "size/type: <span class='size'>{{width}}x{{height}}</span>/<span class='type'>{score.type}</span><br/>" \
               "file_hash: <span class='file'>{score.file_hash}</span><br/>" \
               "image_hash: <span class='image'>{score.image_hash}</span>" \
            .format(score=score_hash, style=style, len=len(self.duplicates[self.dupe2].imageHashes))
        self.comic2Image.setDuplicate(self.duplicates[self.dupe2])
        self.comic2Image.setImage(score_hash.name)
        self.comic2Image.setText(text)
        self.comic2Image.setLabelStyle(style)


class QQlabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.setMinimumSize(1, 1)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def setPixmap(self, pixmap: QtGui.QPixmap) -> None:
        self.image = pixmap
        self.setMaximumWidth(pixmap.width())
        self.setMaximumHeight(pixmap.height())
        super().setPixmap(
            self.image.scaled(self.width(), self.height(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        if self.image is not None:
            super().setPixmap(self.image.scaled(self.width(), self.height(), QtCore.Qt.KeepAspectRatio,
                                                QtCore.Qt.SmoothTransformation))


class DupeImage(QtWidgets.QWidget):
    deleted = QtCore.pyqtSignal(str)

    def __init__(self, duplicate: Duplicate, style=".path {color: black;}.hash {color: black;}",
                 text="path: <span class='path'>{duplicate.path}</span><br/>hash: <span class='hash'>{duplicate.digest}</span>",
                 image="cover", parent=None):
        super().__init__(parent)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.image = QQlabel()
        self.label = QtWidgets.QLabel()
        self.duplicate = duplicate
        self.text = text
        self.labelStyle = style

        self.iHeight = 0
        self.iWidth = 0
        self.setStyleSheet("color: black;")
        self.label.setWordWrap(True)

        self.setImage(image)
        self.setLabelStyle(self.labelStyle)
        self.setText(self.text)

        # label.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.layout().addWidget(self.image)
        self.layout().addWidget(self.label)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        menu = QtWidgets.QMenu()
        delete_action = menu.addAction("delete")
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == delete_action:
            if self.duplicate.delete():
                self.hide()
                self.deleteLater()
                # print("signal emitted")
                self.deleted.emit(self.duplicate.path)

    def setDuplicate(self, duplicate: Duplicate):
        self.duplicate = duplicate
        self.setImage("cover")
        self.label.setText(
            f"<style>{self.labelStyle}</style>" + self.text.format(duplicate=self.duplicate, width=self.iWidth,
                                                                   height=self.iHeight))

    def setText(self, text):
        self.text = text
        self.label.setText(
            f"<style>{self.labelStyle}</style>" + self.text.format(duplicate=self.duplicate, width=self.iWidth,
                                                                   height=self.iHeight))

    def setImage(self, image):
        if self.duplicate is not None:
            pm = QtGui.QPixmap()
            if image == "cover":
                pm.loadFromData(self.duplicate.cover)
            else:
                pm.load(image)
            self.iHeight = pm.height()
            self.iWidth = pm.width()
            self.image.setPixmap(pm)

    def setLabelStyle(self, style):
        self.labelStyle = style
        self.label.setText(
            f"<style>{self.labelStyle}</style>" + self.text.format(duplicate=self.duplicate, width=self.iWidth,
                                                                   height=self.iHeight))


def extract(dupe_set, directory):
    for dupe in dupe_set:
        dupe.extract(unique_dir(os.path.join(directory, os.path.basename(dupe.path))))


def compare_dupe(dupe1: Dict[str, ImageMeta], dupe2: Dict[str, ImageMeta]):
    for k, image1 in dupe1.items():
        score = sys.maxsize
        file_hash = ""
        for k2, image2 in dupe2.items():
            tmp = ImageHasher.hamming_distance(image1.image_hash, image2.image_hash)
            if tmp < score:
                score = tmp
                file_hash = image2.file_hash

        dupe1[k].score = score
        dupe1[k].score_file_hash = file_hash


def make_key(x):
    return "<" + str(x.series) + " #" + str(x.issue) + " - " + str(x.title) + " - " + str(x.year) + ">"


def unique_dir(file_name):
    counter = 1
    file_name_parts = os.path.splitext(file_name)
    while True:
        if not os.path.lexists(file_name):
            return file_name
        file_name = file_name_parts[0] + ' (' + str(counter) + ')' + file_name_parts[1]
        counter += 1


app = None
settings = ComicTaggerSettings()


def main():
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description='ComicTagger Duplicate comparison script')
    parser.add_argument('-w', metavar='workdir', type=str, nargs=1, default=tempfile.mkdtemp(), help='work directory')
    parser.add_argument('paths', metavar='PATH', type=str, nargs='+', help='Path(s) to search for duplicates')
    args = parser.parse_args()

    style = MetaDataStyle.CIX
    global app
    workdir = args.w
    app = QtWidgets.QApplication(sys.argv)
    file_list = utils.get_recursive_filelist(args.paths)

    timer = QtCore.QTimer()
    timer.start(50)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    window = MainWindow(file_list, style, workdir)
    window.show()
    app.exec()
    shutil.rmtree(workdir, True)


def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    sys.stderr.write('\r')
    QtWidgets.QApplication.quit()


if __name__ == '__main__':
    main()
