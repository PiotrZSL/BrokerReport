import xlsxwriter as xw
from Action import *
from Account import ETaxType
from TaxFields import *
import Rounding

class ExcelOutput:
    def __init__(self, output_filename, accounts):
        self.__filename = output_filename
        self._excel = None
        self._accounts = accounts
        self._taxCalculations = []

    def save(self):
        self._excel = xw.Workbook(self.__filename)
        try:
            taxPage = self._excel.add_worksheet("Tax Summary")
            for x in self._accounts:
                self.__addAccountAssetsPage(x)
                self.__addAccountHistoryPage(x)
                self.__addAccountDividendPage(x)
            self.__addTaxSummary(taxPage)
        finally:
            self._excel.close()

    def __getFieldOrEmpty(self, accountId, field, year):
        for a, y, f, v in self._taxCalculations:
            if a == accountId and y == year and f == field:
                return v
        return Decimal(0.0)

    def __addTaxSummary(self, worksheet):
        years = list(set([ x[1] for x in self._taxCalculations ]))
        row = 0
        worksheet.set_column(0, 0, 30)
        number_format = self._excel.add_format({'num_format': '#,##0.00'})
        name_format = self._excel.add_format({'bold' : True})
        center_format = self._excel.add_format()
        center_format.set_align('center')

        value_names = [ FIELD_EQUITY_PIT8C_COST, FIELD_EQUITY_PIT8C_INCOME, FIELD_EQUITY_OTHER_COST, FIELD_EQUITY_OTHER_INCOME, FIELD_EQUITY_SUM, FIELD_DIVIDEND_LOCAL, FIELD_DIVIDEND_REMOTE_PAYED, FIELD_DIVIDEND_REMOTE_TAX, FIELD_DIVIDEND_REMOTE_SUM ]
        worksheet.set_column(1, len(value_names)+2, 15)
        columns = [ {'header':'Account', 'header_format': center_format } ]
        for value in value_names:
            columns.append({'header':value, 'header_format': center_format })
        title = self._excel.add_format({'font_color': 'blue', 'bold' : True})
        title.set_align('center')
        total_format = self._excel.add_format({'bold' : True, 'num_format': '#,##0.00', 'font_color': 'white', 'bg_color' : '#4F81BD'})

        for year in reversed(years):
            worksheet.merge_range(row, 0, row, len(value_names), "Year - %s" % (str(year)), title)
            
            row += 1
            begin = row
            row += 1
            sum_values = [ Decimal(0) for x in value_names ]

            for account in self._accounts:
                worksheet.write_string(row, 0, account.id, name_format)

                for idx, value in enumerate(value_names):
                    result = self.__getFieldOrEmpty(account.id, value, year)
                    worksheet.write_number(row, 1+idx, result, number_format)
                    sum_values[idx] += result

                row += 1

            
            worksheet.add_table(begin, 0, row-1, len(value_names), {'columns': columns})
            worksheet.write_row(row, 0, [''] + sum_values, total_format)

            row += 2


    def __addAccountHistoryPage(self, account):
        years = list(reversed(sorted(list(set([x.time.year for x in account.actions if x.type != EActionType.DIVIDEND])))))
        if not years:
            return False
        worksheet_name = "%s-%s-H" % (account.broker,  account.name)
        worksheet = self._excel.add_worksheet(worksheet_name)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 40)
        worksheet.set_column(3, 3, 10)
        worksheet.set_column(4, 5, 15)
        worksheet.outline_settings(True, False, False, True)
        
        row = 1
        title = self._excel.add_format({'font_color': 'blue', 'bold' : True})
        title.set_align('center')
        worksheet.merge_range(row, 0, row, 4, "History", title)
        
        nrow = row+1
        row += 2

        def calcTax(value):
            return [-value[0], value[1], value[0]+value[1]]
        
        sum_tax = defaultdict(lambda : [Decimal(0), Decimal(0), Decimal(0)])
        for action in  reversed(account.actions):
            if action.type == EActionType.DIVIDEND:
                continue
            row = self.__visitAction(years, worksheet, row, 0, action, None if account.taxType == ETaxType.NO_TAX else calcTax, sum_tax, Rounding.TAX_TRANSACTION_COST_ROUNDING, Rounding.TAX_TRANSACTION_GAIN_ROUNDING)

        center_format = self._excel.add_format()
        center_format.set_align('center')
        worksheet.add_table(nrow, 0, row-1, 5, {'columns': [{'header':'Date', 'header_format': center_format},
                                                            {'header':'Ticker'},
                                                            {'header':'Name'},
                                                            {'header':'Country'},
                                                            {'header':'Action', 'header_format': center_format},
                                                            {'header':'Value', 'header_format': center_format}]})

        total_format = self._excel.add_format({'bold' : True, 'num_format': '#,##0.00', 'font_color': 'white', 'bg_color' : '#4F81BD'})
        worksheet.write_row(row, 0, ['','','','','',''], total_format)
        
        if account.taxType == ETaxType.NO_TAX:
            return True

        column = 7
        columns = [{'header': FIELD_EQUITY_PIT8C_COST if account.taxType == ETaxType.PIT8C else FIELD_EQUITY_OTHER_COST, 'header_format': center_format},
                   {'header': FIELD_EQUITY_PIT8C_INCOME if account.taxType == ETaxType.PIT8C else FIELD_EQUITY_OTHER_INCOME, 'header_format': center_format},
                   {'header': FIELD_EQUITY_SUM, 'header_format': center_format}]
        for year in years:
            worksheet.set_column(column-1, column-1, 5)
            worksheet.set_column(column, column+2, 15)
            worksheet.merge_range(nrow-1, column, nrow-1, column+2, "Tax - %d" % (year), title)
            worksheet.add_table(nrow, column, row-1, column+2, {'columns': columns})
            sum_tax[year][0] = Rounding.round(sum_tax[year][0], Rounding.TAX_ACCOUNT_COST_ROUNDING) 
            sum_tax[year][1] = Rounding.round(sum_tax[year][1], Rounding.TAX_ACCOUNT_GAIN_ROUNDING)
            sum_tax[year][2] = sum_tax[year][1] - sum_tax[year][0]
            worksheet.write_row(row, column, sum_tax[year], total_format)
            self._taxCalculations.append((account.id, year, columns[0]['header'], sum_tax[year][0]))
            self._taxCalculations.append((account.id, year, columns[1]['header'], sum_tax[year][1]))
            self._taxCalculations.append((account.id, year, columns[2]['header'], sum_tax[year][2]))
            column += 4
        return True


    def __addAccountDividendPage(self, account):
        years = list(reversed(sorted(list(set([x.time.year for x in account.actions if x.type == EActionType.DIVIDEND])))))
        if not years:
            return False
        worksheet_name = "%s-%s-D" % (account.broker,  account.name)
        worksheet = self._excel.add_worksheet(worksheet_name)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 40)
        worksheet.set_column(3, 3, 10)
        worksheet.set_column(4, 5, 15)
        worksheet.outline_settings(True, False, False, True)
        
        row = 1
        title = self._excel.add_format({'font_color': 'blue', 'bold' : True})
        title.set_align('center')
        worksheet.merge_range(row, 0, row, 4, "History", title)
        
        nrow = row+1
        row += 2
        
        def calcTax(pit8c, isin, value):
            if pit8c and isin.startswith("PL"):
                return [Decimal(0), Decimal(0), Decimal(0), Decimal(0)]

            if isin.startswith("PL"):
                return [value[1], Decimal(0), Decimal(0), Decimal(0)]
            else:
                return [Decimal(0), -value[0], value[1], value[1]+value[0]]
        
        sum_tax = defaultdict(lambda : [Decimal(0), Decimal(0), Decimal(0), Decimal(0)]) 
        for action in reversed(account.actions):
            if action.type != EActionType.DIVIDEND:
                continue
            localCalcTax = lambda x : calcTax(account.taxType == ETaxType.PIT8C, action.asset.isin, x)
            row = self.__visitAction(years, worksheet, row, 0, action, None if account.taxType == ETaxType.NO_TAX else localCalcTax, sum_tax, Rounding.TAX_TRANSACTION_DIVIDEND_TAX_PAYED_ROUNDING, Rounding.TAX_TRANSACTION_DIVIDEND_TAX_BASE_ROUNDING)

        center_format = self._excel.add_format()
        center_format.set_align('center')
        worksheet.add_table(nrow, 0, row-1, 5, {'columns': [{'header':'Date', 'header_format': center_format},
                                                            {'header':'Ticker'},
                                                            {'header':'Name'},
                                                            {'header':'Country'},
                                                            {'header':'Action', 'header_format': center_format},
                                                            {'header':'Value', 'header_format': center_format}]})

        total_format = self._excel.add_format({'bold' : True, 'num_format': '#,##0.00', 'font_color': 'white', 'bg_color' : '#4F81BD'})
        worksheet.write_row(row, 0, ['','','','','',''], total_format)

        if account.taxType == ETaxType.NO_TAX:
            return True
        
        column = 7
        columns = [
                {'header': FIELD_DIVIDEND_LOCAL, 'header_format': center_format},
                {'header': FIELD_DIVIDEND_REMOTE_PAYED, 'header_format': center_format},
                {'header': FIELD_DIVIDEND_REMOTE_TAX, 'header_format': center_format},
                {'header': FIELD_DIVIDEND_REMOTE_SUM, 'header_format': center_format}]
        for year in years:
            worksheet.set_column(column-1, column-1, 5)
            worksheet.set_column(column, column+3, 15)
            worksheet.merge_range(nrow-1, column, nrow-1, column+3, "Tax - %d" % (year), title)
            worksheet.add_table(nrow, column, row-1, column+3, {'columns' : columns })
            sum_tax[year][0] = Rounding.round(sum_tax[year][0], Rounding.TAX_ACCOUNT_DIVIDEND_TAX_BASE_ROUNDING) 
            sum_tax[year][1] = Rounding.round(sum_tax[year][1], Rounding.TAX_ACCOUNT_DIVIDEND_TAX_PAYED_ROUNDING) 
            sum_tax[year][2] = Rounding.round(sum_tax[year][2], Rounding.TAX_ACCOUNT_DIVIDEND_TAX_BASE_ROUNDING)
            sum_tax[year][3] = sum_tax[year][2] - sum_tax[year][1]
            worksheet.write_row(row, column, sum_tax[year], total_format)
            self._taxCalculations.append((account.id, year, columns[0]['header'], sum_tax[year][0]))
            self._taxCalculations.append((account.id, year, columns[1]['header'], sum_tax[year][1]))
            self._taxCalculations.append((account.id, year, columns[2]['header'], sum_tax[year][2]))
            self._taxCalculations.append((account.id, year, columns[3]['header'], sum_tax[year][3]))
            column += 5
        return True

    def __visitAction(self, years, worksheet, row, level, action, funcColumns, sumTax, roundCost = None, roundIncome = None):
        nrow = row
        color = 'black' if  level == 0 else '#333333'
        formats = [ self._excel.add_format({'font_color': color, 'bold' : level == 0, 'num_format': 'yyyy-mm-dd'}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0}),
                    self._excel.add_format({'font_color': color, 'bold' : level == 0, 'num_format': '#,##0.00'})]

        for x in formats:
            x.set_align('vcenter')

        formats[0].set_align('center')
        formats[3].set_align('center')
        formats[4].set_align('center')
        formats[1].set_indent(level)

        worksheet.write_datetime(nrow, 0, action.time, formats[0])
        worksheet.write_string(nrow, 1, str(action.asset), formats[1])
        worksheet.write_string(nrow, 2, action.asset.name if action.asset.name else action.asset.ticker, formats[2])
        country = action.country
        worksheet.write_string(nrow, 3, "" if not country else country, formats[3])
        tname = action.type.name
        if action.type == EActionType.TAX and action.percent:
            tname = "%s - %s %%" % (action.type.name, str(action.percent))
        worksheet.write_string(nrow, 4, tname, formats[4])
        worksheet.write_number(nrow, 5, action.count, formats[5])

        if funcColumns:
            italic = self._excel.add_format({'font_color': color, 'bold' : level == 0, 'num_format': '#,##0.00'})
            non_italic = self._excel.add_format({'font_color': color, 'bold' : level == 0, 'num_format': '#,##0.00'})
            italic.set_italic()

            tax = action.tax
            flat_tax = action.flat_tax

            for year, value in flat_tax.items():
                year_index = years.index(year)

                ftax = funcColumns(value)
                if 0 == level:
                    ftax = funcColumns((Rounding.round(value[0], roundCost), Rounding.round(value[1], roundIncome)))
                    for idx, v in enumerate(ftax):
                        sumTax[year][idx] += v

                ttax = funcColumns(tax[year] if year in tax else [Decimal(0), Decimal(0)])
                
                begin = 7+year_index*(len(ftax)+1)
                for idx, it in enumerate(ftax):
                    if not it.is_zero():
                        worksheet.write_number(nrow, begin+idx, it, italic if it != ttax[idx] else non_italic)

        nrow += 1
        for a in action.actions:
            nrow = self.__visitAction(years, worksheet, nrow, level + 1, a, funcColumns, sumTax)
       
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

    def __addAccountAssetsPage(self, account):
        assets = account.assets
        if not assets:
            return False

        worksheet_name = "%s-%s-A" % (account.broker, account.name)
        worksheet = self._excel.add_worksheet(worksheet_name)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 40)
        worksheet.set_column(3, 4, 15)
        worksheet.outline_settings(True, False, False, True)
        
        row = 2
        title = self._excel.add_format({'font_color': 'blue', 'bold' : True})
        title.set_align('center')
            
        worksheet.merge_range(row-1, 0, row-1, 4, "Assets", title)
        nrow = row
        row += 1
        for asset, value, time in assets:
            row = self.__visitAsset(worksheet, row, asset, value, time)
        
        center_format = self._excel.add_format()
        center_format.set_align('center')
        worksheet.add_table(nrow, 0, row-1, 4, {'columns': [{'header':'Last Change', 'header_format': center_format},
                                                            {'header':'Ticker'},
                                                            {'header':'Name'},
                                                            {'header':'Type', 'header_format': center_format},
                                                            {'header':'Count', 'header_format': center_format}]})
        total_format = self._excel.add_format({'bold' : True, 'num_format': '#,##0.00', 'font_color': 'white', 'bg_color' : '#4F81BD'})
        worksheet.write_row(row, 0, ['','','','',''], total_format)
        return True
