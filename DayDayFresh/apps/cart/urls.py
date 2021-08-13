# --coding:utf-8--
from django.conf.urls import url
from django.urls import path
from apps.cart import views
app_name = 'cart'
urlpatterns = [
    url(r'^add$',views.CartAddView.as_view(), name='add'),  # 购物车记录添加
    path('',views.CartInfoView.as_view(),name='show'),  # 购物车详情页面
    url(r'^update$',views.CartUpdateView.as_view(),name='update'),  # 更新购物车地址
    url(r'^delete$',views.CartDeletaView.as_view(),name='delete'),  # 删除购物车地址
]