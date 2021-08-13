# --coding:utf-8--
from django.conf.urls import url
from apps.order import views
app_name = 'order'
urlpatterns = [
    url(r'^place$', views.OrderPlaceView.as_view(), name='place'),  # 提交订单页面显示
    url(r'^commit$',views.OrderCommitView.as_view(),name='commit'),  # 订单创建
    url(r'^pay$',views.OrderPayView.as_view(),name='pay'),  # 订单支付
    url(r'^check$',views.CheckPayView.as_view(),name='check'), # 订货查询结果
    url(r'^comment/(?P<order_id>.+)$', views.CommentView.as_view(), name='comment'),
]