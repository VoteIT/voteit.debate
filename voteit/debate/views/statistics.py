import csv
from datetime import timedelta
from decimal import Decimal

from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.view import view_config
from voteit.core import security
from voteit.core.models.interfaces import IMeeting
from voteit.debate.views.base import BaseSLView
from six import StringIO
try:
    from voteit.irl.plugins.gender import GenderStatistics
except ImportError:
    GenderStatistics = None

from voteit.debate import _
from voteit.debate.fanstaticlib import voteit_debate_gender_statistics_css


class StatisticsView(BaseSLView):

    @view_config(name="speaker_statistics", context=IMeeting, permission=security.VIEW,
                 renderer="voteit.debate:templates/speaker_statistics.pt")
    def speaker_statistics_view(self):
        response = {}
        response['number_to_userid'] = self.participant_numbers.number_to_userid
        results = {}
        maxval = 0
        for sl in self.request.speaker_lists.values():
            for (pn, entries) in sl.speaker_log.items():
                current = results.setdefault(pn, [])
                current.extend(entries)
                this_val = sum(current)
                if this_val > maxval:
                    maxval = this_val
        response['results'] = [(x, results[x]) for x in sorted(results)]

        def _get_percentage(num):
            try:
                return int(round(Decimal(num) / maxval * 100))
            except:
                return 0

        response['get_perc'] = _get_percentage
        response['has_gender_stats'] = 'voteit.irl.plugins.gender' in self.request.registry.settings.get('plugins', '')
        response['seconds_to_time'] = lambda s: timedelta(seconds=int(s))
        return response

    @view_config(name='speaker_statistics.csv', context=IMeeting, permission=security.VIEW)
    def export(self):
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([self.context.title.encode('utf-8')])
        writer.writerow([self.request.localizer.translate(_(u"Speaker statistics"))])
        writer.writerow(["#", self.request.localizer.translate(_(u"Seconds"))])
        for sl in self.request.speaker_lists.values():
            if not len(sl.speaker_log):
                continue
            writer.writerow([""])
            writer.writerow([sl.title.encode('utf-8')])
            for (pn, entries) in sl.speaker_log.items():
                for entry in entries:
                    writer.writerow([pn, entry])
        contents = output.getvalue()
        output.close()
        return Response(content_type='text/csv', body=contents)

    @view_config(name="gender_statistics", context=IMeeting, permission=security.VIEW,
                 renderer="voteit.debate:templates/gender_statistics.pt")
    def gender_statistics_view(self):
        if GenderStatistics is None:
            raise HTTPNotFound("GenderStatistics plugin not found in voteit.irl")
        voteit_debate_gender_statistics_css.need()
        results = {
            'expected': GenderStatistics(),
            'entries': GenderStatistics(),
            'people': GenderStatistics(),
            'time': GenderStatistics(),
            'seconds_to_time': lambda s: timedelta(seconds=int(s)),
        }
        pn2u = self.participant_numbers.number_to_userid
        users = self.request.root['users']
        for sl in self.request.speaker_lists.values():
            for (pn, entries) in sl.speaker_log.items():
                userid = pn2u.get(pn)
                gender = ''
                if userid:
                    try:
                        gender = users[userid].gender
                    except (KeyError, AttributeError):
                        pass
                results['entries'].add(gender, len(entries))
                results['people'].add(gender, 1)
                results['time'].add(gender, sum(entries))
        for userid in pn2u.values():
            try:
                gender = users[userid].gender
                results['expected'].add(gender, 1)
            except (KeyError, AttributeError):
                pass
        return results


def includeme(config):
    config.scan(__name__)


#FIXME
#More suitable as view code
# def get_stats(self, pn, sl, format = True):
#     assert isinstance(pn, int)
#     assert ISpeakerList.providedBy(sl)
#     if pn not in sl.speaker_log:
#         return (0, 0)
#     time = sum(sl.speaker_log[pn])
#     if format:
#         time = unicode(timedelta(seconds = time))
#     return (len(sl.speaker_log[pn]), time)
