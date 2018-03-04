import csv
from decimal import Decimal

from pyramid.response import Response
from pyramid.view import view_config
from voteit.core import security
from voteit.core.models.interfaces import IMeeting
from voteit.debate.views.base import BaseSLView
from six import StringIO

from voteit.debate import _


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
                return u"0%"

        response['get_perc'] = _get_percentage
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


def includeme(config):
    config.scan(__name__)
