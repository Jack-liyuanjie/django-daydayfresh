from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from utils.mixin import LoginRequiredMixin


# Create your views here.

# 添加商品到购物车：
# 1) 请求方式，采用ajax,post
# 如果涉及到数据的修改(新增，更新，删除)，采用post
# 如果只涉及到数据获取，采用get
# 2) 传递参数：商品id(sku_id),商品数量(count)
# /cart/add
class CartAddView(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    '''购物车记录添加'''

    def post(self, request):
        '''购物车记录添加'''
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据检验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 检验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：添加啊购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 先尝试获取sku_id的值 -> hget cart_key 属性
        # 如果sku_id在hash中不存在，hget返回None
        cart_count = conn.hget(cart_key, sku_id)
        if cart_count:
            # 累加购物车中商品的数量
            count += int(cart_count)

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 设置hash中sku_id对应的值
        # hset->如果sku_id已经存在，更新数据，如果sku_id不存在，添加数据
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的条目数
        total_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '添加成功', 'total_count': total_count})


class CartInfoView(LoginRequiredMixin, View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    '''购物车页面显示'''

    def get(self, request):
        '''显示'''
        # 获取登录用户
        user = request.user
        # 获取用户购物车中的商品信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # {'商品id':商品数量}
        cart_dict = conn.hgetall(cart_key)
        print(cart_dict)
        print(cart_dict.items())

        skus = []
        # 保存用户购物车中商品的总数目和总价格
        total_count = 0
        total_price = 0
        # 遍历获取商品信息
        for sku_id, count in cart_dict.items():
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku对象增加一个属性amount,保存商品的小计
            sku.amount = amount
            # 动态给sku对象增加一个属性count，保存购物车中对应商品的数量
            sku.count = int(count)
            # 添加
            skus.append(sku)

            # 累加计算商品的总数目和总价格
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {'total_count': total_count,
                   'total_price': total_price,
                   'skus': skus}

        return render(request, 'cart.html', context)


# 更新购物车记录
# 采用ajax post请求
# 前端需要传递的参数：商品id(sku_id) 更新的商品数目(count)
# /cart/update
class CartUpdateView(View):
    '''购物车记录更新'''

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        '''购物车记录更新'''
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据检验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 检验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：更新购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart%d' % user.id

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 更新
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的总件数{'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '更新成功', 'total_count': total_count})

class CartDeletaView(View):
    '''购物车记录的删除'''

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self,request):
        '''购物车记录删除'''
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 数据校验
        if not sku_id:
            return JsonResponse({'res':1, 'errmsg':'无效的商品id'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res':2, 'errmsg':'商品不存在'})

        # 业务处理：删除购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 删除 hdel
        conn.hdel(cart_key, sku_id)

        # 计算用户购物车中商品的总件数{'1':5, '2':3}
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res':3, 'message':'删除成功','total_count':total_count})

