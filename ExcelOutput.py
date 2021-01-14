import xlsxwriter as xw
from Action import *

class ExcelOutput:
    def __init__(self, output_filename, accounts):
        self.__filename = output_filename
        self._excel = None
        self._accounts = accounts

    def save(self):
        self._excel = xw.Workbook(self.__filename)
        try:
            for x in self._accounts:
                self.createAccountTab(x)
        finally:
            self._excel.close()

    def __visitAction(self, years, worksheet, row, level, action):
        nrow = row
        color = 'black' if  level == 0 else '#333333'
        formats = [ self._excel.add_format({'font_color': color, 'bold' : level == 0, 'num_format': 'yyyy-mm-dd'}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0, 'num_format': '#,##0.00'})]

        for x in formats:
            x.set_align('vcenter')

        formats[0].set_align('center')
        formats[3].set_align('center')
        formats[1].set_indent(level)

        worksheet.write_datetime(nrow, 0, action.time, formats[0])
        worksheet.write_string(nrow, 1, str(action.asset), formats[1])
        worksheet.write_string(nrow, 2, action.asset.name if action.asset.name else action.asset.ticker, formats[2])
        tname = action.type.name
        if action.type == EActionType.TAX and action.percent:
            tname = "%s - %s %%" % (action.type.name, str(action.percent))
        worksheet.write_string(nrow, 3, tname, formats[3])
        worksheet.write_number(nrow, 4, action.count, formats[4])

        italic = self._excel.add_format({'font_color': color, 'bold' : level == 0, 'num_format': '#,##0.00'})
        tax = action.tax
        if action.actions:
            tax = action.flat_tax
            italic.set_italic()

        for year, value in tax.items():
            idx = years.index(year)
            begin = 6+idx*3
            if not value[0].is_zero():
                worksheet.write_number(nrow, begin, value[0], italic)
            if not value[1].is_zero():
                worksheet.write_number(nrow, begin+1, value[1], italic)

        nrow += 1
        for a in action.actions:
            nrow = self.__visitAction(years, worksheet, nrow, level + 1, a)
       
        worksheet.set_row(row, None, None, {'level': level, 'collapsed': level != 0, 'hidden': level != 0})
        return nrow

    def __visitAsset(self, worksheet, row, asset, count, time):
        formats = [ self._excel.add_format({'font_color': 'black', 'bold' : False, 'num_format': 'yyyy-mm-dd'}),
                    self._excel.add_format({'font_color': 'black', 'bold' : False}),
                    self._excel.add_format({'font_color': 'black', 'bold' : False}),
                    self._excel.add_format({'font_color': 'black', 'bold' : False}),
                    self._excel.add_format({'font_color': 'black', 'bold' : False, 'num_format': '#,##0.00'})]

        for x in formats:
            x.set_align('vcenter')
        formats[0].set_align('center')
        formats[3].set_align('center')

        worksheet.write_datetime(row, 0, time, formats[0])
        worksheet.write_string(row, 1, str(asset), formats[1])
        worksheet.write_string(row, 2, asset.name if asset.name else asset.ticker, formats[2])
        worksheet.write_string(row, 3, asset.type, formats[3])
        worksheet.write_number(row, 4, count, formats[4])

        return row + 1

    def createAccountTab(self, account):
        years = list(reversed(sorted(list(set([x.time.year for x in account.actions if x.type != EActionType.DIVIDEND])))))
        worksheet_name = "%s - %s" % (account.broker,  account.name)
        worksheet = self._excel.add_worksheet(worksheet_name)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 40)
        worksheet.set_column(3, 4, 15)
        worksheet.outline_settings(True, False, False, True)

        menu_column = 0
        row = 2

        title = self._excel.add_format({'font_color': 'blue', 'bold' : True})
        title.set_align('center')
        worksheet.merge_range(row, 0, row, 4, "History", title)
        worksheet.write_url(0, menu_column, "internal:'%s'!A%d" % (worksheet_name, row+1), string="History")
        nrow = row+1
        menu_column += 1
        row += 2
        sum_tax = defaultdict(lambda : [Decimal(0), Decimal(0)]) 
        for action in  account.actions:
            if action.type == EActionType.DIVIDEND:
                continue
            row = self.__visitAction(years, worksheet, row, 0, action)
            for year, value in action.flat_tax.items():
                sum_tax[year][0] += value[0]
                sum_tax[year][1] += value[1]

        center_format = self._excel.add_format()
        center_format.set_align('center')
        worksheet.add_table(nrow, 0, row-1, 4, {'columns': [{'header':'Date', 'header_format': center_format},
                                                         {'header':'Ticker'},
                                                         {'header':'Name'},
                                                         {'header':'Action', 'header_format': center_format},
                                                         {'header': 'Value', 'header_format': center_format}]})

        total_format = self._excel.add_format({'bold' : True, 'num_format': '#,##0.00', 'font_color': 'white', 'bg_color' : '#4F81BD'})
        worksheet.write_row(row, 0, ['','','','',''], total_format)
        column = 6
        for year in years:
            worksheet.set_column(column-1, column-1, 5)
            worksheet.set_column(column, column+1, 10)
            worksheet.merge_range(nrow-1, column, nrow-1, column+1, year, title)
            worksheet.add_table(nrow, column, row-1, column+1, {'columns': [
                {'header':'Cost', 'header_format': center_format},
                {'header':'Income', 'header_format': center_format}]})
            worksheet.write_row(row, column, sum_tax[year], total_format)
            column += 3
        
       
        if [x for x in account.actions if x.type == EActionType.DIVIDEND]:
            row += 3
            nrow = row
            worksheet.merge_range(row-1, 0, row-1, 4, "Dividends", title)
            worksheet.write_url(0, menu_column, "internal:'%s'!A%d" % (worksheet_name, row), string="Dividends")
            menu_column += 1
            sum_tax = defaultdict(lambda : [Decimal(0), Decimal(0)])
            row += 1
            for action in  account.actions:
                if action.type != EActionType.DIVIDEND:
                    continue
                row = self.__visitAction(years, worksheet, row, 0, action)
                for year, value in action.flat_tax.items():
                    sum_tax[year][0] += value[0]
                    sum_tax[year][1] += value[1]

            worksheet.add_table(nrow, 0, row-1, 4, {'columns': [{'header':'Date', 'header_format': center_format},
                                                                {'header':'Ticker'},
                                                                {'header':'Name'},
                                                                {'header':'Action', 'header_format': center_format},
                                                                {'header': 'Value', 'header_format': center_format}]})
            worksheet.write_row(row, 0, ['','','','',''], total_format)
            column = 6
            for year in years:
                worksheet.set_column(column-1, column-1, 5)
                worksheet.set_column(column, column+1, 10)
                worksheet.merge_range(nrow-1, column, nrow-1, column+1, year, title)
                worksheet.add_table(nrow, column, row-1, column+1, {'columns': [
                    {'header':'Paid', 'header_format': center_format},
                    {'header':'19%', 'header_format': center_format}]})
                worksheet.write_row(row, column, sum_tax[year], total_format)
                column += 3

        assets = account.assets
        if assets:
            row += 3
            nrow  = row
            worksheet.merge_range(row-1, 0, row-1, 4, "Assets", title)
            worksheet.write_url(0, menu_column, "internal:'%s'!A%d" % (worksheet_name, row), string="Assets")
            menu_column += 1
            row += 1
            for asset, value, time in assets:
                row = self.__visitAsset(worksheet, row, asset, value, time)
            worksheet.add_table(nrow, 0, row-1, 4, {'columns': [{'header':'Last Change', 'header_format': center_format},
                                                                {'header':'Ticker'},
                                                                {'header':'Name'},
                                                                {'header':'Type', 'header_format': center_format},
                                                                {'header':'Count', 'header_format': center_format}]})
            worksheet.write_row(row, 0, ['','','','',''], total_format)
