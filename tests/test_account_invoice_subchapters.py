# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction

from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account.tests import create_chart, get_fiscalyear
from trytond.modules.account_invoice.tests import set_invoice_sequences


class TestCase(ModuleTestCase):
    'Test module'
    module = 'account_invoice_subchapters'

    @with_transaction()
    def test0010subsubtotal_amount(self):
        'Test subsubtotal line amount'
        pool = Pool()
        Account = pool.get('account.account')
        PaymentTerm = pool.get('account.invoice.payment_term')
        Invoice = pool.get('account.invoice')
        InvoiceLine = pool.get('account.invoice.line')
        Journal = pool.get('account.journal')
        Party = pool.get('party.party')

        # Create Company
        company = create_company()
        with set_company(company):
            # Create Chart and Fiscalyear
            create_chart(company)
            fiscalyear = get_fiscalyear(company)
            fiscalyear = set_invoice_sequences(fiscalyear)
            fiscalyear.save()
            fiscalyear.create_period([fiscalyear])
            journal, = Journal.search([
                    ('code', '=', 'REV'),
                    ])
            revenue, = Account.search([
                    ('type.revenue', '=', True),
                    ])
            receivable, = Account.search([
                    ('type.receivable', '=', True),
                    ])
            expense, = Account.search([
                    ('type.expense', '=', True),
                    ])
            payable, = Account.search([
                    ('type.payable', '=', True),
                    ])

            payment_term, = PaymentTerm.create([{
                        'name': 'Direct',
                        'lines': [('create', [{'type': 'remainder'}])]
                        }])

            customer, = Party.create([{
                        'name': 'customer',
                        'addresses': [
                            ('create', [{}]),
                            ],
                        'account_receivable': receivable.id,
                        'customer_payment_term': payment_term.id,
                        }])

            def create_invoice():
                invoice = Invoice()
                invoice.company = company
                invoice.type = 'out'
                invoice.party = customer
                invoice.invoice_address = customer.addresses[0]
                invoice.currency = company.currency
                invoice.journal = journal
                invoice.account = receivable
                invoice.payment_term = payment_term
                invoice.lines = []
                return invoice

            def create_invoice_line(invoice, line_type):
                invoice_line = InvoiceLine()
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
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
