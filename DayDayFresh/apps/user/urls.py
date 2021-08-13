# --coding:utf-8--
from django.conf.urls import url
from django.urls import path
from apps.user import views
from django.contrib.auth.decorators import login_required

app_name = 'user'
urlpatterns = [
    # path('register/',views.register,name='register'),  # 注册
    # path('register_handle',views.register_handle,name='register_handle') # 注册处理
    path('register', views.RegisterView.as_view(), name='register'),  # 注册处理
    url(r'^active/(?P<token>.*)$', views.ActiveView.as_view(), name='active'),  # 用户激活

    path('login', views.LoginView.as_view(), name='login'),  # 登录
    path('logout', views.LogoutView.as_view(), name='logout'),  # 登出
    # path('',login_required(views.UserInfoView.as_view()),name='user'),  # 用户中心-信息页
    # path('order',login_required(views.UserOrderView.as_view()),name='order'),  # 用户中心-订单页
    # path('address',login_required(views.AddressView.as_view()),name='address'),  # 用户中心地址页
    path('', views.UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    url(r'^order/(?P<page>\d+)$', views.UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    path('address', views.AddressView.as_view(), name='address'),  # 用户中心地址页
]

# login_required的作用：验证访问改装饰器下的url时，是否时登录状态，不是的话返回setting中LOGIN_URL指定的url，这里设置为登陆页面如下
# path('', login_required(views.UserInfoView.as_view()), name='user'),  # 用户中心-信息页
# path('order', login_required(views.UserOrderView.as_view()), name='order'),  # 用户中心-订单页
# path('address', login_required(views.AddressView.as_view()), name='address'),  # 用户中心地址页
# 太麻烦了！ 可以使用utils里面的mixin脚本定义一个装饰类LoginRequiredMixin，然后在view函数中继承时，先继承这个类，后面在url.py中正常写即可
