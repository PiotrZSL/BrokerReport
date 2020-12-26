from IngAccount import IngAccount
from MBankAccount import MBankAccount
from DifAccount import DifAccount
from ExanteAccount import ExanteAccount
from ExcelOutput import ExcelOutput

from TaxCalculator import TaxCalculator

import argparse, os, os.path

parser = argparse.ArgumentParser(description='Makler Reports Processor')
parser.add_argument('--cache-file', required=False, help='location of cache file used to reduce network usage')
parser.add_argument('--reports-folder', required=True, help='location of folder with reports to import, folder should contain `broker/account_name` folders with required reports in it')
parser.add_argument('--output-xls', required=True, help='output location of cumulative excel report to generate')

args = parser.parse_args()

accounts = []
for broker in os.listdir(args.reports_folder):
    for account in os.listdir(os.path.join(args.reports_folder, broker)):
        if 'ING' == broker:
            try:
                accounts.append(IngAccount(account, os.path.join(args.reports_folder, broker, account)))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e

        if 'MBANK' == broker:
            try:
                accounts.append(MBankAccount(account, os.path.join(args.reports_folder, broker, account)))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e
        
        if 'DIF' == broker:
            try:
                accounts.append(DifAccount(account, os.path.join(args.reports_folder, broker, account)))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e
        
        if 'EXANTE' == broker:
            try:
                accounts.append(ExanteAccount(account, os.path.join(args.reports_folder, broker, account)))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e

for x in accounts:
    TaxCalculator(x).calculate()

for x in accounts:
    x.dump()

ExcelOutput(args.output_xls, accounts).save()
