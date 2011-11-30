from datetime import date
import hashlib
import os
import re

raw_parsers = (
    ['Calling completed', 'ipn_completed'],
    ['Completed IPN received', 'ipn_completed_received'],
    ['Contribution not found', 'ipn_fatal'],
    ['IPN received', 'ipn_received'],
    ['Paypal Error', 'paypal_error'],
    ['HTTP Error', 'http_error'],
    ['<urlopen error The read operation timed out>', 'http_error'],
    ['\[\d+\] PayPal sent a transaction', 'ipn_fatal'],
    ['\[\d+\] PayPal Data', 'ipn_fatal'],
    ['Completed successfully processed', 'ipn_complete'],
    ['Getting refund permission URL', 'refund_permission'],
    ['Refund successfully processed', 'ipn_refund_processed'],
    ['Refund IPN received', 'ipn_refund_received'],
    ['User approved refund for addon', 'refund_approved'],
    ['Refund issued for transaction', 'refund_issued'],
    ['Refund successful for', 'ipn_refund_successful'],
    ['Paypal returned permissions for token', 'refund_permission_complete'],
    ['\[\d+] Expecting \'VERIFIED\' from PayPal, got', 'ipn_check_fail'],
    ['Refund declined for transaction', 'refund_declined'],
    ['Checking refund permission for token', ''],
    ['AddonPremium', ''],
    ['Refund error', 'refund_error'],
    ['Got refund token', '']
)

prefix = '^(?P<level>INFO|WARNING|ERROR|DEBUG) '
parsers = [(re.compile('%s%s' % (prefix, r)), m) for r, m in raw_parsers]

from functools import partial

def trunc(length, match):
    item = match.group(0)
    return item[:length] + ((len(item) - length) * '*')

raw_scrubs = (
    ['tracking_id=[a-f0-9]{32}', partial(trunc, 22)],
    ['email=.*?&', partial(trunc, 6)],
    ['pay_key=[A-Z0-9\-]+', partial(trunc, 20)],
    ["'payer_email': u'.*?'", partial(trunc, 17)],
)

scrubs = [(re.compile(r), f) for r, f in raw_scrubs]

from app.models import PapalStats

class Parser(object):

    def __init__(self, filename):
        self.filename = filename

    def process(self):
        with open(self.filename) as fl:
            lines = fl.read().split('\n')
            for line in lines:
                self.parse_line(line)

    def parse_line(self, line):
        try:
            data = line.split('z.paypal:')[1]
        except IndexError:
            return

        for (regex, flag) in parsers:
            match = regex.match(data)
            if match:
                if flag:
                    self.find_method(flag)(flag, data, match)
                return

        print 'Unmatched line: %s' % line[:150]

    def find_method(self, flag):
        return getattr(self, 'line_parser_%s' % flag,
                       getattr(self, 'line_parser_default'))

    def scrub_line(self, line):
        for regex, func in scrubs:
            line = regex.sub(func, line)
        return line

    def line_parser_default(self, flag, line, match):
        md5 = hashlib.md5('%s.%s.%s' %
                          (self.filename, flag, line)).hexdigest()
        try:
            papal = PapalStats.objects.get(md5=md5)
        except PapalStats.DoesNotExist:
            papal = PapalStats(md5=md5)
        line = self.scrub_line(line)
        papal.flag = flag
        papal.data = line
        papal.level = match.group('level')
        filename, date_str = self.filename.split('.')
        papal.server = os.path.basename(filename)
        papal.date = date(*[int(x) for x in date_str.split('-')])
        papal.save()

if __name__=='__main__':
    directory = '/Users/andy/paypal/'
    for fl in os.listdir(directory):
        print 'Parsing: %s' % fl
        p = Parser(os.path.join(directory, fl))
        p.process()
