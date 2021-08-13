from django.http import HttpResponse
from django.shortcuts import render, redirect
import re
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.mail import send_mail
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate,login,logout
from utils.mixin import LoginRequiredMixin

from django.core.paginator import Paginator
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from user.models import User,Address
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection

# Create your views here.
# @csrf_exempt
# def register(request):
#     '''注册'''
#     if request.Method == 'GET':
#         return render(request, 'register.html')
#     else:
#         '''进行注册处理'''
#         # 接收数据
#         username = request.POST.get('user_name')
#         password = request.POST.get('pwd')
#         cpassword = request.POST.get('cpwd')
#         email = request.POST.get('email')
#         allow = request.POST.get('allow')
#         # 进行数据校验
#         if not all([username, password, email]):
#             # 数据不完整
#             return render(request, 'register.html', {'errmsg': '数据不完整'})
#
#         # 2次密码是否相同
#         if password != cpassword:
#             return render(request, 'register.html', {'errmsg': '2次密码不一致'})
#
#         # 校验邮箱
#         if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#             return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
#
#         # 判断用户名是否存在
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             # 用户名不存在
#             user = None
#         if user:
#             # 用户名已存在
#             return render(request, 'register.html', {'errmsg': '用户名已存在'})
#
#         # 判断是否同意用户协议
#         if allow != 'on':
#             return render(request, 'register.html', {'errmsg': '请同意用户协议'})
#         # 进行业务处理：进行用户注册
#         user = User.objects.create_user(username, password, email)
#         user.is_active = 0
#         user.save()
#         # 返回应答,跳转首页
#         return redirect(reverse('goods:index'))


'''同一个url处理就不需要下面这个'''
# @csrf_exempt
# def register_handle(request):
#     '''进行注册处理'''
#     # 接收数据
#     username = request.POST.get('user_name')
#     password = request.POST.get('pwd')
#     cpassword = request.POST.get('cpwd')
#     email = request.POST.get('email')
#     allow = request.POST.get('allow')
#     # 进行数据校验
#     if not all([username, password, email]):
#         # 数据不完整
#         return render(request, 'register.html', {'errmsg': '数据不完整'})
#
#     # 2次密码是否相同
#     if password != cpassword:
#         return render(request, 'register.html', {'errmsg': '2次密码不一致'})
#
#     # 校验邮箱
#     if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#         return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
#
#     # 判断用户名是否存在
#     try:
#         user = User.objects.get(username=username)
#     except User.DoesNotExist:
#         # 用户名不存在
#         user = None
#     if user:
#         # 用户名已存在
#         return render(request, 'register.html', {'errmsg': '用户名已存在'})
#
#     # 判断是否同意用户协议
#     if allow != 'on':
#         return render(request, 'register.html', {'errmsg': '请同意用户协议'})
#     # 进行业务处理：进行用户注册
#     user = User.objects.create_user(username, password, email)
#     user.is_active = 0
#     user.save()
#     # 返回应答,跳转首页
#     return redirect(reverse('goods:index'))


'''如何用类试图处理呢'''


class RegisterView(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        '''进行注册处理'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 2次密码是否相同
        if password != cpassword:
            return render(request, 'register.html', {'errmsg': '2次密码不一致'})

        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        # 判断用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 判断是否同意用户协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意用户协议'})

        # 进行业务处理：进行用户注册
        user = User.objects.create_user(username=username, password=password, email=email)
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/3
        # 激活链接中需要包含用户的身份信息,并且要把身份信息加密，如何加密呢？使用itsdangerous

        # 加密用户的身份信息，生成激活的token
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info).decode()

        # 发邮件 这里使用celery+redis异步处理
        # subject = '天天生鲜欢迎信息'
        # message = '您好'
        # html_message = '<h1>%s 欢迎您成为天天生鲜注册会员</h1>' \
        #                '请点击下面链接激活您的账户<br/>' \
        #                '<a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
        #                    username, token, token)
        # sender = settings.EMAIL_FROM
        # receiver = [email,'Jack_liyuanjie@163.com']
        #
        # send_mail(subject, message, sender, receiver,html_message=html_message)
        send_register_active_email.delay(email,username,token)

        # 返回应答,跳转首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''

    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的id
            user_id = info['confirm']

            # 根据用户id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转对的登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired:
            # 激活链接已过期
            return HttpResponse('激活链接已过期')


# /user/login
class LoginView(View):
    '''登录'''
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        '''显示登陆页面'''
        # 判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html',{'username':username,'checked':checked})

    def post(self,request):
        '''登录校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # 校验数据
        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'数据不完整'})

        # 业务处理：登录校验
        user = authenticate(username=username,password=password)
        # 注意authenticate的使用，django内置的验证方法，可以直接匹配df_user表中的注册消息, django2.1好像有bug，
        # 在setting中加入AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.AllowAllUsersModelBackend']

        if user is not None:
            # 用户名和密码正确
            if user.is_active:
                # 用户已激活
                # 记录用户的登录状态
                login(request,user)  # 注意login的使用，django内置的保存用户登录session的消息，但是这个保存在数据库中每次要用都要读数据库，这时候可以使用redis缓存cache

                # 获取登陆后所要跳转的地址
                # 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到首页
                response = redirect(next_url)  # HttpResponseRedirect

                # 判断是否需要记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                # 返回response
                return response

            else:
                # 用户未激活
                return render(request,'login.html',{'errmsg':'账户未激活'})
        else:
            # 用户名或密码错误
            return render(request,'login.html',{'errmsg':'用户名或密码错误'})


# /user/logout
class LogoutView(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self,request):
        '''退出登录'''
        # 清除用户的session信息
        logout(request)

        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequiredMixin,View):
    '''登录'''
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    '''用户中心-信息页'''
    def get(self,request):
        '''显示'''
        # request.user.is_authenticated()
        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        # 如果用户未登录，request.user->AnonymousUser类的一个实列，返回False
        # 如果用户登录，request.user->User类的一个实列,返回True

        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # -----------------------------------------------------------中间这段没搞懂
        # 获取用户的历史浏览数据
        # from redis import StrictRedis
        # StrictRedis(host='116.62.193.152',port='6379',db=10)
        con = get_redis_connection('default')

        history_key = 'history_%d'%user.id

        # 获取用户最新浏览的5条商品id
        sku_ids = con.lrange(history_key, 0, 4)

        # 遍历获取用户浏览的信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)
        # -----------------------------------------------------------中间这段没搞懂
        # 组织上下文
        context = {
            'page':'user',
            'goods_li':goods_li
        }
        return render(request,'user_center_info.html',locals())


# /user/order
class UserOrderView(LoginRequiredMixin,View):
    '''登录'''

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    '''用户中心-订单页'''
    def get(self, request, page):
        '''显示'''
        # 获取用户的订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count*order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page':order_page,
                   'pages':pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


# /user/address
class AddressView(LoginRequiredMixin,View):
    '''登录'''

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''
        # 获取登录用户对于的User对象
        user = request.user

        # 获取用户的默认收货地址‘
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)
        page = 'address'
        return render(request, 'user_center_site.html',locals())

    def post(self,request):
        '''地址添加'''
        # 接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver,addr,phone]):
            return render(request,'user_center_site.html',{'errmsg':'数据不完整'})

        # 校验手机号
        if not re.match(r'^1[|3|4|5|7|8][0-9]{9}$',phone):
            return render(request,'user_center_site.html',{'errmsg':'手机格式不正确'})

        # 业务处理：添加地址
        # 如果用户已经存在默认地址，则添加的地址不作为默认地址，否则作为默认地址
        # 获取登录用户对应的User对象
        user = request.user

        # try:
        #     address = Address.objects.get(user=user,is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认地址
        #     address = None
        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,addr=addr,receiver=receiver,zip_code=zip_code,phone=phone,is_default=is_default)

        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))  # get请求方式
