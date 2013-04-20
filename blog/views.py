from django.shortcuts import render, get_object_or_404
from blog.models import Entry

def entries_index(request):
    return render(request, 'blog/entry_index.html',
                              {'entry_list': Entry.objects.all()})

def entry_detail(request, year, month, day, slug):
    import datetime, time
    date_stamp = time.strptime(year+month+day, "%Y%b%d")
    pub_date = datetime.date(*date_stamp[:3])
    entry = get_object_or_404(Entry, pub_date__year=pub_date.year,
                                     pub_date__month=pub_date.month,
                                     pub_date__day=pub_date.day,
                                     slug=slug)
    return render(request, 'blog/entry_detail.html',
                              {'entry': entry})
