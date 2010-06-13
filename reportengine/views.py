from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.core.paginator import Paginator
from django.contrib.admin.views.main import ALL_VAR,ORDER_VAR, PAGE_VAR
import reportengine
from urllib import urlencode

# TODO add calendar view for date-ranged reports

# TODO Maybe use a class based view? how do i make it easy to build SQLReports?
def report_list(request):
    r = reportengine.all_reports()
    return render_to_response('reportengine/list.html', {'reports': r}, 
                              context_instance=RequestContext(request))

def view_report(request, slug):
    report = reportengine.get_report(slug)()
    params=dict(request.REQUEST)

    order_by=params.pop(ORDER_VAR,None)

    page,per_page=0,report.per_page
    try:
        page=int(params.pop(PAGE_VAR,0))
    except ValueError:
        pass # ignore bogus page/per_page

    # TODO put together filters here (use forms?)
    filters=params

    rows,aggregates = report.get_rows(filters,order_by=order_by)

    paginator=None
    cl=None
    if per_page:
        paginator=Paginator(rows,per_page)
        p=paginator.page(page+1)
        rows=p.object_list

        # HACK: fill up a fake ChangeList object to use the admin paginator
        class MiniChangeList:
            def __init__(self,paginator,page,per_page,params):
                self.paginator=paginator
                self.page_num=page
                self.show_all=report.can_show_all
                self.can_show_all=False
                self.multi_page=True
                self.params=params

            def get_query_string(self,new_params=None,remove=None):
                # Do I need to deal with new_params/remove?
                if remove != None:
                    for k in remove:
                        del self.params[k]
                if new_params != None:
                    self.params.update(new_params)
                return "?%s"%urlencode(self.params)

        cl_params=order_by and dict(params,order_by=order_by) or params
        cl=MiniChangeList(paginator,page,per_page,cl_params)

    data = {'report': report, 
            'title':report.verbose_name,
            'rows':rows,
            "aggregates":aggregates,
            "paginator":paginator,
            "cl":cl,
            "page":page}

    return render_to_response('reportengine/view.html', data, 
                              context_instance=RequestContext(request))


