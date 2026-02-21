"""Shared format constants for worksheet tabs."""

HEADER_FORMAT = {
    'horizontalAlignment': 'CENTER',
    'textFormat': {'fontSize': 10, 'bold': True},
}

CURRENCY_FORMAT = {'numberFormat': {'type': 'CURRENCY', 'pattern': '$#,##0'}}
PERCENT_FORMAT = {'numberFormat': {'type': 'PERCENT', 'pattern': '#0.0#%'}}
LEFT_ALIGN = {'horizontalAlignment': 'LEFT'}
RIGHT_ALIGN = {'horizontalAlignment': 'RIGHT'}
CENTER_ALIGN = {'horizontalAlignment': 'CENTER'}

BETTER_PICK_NOTE = 'A movie is considered a better pick if it was drafted after by a different drafter and made more revenue (adjusted for multiplier).'
STILL_IN_THEATERS_NOTE = 'A movie is considered still in theaters if the first record is within the last week or the revenue has changed in the last week.'
