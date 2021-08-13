# --coding:utf-8--
from django.conf.urls import url
from django.urls import path
from apps.goods import views

app_name = 'goods'
urlpatterns = [
    path('index', views.IndexView.as_view(), name='index'),  # 首页
    url(r'^goods/(?P<goods_id>\d+)$', views.DetailView.as_view(), name='detail'),  # 详情页
    url(r'^list/(?P<type_id>\d+)/(?P<page>\d+)$',views.ListView.as_view(),name='list')
]
