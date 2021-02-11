from IngAccount import IngAccount
from MBankAccount import MBankAccount
from DifAccount import DifAccount
from ExanteAccount import ExanteAccount
from CustomAccount import CustomAccount
from ExcelOutput import ExcelOutput
from Cache import loadCache, saveCache

from TaxCalculator import TaxCalculator

import argparse, os, os.path

parser = argparse.ArgumentParser(description='Makler Reports Processor')
parser.add_argument('--cache-file', required=False, help='location of optional cache file used to reduce network usage')
parser.add_argument('--reports-folder', required=True, help='location of folder with reports to import, folder should contain `broker/account_name` folders with required reports in it')
parser.add_argument('--output-xls', required=True, help='output location of cumulative excel report to generate')
parser.add_argument('-v', '--verbose', required=False, help='Shows more detailed output', action="store_true")

args = parser.parse_args()
loadCache(args.cache_file)

print("\nImporting & processing reports", flush=True)
accounts = []
for broker in os.listdir(args.reports_folder):
    if not os.path.isdir(os.path.join(args.reports_folder, broker)):
        continue

    for account in os.listdir(os.path.join(args.reports_folder, broker)):

        directory = os.path.join(args.reports_folder, broker, account)
        if not os.path.isdir(directory):
            continue
        
        if 'ING' == broker:
            try:
                accounts.append(IngAccount(account, directory))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e

        if 'MBANK' == broker:
            try:
                accounts.append(MBankAccount(account, directory))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e
        
        if 'DIF' == broker:
            try:
                accounts.append(DifAccount(account, directory))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e
        
        if 'EXANTE' == broker:
            try:
                accounts.append(ExanteAccount(account, directory))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e
        
        if 'CUSTOM' == broker:
            try:
                accounts.append(CustomAccount(account, directory))
                print(" - imported %s/%s" % (broker, account), flush=True)
                continue
            except Exception as e:
                print(" - failed to import %s/%s - %s" % (broker, account, e), flush=True)
                raise e

if args.verbose:
    for x in accounts:
        x.dump()

for x in accounts:
    TaxCalculator(x).calculate()


ExcelOutput(args.output_xls, accounts).save()
print("Saved %s" % (args.output_xls), flush=True)
saveCache(args.cache_file)
print("Finished...\n", flush=True)
