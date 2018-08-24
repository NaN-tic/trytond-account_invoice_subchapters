# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal

from trytond.pool import PoolMeta
from trytond.pyson import Eval

__all__ = ['InvoiceLine']


_ZERO = Decimal('0.0')
_NEW_TYPES = [
    ('total', 'Total'),
    ('subsubtotal', 'Subsubtotal'),
    ('subtitle', 'Subtitle')
    ]


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        for item in _NEW_TYPES:
            if item not in cls.type.selection:
                cls.type.selection.append(item)

        cls.amount.states['invisible'] &= (
            ~Eval('type', '').in_(['subsubtotal', 'total']))

    def get_amount(self, name):
        if self.type not in ('total', 'subtotal', 'subsubtotal'):
            return super(InvoiceLine, self).get_amount(name)
        amount = _ZERO
        for line2 in self.invoice.lines:
            if self == line2:
                break
            if line2.type == 'line':
                amount += line2.invoice.currency.round(
                    Decimal(str(line2.quantity)) * line2.unit_price)
            elif (self.type == 'subsubtotal'
                    and line2.type in ('total', 'subtotal', 'subsubtotal')):
                amount = _ZERO
            elif (self.type == 'subtotal'
                    and line2.type in ('total', 'subtotal')):
                amount = _ZERO
        return amount
