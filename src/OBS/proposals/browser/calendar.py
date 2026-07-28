'''Override the default Calendar Portlet view to give us dark/grey/light'''

from plone import api
from plone.app.event.portlets.portlet_calendar import Renderer as BaseCalendarRenderer
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from datetime import date, datetime, timedelta
import calendar
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
   base_date = datetime(2000, 1, 6, 18, 14, 0)
   target_date = datetime(year, month, day)
   
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
   if moon_age <= 0.5:
      emoji = "&#127761;"
   elif abs(moon_age-0.25*synodic_month) <= 0.5:
      emoji = "&#127763;"
   elif abs(moon_age-0.5*synodic_month) <= 0.5:
      emoji = "&#127765;"
   elif abs(moon_age-0.75*synodic_month) <= 0.5:
      emoji = "&#127767;"

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


class YearlyCalendarView(BrowserView):
   """Browser view producing a 12-month calendar grid matching Plone Classic UI portlet styling."""

   def __init__(self, context, request):
      super().__init__(context, request)
      self.cal = calendar.Calendar(firstweekday=calendar.SUNDAY)

   @property
   def year(self):
      """Extract requested start year from query string or default to current 
      year."""
      try:
         return int(self.request.get("year", datetime.now().year))
      except (ValueError, TypeError):
         return datetime.now().year

   @property
   def month(self):
      """Extract requested start month from query string or default to current 
      month."""
      try:
         return int(self.request.get("month", datetime.now().month))
      except (ValueError, TypeError):
         return datetime.now().month

   def get_events_map_for_year(self):
      """Queries the portal catalog for events in the selected year.
      Returns a dict mapping (month, day) -> list of event brains.
      """
      start_date = datetime(self.year, self.month, 1, 0, 0, 0)
      if self.month == 1:
         # Jan 1st --> Dec 31st
         end_date = datetime(self.year, 12, 31, 23, 59, 59)
      else:
         # Gotta figure out last day of last month. We'll definitely
         # go into the next year
         last_month = self.month - 1
         last_day = calendar.monthrange(self.year+1,last_month)[1]
         end_date = datetime(self.year+1, last_month, last_day, 23, 59, 59)

      # Query catalog for Events overlapping the target year
      brains = api.portal.get_tool("portal_catalog")(
         portal_type="Event",
         start={"query": end_date, "range": "max"},
         end={"query": start_date, "range": "min"},
         sort_on="start",
      )

      events_by_date = {}
      for brain in brains:
         # Handle start/end attributes
         evt_start = brain.start
         evt_end = brain.end
         if hasattr(evt_start, "asdatetime"):
            evt_start = evt_start.asdatetime()
         if hasattr(evt_end, "asdatetime"):
            evt_end = evt_end.asdatetime()

         # Map event to every day it active/spans in the target year
         curr = max(evt_start.date(), start_date.date())
         limit = min(evt_end.date(), end_date.date())

         while curr <= limit:
            key = (curr.year, curr.month, curr.day)
            events_by_date.setdefault(key, []).append(brain)
            curr = curr + timedelta(days=1)
            #if curr.day < calendar.monthrange(curr.year, curr.month)[1]:
            #   curr = curr.replace(day=curr.day + 1)
            #else: 
            #   curr = curr.replace(month=curr.month + 1, day=1)

      return events_by_date

   def months_data(self):
      """Generates structured data for rendering each month."""
      events_map = self.get_events_map_for_year()
      portal_url = api.portal.get().absolute_url()
      today = datetime.now().date()

      months = []
      # Loop over 12 months
      for m in range(0, 12):
         month = self.month + m
         year = self.year
         if month > 12:
            month = month - 12
            year = self.year + 1
         month_name = calendar.month_name[month]
         month_days = self.cal.monthdatescalendar(year, month)

         weeks = []
         for week in month_days:
            days_in_week = []
            for d in week:
               in_month = d.month == month
               is_today = (d == today)
               phase_info = get_lunar_phase(d.year, d.month, d.day)
               day_events = events_map.get((d.year, d.month, d.day), []) \
                  if in_month else []

               # Build link: Direct event link if single event, search query if multiple
               day_url = None
               klass = ""
               if day_events:
                  if len(day_events) == 1:
                     day_url = day_events[0].getURL()
                  else:
                     day_url = f"{portal_url}/@@search?portal_type=Event&"\
                                "start.query:record:list:date={d.isoformat()}"\
                                "&start.range:record=min"
                  # Figure out if Light or Dark time.
                  for event in day_events:
                     res = dl_pat.search(event.Title)
                     if res:
                        year,dl,run = res.groups()
                     if dl == "D":
                        klass = "dark-run"
                     else:
                        klass = "light-run"
          
               days_in_week.append({
                  "day": d.day,
                  "in_month": in_month,
                  "is_today": is_today,
                  "has_events": len(day_events) > 0,
                  "events_count": len(day_events),
                  "url": day_url,
                  "class":klass,
                  "emoji":phase_info['emoji']
               })
            weeks.append(days_in_week)

         months.append({
            "number": month,
            "name": month_name,
            "weeks": weeks,
         })

      return months        