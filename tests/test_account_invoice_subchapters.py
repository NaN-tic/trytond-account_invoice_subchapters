# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import doctest
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_depends
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('account_invoice_subchapters')
        self.account = POOL.get('account.account')
        self.company = POOL.get('company.company')
        self.invoice = POOL.get('account.invoice')
        self.invoice_line = POOL.get('account.invoice.line')
        self.journal = POOL.get('account.journal')
        self.party = POOL.get('party.party')
        self.payment_term = POOL.get('account.invoice.payment_term')
        self.user = POOL.get('res.user')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010subsubtotal_amount(self):
        'Test subsubtotal line amount'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            journal, = self.journal.search([
                    ('code', '=', 'REV'),
                    ])
            receivable, = self.account.search([
                ('kind', '=', 'receivable'),
                ('company', '=', company.id),
                ])
            revenue, = self.account.search([
                ('kind', '=', 'revenue'),
                ('company', '=', company.id),
                ])
            payment_term, = self.payment_term.create([{
                        'name': 'Payment Term',
                        'lines': [
                            ('create', [{
                                        'sequence': 0,
                                        'type': 'remainder',
                                        'months': 0,
                                        'days': 0,
                                        }])]
                        }])
            customer, = self.party.create([{
                        'name': 'customer',
                        'addresses': [
                            ('create', [{}]),
                            ],
                        'account_receivable': receivable.id,
                        'customer_payment_term': payment_term.id,
                        }])

            def create_invoice():
                invoice = self.invoice()
                invoice.company = company
                invoice.type = 'out_invoice'
                invoice.party = customer
                invoice.invoice_address = customer.addresses[0]
                invoice.currency = company.currency
                invoice.journal = journal
                invoice.account = receivable
                invoice.payment_term = payment_term
                invoice.lines = []
                return invoice

            def create_invoice_line(invoice, line_type):
                invoice_line = self.invoice_line()
                invoice.lines = list(invoice.lines) + [invoice_line]
                invoice_line.company = company
                invoice_line.type = line_type
                if line_type == 'line':
                    invoice_line.quantity = 1
                    invoice_line.account = revenue
                    invoice_line.unit_price = 10
                    invoice_line.description = 'Normal line'
                elif line_type in ('title', 'subtitle'):
                    invoice_line.description = 'Title line'
                elif line_type in ('subtotal', 'subsubtotal'):
                    invoice_line.description = 'Subtotal line'

            # Invoice with 1 subtotal line
            invoice1 = create_invoice()
            create_invoice_line(invoice1, 'line')
            create_invoice_line(invoice1, 'line')
            create_invoice_line(invoice1, 'subtotal')
            create_invoice_line(invoice1, 'line')
            invoice1.save()
            self.assertEqual(invoice1.lines[-2].amount, Decimal('20'))

            # Invoice with 1 subsubtotal line
            invoice2 = create_invoice()
            create_invoice_line(invoice2, 'line')
            create_invoice_line(invoice2, 'line')
            create_invoice_line(invoice2, 'subsubtotal')
            create_invoice_line(invoice2, 'line')
            invoice2.save()
            self.assertEqual(invoice2.lines[-2].amount, Decimal('20'))

            # Invoice with 1 subsubtotal and 1 subtotal
            invoice3 = create_invoice()
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'subsubtotal')
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'subtotal')
            create_invoice_line(invoice3, 'line')
            invoice3.save()
            self.assertEqual(invoice3.lines[2].amount, Decimal('20'))
            self.assertEqual(invoice3.lines[-2].amount, Decimal('40'))

            # Invoice with 1 subtotal and 1 subsubtotal
            invoice3 = create_invoice()
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'subtotal')
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'line')
            create_invoice_line(invoice3, 'subsubtotal')
            create_invoice_line(invoice3, 'line')
            invoice3.save()
            self.assertEqual(invoice3.lines[2].amount, Decimal('20'))
            self.assertEqual(invoice3.lines[-2].amount, Decimal('20'))

            # Invoice with some subtotals and subsubtotals
            invoice4 = create_invoice()
            create_invoice_line(invoice4, 'title')
            create_invoice_line(invoice4, 'subtitle')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'subsubtotal')
            create_invoice_line(invoice4, 'subtitle')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'subsubtotal')
            create_invoice_line(invoice4, 'subtotal')
            create_invoice_line(invoice4, 'title')
            create_invoice_line(invoice4, 'subtitle')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'subsubtotal')
            create_invoice_line(invoice4, 'subtitle')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'line')
            create_invoice_line(invoice4, 'subsubtotal')
            create_invoice_line(invoice4, 'subtotal')
            invoice4.save()
            self.assertEqual(invoice4.lines[4].amount, Decimal('20'))
            self.assertEqual(invoice4.lines[9].amount, Decimal('30'))
            self.assertEqual(invoice4.lines[10].amount, Decimal('50'))
            self.assertEqual(invoice4.lines[14].amount, Decimal('10'))
            self.assertEqual(invoice4.lines[-2].amount, Decimal('50'))
            self.assertEqual(invoice4.lines[-1].amount, Decimal('60'))


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    from trytond.modules.account.tests import test_account
    for test in test_account.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
