import os
import random
import sys
import time
from collections import deque


def clearTerminal():
    if sys.platform == 'linux' or sys.platform == 'linux2' or sys.platform == 'darwin':
        os.system('clear')
    elif sys.platform == 'cygwin' or sys.platform == 'win32' or sys.platform == 'msys':
        os.system('cls')


COLOR_RED = '\033[91m'
COLOR_YELLOW = '\033[93m'
COLOR_GREEN = '\033[92m'
COLOR_END = '\033[0m'

oldCodeByNew = [i for i in range(256)]
newCodeByOld = [0] * 256
random.seed(123456789)  # сид для одинакого шифрования при разных запусках
random.shuffle(oldCodeByNew)
for i in range(256):
    newCodeByOld[oldCodeByNew[i]] = i


class Field:
    def __init__(self, cntRows=0, cntCols=0, cntMines=0):
        self.isFieldBuilt = False
        self.cntFlags = 0
        self.lastNotification = ''
        self.cntRows = cntRows
        self.cntCols = cntCols
        self.cntMines = cntMines
        self.fieldArr = [['.'] * cntCols for _ in
                         range(cntRows)]  # * - мина; цифра - есть мины поблизости; . - нет мин поблизости
        self.fieldVisible = [[0] * cntCols for _ in
                             range(cntRows)]  # 2 - установлен флаг; 1 - клетка открыта; 0 - еще не открыта

        self.isInField = lambda row, col: 0 <= row < cntRows and 0 <= col < cntCols

    def buildField(self, row, col):  # построение поля после первого хода, чтобы первый ход не был проигрышным
        cells = [(x, y) for x in range(self.cntRows) for y in range(self.cntCols) if x != row or y != col]
        random.shuffle(cells)
        cells = cells[:self.cntMines]
        for x, y in cells:
            self.fieldArr[x][y] = '*'
        for x in range(self.cntRows):
            for y in range(self.cntCols):
                if self.fieldArr[x][y] == '*':
                    continue
                minesNearby = 0
                for xx in range(x - 1, x + 2):
                    for yy in range(y - 1, y + 2):
                        minesNearby += self.isInField(xx, yy) and self.fieldArr[xx][yy] == '*'
                if minesNearby > 0:
                    self.fieldArr[x][y] = str(minesNearby)

    def findCellsToOpen(self, row,
                        col):  # алгоритм обхода в ширину для нахождения области, которую необходимо открыть после хода
        used = [[False] * self.cntCols for _ in range(self.cntRows)]
        q = deque()
        q.append((row, col))
        visitedCells = []
        while len(q) > 0:
            row, col = q.popleft()
            visitedCells.append((row, col))
            for nextRow in range(row - 1, row + 2):
                for nextCol in range(col - 1, col + 2):
                    if self.isInField(nextRow, nextCol) and self.fieldArr[nextRow][nextCol] == '.' and not \
                            used[nextRow][nextCol]:
                        used[nextRow][nextCol] = True
                        q.append((nextRow, nextCol))
        newUsed = used.copy()
        addToVisited = []
        for row, col in visitedCells:
            for nextRow in range(row - 1, row + 2):
                for nextCol in range(col - 1, col + 2):
                    if self.isInField(nextRow, nextCol) and not newUsed[nextRow][nextCol] and self.fieldArr[nextRow][
                        nextCol] != '*':
                        newUsed[nextRow][nextCol] = True
                        addToVisited.append((nextRow, nextCol))
        visitedCells.extend(addToVisited)
        return visitedCells

    def printVisible(self):  # вывод поля
        for row in range(self.cntRows):
            for col in range(self.cntCols):
                if self.fieldVisible[row][col] == 0:
                    print('#', end='')
                elif self.fieldVisible[row][col] == 1:
                    print(self.fieldArr[row][col], end='')
                else:
                    print('F', end='')
            print()

    def printColourful(self, color):  # вывод поля при наступлении на мину или победе
        for row in range(self.cntRows):
            for col in range(self.cntCols):
                if self.fieldArr[row][col] == '*':
                    print(color + '*' + COLOR_END, end='')
                elif self.fieldVisible[row][col] == 0:
                    print('#', end='')
                elif self.fieldVisible[row][col] == 1:
                    print(self.fieldArr[row][col], end='')
                else:
                    print('F', end='')
            print()

    def getCntClosed(self):  # подсчет количества неоткрытых клеток
        ans = self.cntRows * self.cntCols
        for i in range(self.cntRows):
            ans -= self.fieldVisible[i].count(1)
        return ans

    def OpenCell(self, row, col, person):
        if not self.isFieldBuilt:
            self.buildField(row, col)
            self.isFieldBuilt = True
        if self.fieldArr[row][col] == '*':
            clearTerminal()
            print(COLOR_RED + person + ' на мину. Игра окончена' + COLOR_END)
            self.printColourful(COLOR_RED)
            return False
        if self.fieldVisible[row][col] == 1:
            self.lastNotification = 'Эта клетка уже открыта'
            return True
        if self.fieldArr[row][col] == '.':
            for x, y in self.findCellsToOpen(row, col):
                self.fieldVisible[x][y] = 1
        else:
            self.fieldVisible[row][col] = 1
        return True

    def SetFlag(self, row, col):
        if self.cntFlags == self.cntMines:
            self.lastNotification = 'Вы не можете больше устанавливать флаги, так как их уже установлено столько же, сколько и мин. Попробуйте сделать другой ход'
        else:
            if self.fieldVisible[row][col] == 1:
                self.lastNotification = 'В эту клетку нельзя поставить флаг, так как она уже открыта. Попробуйте сделать другой ход.'
            elif self.fieldVisible[row][col] == 0:
                self.fieldVisible[row][col] = 2
                self.cntFlags += 1
            else:
                self.fieldVisible[row][col] = 0
                self.cntFlags -= 1

    def SaveToFile(self, filename):
        # что надо зашифровать: cntRows, cntCols, cntMines, fieldArr, fieldVisible, isFieldBuilt, cntFlags
        arrayToWrite = [chr(newCodeByOld[self.cntRows]), chr(newCodeByOld[self.cntCols]),
                        chr(newCodeByOld[self.cntMines])]
        for i in range(self.cntRows):
            for j in range(self.cntCols):
                arrayToWrite.append(chr(newCodeByOld[ord(self.fieldArr[i][j])]))
        for i in range(self.cntRows):
            for j in range(self.cntCols):
                arrayToWrite.append(chr(newCodeByOld[self.fieldVisible[i][j]]))
        arrayToWrite.append(chr(newCodeByOld[int(self.isFieldBuilt)]))
        arrayToWrite.append(chr(newCodeByOld[self.cntFlags >> 8]))
        arrayToWrite.append(chr(newCodeByOld[self.cntFlags & 255]))
        fileToWrite = open(filename, "w")
        fileToWrite.write(''.join(arrayToWrite))
        fileToWrite.close()

    def LoadFromFile(self, filename):
        try:
            fileToRead = open(filename, "r", encoding='utf8')
        except:
            self.lastNotification = "Такого файла нет"
            return
        stringFromFile = fileToRead.read()
        fileToRead.close()
        self.cntRows, self.cntCols, self.cntMines = [oldCodeByNew[ord(stringFromFile[_])] for _ in range(3)]
        for i in range(self.cntRows):
            for j in range(self.cntCols):
                field.fieldArr[i][j] = chr(oldCodeByNew[ord(stringFromFile[3 + i * self.cntCols + j])])
        for i in range(self.cntRows):
            for j in range(self.cntCols):
                field.fieldVisible[i][j] = oldCodeByNew[
                    ord(stringFromFile[3 + self.cntRows * self.cntCols + i * self.cntCols + j])]
        stringFromFile = stringFromFile[3 + 2 * self.cntRows * self.cntCols:]
        self.isFieldBuilt = bool(oldCodeByNew[ord(stringFromFile[0])])
        self.cntFlags = (oldCodeByNew[ord(stringFromFile[1])] << 8) + oldCodeByNew[ord(stringFromFile[2])]


def Greating():
    clearTerminal()

    if field.getCntClosed() == field.cntMines:
        print(COLOR_GREEN + 'Вы победили!' + COLOR_END)
        field.printColourful(COLOR_GREEN)
        exit(0)

    print(COLOR_YELLOW + field.lastNotification + COLOR_END)
    field.lastNotification = ''

    field.printVisible()


field = Field()

while True:  # ввод размеров поля с отлавливанием неверного формата
    try:
        xx, yy = map(int, input('Введите количество строк и столбцов поля (от 1 до 255): ').split())
        if xx <= 0 or yy > 255 or xx <= 0 or yy > 255:
            print(COLOR_RED + 'Размер не подходит под ограничение. Попробуйте снова.' + COLOR_END)
            continue
    except:
        print(COLOR_RED + 'Неправильный формат ввода. Попробуйте снова.' + COLOR_END)
        continue
    break

while True:  # ввод количества мин с отлавливанием неверного формата
    try:
        rr = int(input('Введите количество мин (рекомендуется около ' + str(xx * yy // 6) + '): '))
        if rr < 0 or rr >= xx * yy:
            print(COLOR_RED + 'Неправильный формат ввода. Попробуйте снова.' + COLOR_END)
            continue
    except:
        print(COLOR_RED + 'Неправильный формат ввода. Попробуйте снова.' + COLOR_END)
        continue
    break
field = Field(xx, yy, rr)

is_bot_running = False

while True:
    Greating()

    if is_bot_running:
        if not field.isFieldBuilt:
            row = random.randint(0, field.cntRows - 1)
            col = random.randint(0, field.cntCols - 1)
            print('бот делает ход:', row + 1, col + 1, 'Open', sep='')
            print('Ожидайте 5 секунд')
            time.sleep(5)
            field.OpenCell(row, col, 'Бот наткнулся')
            field.isFieldBuilt = True
            continue
        for row in range(field.cntRows):
            for col in range(field.cntCols):
                if field.fieldVisible[row][col] == 2:
                    print('Бот делает ход:', row + 1, col + 1, 'Flag', sep=' ')
                    print('Ожидайте 5 секунд')
                    time.sleep(5)
                    field.SetFlag(row, col)
        is_cell_found = False
        for row in range(field.cntRows):
            for col in range(field.cntCols):
                if field.fieldVisible[row][col] == 1:  # if it is a number
                    cnt_closed = 0  # calc count of closed cells next to current
                    for next_row in range(row - 1, row + 2):
                        for next_col in range(col - 1, col + 2):
                            if field.isInField(next_col, next_row):
                                cnt_closed += field.fieldVisible[next_row][next_col] != 1
                    number_in_cell = 0
                    if field.fieldArr[row][col].isnumeric():
                        number_in_cell = int(field.fieldArr[row][col])
                    if cnt_closed == number_in_cell:
                        for next_row in range(row - 1, row + 2):
                            for next_col in range(col - 1, col + 2):
                                if field.isInField(next_col, next_row) and field.fieldVisible[next_row][next_col] != 1:
                                    print('Бот делает ход:', next_row + 1, next_col + 1, 'Flag', sep=' ')
                                    print('Ожидайте 5 секунд')
                                    time.sleep(5)
                                    field.SetFlag(next_row, next_col)
                                    is_cell_found = True
                                    Greating()
        for row in range(field.cntRows):
            for col in range(field.cntCols):
                if field.fieldVisible[row][col] == 1:  # if it is a number
                    cnt_closed = 0  # calc count of closed cells next to current
                    cnt_flags_here = 0
                    for next_row in range(row - 1, row + 2):
                        for next_col in range(col - 1, col + 2):
                            if field.isInField(next_col, next_row):
                                cnt_closed += field.fieldVisible[next_row][next_col] != 1
                                cnt_flags_here += field.fieldVisible[next_row][next_col] == 2
                    number_in_cell = 0
                    field.fieldArr
                    if field.fieldArr[row][col].isnumeric():
                        number_in_cell = int(field.fieldArr[row][col])
                    if cnt_closed - cnt_flags_here == number_in_cell:
                        for next_row in range(row - 1, row + 2):
                            for next_col in range(col - 1, col + 2):
                                if field.isInField(next_col, next_row) and field.fieldVisible[next_row][next_col] == 0:
                                    print('Бот делает ход:', next_row + 1, next_col + 1, 'Open', sep=' ')
                                    print('Ожидайте 5 секунд')
                                    time.sleep(5)
                                    if not field.OpenCell(next_row, next_col, 'Бот наткнулся'):
                                        exit(0)
                                    is_cell_found = True
                                    Greating()
        if field.getCntClosed() == field.cntMines:
            print(COLOR_GREEN + 'Бот победил!' + COLOR_END)
            field.printColourful(COLOR_GREEN)
            # дописать сохренение в файл
            exit(0)
        if not is_cell_found:
            print('Клетка, в которой гарантирована бомба, не найдена. :(  Поэтому бот ходит наугад')
            closed_cells = []
            for col in range(field.cntRows):
                for row in range(field.cntCols):
                    if field.fieldVisible[row][col] == 0:
                        closed_cells.append([col, row])
            col, row = closed_cells[random.randint(0, len(closed_cells) - 1)]
            print('Бот делает ход:', row + 1, col + 1, 'Open', sep=' ')
            print('Ожидайте 5 секунд')
            time.sleep(5)
            if not field.OpenCell(row, col, 'Бот наткнулся'):
                print()
                # дописать сохренение в файл
                exit(0)
            Greating()

    print('Введите команду (без кавычек). Типы команд:')
    print('1. "X Y Open" - Открыть клетку, нумерация с 1')
    print('2. "X Y Flag" - Поставить/снять флаг с клетки, нумерация с 1')
    print('3. "Load filename.txt" - загрузить файл сохранения')
    print('4. "Save filename.txt" - сохранить игру в файл')
    print('5. "Bot" - запутить бота для решения поля (нельзя будет остановить, пока он не закончит)')
    s = input()
    if s.count(' ') == 0:
        if s == 'Bot':
            is_bot_running = True
        else:
            field.lastNotification = 'Эта команда не поддерживается'
            continue
    elif s.count(' ') == 2:
        row, col, commandType = s.split()
        try:
            row, col = int(row) - 1, int(col) - 1
        except:
            field.lastNotification = 'Неверные координаты поля'
            continue
        if not field.isInField(row, col):
            field.lastNotification = 'Данная клетка находится вне поля'
            continue
        if commandType == 'Open':
            if not field.OpenCell(row, col, 'Вы наткнулись'):
                exit(0)
        elif commandType == 'Flag':
            field.SetFlag(row, col)
        else:
            field.lastNotification = 'Эта команда не поддерживается'
            continue
    else:
        try:
            commandType, filename = s.split()
        except:
            field.lastNotification = 'Эта команда не поддерживается'
            continue
        if commandType == 'Save':
            field.SaveToFile(filename)
        elif commandType == 'Load':
            field.LoadFromFile(filename)
        else:
            field.lastNotification = 'Эта команда не поддерживается'
            continue
