'''Override the default Calendar Portlet view to give us dark/grey/light'''

from plone.app.event.portlets.portlet_calendar import Renderer as BaseCalendarRenderer
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
import datetime
from math import floor
import re

dl_pat = re.compile('([0-9]{4,4})_([DL])([0-9]{2,2})')

# Compute Lunar phase

def phase_to_rgb(phase: float) -> str:
    '''Given phase as 0 --> 1, convert to a grey scale.
    Note that 0/1 is dark, 0.5 is bright'''
    dec_val = int(floor((1 - 2*abs(phase-0.5))*255))
    hex_val = hex(dec_val).split('x')[1].upper()    
    return "#{}{}{}".format(hex_val,hex_val,hex_val)


def get_lunar_phase(year: int, month: int, day: int) -> dict:
    """Calculates the approximate moon phase and returns phase information."""
    # Known New Moon reference point: January 6, 2000
    base_date = datetime.datetime(2000, 1, 6, 18, 14, 0)
    target_date = datetime.datetime(year, month, day)
    
    # Calculate days elapsed since the reference base date
    diff = target_date - base_date
    days_elapsed = diff.total_seconds() / 86400.0
    
    # Synodic month length (average time between two identical moon phases)
    synodic_month = 29.530588853
    
    # Position in the current cycle (0.0 to 1.0)
    cycle_position = (days_elapsed / synodic_month) % 1.0
    if cycle_position < 0:
        cycle_position += 1.0
        
    # Age of the moon in days
    moon_age = cycle_position * synodic_month

    # See if we are at any transitions
    emoji = ""
    if moon_age < 1:
        emoji = "&127761;"
    elif abs(moon_age-0.25*synodic_month) < 1:
        emoji = "&127763;"
    elif abs(moon_age-0.5*synodic_month) < 1:
        emoji = "&127765;"
    elif abs(moon_age-0.75*synodic_month) < 1:
        emoji = "&127767;"

    color = phase_to_rgb(cycle_position)
    
    # Map cycle position to text labels
    if cycle_position < 0.167 or cycle_position > 0.833:
        phase_name = "dark"
    elif cycle_position < 0.375 or cycle_position > 0.625:
        phase_name = "gray"
    else:
        phase_name = "bright"

    return {
        "cycle_position": round(cycle_position, 4),
        "moon_age_days": round(moon_age, 2),
        "phase_name": phase_name,
        "emoji": emoji
    }


class MyCustomCalendarRenderer(BaseCalendarRenderer):
    # Bind to a custom template (or omit if using the default markup)
    render = ViewPageTemplateFile('custom_calendar.pt')

    def update(self):
        # Always invoke the parent update to populate base calendar variables
        super().update()
        # Your custom setup logic goes here

    def darkness(self, events):
        """Check for dark or light runs and color accordingly"""
        if not events:
            return "background-color: #FFFFFF;"
        for event in events:
            title = event.Title()
            res = dl_pat.search(title)
            if res:
                year,dl,run = res.groups()
            if dl == "D":
                # dark run
                return 'background-color: #AAAAAA;'
            else:
                return 'background-color: #DDDDDD;'
            
        return "background-color: #FFFFFF;"

        

